"""
app_pages/maquilas.py
=======================
Gestión de moldes entregados a maquiladores externos: registrar envíos,
reportar producción, y llevar el historial por molde.
"""

import streamlit as st

from services.maquilas_service import (
    list_maquiladores, list_registros, crear_registro, crear_maquilador,
)
from utils.tabs import build_tabs

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

usuario = st.session_state["usuario"]

st.title("🏗️ Maquilas")

tabs = build_tabs("maquilas", usuario["rol"])

if "historial" in tabs:
    with tabs["historial"]:
        molde_filtro = st.text_input("🔍 Filtrar por ID de molde (opcional)")
        registros = list_registros(molde_id=molde_filtro or None)
        if registros:
            st.dataframe(registros, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros de maquilas.")

if "registrar_movimiento" in tabs:
    with tabs["registrar_movimiento"]:
        st.subheader("Registrar envío o producción")
        maquiladores = list_maquiladores()

        with st.form("registrar_maquila_form", clear_on_submit=True):
            molde_id = st.text_input("ID del molde *")
            maquilador = st.selectbox("Maquilador", maquiladores,
                                        format_func=lambda m: m["nombre_empresa"]) if maquiladores else None
            tipo_movimiento = st.selectbox("Tipo de movimiento", ["ENVIO", "PRODUCCION"])
            orden_produccion = st.text_input("Orden de producción (si aplica)")
            unidades = st.number_input("Unidades inyectadas", min_value=0, step=100)
            observaciones = st.text_area("Observaciones")
            enviado = st.form_submit_button("Registrar")

        if enviado:
            if not molde_id or not maquilador:
                st.error("El molde y el maquilador son obligatorios.")
            else:
                resultado = crear_registro({
                    "molde_id": molde_id,
                    "maquilador_id": maquilador["id_maquilador"],
                    "tipo_movimiento": tipo_movimiento,
                    "orden_produccion": orden_produccion or None,
                    "unidades_inyectadas": unidades or None,
                    "observaciones": observaciones or None,
                }, registrado_por=usuario["email"])
                st.success(f"Movimiento registrado: {resultado['id_registro']}")

if "nuevo_maquilador" in tabs:
    with tabs["nuevo_maquilador"]:
        st.subheader("Registrar un maquilador nuevo")
        with st.form("crear_maquilador_form", clear_on_submit=True):
            nombre_empresa = st.text_input("Nombre de la empresa *")
            contacto_nombre = st.text_input("Nombre del contacto")
            contacto_telefono = st.text_input("Teléfono del contacto")
            enviado = st.form_submit_button("Crear maquilador")

        if enviado:
            if not nombre_empresa:
                st.error("El nombre de la empresa es obligatorio.")
            else:
                resultado = crear_maquilador(nombre_empresa, contacto_nombre, contacto_telefono)
                st.success(f"Maquilador creado: {resultado['id_maquilador']} — {resultado['nombre_empresa']}")

        st.divider()
        st.caption("Maquiladores activos:")
        for m in list_maquiladores():
            st.markdown(f"- **{m['nombre_empresa']}** — {m.get('contacto_nombre', '—')} ({m.get('contacto_telefono', '—')})")
