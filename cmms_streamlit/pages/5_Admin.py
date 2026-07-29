"""
pages/5_Admin.py
==================
PENDIENTE DE MIGRAR. Origen: admin.html + admin_geestion.gs + adminLogic.gs
+ parametrización.html. Gestión de usuarios, repuestos, parámetros
(PARAM_CHEQUEOS, PARAM_VERSIONES), tareas programadas, reportes
(reportes.gs). Restringir por rol (solo PLANEADOR/AUDITOR, ver
services/users_service.py).
"""

import streamlit as st

st.set_page_config(page_title="Admin · CMMS", page_icon="⚙️")

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

if st.session_state["usuario"]["rol"] not in ("PLANEADOR", "AUDITOR"):
    st.error("No tienes permisos para ver esta sección.")
    st.stop()

st.title("⚙️ Administración")
st.warning("Módulo pendiente de portar (admin.html, admin_geestion.gs, adminLogic.gs, reportes.gs).")
