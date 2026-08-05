"""
services/dashboard_service.py
================================
KPIs para la página de inicio: un vistazo rápido al estado de planta
sin tener que entrar a cada módulo.
"""

from db.factory import get_connector


def get_kpis() -> dict:
    db = get_connector()

    def contar(query: str) -> int:
        rows = db.execute_raw(query)
        return rows[0]["c"] if rows else 0

    return {
        "activos_total": contar("SELECT COUNT(*) as c FROM activos WHERE activo = TRUE"),
        "ot_abiertas": contar(
            "SELECT COUNT(*) as c FROM ot WHERE estado NOT IN ('FINALIZADA', 'TERMINADA')"
        ),
        "ot_alta_prioridad": contar(
            "SELECT COUNT(*) as c FROM ot WHERE estado NOT IN ('FINALIZADA', 'TERMINADA') "
            "AND prioridad = 'ALTA'"
        ),
        "novedades_pendientes": contar(
            "SELECT COUNT(*) as c FROM novedades WHERE estado = 'ASIGNADA'"
        ),
    }


def get_ot_por_estado() -> dict[str, int]:
    """Para el tablero tipo kanban en Órdenes de Trabajo."""
    db = get_connector()
    rows = db.execute_raw("SELECT estado, COUNT(*) as c FROM ot GROUP BY estado")
    return {r["estado"]: r["c"] for r in rows}


def get_ot_por_prioridad() -> dict[str, int]:
    db = get_connector()
    rows = db.execute_raw(
        "SELECT prioridad, COUNT(*) as c FROM ot "
        "WHERE estado NOT IN ('FINALIZADA', 'TERMINADA') GROUP BY prioridad"
    )
    return {r["prioridad"] or "Sin definir": r["c"] for r in rows}


def get_novedades_por_estado() -> dict[str, int]:
    db = get_connector()
    rows = db.execute_raw("SELECT estado, COUNT(*) as c FROM novedades GROUP BY estado")
    return {r["estado"] or "Sin definir": r["c"] for r in rows}


def get_activos_por_tipo() -> dict[str, int]:
    db = get_connector()
    rows = db.execute_raw(
        "SELECT tipo, COUNT(*) as c FROM activos WHERE activo = TRUE GROUP BY tipo"
    )
    return {r["tipo"] or "Sin definir": r["c"] for r in rows}
