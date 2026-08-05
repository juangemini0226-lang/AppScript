"""
services/users_service.py
===========================
Portado desde users.gs.

DIFERENCIA IMPORTANTE respecto al original:
En Apps Script, `Session.getActiveUser().getEmail()` identificaba al
usuario automáticamente porque la app corría dentro del ecosistema Google
(el usuario ya estaba logueado en su cuenta @estra.com.co).

En Streamlit eso NO existe de forma nativa: no hay sesión de Google
integrada. Por eso `get_current_user()` recibe el email como parámetro
(se lo pide Streamlit al usuario en el login, o se integra más adelante
con Google OAuth / Identity-Aware Proxy si se despliega en GCP).

El PIN rápido (validar_login_por_pin_rapido) se portó igual, sirve de
respaldo para planta donde no todos tienen correo a mano.
"""

from db.factory import get_connector

SUPERADMINS = {
    "jegonzalez@estra.com.co": "Planeador VIP",
    "pract-ingenieria@estra.com.co": "Planeador VIP",
}


def get_current_user(email: str) -> dict:
    email = (email or "").strip().lower()

    if email in SUPERADMINS:
        return {"email": email, "nombre": SUPERADMINS[email], "rol": "PLANEADOR"}

    db = get_connector()
    row = db.fetch_one("usuarios", where={"correo": email})

    if row and str(row.get("activo")).upper() in ("TRUE", "1"):
        return {
            "email": email,
            "nombre": row.get("nombre", "").strip(),
            "rol": str(row.get("rol", "")).strip().upper(),
        }

    raise ValueError(f"Tu correo ({email}) no está registrado o está inactivo.")


def validar_login_por_pin_rapido(pin_ingresado: str) -> dict:
    """
    El PIN identifica un ROL (no una persona puntual) — se usa en
    planta para entrar rápido sin escribir el correo. Los PINes se
    administran desde Admin -> Roles y PINes, ya no están fijos aquí.
    """
    pin = str(pin_ingresado).strip()
    db = get_connector()
    fila = db.fetch_one("roles_pines", where={"pin": pin})
    if not fila:
        raise ValueError("PIN incorrecto. Acceso denegado.")

    return {
        "id": f"PIN_{fila['rol_key']}",
        "email": f"pin.{fila['rol_key'].lower()}@estra.com.co",
        "nombre": fila.get("nombre_generico") or fila["rol_key"].title(),
        "rol": fila["rol_key"],
    }


def _tecnicos_por_rol(rol: str) -> list[dict]:
    db = get_connector()
    rows = db.fetch_all("usuarios", where={"rol": rol, "activo": True})
    return [{"id": r["id_usuario"], "nombre": r["nombre"]} for r in rows]


def get_tecnicos_simple() -> list[dict]:
    return _tecnicos_por_rol("TECNICO")


def get_tecnicos_b_simple() -> list[dict]:
    return _tecnicos_por_rol("TECNICO_B")


def get_tecnicos_montaje_simple() -> list[dict]:
    return _tecnicos_por_rol("TECNICO_MONTAJE")
