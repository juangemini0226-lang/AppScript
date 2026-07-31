"""
services/maquilas_service.py
===============================
Nuevo (reconstrucción). Registrar movimientos de moldes/periféricos
entregados a maquiladores externos: envío y reporte de producción.
"""

from datetime import datetime

from utils.ids import new_id
from db.factory import get_connector


def list_maquiladores() -> list[dict]:
    db = get_connector()
    # 'estado' quedó como TEXT en el schema ('TRUE'/'FALSE'), no BOOLEAN —
    # se compara como texto para que coincida con los datos ya migrados.
    return db.fetch_all("maquiladores", where={"estado": "TRUE"}, order_by="nombre_empresa")


def list_registros(molde_id: str | None = None, limit: int = 200) -> list[dict]:
    db = get_connector()
    where = {"molde_id": molde_id} if molde_id else None
    return db.fetch_all("maquilas", where=where, order_by="fecha_registro DESC", limit=limit)


def crear_registro(data: dict, registrado_por: str) -> dict:
    """
    data espera: molde_id, maquilador_id, tipo_movimiento (ENVIO/PRODUCCION),
    orden_produccion, unidades_inyectadas, observaciones.
    """
    db = get_connector()
    registro = {
        "id_registro": new_id("REG"),
        "molde_id": data.get("molde_id"),
        "maquilador_id": data.get("maquilador_id"),
        "fecha_registro": datetime.now(),
        "tipo_movimiento": data.get("tipo_movimiento", "ENVIO"),
        "orden_produccion": data.get("orden_produccion"),
        "unidades_inyectadas": data.get("unidades_inyectadas"),
        "observaciones": data.get("observaciones"),
        "registrado_por": registrado_por,
    }
    return db.insert("maquilas", registro)


def crear_maquilador(nombre_empresa: str, contacto_nombre: str, contacto_telefono: str) -> dict:
    db = get_connector()
    registro = {
        "id_maquilador": new_id("MAQ"),
        "nombre_empresa": nombre_empresa,
        "contacto_nombre": contacto_nombre,
        "contacto_telefono": contacto_telefono,
        "estado": "TRUE",
    }
    return db.insert("maquiladores", registro)
