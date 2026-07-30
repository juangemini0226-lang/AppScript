"""
services/admin_service.py
============================
Nuevo (reconstrucción). Todo lo que antes requería editar el Sheet o la
base a mano, ahora se gestiona desde la página Admin del frontend:

  - Usuarios: crear, editar rol, activar/desactivar.
  - Feature flags: prender/apagar módulos completos de la app sin
    tocar código ni base de datos a mano — solo un switch en la UI.

La tabla `feature_flags` no existe en el schema original (es nueva).
Ver db/schema_updates.sql para el CREATE TABLE correspondiente.
"""

from utils.ids import new_id
from db.factory import get_connector

# Catálogo de módulos que la app puede mostrar/ocultar. La 'key' es lo
# que se guarda en la tabla feature_flags; 'label' es lo que ve el admin.
MODULOS_DISPONIBLES = [
    {"key": "activos", "label": "Activos"},
    {"key": "ordenes_trabajo", "label": "Órdenes de Trabajo"},
    {"key": "novedades", "label": "Novedades"},
    {"key": "maquilas", "label": "Maquilas"},
]


# ----------------------------------------------------------------------
# USUARIOS
# ----------------------------------------------------------------------

def list_usuarios() -> list[dict]:
    db = get_connector()
    return db.fetch_all("usuarios", order_by="nombre")


def crear_usuario(nombre: str, correo: str, rol: str) -> dict:
    db = get_connector()
    registro = {
        "id_usuario": new_id("USR"),
        "nombre": nombre.strip(),
        "correo": correo.strip().lower(),
        "rol": rol.strip().upper(),
        "activo": True,
    }
    return db.insert("usuarios", registro)


def actualizar_usuario(id_usuario: str, nombre: str, rol: str) -> int:
    db = get_connector()
    return db.update("usuarios", where={"id_usuario": id_usuario},
                       data={"nombre": nombre.strip(), "rol": rol.strip().upper()})


def set_usuario_activo(id_usuario: str, activo: bool) -> int:
    db = get_connector()
    return db.update("usuarios", where={"id_usuario": id_usuario}, data={"activo": activo})


# ----------------------------------------------------------------------
# FEATURE FLAGS (encender/apagar módulos)
# ----------------------------------------------------------------------

def list_feature_flags() -> dict[str, bool]:
    """
    Devuelve {modulo_key: activo_bool} para TODOS los módulos del
    catálogo. Si un módulo no tiene fila en la tabla todavía, se asume
    activo=True por defecto (para que un módulo nuevo no aparezca
    apagado sin que el admin lo haya decidido).
    """
    db = get_connector()
    rows = db.fetch_all("feature_flags")
    estado = {r["feature_key"]: bool(r["activo"]) for r in rows}
    return {m["key"]: estado.get(m["key"], True) for m in MODULOS_DISPONIBLES}


def set_feature_flag(feature_key: str, activo: bool) -> None:
    db = get_connector()
    existente = db.fetch_one("feature_flags", where={"feature_key": feature_key})
    if existente:
        db.update("feature_flags", where={"feature_key": feature_key}, data={"activo": activo})
    else:
        db.insert("feature_flags", {"feature_key": feature_key, "activo": activo,
                                      "descripcion": feature_key})


def is_feature_enabled(feature_key: str) -> bool:
    return list_feature_flags().get(feature_key, True)
