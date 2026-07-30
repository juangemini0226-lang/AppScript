"""
app_pages/activos.py
======================
Consulta de jerarquía técnica + creación de activos nuevos desde el
frontend (planta, equipo o molde), sin tocar el Sheet ni la base a mano.
"""

import streamlit as st

from services.activos_service import (
    get_equipos, get_sistemas_simple, get_subsistemas_simple, get_items_simple,
    get_averias_simple, get_soluciones_simple, consultar_ubicacion_molde,
    list_activos_todos, crear_activo, actualizar_activo, desactivar_activo,
)

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🏭 Activos y jerarquía técnica")

tab_jerarquia, tab_molde, tab_crear, tab_listado = st.tabs(
    ["Explorar jerarquía", "Consultar molde", "➕ Crear activo", "Listado completo"]
)

with tab_jerarquia:
    equipos = get_equipos()
    if not equipos:
        st.warning("No hay equipos activos registrados.")
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

with tab_molde:
    molde_id = st.text_input("ID del molde (ej: MOL-001)")
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

with tab_crear:
    st.subheader("Registrar un activo nuevo")
    with st.form("crear_activo_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del activo *")
            tipo = st.selectbox("Tipo *", ["PLANTA", "EQUIPO", "MOLDE"])
            fabricante = st.text_input("Fabricante")
        with col2:
            ubicacion = st.text_input("Ubicación física")
            familia = st.text_input("Familia (ej: MOLDE, INYECTORA)")
            peso = st.number_input("Peso (kg)", min_value=0.0, step=1.0)

        padre_opciones = [{"id": None, "nombre": "— Ninguno (raíz) —"}] + list_activos_todos()
        padre = st.selectbox("Activo padre (jerarquía)", padre_opciones,
                               format_func=lambda a: a.get("nombre", a.get("id_activo", "—")))

        enviado = st.form_submit_button("Crear activo")

    if enviado:
        if not nombre:
            st.error("El nombre es obligatorio.")
        else:
            padre_id = padre.get("id") if isinstance(padre, dict) and "id" in padre else padre.get("id_activo")
            resultado = crear_activo({
                "nombre": nombre, "tipo": tipo, "fabricante": fabricante or None,
                "ubicacion": ubicacion or None, "familia": familia or None,
                "peso": peso or None, "padre_id": padre_id,
            })
            st.success(f"Activo creado: {resultado['id_activo']} — {resultado['nombre']}")

with tab_listado:
    st.subheader("Listado completo — edición rápida")
    busqueda = st.text_input("🔍 Buscar por nombre o ID")

    activos = list_activos_todos(solo_activos=True)
    if busqueda:
        b = busqueda.lower()
        activos = [a for a in activos if b in (a.get("nombre") or "").lower()
                   or b in (a.get("id_activo") or "").lower()]

    if not activos:
        st.info("No hay activos que coincidan.")
    else:
        st.caption(f"{len(activos)} resultado(s). Expande una fila para editarla.")
        for a in activos:
            with st.expander(f"{a['id_activo']} — {a.get('nombre', '—')} ({a.get('tipo', '—')})"):
                col1, col2 = st.columns(2)
                with col1:
                    nombre_e = st.text_input("Nombre", value=a.get("nombre", ""), key=f"edn_{a['id_activo']}")
                    ubicacion_e = st.text_input("Ubicación", value=a.get("ubicacion") or "", key=f"edu_{a['id_activo']}")
                with col2:
                    fabricante_e = st.text_input("Fabricante", value=a.get("fabricante") or "", key=f"edf_{a['id_activo']}")
                    familia_e = st.text_input("Familia", value=a.get("familia") or "", key=f"edfam_{a['id_activo']}")

                bcol1, bcol2 = st.columns(2)
                if bcol1.button("💾 Guardar cambios", key=f"save_{a['id_activo']}"):
                    actualizar_activo(a["id_activo"], {
                        "nombre": nombre_e, "ubicacion": ubicacion_e or None,
                        "fabricante": fabricante_e or None, "familia": familia_e or None,
                    })
                    st.success("Actualizado.")
                    st.rerun()
                if bcol2.button("🗑️ Desactivar", key=f"deact_{a['id_activo']}"):
                    desactivar_activo(a["id_activo"])
                    st.warning("Activo desactivado.")
                    st.rerun()
