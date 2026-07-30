"""
services/jerarquia_service.py
================================
Nuevo. Gestión de la jerarquía técnica (Sistema → Subsistema → Ítem →
Parte) con clasificación ISO 14224, y del catálogo de tipos de activo,
todo editable desde Admin.

ISO 14224 (simplificado para este catálogo) clasifica los activos en:
    - Unidad de equipo (Equipment Unit)
    - Subunidad (Subunit)
    - Componente (Component)
    - Ítem mantenible (Maintainable Item)

Esto es metadata de clasificación, independiente del campo `tipo`
(SISTEMA/SUBSISTEMA/ITEM/PARTE) que ya usa la jerarquía original —
permite reportar y agrupar fallas siguiendo el estándar, sin obligar
a rehacer la estructura de datos existente.
"""

from utils.ids import new_id
from db.factory import get_connector

CLASES_ISO14224 = ["Unidad de equipo", "Subunidad", "Componente", "Ítem mantenible"]
TIPOS_JERARQUIA = ["SISTEMA", "SUBSISTEMA", "ITEM", "PARTE"]


# ----------------------------------------------------------------------
# JERARQUÍA TÉCNICA
# ----------------------------------------------------------------------

def list_nodos(tipo: str | None = None) -> list[dict]:
    db = get_connector()
    where = {"tipo": tipo} if tipo else None
    return db.fetch_all("jerarquia_tecnica", where=where, order_by="nombre")


def crear_nodo(nombre: str, tipo: str, padre_id: str | None, clase_iso14224: str | None) -> dict:
    db = get_connector()
    registro = {
        "id_activo": new_id("JT"),
        "nombre": nombre,
        "tipo": tipo,
        "padre_id": padre_id,
        "activo": True,
        "clase_iso14224": clase_iso14224,
    }
    return db.insert("jerarquia_tecnica", registro)


def actualizar_nodo(id_nodo: str, nombre: str, tipo: str, clase_iso14224: str | None) -> int:
    db = get_connector()
    return db.update("jerarquia_tecnica", where={"id_activo": id_nodo},
                       data={"nombre": nombre, "tipo": tipo, "clase_iso14224": clase_iso14224})


def desactivar_nodo(id_nodo: str) -> int:
    db = get_connector()
    return db.update("jerarquia_tecnica", where={"id_activo": id_nodo}, data={"activo": False})


def eliminar_nodo(id_nodo: str) -> int:
    """Borrado definitivo — usar con cuidado, solo si el nodo no tiene
    referencias (averías, activos, etc.) apuntándole."""
    db = get_connector()
    return db.delete("jerarquia_tecnica", where={"id_activo": id_nodo})


# ----------------------------------------------------------------------
# CATÁLOGO DE TIPOS DE ACTIVO
# ----------------------------------------------------------------------

def list_tipos_activo(solo_activos: bool = True) -> list[dict]:
    db = get_connector()
    where = {"activo": True} if solo_activos else None
    return db.fetch_all("tipos_activo", where=where, order_by="nombre")


def crear_tipo_activo(nombre: str, clase_iso14224: str, descripcion: str) -> dict:
    db = get_connector()
    registro = {
        "id_tipo": new_id("TA"),
        "nombre": nombre,
        "clase_iso14224": clase_iso14224,
        "descripcion": descripcion,
        "activo": True,
    }
    return db.insert("tipos_activo", registro)


def desactivar_tipo_activo(id_tipo: str) -> int:
    db = get_connector()
    return db.update("tipos_activo", where={"id_tipo": id_tipo}, data={"activo": False})
