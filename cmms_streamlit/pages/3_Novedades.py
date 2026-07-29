"""
pages/3_Novedades.py
======================
PENDIENTE DE MIGRAR. Origen: novedades_consulta.gs (~400 líneas).
Registra fallas reportadas por técnicos, con evidencias (fotos) que en
el original se guardaban en Drive (NOV_EVIDENCIAS) — migrar a Cloud
Storage y guardar solo la URL en la tabla `nov_evidencias`.
Sigue el mismo patrón: services/novedades_service.py + esta página.
"""

import streamlit as st

st.set_page_config(page_title="Novedades · CMMS", page_icon="📋")

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("📋 Novedades")
st.warning("Módulo pendiente de portar desde novedades_consulta.gs.")
