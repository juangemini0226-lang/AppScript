"""
services/ot_service.py
========================
Nuevo (reconstrucción, versión inicial). Portado en espíritu de
ot_consulta.gs / ot_gestion.gs: crear una OT (directa o desde una
novedad), listar el tablero de trabajos en curso, y cambiar de estado
registrando el tiempo dedicado.

Pendiente para una siguiente vuelta: repuestos usados (ot_repuestos),
evidencias fotográficas (ot_evidencias) y generación de PDF de cierre
(pdf_generator.gs) — ver DOCUMENTATION.md.
"""

from datetime import datetime

from utils.ids import new_id
from db.factory import get_connector
from services import novedades_service

ESTADOS_OT = ["PROGRAMADA", "EN_EJECUCION", "EN_ESPERA", "TERMINADA", "FINALIZADA"]


def crear_ot(data: dict, planeador_id: str) -> dict:
    """
    data espera: equipo_id, sistema_id, subsistema_id, item_id, prioridad,
    tecnico_asignador_id, descripcion_solicitud, tipo_actividad,
    origen_id ('DIRECTA' o id de novedad), causa_id (opcional).
    """
    db = get_connector()
    id_ot = new_id("OT")

    registro = {
        "id_ot": id_ot,
        "fecha": datetime.now().date(),
        "creacion_nov": data.get("novedad_id"),
        "origen_id": data.get("novedad_id") or "DIRECTA",
        "equipo_id": data.get("equipo_id"),
        "sistema_id": data.get("sistema_id"),
        "subsistema_id": data.get("subsistema_id"),
        "item_id": data.get("item_id"),
        "prioridad": data.get("prioridad", "MEDIA"),
        "planeador_id": planeador_id,
        "tecnico_asignador_id": data.get("tecnico_id"),
        "estado": "PROGRAMADA",
        "descripcion_solicitud": data.get("descripcion_solicitud"),
        "tipo_actividad": data.get("tipo_actividad", "CORRECTIVO"),
        "fecha_estimada": data.get("fecha_estimada"),
    }
    resultado = db.insert("ot", registro)

    novedad_id = data.get("novedad_id")
    if novedad_id:
        novedades_service.actualizar_estado_novedad(novedad_id, "CONVERTIDA_A_OT", ot_id=id_ot)

    return resultado


def list_ot(estado: str | None = None, limit: int = 200) -> list[dict]:
    db = get_connector()
    where = {"estado": estado} if estado else None
    return db.fetch_all("ot", where=where, order_by="fecha DESC", limit=limit)


def get_ot(id_ot: str) -> dict | None:
    db = get_connector()
    return db.fetch_one("ot", where={"id_ot": id_ot})


ESTADOS_QUE_MUEVEN_A_TALLER = {"EN_EJECUCION", "EN_ESPERA"}
ESTADOS_QUE_CIERRAN_OT = {"TERMINADA", "FINALIZADA"}


def cambiar_estado_ot(id_ot: str, nuevo_estado: str, tecnico_id: str,
                        minutos: int, comentario: str) -> None:
    """
    Cambia el estado de la OT Y registra el tiempo/comentario asociado
    a ese cambio (equivalente a lo que hacía OT_TIEMPOS en el original:
    cada cambio de estado queda trazado con quién, cuánto tiempo y por qué).

    Automatización de ubicación: si el equipo asociado es un molde y la
    OT pasa a EN_EJECUCION o EN_ESPERA, su ubicación física temporal
    pasa a "TALLER" (queda registrado en ACTIVOS.ubicacion). Al cerrar
    la OT (TERMINADA/FINALIZADA), la ubicación vuelve a la zona
    permanente asignada (ACTIVOS.zona).
    """
    db = get_connector()

    db.update("ot", where={"id_ot": id_ot}, data={"estado": nuevo_estado})

    db.insert("ot_tiempos", {
        "id_tiempo": new_id("OTT"),
        "ot_id": id_ot,
        "tecnico_id": tecnico_id,
        "minutos": minutos,
        "comentario": f"[CAMBIO ESTADO -> {nuevo_estado}] {comentario}",
        "creado_en": datetime.now(),
    })

    ot = db.fetch_one("ot", where={"id_ot": id_ot})
    equipo_id = ot.get("equipo_id") if ot else None
    if equipo_id:
        if nuevo_estado in ESTADOS_QUE_MUEVEN_A_TALLER:
            db.update("activos", where={"id_activo": equipo_id},
                       data={"ubicacion": f"TALLER (OT {id_ot})"})
        elif nuevo_estado in ESTADOS_QUE_CIERRAN_OT:
            activo = db.fetch_one("activos", where={"id_activo": equipo_id})
            zona_original = activo.get("zona") if activo else None
            if zona_original:
                db.update("activos", where={"id_activo": equipo_id},
                           data={"ubicacion": zona_original})


def get_tiempos_ot(id_ot: str) -> list[dict]:
    db = get_connector()
    return db.fetch_all("ot_tiempos", where={"ot_id": id_ot}, order_by="creado_en")
