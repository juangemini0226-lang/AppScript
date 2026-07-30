"""
services/activos_service.py
=============================
Portado desde activos.gs, mismas firmas en snake_case, hablando con
DBConnector en vez de SpreadsheetApp.

Sección nueva (reconstrucción): creación y edición de activos desde el
frontend, para que el rol PLANEADOR no dependa del Sheet ni de tocar
la base a mano.
"""

from utils.ids import new_id
from db.factory import get_connector


# ----------------------------------------------------------------------
# LECTURA
# ----------------------------------------------------------------------

def get_equipos() -> list[dict]:
    db = get_connector()
    rows = db.fetch_all("activos", where={"activo": True, "tipo": "EQUIPO"})
    return [{"id": r["id_activo"], "nombre": r["nombre"]} for r in rows]


def get_data_jerarquia(tipo: str, padre_id: str | None = None) -> list[dict]:
    db = get_connector()
    where = {"activo": True, "tipo": tipo}
    if padre_id:
        where["padre_id"] = padre_id
    rows = db.fetch_all("jerarquia_tecnica", where=where)
    return [{"id": r["id_activo"], "nombre": r["nombre"]} for r in rows]


def get_sistemas_simple(equipo_id: str) -> list[dict]:
    return get_data_jerarquia("SISTEMA", equipo_id)


def get_subsistemas_simple(sistema_id: str) -> list[dict]:
    return get_data_jerarquia("SUBSISTEMA", sistema_id)


def get_items_simple(subsistema_id: str) -> list[dict]:
    return get_data_jerarquia("ITEM", subsistema_id)


def get_averias_simple(item_id: str) -> list[dict]:
    db = get_connector()
    rows = db.fetch_all("averias", where={"activo": True, "item_id": item_id})
    return [{"id": r["id_averia"], "nombre": r["descripcion"]} for r in rows]


def get_soluciones_simple(averia_id: str) -> list[dict]:
    db = get_connector()
    rows = db.fetch_all("soluciones_averia", where={"activo": True, "averia_id": averia_id})
    return [{"id": r["id_solucion"], "nombre": r["descripcion"]} for r in rows]


def consultar_ubicacion_molde(molde_id: str) -> dict:
    db = get_connector()
    row = db.fetch_one("activos", where={"id_activo": molde_id})

    info = {
        "id": molde_id, "nombre": "Desconocido", "tipo": "-", "ciclos": 0,
        "ultimo_alistamiento": "No registrado", "ubicacion_fisica": "No definida",
        "version": "N/A", "gancho": "N/A", "botadores": "N/A",
        "puentes_agua": "N/A", "puentes_aire": "N/A", "chapetas": "N/A",
        "manipulador": "N/A", "atemperador": "N/A", "accesorios": "N/A", "tip": "N/A",
    }
    if row:
        info.update({
            "nombre": row.get("nombre") or "Sin nombre",
            "ubicacion_fisica": row.get("ubicacion") or "Sin asignar",
            "ciclos": row.get("ciclosactuales") or 0,
            "tipo": row.get("familia") or "MOLDE",
            "gancho": row.get("gancho") or "N/A",
            "botadores": row.get("botadores") or "N/A",
            "puentes_agua": row.get("puentes_agua") or "N/A",
            "puentes_aire": row.get("puentes_aire") or "N/A",
            "chapetas": row.get("chapetas") or "N/A",
            "manipulador": row.get("manipulador") or "N/A",
            "atemperador": row.get("atemperador") or "N/A",
            "accesorios": row.get("accesorios") or "N/A",
            "tip": row.get("tip") or "N/A",
            "version": row.get("version_actual") or "N/A",
            "ultimo_alistamiento": row.get("ultimo_alistamiento") or "No registrado",
        })
    return info


def list_activos_todos(solo_activos: bool = True) -> list[dict]:
    db = get_connector()
    where = {"activo": True} if solo_activos else None
    return db.fetch_all("activos", where=where, order_by="nombre")


# ----------------------------------------------------------------------
# ESCRITURA (nuevo)
# ----------------------------------------------------------------------

def crear_activo(data: dict) -> dict:
    """
    data espera: nombre, tipo (PLANTA/EQUIPO/MOLDE), padre_id,
    tipoactivo, fabricante, ubicacion, peso, familia.
    """
    db = get_connector()
    prefijos = {"PLANTA": "PLT", "EQUIPO": "EQ", "MOLDE": "MOL"}
    prefijo = prefijos.get((data.get("tipo") or "").upper(), "ACT")

    registro = {
        "id_activo": new_id(prefijo),
        "nombre": data["nombre"],
        "tipo": data.get("tipo", "EQUIPO"),
        "padre_id": data.get("padre_id"),
        "activo": True,
        "tipoactivo": data.get("tipoactivo"),
        "fabricante": data.get("fabricante"),
        "ubicacion": data.get("ubicacion"),
        "peso": data.get("peso"),
        "familia": data.get("familia"),
    }
    return db.insert("activos", registro)


def actualizar_activo(id_activo: str, data: dict) -> int:
    db = get_connector()
    return db.update("activos", where={"id_activo": id_activo}, data=data)


def desactivar_activo(id_activo: str) -> int:
    db = get_connector()
    return db.update("activos", where={"id_activo": id_activo}, data={"activo": False})
