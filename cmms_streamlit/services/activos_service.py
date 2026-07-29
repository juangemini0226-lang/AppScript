"""
services/activos_service.py
=============================
Portado desde activos.gs (Apps Script). Misma lógica de negocio, mismas
firmas de función (traducidas a snake_case), pero en vez de leer un
Google Sheet con SpreadsheetApp, consulta el DBConnector activo
(hoy Cloud SQL, ver db/factory.py).

Equivalencias con el código original:
    getEquipos()            -> get_equipos()
    getDataJerarquia()      -> get_data_jerarquia()
    getSistemasSimple()     -> get_sistemas_simple()
    getSubsistemasSimple()  -> get_subsistemas_simple()
    getItemsSimple()        -> get_items_simple()
    getAveriasSimple()      -> get_averias_simple()
    getSolucionesSimple()   -> get_soluciones_simple()
    consultarUbicacionMolde() -> consultar_ubicacion_molde()
"""

from db.factory import get_connector


def get_equipos() -> list[dict]:
    """Equipos principales de la tabla ACTIVOS (activo=True y tipo=EQUIPO)."""
    db = get_connector()
    rows = db.fetch_all("activos", where={"activo": True, "tipo": "EQUIPO"})
    return [{"id": r["id_activo"], "nombre": r["nombre"]} for r in rows]


def get_data_jerarquia(tipo: str, padre_id: str | None = None) -> list[dict]:
    """Lee JERARQUIA_TECNICA filtrando por tipo (SISTEMA/SUBSISTEMA/ITEM) y,
    opcionalmente, por el padre."""
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
    """
    Ficha técnica + ubicación actual de un molde.
    Portado de consultarUbicacionMolde() en activos.gs.
    """
    db = get_connector()
    row = db.fetch_one("activos", where={"id_activo": molde_id})

    info = {
        "id": molde_id,
        "nombre": "Desconocido",
        "tipo": "-",
        "ciclos": 0,
        "ultimo_alistamiento": "No registrado",
        "ubicacion_fisica": "No definida",
        "version": "N/A",
        "gancho": "N/A", "botadores": "N/A",
        "puentes_agua": "N/A", "puentes_aire": "N/A",
        "chapetas": "N/A", "manipulador": "N/A",
        "atemperador": "N/A", "accesorios": "N/A", "tip": "N/A",
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
