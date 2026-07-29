"""
pages/2_Ordenes_de_Trabajo.py
================================
PENDIENTE DE MIGRAR. Módulo origen en Apps Script: ot_consulta.gs +
ot_gestion.gs + pdf_generator.gs (~1.900 líneas en total: creación de OT,
asignación de técnico, tiempos, repuestos, cierre, generación de PDF).

Sigue el patrón de pages/1_Activos.py + services/activos_service.py:
    1. Crear services/ot_service.py portando función por función desde
       ot_consulta.gs y ot_gestion.gs (misma lógica, cambiando
       sheet.getDataRange() por db.fetch_all(...)).
    2. La generación de PDF (pdf_generator.gs usaba DocumentApp/DriveApp)
       debe migrar a una librería Python (ej. reportlab o WeasyPrint) +
       guardar el archivo en Google Cloud Storage en vez de Drive.
    3. Construir esta página con formularios Streamlit (st.form) para
       crear/editar OT, y st.dataframe para listarlas.
"""

import streamlit as st

st.set_page_config(page_title="Órdenes de Trabajo · CMMS", page_icon="🛠️")

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🛠️ Órdenes de Trabajo")
st.warning(
    "Módulo pendiente de portar desde ot_consulta.gs / ot_gestion.gs / "
    "pdf_generator.gs. Ver docstring de este archivo para el plan."
)
