"""
app.py
======
Entrada principal. Navegación dinámica (rol + módulos activos) +
dashboard de inicio con indicadores reales y atajos de creación rápida.
"""

import streamlit as st

from services.users_service import get_current_user, validar_login_por_pin_rapido
from services.admin_service import is_module_visible_for_role
from services.dashboard_service import get_kpis

st.set_page_config(
    page_title="CMMS FLA-EICE · Línea 3 Envasado",
    page_icon="🛠️",
    layout="wide",
)

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 14px 16px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
    }
    button[kind="primary"], button[kind="secondary"] {
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)


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
    st.caption(f"Bienvenido, **{usuario['nombre']}** · Rol: {usuario['rol']}")

    try:
        kpis = get_kpis()
    except Exception:
        kpis = None

    if kpis:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Activos registrados", kpis["activos_total"])
        c2.metric("OT abiertas", kpis["ot_abiertas"])
        c3.metric("OT alta prioridad", kpis["ot_alta_prioridad"], delta=None,
                   delta_color="inverse" if kpis["ot_alta_prioridad"] > 0 else "normal")
        c4.metric("Novedades pendientes", kpis["novedades_pendientes"])

    st.divider()
    st.subheader("⚡ Accesos rápidos")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander("📋 Reportar novedad rápida"):
            with st.form("home_reportar_novedad", clear_on_submit=True):
                desc = st.text_area("Descripción de la falla *", key="home_nov_desc")
                prioridad = st.selectbox("Prioridad", ["BAJA", "MEDIA", "ALTA"], index=1, key="home_nov_prio")
                enviar = st.form_submit_button("Reportar")
            if enviar and desc:
                from services.novedades_service import crear_novedad
                res = crear_novedad({"descripcion": desc, "prioridad": prioridad}, creado_por=usuario["email"])
                st.success(f"Novedad reportada: {res['id_nov']}")

    with col2:
        with st.expander("🏭 Crear activo rápido"):
            with st.form("home_crear_activo", clear_on_submit=True):
                nombre = st.text_input("Nombre *", key="home_act_nombre")
                tipo = st.selectbox("Tipo", ["MOLDE", "EQUIPO", "PLANTA"], key="home_act_tipo")
                enviar = st.form_submit_button("Crear")
            if enviar and nombre:
                from services.activos_service import crear_activo
                res = crear_activo({"nombre": nombre, "tipo": tipo})
                st.success(f"Activo creado: {res['id_activo']}")

    with col3:
        with st.expander("🛠️ Ver mis módulos"):
            st.write("Usa el menú de la izquierda para navegar entre los módulos disponibles para tu rol.")
            if usuario["rol"] in ("PLANEADOR", "AUDITOR"):
                st.caption("Como administrador, puedes prender/apagar módulos en **Admin → Módulos de la app**.")


def _build_navigation():
    usuario = st.session_state["usuario"]
    rol = usuario["rol"]

    home = st.Page(_home_page, title="Inicio", icon="🏠", default=True)
    pages = [home]

    if is_module_visible_for_role("activos", rol):
        pages.append(st.Page("app_pages/activos.py", title="Activos", icon="🏭"))
    if is_module_visible_for_role("ordenes_trabajo", rol):
        pages.append(st.Page("app_pages/ordenes_trabajo.py", title="Órdenes de Trabajo", icon="🛠️"))
    if is_module_visible_for_role("novedades", rol):
        pages.append(st.Page("app_pages/novedades.py", title="Novedades", icon="📋"))
    if is_module_visible_for_role("maquilas", rol):
        pages.append(st.Page("app_pages/maquilas.py", title="Maquilas", icon="🏗️"))

    if rol in ("PLANEADOR", "AUDITOR"):
        pages.append(st.Page("app_pages/admin.py", title="Admin", icon="⚙️"))

    return st.navigation(pages)


def main():
    if "usuario" not in st.session_state:
        _login_form()
        return

    usuario = st.session_state["usuario"]

    with st.sidebar:
        st.markdown(f"### 👤 {usuario['nombre']}")
        st.caption(f"Rol: **{usuario['rol']}**")
        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            del st.session_state["usuario"]
            st.rerun()

    nav = _build_navigation()
    nav.run()


if __name__ == "__main__":
    main()
