"""
app.py
======
Entrada principal de la app CMMS en Streamlit.

Reemplaza a ui.html / admin.html (los formularios web servidos por el
Apps Script). La navegación por páginas usa el sistema nativo de
Streamlit (carpeta `pages/`), equivalente a las distintas vistas que
antes vivían todas en un solo HTML con showModalDialog / includes.
"""

import streamlit as st

from services.users_service import get_current_user, validar_login_por_pin_rapido

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

    st.title("Panel CMMS - Línea 3 Envasado")
    st.info(
        "Usa el menú de la izquierda (páginas) para navegar: "
        "Activos, Órdenes de Trabajo, Novedades, Maquilas, Admin."
    )


if __name__ == "__main__":
    main()
