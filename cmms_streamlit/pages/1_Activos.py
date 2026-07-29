"""
pages/1_Activos.py
====================
Módulo de consulta de Activos / jerarquía técnica / ubicación de moldes.
Portado completo de activos.gs. Este es el módulo de referencia: úsalo
como plantilla para portar los que faltan (OT, Novedades, Maquilas...).
"""

import streamlit as st

from services.activos_service import (
    get_equipos,
    get_sistemas_simple,
    get_subsistemas_simple,
    get_items_simple,
    get_averias_simple,
    get_soluciones_simple,
    consultar_ubicacion_molde,
)

st.set_page_config(page_title="Activos · CMMS", page_icon="🏭", layout="wide")

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🏭 Activos y jerarquía técnica")

tab_jerarquia, tab_molde = st.tabs(["Explorar jerarquía", "Consultar molde"])

with tab_jerarquia:
    equipos = get_equipos()
    if not equipos:
        st.warning("No hay equipos activos registrados (tabla ACTIVOS).")
    else:
        equipo = st.selectbox("Equipo", equipos, format_func=lambda e: e["nombre"])
        if equipo:
            sistemas = get_sistemas_simple(equipo["id"])
            sistema = st.selectbox("Sistema", sistemas, format_func=lambda s: s["nombre"]) if sistemas else None
            if sistema:
                subsistemas = get_subsistemas_simple(sistema["id"])
                subsistema = st.selectbox("Subsistema", subsistemas, format_func=lambda s: s["nombre"]) if subsistemas else None
                if subsistema:
                    items = get_items_simple(subsistema["id"])
                    item = st.selectbox("Ítem", items, format_func=lambda i: i["nombre"]) if items else None
                    if item:
                        averias = get_averias_simple(item["id"])
                        if averias:
                            averia = st.selectbox("Avería típica", averias, format_func=lambda a: a["nombre"])
                            if averia:
                                soluciones = get_soluciones_simple(averia["id"])
                                if soluciones:
                                    st.write("**Soluciones registradas:**")
                                    for s in soluciones:
                                        st.markdown(f"- {s['nombre']}")
                                else:
                                    st.caption("Sin soluciones registradas para esta avería.")
                        else:
                            st.caption("Sin averías registradas para este ítem.")

with tab_molde:
    molde_id = st.text_input("ID del molde (ej: MOLDE-001)")
    if st.button("Consultar"):
        info = consultar_ubicacion_molde(molde_id)
        c1, c2, c3 = st.columns(3)
        c1.metric("Nombre", info["nombre"])
        c1.metric("Ubicación física", info["ubicacion_fisica"])
        c2.metric("Ciclos actuales", info["ciclos"])
        c2.metric("Versión", info["version"])
        c3.metric("Último alistamiento", info["ultimo_alistamiento"])

        with st.expander("Ficha técnica de montaje"):
            st.json({
                "Gancho": info["gancho"], "Botadores": info["botadores"],
                "Puentes agua": info["puentes_agua"], "Puentes aire": info["puentes_aire"],
                "Chapetas": info["chapetas"], "Manipulador": info["manipulador"],
                "Atemperador": info["atemperador"], "Accesorios": info["accesorios"],
                "TIP": info["tip"],
            })
