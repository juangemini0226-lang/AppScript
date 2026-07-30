"""
app.py
======
Entrada principal. Reconstrucción: navegación dinámica.

En vez de la carpeta pages/ fija de Streamlit (donde todo usuario ve
todos los módulos), el menú se arma en tiempo real combinando:
  1. Qué módulos están ACTIVOS (tabla feature_flags, controlada por Admin)
  2. Qué rol tiene el usuario logueado (algunos módulos son solo Admin)

Así, apagar un módulo desde la página Admin lo quita del menú de todos
los usuarios al instante (con un refresh), sin tocar código.
"""

import streamlit as st

from services.users_service import get_current_user, validar_login_por_pin_rapido
from services.admin_service import list_feature_flags

st.set_page_config(
    page_title="CMMS FLA-EICE · Línea 3 Envasado",
    page_icon="🛠️",
    layout="wide",
)


def _login_form():
    st.title("🛠️ CMMS · FLA-EICE")
    st.caption("Línea 3 - Envasado · Mantenimiento")

    tab_email, tab_pin = st.tabs(["Correo corporativo", "PIN rápido (planta)"])

    with tab_email:
        with st.form("login_email"):
            email = st.text_input("Correo @estra.com.co")
            enviar = st.form_submit_button("Entrar")
        if enviar:
            try:
                st.session_state["usuario"] = get_current_user(email)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with tab_pin:
        with st.form("login_pin"):
            pin = st.text_input("PIN", type="password", max_chars=4)
            enviar_pin = st.form_submit_button("Entrar")
        if enviar_pin:
            try:
                st.session_state["usuario"] = validar_login_por_pin_rapido(pin)
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def _home_page():
    usuario = st.session_state["usuario"]
    st.title("Panel CMMS - Línea 3 Envasado")
    st.info(
        f"Bienvenido, **{usuario['nombre']}**. Usa el menú de la izquierda "
        "para navegar entre los módulos disponibles para tu rol."
    )


def _build_navigation():
    usuario = st.session_state["usuario"]
    flags = list_feature_flags()

    home = st.Page(_home_page, title="Inicio", icon="🏠", default=True)
    pages = [home]

    if flags.get("activos"):
        pages.append(st.Page("app_pages/activos.py", title="Activos", icon="🏭"))
    if flags.get("ordenes_trabajo"):
        pages.append(st.Page("app_pages/ordenes_trabajo.py", title="Órdenes de Trabajo", icon="🛠️"))
    if flags.get("novedades"):
        pages.append(st.Page("app_pages/novedades.py", title="Novedades", icon="📋"))
    if flags.get("maquilas"):
        pages.append(st.Page("app_pages/maquilas.py", title="Maquilas", icon="🏗️"))

    # Admin siempre visible para PLANEADOR/AUDITOR, sin importar feature_flags
    # (si no, un admin podría apagarse a sí mismo el acceso a Admin).
    if usuario["rol"] in ("PLANEADOR", "AUDITOR"):
        pages.append(st.Page("app_pages/admin.py", title="Admin", icon="⚙️"))

    return st.navigation(pages)


def main():
    if "usuario" not in st.session_state:
        _login_form()
        return

    usuario = st.session_state["usuario"]

    with st.sidebar:
        st.success(f"👤 {usuario['nombre']}\n\n**Rol:** {usuario['rol']}")
        if st.button("Cerrar sesión"):
            del st.session_state["usuario"]
            st.rerun()

    nav = _build_navigation()
    nav.run()


if __name__ == "__main__":
    main()
