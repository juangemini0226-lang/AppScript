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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --grafito: #1E2530;
        --acero: #3B6E8F;
        --ambar: #E8A43B;
        --exito: #2F9E52;
        --peligro: #C4483D;
        --lienzo: #F5F6F8;
        --superficie: #FFFFFF;
        --borde: #E1E4EA;
        --texto: #1E2530;
        --texto-tenue: #5B6472;
    }

    html, body, [class*="css"] {
        background-color: var(--lienzo);
    }

    /* ---- Tipografía: Oswald para títulos (placa de máquina),
       IBM Plex Sans para texto, IBM Plex Mono para IDs/tags/códigos ---- */
    h1, h2, h3, .stTabs [data-baseweb="tab"] p {
        font-family: 'Oswald', sans-serif !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        color: var(--grafito) !important;
    }
    body, p, div, span, label, li {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    code, .stCodeBlock, div[data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace !important;
    }

    h1 {
        font-size: 1.9rem !important;
        border-bottom: 3px solid var(--ambar);
        padding-bottom: 10px;
        margin-bottom: 1.2rem !important;
    }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.05rem !important; }

    /* ---- Sidebar: panel de control oscuro ---- */
    section[data-testid="stSidebar"] {
        background-color: var(--grafito);
        border-right: none;
    }
    section[data-testid="stSidebar"] * {
        color: #E8EAED !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
    }
    section[data-testid="stSidebar"] button {
        background-color: transparent;
        border: 1px solid #454F5F !important;
        border-radius: 6px;
    }
    section[data-testid="stSidebar"] button:hover {
        border-color: var(--ambar) !important;
        color: var(--ambar) !important;
    }
    /* Ítem activo del menú de navegación en el sidebar */
    section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
        background-color: rgba(232, 164, 59, 0.16);
        border-left: 3px solid var(--ambar);
    }

    /* ---- Tarjetas de métricas (dashboard) ---- */
    div[data-testid="stMetric"] {
        background-color: var(--superficie);
        border: 1px solid var(--borde);
        border-left: 4px solid var(--acero);
        border-radius: 6px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(30, 37, 48, 0.04);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: var(--grafito);
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Sans', sans-serif;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        color: var(--texto-tenue);
    }

    /* ---- Pestañas: barra tipo indicador ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--borde);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid var(--ambar) !important;
    }

    /* ---- Expanders (filas editables) ---- */
    div[data-testid="stExpander"] {
        border: 1px solid var(--borde);
        border-radius: 6px;
        background-color: var(--superficie);
    }
    div[data-testid="stExpander"] summary {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
    }

    /* ---- Botones ---- */
    button[kind="primary"] {
        background-color: var(--acero) !important;
        border-color: var(--acero) !important;
        border-radius: 6px;
        font-weight: 600;
    }
    button[kind="primary"]:hover {
        background-color: #2E5872 !important;
        border-color: #2E5872 !important;
    }
    button[kind="secondary"] {
        border-radius: 6px;
    }

    /* ---- Inputs y formularios ---- */
    div[data-testid="stForm"] {
        border: 1px solid var(--borde);
        border-radius: 8px;
        padding: 1.2rem;
        background-color: var(--superficie);
    }

    /* ---- Tablas / dataframes ---- */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--borde);
        border-radius: 6px;
    }

    /* ---- Alertas: acento de color a la izquierda, sin globo genérico ---- */
    div[data-testid="stAlert"] {
        border-radius: 6px;
        border-left-width: 4px;
    }

    /* ---- Responsive / móvil ---- */
    @media (max-width: 640px) {
        div[data-testid="stMetric"] { padding: 10px 12px; }
        div[data-testid="stMetricValue"] { font-size: 1.3rem; }
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.1rem !important; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        div[data-testid="column"] { min-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)



def _login_form():
    st.markdown("""
    <div style="background:#1E2530;border-radius:8px;padding:2rem 2rem 1.6rem 2rem;
                margin-bottom:1.5rem;border-left:6px solid #E8A43B;">
        <p style="font-family:'IBM Plex Mono',monospace;color:#8FA3B8;font-size:0.78rem;
                  letter-spacing:0.12em;margin:0 0 6px 0;text-transform:uppercase;">
            Sistema de mantenimiento · CMMS
        </p>
        <h1 style="font-family:'Oswald',sans-serif;color:#F5F6F8 !important;font-size:2.2rem;
                   margin:0;border:none;padding:0;letter-spacing:0.02em;">
            FLA-EICE
        </h1>
        <p style="font-family:'IBM Plex Sans',sans-serif;color:#B8C1CC;font-size:0.95rem;margin:6px 0 0 0;">
            Línea 3 · Envasado · Control de piso de mantenimiento
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_email, tab_pin = st.tabs(["Correo corporativo", "PIN rápido (planta)"])

    with tab_email:
        with st.form("login_email"):
            email = st.text_input("Correo @estra.com.co")
            enviar = st.form_submit_button("Entrar", type="primary")
        if enviar:
            try:
                st.session_state["usuario"] = get_current_user(email)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with tab_pin:
        with st.form("login_pin"):
            pin = st.text_input("PIN", type="password", max_chars=4)
            enviar_pin = st.form_submit_button("Entrar", type="primary")
        if enviar_pin:
            try:
                st.session_state["usuario"] = validar_login_por_pin_rapido(pin)
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def _home_page():
    usuario = st.session_state["usuario"]
    st.markdown("""
    <p style="font-family:'IBM Plex Mono',monospace;color:#5B6472;font-size:0.75rem;
              letter-spacing:0.1em;text-transform:uppercase;margin:0 0 4px 0;">
        FLA-EICE · Línea 3 · Envasado
    </p>
    """, unsafe_allow_html=True)
    st.title("Panel de control")
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
    if is_module_visible_for_role("mapa_planta", rol):
        pages.append(st.Page("app_pages/mapa_planta.py", title="Mapa de planta", icon="🗺️"))

    if rol in ("PLANEADOR", "AUDITOR"):
        pages.append(st.Page("app_pages/admin.py", title="Admin", icon="⚙️"))

    return st.navigation(pages)


def main():
    if "usuario" not in st.session_state:
        _login_form()
        return

    usuario = st.session_state["usuario"]

    with st.sidebar:
        st.markdown(f"""
        <div style="border:1px solid #454F5F;border-radius:6px;padding:10px 12px;margin-bottom:10px;">
            <p style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:#8FA3B8;
                      text-transform:uppercase;letter-spacing:0.08em;margin:0 0 4px 0;">Sesión activa</p>
            <p style="font-family:'IBM Plex Sans',sans-serif;font-size:1rem;font-weight:600;margin:0;">
                {usuario['nombre']}
            </p>
            <p style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#E8A43B;margin:2px 0 0 0;">
                {usuario['rol']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            del st.session_state["usuario"]
            st.rerun()

    nav = _build_navigation()
    nav.run()


if __name__ == "__main__":
    main()
