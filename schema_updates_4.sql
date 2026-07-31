"""
db/migrate_from_sheets.py
===========================
Script de migración Sheet -> Cloud SQL. Versión robusta: además de
volcar los datos, LIMPIA los problemas típicos de un Sheet que lleva
años editándose a mano:

  - "#N/A", "#REF!", "#DIV/0!" en columnas numéricas -> NULL
  - Booleanos con espacios en blanco o vacíos -> NULL (no revienta el INSERT)
  - Fechas en formato DD/MM/YYYY (como las escribe Google Sheets en
    español) -> se convierten a formato ISO antes de insertar, porque
    Postgres por defecto espera MM/DD/YYYY y si no, revienta con
    "date/time field value out of range"
  - IDs duplicados en la primera columna (que se asume PK) -> se les
    agrega un sufijo automático para no perder la fila, y se listan al
    final para que decidas si hay que corregir el dato en el Sheet

CÓMO CORRERLO (sin entorno local, todo desde Cloud Shell / GitHub):
  1. Abre un túnel a Cloud SQL con cloud-sql-proxy (ver DOCUMENTATION.md).
  2. Define las variables de entorno: SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
     DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME.
  3. python3 -m db.migrate_from_sheets

Es idempotente por tabla: TRUNCATE + INSERT, se puede correr las veces
que haga falta sin duplicar datos.
"""

import os
import re
import json
import time
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
import sqlalchemy

SHEET_NAMES = [
    "USUARIOS", "CONFIG", "ACTIVOS", "JERARQUIA_TECNICA", "AVERIAS",
    "SOLUCIONES_AVERIA", "NOVEDADES", "NOV_DETALLE", "NOV_EVIDENCIAS",
    "CAUSAS_FALLA", "OT", "OT_TIEMPOS", "OT_REPUESTOS", "OT_EVIDENCIAS",
    "REPUESTOS", "PARAM_CHEQUEOS", "PARAM_VERSIONES", "HISTORIAL_VERSIONES",
    "DOCS", "MAQUILADORES", "MAQUILAS", "Nodisponibles", "ALISTAMIENTO",
    "MONTAJES", "TAREAS_PROGRAMADAS",
]

MARCADORES_VACIOS = {"#N/A", "#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "N/A", "-"}
FORMATOS_FECHA = [
    "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
]


def pgname(h: str) -> str:
    h = h.strip()
    for a, b in zip("ÁÉÍÓÚÑ", "AEIOUN"):
        h = h.replace(a, b)
    h = re.sub(r"[^A-Za-z0-9_]+", "_", h)
    h = re.sub(r"_+", "_", h).strip("_").lower()
    return h


def guess_type(col: str) -> str:
    """Debe coincidir con la lógica que generó schema.sql."""
    c = col.upper()
    if c.startswith("ID_") or c == "ID":
        return "VARCHAR"
    if "FECHA" in c or c.endswith("_EN"):
        return "TIMESTAMP"
    if c in ("ACTIVO", "RESUELTO", "SOLICITA_CIERRE"):
        return "BOOLEAN"
    if c in ("STOCK", "STOCK_MINIMO", "CANTIDAD", "MINUTOS", "TIEMPO_MINUTOS",
              "TIEMPO_EMPLEADO_MIN", "MINUTOS_TOTALES", "TIEMPO_EVENTOS_MIN",
              "UNIDADES_INYECTADAS", "UNDS", "CICLOSACTUALES", "CICLOS_ULT_MANT",
              "FRECUENCIA_MANT", "CICLOS_DESDE_MANT", "CICLOS_PARA_MANT", "PESO"):
        return "NUMERIC"
    return "TEXT"


def limpiar_valor(valor: str, tipo: str):
    valor = (valor or "").strip()
    if not valor or valor.upper() in MARCADORES_VACIOS:
        return None

    if tipo == "BOOLEAN":
        v = valor.strip().upper()
        if v in ("TRUE", "1", "X", "SI", "SÍ", "YES"):
            return True
        if v in ("FALSE", "0", "NO"):
            return False
        return None  # ambiguo (ej: un solo espacio) -> NULL, no revienta el insert

    if tipo == "NUMERIC":
        try:
            return float(valor.replace(",", "."))
        except ValueError:
            return None

    if tipo == "TIMESTAMP":
        for fmt in FORMATOS_FECHA:
            try:
                return datetime.strptime(valor, fmt).isoformat()
            except ValueError:
                continue
        return None  # no se pudo parsear -> NULL en vez de reventar el INSERT

    return valor


def get_sheet_client():
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)


def get_pg_engine():
    user = os.environ["DB_USER"]
    pwd = os.environ["DB_PASS"]
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    url = f"postgresql+pg8000://{user}:{pwd}@{host}:{port}/{name}"
    return sqlalchemy.create_engine(url)


def migrate_sheet(gc, engine, sheet_id: str, sheet_name: str) -> list[str]:
    """Devuelve la lista de IDs que tuvieron que de-duplicarse (para el resumen final)."""
    table = pgname(sheet_name)
    print(f"→ Migrando {sheet_name} -> tabla `{table}`")

    ws = gc.open_by_key(sheet_id).worksheet(sheet_name)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        print("  (vacía, se omite)")
        return []

    headers_originales = [h for h in values[0] if h.strip()]
    headers = [pgname(h) for h in headers_originales]
    tipos = [guess_type(h) for h in headers_originales]
    rows = values[1:]

    duplicados_encontrados = []

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(f"TRUNCATE TABLE {table} CASCADE"))

        insert_sql = sqlalchemy.text(
            f"INSERT INTO {table} ({', '.join(headers)}) "
            f"VALUES ({', '.join(':' + h for h in headers)})"
        )

        batch = []
        ids_vistos = set()
        pk_col = headers[0]  # se asume que la primera columna es la PK, como en schema.sql

        for row in rows:
            if not any(cell.strip() for cell in row):
                continue  # fila vacía

            record = {}
            for i, h in enumerate(headers):
                crudo = row[i] if i < len(row) else ""
                record[h] = limpiar_valor(crudo, tipos[i])

            # de-duplicar la PK si se repite, para no perder la fila
            pk_val = record.get(pk_col)
            if pk_val is not None:
                pk_original = pk_val
                contador = 2
                while pk_val in ids_vistos:
                    pk_val = f"{pk_original}_DUP{contador}"
                    contador += 1
                if pk_val != pk_original:
                    duplicados_encontrados.append(f"{table}.{pk_col}: {pk_original} -> {pk_val}")
                    record[pk_col] = pk_val
                ids_vistos.add(pk_val)

            batch.append(record)

        if batch:
            conn.execute(insert_sql, batch)

    print(f"  ✔ {len(batch)} filas migradas" +
          (f" ({len(duplicados_encontrados)} de-duplicadas)" if duplicados_encontrados else ""))
    return duplicados_encontrados


def main():
    sheet_id = os.environ["SHEET_ID"]
    gc = get_sheet_client()
    engine = get_pg_engine()

    todos_los_duplicados = []

    for name in SHEET_NAMES:
        try:
            duplicados = migrate_sheet(gc, engine, sheet_id, name)
            todos_los_duplicados.extend(duplicados)
        except Exception as e:
            print(f"  ✘ ERROR en {name}: {e}")
        time.sleep(2)  # evita el límite de cuota de lectura de Google Sheets

    print("\nMigración terminada.")
    if todos_los_duplicados:
        print(f"\n⚠️  Se de-duplicaron {len(todos_los_duplicados)} ID(s) repetidos "
              "(la fila se conservó, pero revisa si el dato original está bien):")
        for d in todos_los_duplicados:
            print(f"   - {d}")


if __name__ == "__main__":
    main()
