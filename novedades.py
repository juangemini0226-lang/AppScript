"""
app_pages/ordenes_trabajo.py
==============================
Creación de OT (directa o desde una novedad) y tablero de "trabajos en
curso" — lo que el usuario pidió como control de piso de mantenimiento.
"""

import streamlit as st

from services.ot_service import crear_ot, list_ot, cambiar_estado_ot, get_tiempos_ot, ESTADOS_OT
from services.dashboard_service import get_ot_por_estado
from services.novedades_service import list_novedades
from services.activos_service import get_equipos, get_sistemas_simple, get_subsistemas_simple, get_items_simple
from services.users_service import get_tecnicos_simple

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

usuario = st.session_state["usuario"]

st.title("🛠️ Órdenes de Trabajo")

tab_kanban, tab_tablero, tab_crear = st.tabs(["📊 Tablero Kanban", "Lista y detalle", "➕ Crear OT"])

with tab_kanban:
    conteos = get_ot_por_estado()
    colores_prioridad = {"ALTA": "#e74c3c", "MEDIA": "#f39c12", "BAJA": "#27ae60"}
    cols = st.columns(len(ESTADOS_OT))
    for col, estado in zip(cols, ESTADOS_OT):
        with col:
            st.metric(estado.replace("_", " "), conteos.get(estado, 0))
            ordenes_col = list_ot(estado=estado, limit=10)
            for ot in ordenes_col:
                color = colores_prioridad.get(ot.get("prioridad"), "#bbb")
                st.markdown(
                    f"<div style='border-left:4px solid {color};border:1px solid #e6e6e6;"
                    f"border-left-width:4px;border-radius:8px;padding:8px 10px;"
                    f"margin-bottom:8px;font-size:0.85em;background:#fafafa;'>"
                    f"<b>{ot['id_ot']}</b><br>{ot.get('equipo_id','—')}<br>"
                    f"<span style='color:{color};font-weight:600;'>{ot.get('prioridad','—')}</span></div>",
                    unsafe_allow_html=True,
                )
            if not ordenes_col:
                st.caption("Sin OT en este estado.")

with tab_tablero:
    filtro = st.selectbox("Filtrar por estado", ["TODAS"] + ESTADOS_OT)
    ordenes = list_ot(estado=None if filtro == "TODAS" else filtro)

    if not ordenes:
        st.info("No hay órdenes de trabajo con ese filtro.")
    else:
        for ot in ordenes:
            with st.expander(f"{ot['id_ot']} · {ot.get('equipo_id', '—')} · {ot.get('estado', '—')}"):
                st.write(f"**Prioridad:** {ot.get('prioridad', '—')}")
                st.write(f"**Descripción:** {ot.get('descripcion_solicitud', '—')}")
                st.write(f"**Fecha:** {ot.get('fecha', '—')}")

                tiempos = get_tiempos_ot(ot["id_ot"])
                if tiempos:
                    st.caption("Historial de avance:")
                    for t in tiempos:
                        st.markdown(f"- `{t['creado_en']}` — {t['comentario']} ({t['minutos']} min)")

                st.divider()
                st.caption("Registrar avance / cambiar estado")
                tecnicos = get_tecnicos_simple()
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    comentario = st.text_input("Comentario", key=f"com_{ot['id_ot']}")
                with col2:
                    nuevo_estado = st.selectbox("Nuevo estado", ESTADOS_OT,
                                                  index=ESTADOS_OT.index(ot.get("estado", "PROGRAMADA"))
                                                  if ot.get("estado") in ESTADOS_OT else 0,
                                                  key=f"est_{ot['id_ot']}")
                with col3:
                    minutos = st.number_input("Minutos", min_value=0, step=5, key=f"min_{ot['id_ot']}")

                tecnico_sel = st.selectbox("Técnico", tecnicos, format_func=lambda t: t["nombre"],
                                             key=f"tec_{ot['id_ot']}") if tecnicos else None

                if st.button("Guardar avance", key=f"btn_{ot['id_ot']}"):
                    cambiar_estado_ot(
                        ot["id_ot"], nuevo_estado,
                        tecnico_id=tecnico_sel["id"] if tecnico_sel else usuario["email"],
                        minutos=minutos, comentario=comentario or "(sin comentario)",
                    )
                    st.success("Avance registrado.")
                    st.rerun()

with tab_crear:
    st.subheader("Crear una orden de trabajo")

    origen = st.radio("Origen", ["Directa", "Desde una novedad"])
    novedad_sel = None
    if origen == "Desde una novedad":
        novedades_pendientes = list_novedades(estado="ASIGNADA")
        if novedades_pendientes:
            novedad_sel = st.selectbox(
                "Novedad", novedades_pendientes,
                format_func=lambda n: f"{n['id_nov']} — {n.get('descripcion', '')[:60]}"
            )
        else:
            st.info("No hay novedades pendientes de convertir en OT.")

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
        item = st.selectbox("Ítem", items, format_func=lambda i: i["nombre"]) if items else None

    with st.form("crear_ot_form", clear_on_submit=True):
        tecnicos = get_tecnicos_simple()
        tecnico = st.selectbox("Técnico asignado", tecnicos, format_func=lambda t: t["nombre"]) if tecnicos else None
        descripcion = st.text_area("Descripción de la solicitud *")
        prioridad = st.selectbox("Prioridad", ["BAJA", "MEDIA", "ALTA"], index=1)
        tipo_actividad = st.selectbox("Tipo de actividad", ["CORRECTIVO", "PREVENTIVO", "ALISTAMIENTO"])
        fecha_estimada = st.date_input("Fecha estimada de cierre")
        enviado = st.form_submit_button("Crear OT")

    if enviado:
        if not descripcion:
            st.error("La descripción es obligatoria.")
        else:
            resultado = crear_ot({
                "novedad_id": novedad_sel["id_nov"] if novedad_sel else None,
                "equipo_id": equipo["id"] if equipo else None,
                "sistema_id": sistema["id"] if sistema else None,
                "subsistema_id": subsistema["id"] if subsistema else None,
                "item_id": item["id"] if item else None,
                "prioridad": prioridad,
                "tecnico_id": tecnico["id"] if tecnico else None,
                "descripcion_solicitud": descripcion,
                "tipo_actividad": tipo_actividad,
                "fecha_estimada": fecha_estimada,
            }, planeador_id=usuario["email"])
            st.success(f"OT creada: {resultado['id_ot']}")
