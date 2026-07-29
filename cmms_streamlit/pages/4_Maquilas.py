"""
pages/4_Maquilas.py
=====================
PENDIENTE DE MIGRAR. Origen: maquilas.html + lógica repartida en
código.gs / admin_geestion.gs. Gestiona moldes/periféricos entregados
a maquiladores externos (tablas maquiladores, maquilas).
"""

import streamlit as st

st.set_page_config(page_title="Maquilas · CMMS", page_icon="🏗️")

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🏗️ Maquilas")
st.warning("Módulo pendiente de portar (maquilas.html + código.gs).")
