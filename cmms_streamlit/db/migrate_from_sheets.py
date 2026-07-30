"""
db/migrate_from_sheets.py
===========================
Script de UNA sola ejecución para volcar los datos actuales del Google
Sheet (fuente de verdad hoy) hacia Cloud SQL (fuente de verdad futura).

CÓMO CORRERLO (sin entorno local, todo desde GitHub):
  1. Sube este repo a GitHub.
  2. Créalo como un GitHub Codespace, o usa un workflow de GitHub Actions
     manual (workflow_dispatch) que instale requirements.txt y corra:
         python -m db.migrate_from_sheets
  3. Variables de entorno necesarias (Secrets del repo/Codespace):
       GOOGLE_SERVICE_ACCOUNT_JSON   -> JSON de la cuenta de servicio con
                                        permiso de LECTURA sobre el Sheet
       SHEET_ID                     -> ID del Google Sheet origen
       (+ las mismas variables de conexión a Cloud SQL que usa la app,
        ver .streamlit/secrets.toml.example; aquí se leen de env, no de
        st.secrets, porque este script corre fuera de Streamlit)

Qué hace:
  - Lee cada hoja del Sheet (mismos 25 nombres que en CONFIG.SHEETS del
    Apps Script original).
  - Normaliza encabezados a snake_case (misma función que generó schema.sql).
  - Inserta todo en la tabla Postgres equivalente, en lotes.

Es idempotente por tabla: si quieres re-correrlo, primero hace TRUNCATE
de la tabla destino (evita duplicados). Pensado para migraciones de
"corte" (apagar Sheet, encender Cloud SQL), no para sincronización
continua.
"""

import os
import re
import json
import time

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


def pgname(h: str) -> str:
    h = h.strip()
    for a, b in zip("ÁÉÍÓÚÑ", "AEIOUN"):
        h = h.replace(a, b)
    h = re.sub(r"[^A-Za-z0-9_]+", "_", h)
    h = re.sub(r"_+", "_", h).strip("_").lower()
    return h


def get_sheet_client():
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return gspread.authorize(creds)


def get_pg_engine():
    """
    Conexión directa vía instancia pública + IP allowlisted, para
    scripts batch que no corren dentro de Streamlit (no usan st.secrets).
    Ajusta a Cloud SQL Connector si prefieres no exponer IP pública.
    """
    user = os.environ["DB_USER"]
    pwd = os.environ["DB_PASS"]
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    url = f"postgresql+pg8000://{user}:{pwd}@{host}:{port}/{name}"
    return sqlalchemy.create_engine(url)


def migrate_sheet(gc, engine, sheet_id: str, sheet_name: str):
    table = pgname(sheet_name)
    print(f"→ Migrando {sheet_name} -> tabla `{table}`")

    ws = gc.open_by_key(sheet_id).worksheet(sheet_name)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        print(f"  (vacía, se omite)")
        return

    headers = [pgname(h) for h in values[0] if h.strip()]
    rows = values[1:]

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(f"TRUNCATE TABLE {table} CASCADE"))

        insert_sql = sqlalchemy.text(
            f"INSERT INTO {table} ({', '.join(headers)}) "
            f"VALUES ({', '.join(':' + h for h in headers)})"
        )

        batch = []
        for row in rows:
            if not any(cell.strip() for cell in row):
                continue  # fila vacía
            record = {headers[i]: (row[i] if i < len(row) else None)
                       for i in range(len(headers))}
            # Strings vacíos -> NULL para no romper columnas NUMERIC/TIMESTAMP
            record = {k: (v if v != "" else None) for k, v in record.items()}
            batch.append(record)

        if batch:
            conn.execute(insert_sql, batch)

    print(f"  ✔ {len(batch)} filas migradas")


def main():
    sheet_id = os.environ["SHEET_ID"]
    gc = get_sheet_client()
    engine = get_pg_engine()

    for name in SHEET_NAMES:
        try:
            migrate_sheet(gc, engine, sheet_id, name)
        except Exception as e:
            print(f"  ✘ ERROR en {name}: {e}")
        time.sleep(2)  # evita el límite de cuota de lectura de Google Sheets

    print("\nMigración terminada. Revisa los ✘ arriba si algo falló.")


if __name__ == "__main__":
    main()
