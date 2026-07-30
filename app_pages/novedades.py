"""
app_pages/novedades.py
=========================
Reporte de novedades (fallas) desde planta, y tablero de seguimiento.
"""

import streamlit as st

from services.novedades_service import crear_novedad, list_novedades, ESTADOS
from services.activos_service import get_equipos, get_sistemas_simple, get_subsistemas_simple, get_items_simple
from services.users_service import get_tecnicos_simple
from services.ot_service import crear_ot

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

usuario = st.session_state["usuario"]

st.title("📋 Novedades")

tab_reportar, tab_tablero = st.tabs(["➕ Reportar novedad", "Tablero de seguimiento"])

with tab_reportar:
    st.subheader("Reportar una falla")

    equipos = get_equipos()
    equipo = st.selectbox("Equipo", equipos, format_func=lambda e: e["nombre"]) if equipos else None
    sistema = subsistema = item = None
    if equipo:
        sistemas = get_sistemas_simple(equipo["id"])
        sistema = st.selectbox("Sistema", sistemas, format_func=lambda s: s["nombre"]) if sistemas else None
    if sistema:
        subsistemas = get_subsistemas_simple(sistema["id"])
        subsistema = st.selectbox("Subsistema", subsistemas, format_func=lambda s: s["nombre"]) if subsistemas else None
    if subsistema:
        items = get_items_simple(subsistema["id"])
        item = st.selectbox("Ítem afectado", items, format_func=lambda i: i["nombre"]) if items else None

    with st.form("reportar_novedad_form", clear_on_submit=True):
        tecnicos = get_tecnicos_simple()
        tecnico = st.selectbox("Reportado por (técnico)", tecnicos, format_func=lambda t: t["nombre"]) if tecnicos else None
        descripcion = st.text_area("Descripción de la falla *")
        prioridad = st.selectbox("Prioridad", ["BAJA", "MEDIA", "ALTA"], index=1)
        zona = st.text_input("Zona / línea")
        maquina_parada = st.selectbox("¿Máquina parada?", ["NO", "SI"])
        enviado = st.form_submit_button("Reportar novedad")

    if enviado:
        if not descripcion:
            st.error("La descripción es obligatoria.")
        else:
            resultado = crear_novedad({
                "zona": zona or None,
                "tecnico_id": tecnico["id"] if tecnico else None,
                "equipo_id": equipo["id"] if equipo else None,
                "sistema_id": sistema["id"] if sistema else None,
                "subsistema_id": subsistema["id"] if subsistema else None,
                "item_id": item["id"] if item else None,
                "descripcion": descripcion,
                "prioridad": prioridad,
                "maquina": maquina_parada,
            }, creado_por=usuario["email"])
            st.success(f"Novedad reportada: {resultado['id_nov']}")

with tab_tablero:
    filtro = st.selectbox("Filtrar por estado", ["TODAS"] + ESTADOS)
    novedades = list_novedades(estado=None if filtro == "TODAS" else filtro)

    if not novedades:
        st.info("No hay novedades con ese filtro.")
    else:
        for n in novedades:
            etiqueta = f"{n['id_nov']} · {n.get('prioridad', '—')} · {n.get('estado', '—')}"
            with st.expander(etiqueta):
                st.write(f"**Descripción:** {n.get('descripcion', '—')}")
                st.write(f"**Zona:** {n.get('zona', '—')} · **Equipo:** {n.get('equipo_id', '—')}")
                st.write(f"**Fecha:** {n.get('fecha', '—')}")

                if n.get("estado") == "ASIGNADA":
                    if st.button("⚡ Convertir en OT", key=f"conv_{n['id_nov']}"):
                        resultado = crear_ot({
                            "novedad_id": n["id_nov"],
                            "equipo_id": n.get("equipo_id"),
                            "sistema_id": n.get("sistema_id"),
                            "subsistema_id": n.get("subsistema_id"),
                            "item_id": n.get("item_id"),
                            "prioridad": n.get("prioridad", "MEDIA"),
                            "descripcion_solicitud": n.get("descripcion"),
                            "tipo_actividad": "CORRECTIVO",
                        }, planeador_id=usuario["email"])
                        st.success(f"OT creada: {resultado['id_ot']} — ve a Órdenes de Trabajo para asignarla.")
                        st.rerun()
                elif n.get("ot_id"):
                    st.caption(f"Ya convertida en OT: {n['ot_id']}")
