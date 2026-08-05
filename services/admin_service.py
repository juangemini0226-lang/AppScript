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
    {"key": "mapa_planta", "label": "Mapa de planta"},
]

ROLES_DISPONIBLES = ["TECNICO", "TECNICO_B", "TECNICO_MONTAJE", "PLANEADOR", "AUDITOR"]


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


def eliminar_usuario(id_usuario: str) -> int:
    """Borrado definitivo. Para uso ocasional — normalmente basta con
    desactivar (set_usuario_activo) para conservar el historial de OT
    y novedades donde ese usuario aparece como técnico/creador."""
    db = get_connector()
    return db.delete("usuarios", where={"id_usuario": id_usuario})


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


def get_feature_flags_full() -> dict[str, dict]:
    """
    Devuelve {key: {"activo": bool, "roles": [lista de roles permitidos]}}
    para cada módulo del catálogo. Si un módulo no tiene fila todavía,
    se asume activo=True y visible para todos los roles.
    """
    db = get_connector()
    rows = db.fetch_all("feature_flags")
    por_key = {r["feature_key"]: r for r in rows}

    resultado = {}
    for m in MODULOS_DISPONIBLES:
        key = m["key"]
        row = por_key.get(key)
        if row:
            roles_raw = (row.get("roles_permitidos") or "TODOS").strip()
            roles = ROLES_DISPONIBLES if roles_raw == "TODOS" else \
                [r.strip() for r in roles_raw.split(",") if r.strip()]
            resultado[key] = {"activo": bool(row.get("activo", True)), "roles": roles}
        else:
            resultado[key] = {"activo": True, "roles": list(ROLES_DISPONIBLES)}
    return resultado


def set_feature_flag_full(feature_key: str, activo: bool, roles: list[str]) -> None:
    """Guarda el interruptor global Y la lista de roles que pueden ver el módulo."""
    db = get_connector()
    roles_str = "TODOS" if set(roles) >= set(ROLES_DISPONIBLES) else ",".join(roles)
    existente = db.fetch_one("feature_flags", where={"feature_key": feature_key})
    data = {"activo": activo, "roles_permitidos": roles_str}
    if existente:
        db.update("feature_flags", where={"feature_key": feature_key}, data=data)
    else:
        db.insert("feature_flags", {"feature_key": feature_key, "descripcion": feature_key, **data})


def is_module_visible_for_role(feature_key: str, rol: str) -> bool:
    """Combina el interruptor global con la lista de roles permitidos."""
    info = get_feature_flags_full().get(feature_key, {"activo": True, "roles": ROLES_DISPONIBLES})
    return info["activo"] and (rol in info["roles"])


# ----------------------------------------------------------------------
# SUB-FUNCIONES (widgets/pestañas dentro de cada módulo) — nuevo
# ----------------------------------------------------------------------
# Catálogo de qué pestañas/widgets tiene cada módulo, para que Admin
# pueda prender/apagarlas individualmente y decidir qué roles las ven,
# igual que con los módulos completos, pero un nivel más abajo.

SUBFEATURES_CATALOGO = {
    "activos": [
        {"key": "explorar_jerarquia", "label": "Explorar jerarquía"},
        {"key": "consultar_molde", "label": "Consultar molde"},
        {"key": "crear_activo", "label": "Crear activo"},
        {"key": "csv_masivo", "label": "Cargar CSV masivo"},
        {"key": "plantilla_ubicaciones", "label": "Plantilla de ubicaciones"},
        {"key": "generar_qr", "label": "Generar QR"},
        {"key": "exportar", "label": "Exportar a Excel"},
        {"key": "listado", "label": "Listado completo"},
    ],
    "ordenes_trabajo": [
        {"key": "kanban", "label": "Tablero Kanban"},
        {"key": "lista_detalle", "label": "Lista y detalle"},
        {"key": "crear_ot", "label": "Crear OT"},
    ],
    "novedades": [
        {"key": "reportar", "label": "Reportar novedad"},
        {"key": "tablero", "label": "Tablero de seguimiento"},
    ],
    "maquilas": [
        {"key": "historial", "label": "Historial"},
        {"key": "registrar_movimiento", "label": "Registrar movimiento"},
        {"key": "nuevo_maquilador", "label": "Nuevo maquilador"},
    ],
    "mapa_planta": [
        {"key": "ver_mapa", "label": "Ver mapa"},
        {"key": "foto_planta", "label": "Foto de planta"},
        {"key": "zonas", "label": "Zonas"},
        {"key": "ubicar_activo", "label": "Ubicar activo"},
    ],
}


def get_subfeatures_full(modulo_key: str) -> dict[str, dict]:
    """{"sub_key": {"activo": bool, "roles": [...]}} para todas las
    sub-funciones de un módulo. Igual que get_feature_flags_full() pero
    un nivel más abajo."""
    db = get_connector()
    rows = db.fetch_all("sub_feature_flags", where={"modulo_key": modulo_key})
    por_key = {r["sub_feature_key"]: r for r in rows}

    catalogo = SUBFEATURES_CATALOGO.get(modulo_key, [])
    resultado = {}
    for sf in catalogo:
        key = sf["key"]
        row = por_key.get(key)
        if row:
            roles_raw = (row.get("roles_permitidos") or "TODOS").strip()
            roles = ROLES_DISPONIBLES if roles_raw == "TODOS" else \
                [r.strip() for r in roles_raw.split(",") if r.strip()]
            resultado[key] = {"activo": bool(row.get("activo", True)), "roles": roles}
        else:
            resultado[key] = {"activo": True, "roles": list(ROLES_DISPONIBLES)}
    return resultado


def set_subfeature_full(modulo_key: str, sub_feature_key: str, activo: bool, roles: list[str]) -> None:
    db = get_connector()
    roles_str = "TODOS" if set(roles) >= set(ROLES_DISPONIBLES) else ",".join(roles)
    existente = db.fetch_one("sub_feature_flags",
                               where={"modulo_key": modulo_key, "sub_feature_key": sub_feature_key})
    data = {"activo": activo, "roles_permitidos": roles_str}
    if existente:
        db.update("sub_feature_flags",
                   where={"modulo_key": modulo_key, "sub_feature_key": sub_feature_key}, data=data)
    else:
        db.insert("sub_feature_flags", {"modulo_key": modulo_key, "sub_feature_key": sub_feature_key, **data})


def visible_subfeatures(modulo_key: str, rol: str) -> list[dict]:
    """
    Devuelve, en orden, las sub-funciones del módulo que el rol actual
    puede ver: [{"key":..., "label":...}, ...]. Las páginas usan esto
    para armar sus pestañas dinámicamente (ver utils/tabs.py).
    """
    flags = get_subfeatures_full(modulo_key)
    catalogo = SUBFEATURES_CATALOGO.get(modulo_key, [])
    return [sf for sf in catalogo if flags.get(sf["key"], {}).get("activo", True)
            and rol in flags.get(sf["key"], {}).get("roles", ROLES_DISPONIBLES)]


# ----------------------------------------------------------------------
# EXPLORADOR DE BASE DE DATOS (nuevo)
# ----------------------------------------------------------------------

def list_tables() -> list[str]:
    """Lista todas las tablas del schema 'public', para el selector del
    explorador de base de datos en Admin."""
    db = get_connector()
    rows = db.execute_raw(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )
    return [r["table_name"] for r in rows]


def get_table_preview(table_name: str, limit: int = 200) -> list[dict]:
    """
    Trae filas de una tabla para vista rápida. table_name se valida
    contra list_tables() antes de usarse en el SQL (nunca se interpola
    input libre del usuario en la consulta).
    """
    if table_name not in list_tables():
        raise ValueError("Tabla no reconocida.")
    db = get_connector()
    return db.execute_raw(f"SELECT * FROM {table_name} LIMIT {int(limit)}")


def get_table_row_count(table_name: str) -> int:
    if table_name not in list_tables():
        raise ValueError("Tabla no reconocida.")
    db = get_connector()
    rows = db.execute_raw(f"SELECT COUNT(*) as c FROM {table_name}")
    return rows[0]["c"] if rows else 0


def run_readonly_query(sql: str, limit: int = 500) -> list[dict]:
    """
    Corre una consulta SQL arbitraria pero SOLO de lectura: exige que
    empiece por SELECT (o WITH ... SELECT) y bloquea palabras clave de
    escritura, como red de seguridad básica para un panel de admin.
    No reemplaza permisos de base de datos reales, pero evita que un
    error de tecleo borre datos por accidente desde este panel.
    """
    sql_limpio = sql.strip().rstrip(";")
    sql_upper = sql_limpio.upper()

    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        raise ValueError("Solo se permiten consultas SELECT (de lectura) desde este panel.")

    palabras_prohibidas = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
                             "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for palabra in palabras_prohibidas:
        if palabra in sql_upper:
            raise ValueError(f"La palabra '{palabra}' no está permitida en este panel de solo lectura.")

    db = get_connector()
    if "LIMIT" not in sql_upper:
        sql_limpio = f"{sql_limpio} LIMIT {int(limit)}"
    return db.execute_raw(sql_limpio)
