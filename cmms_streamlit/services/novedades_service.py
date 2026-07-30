"""
services/novedades_service.py
================================
Nuevo (reconstrucción). Portado en espíritu de novedades_consulta.gs:
reportar una falla desde planta y darle seguimiento hasta que se
convierte en OT.
"""

from datetime import datetime

from utils.ids import new_id
from db.factory import get_connector

ESTADOS = ["ASIGNADA", "EN_REVISION", "CONVERTIDA_A_OT", "DESCARTADA"]


def crear_novedad(data: dict, creado_por: str) -> dict:
    """
    data espera: zona, tecnico_id, equipo_id, sistema_id, subsistema_id,
    item_id, descripcion, prioridad, maquina.
    """
    db = get_connector()
    registro = {
        "id_nov": new_id("NOV"),
        "fecha": datetime.now(),
        "zona": data.get("zona"),
        "tecnico_id": data.get("tecnico_id"),
        "equipo_id": data.get("equipo_id"),
        "sistema_id": data.get("sistema_id"),
        "subsistema_id": data.get("subsistema_id"),
        "item_id": data.get("item_id"),
        "descripcion": data.get("descripcion"),
        "prioridad": data.get("prioridad", "MEDIA"),
        "tiempo_empleado_min": data.get("tiempo_empleado_min"),
        "maquina": data.get("maquina", "NO"),
        "resuelto": False,
        "estado": "ASIGNADA",
        "creado_por": creado_por,
        "creado_en": datetime.now(),
        "ot_id": None,
    }
    return db.insert("novedades", registro)


def list_novedades(estado: str | None = None, limit: int = 100) -> list[dict]:
    db = get_connector()
    where = {"estado": estado} if estado else None
    return db.fetch_all("novedades", where=where, order_by="fecha DESC", limit=limit)


def get_novedad(id_nov: str) -> dict | None:
    db = get_connector()
    return db.fetch_one("novedades", where={"id_nov": id_nov})


def actualizar_estado_novedad(id_nov: str, estado: str, ot_id: str | None = None) -> int:
    db = get_connector()
    data = {"estado": estado}
    if ot_id:
        data["ot_id"] = ot_id
    if estado == "CONVERTIDA_A_OT":
        data["resuelto"] = True
    return db.update("novedades", where={"id_nov": id_nov}, data=data)
