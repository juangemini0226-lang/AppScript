"""
app_pages/maquilas.py
=======================
PENDIENTE de portar la lógica completa (entrega/recepción de moldes a
maquiladores externos). Ya migrado en base de datos (tablas
maquiladores, maquilas con datos reales). Sigue el patrón de
novedades_service.py / ot_service.py para construir maquilas_service.py.
"""

import streamlit as st

from db.factory import get_connector

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🏗️ Maquilas")

db = get_connector()
maquilas = db.fetch_all("maquilas", limit=100)

if maquilas:
    st.caption("Vista de solo lectura por ahora — falta portar creación/edición.")
    st.dataframe(maquilas, use_container_width=True, hide_index=True)
else:
    st.info("No hay registros de maquilas.")
