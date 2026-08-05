"""
app_pages/admin.py
====================
Panel de administración: crear/editar/desactivar usuarios, y prender o
apagar módulos completos de la app (feature flags). Es la pieza central
de lo que pediste: todo lo de base de datos manejable desde el
frontend, con el rol PLANEADOR/AUDITOR.
"""

import streamlit as st

from services.admin_service import (
    list_usuarios, crear_usuario, actualizar_usuario, set_usuario_activo, eliminar_usuario,
    list_feature_flags, set_feature_flag, MODULOS_DISPONIBLES, ROLES_DISPONIBLES,
    get_feature_flags_full, set_feature_flag_full,
    SUBFEATURES_CATALOGO, get_subfeatures_full, set_subfeature_full,
    list_tables, get_table_preview, get_table_row_count, run_readonly_query,
)
from services.activos_service import list_activos_todos, eliminar_activos_bulk, desactivar_activo, editar_campo_bulk
from services.jerarquia_service import (
    list_nodos, crear_nodo, actualizar_nodo, desactivar_nodo, eliminar_nodo,
    list_tipos_activo, crear_tipo_activo, desactivar_tipo_activo,
    CLASES_ISO14224, TIPOS_JERARQUIA,
)

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

if st.session_state["usuario"]["rol"] not in ("PLANEADOR", "AUDITOR"):
    st.error("No tienes permisos para ver esta sección.")
    st.stop()

st.title("Administración")

tab_modulos, tab_subfunciones, tab_usuarios, tab_crear_usuario, tab_jerarquia, tab_db, tab_activos_masivo = st.tabs(
    ["Módulos de la app", " Permisos por sub-función", "Usuarios", " Crear usuario", " Jerarquía ISO 14224",
     " Explorador de base de datos", " Gestión masiva de activos"]
)

with tab_modulos:
    st.subheader("Prender / apagar módulos, y elegir quién los ve")
    st.caption(
        "El interruptor prende/apaga el módulo para TODA la app. La lista "
        "de roles debajo controla, además, quién lo ve aunque esté "
        "prendido — por ejemplo, un TECNICO puede no necesitar ver Admin "
        "ni Maquilas, aunque el módulo esté activo para Planeadores."
    )
    flags_full = get_feature_flags_full()
    for modulo in MODULOS_DISPONIBLES:
        key = modulo["key"]
        info = flags_full.get(key, {"activo": True, "roles": ROLES_DISPONIBLES})

        st.markdown(f"**{modulo['label']}**")
        col1, col2 = st.columns([1, 3])
        with col1:
            nuevo_activo = st.toggle("Activo", value=info["activo"], key=f"flag_{key}")
        with col2:
            nuevos_roles = st.multiselect(
                "Visible para estos roles", ROLES_DISPONIBLES,
                default=info["roles"], key=f"roles_{key}",
                label_visibility="collapsed",
            )

        if nuevo_activo != info["activo"] or set(nuevos_roles) != set(info["roles"]):
            set_feature_flag_full(key, nuevo_activo, nuevos_roles)
            st.success(f"'{modulo['label']}' actualizado.")
            st.rerun()
        st.divider()

with tab_usuarios:
    st.subheader("Usuarios registrados")
    usuarios = list_usuarios()

    for u in usuarios:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
        with col1:
            nuevo_nombre = st.text_input("Nombre", value=u["nombre"], key=f"nom_{u['id_usuario']}",
                                           label_visibility="collapsed")
        with col2:
            st.text(u["correo"])
        with col3:
            nuevo_rol = st.selectbox(
                "Rol", ["TECNICO", "TECNICO_B", "TECNICO_MONTAJE", "PLANEADOR", "AUDITOR"],
                index=["TECNICO", "TECNICO_B", "TECNICO_MONTAJE", "PLANEADOR", "AUDITOR"].index(u["rol"])
                if u["rol"] in ["TECNICO", "TECNICO_B", "TECNICO_MONTAJE", "PLANEADOR", "AUDITOR"] else 0,
                key=f"rol_{u['id_usuario']}", label_visibility="collapsed",
            )
        with col4:
            activo = st.checkbox("Activo", value=bool(u.get("activo", True)), key=f"act_{u['id_usuario']}")
        with col5:
            if st.button("", key=f"del_{u['id_usuario']}", help="Eliminar definitivamente"):
                st.session_state[f"confirmar_del_{u['id_usuario']}"] = True

        if st.session_state.get(f"confirmar_del_{u['id_usuario']}"):
            st.warning(
                f"¿Seguro que quieres eliminar DEFINITIVAMENTE a **{u['nombre']}**? "
                "Esto no se puede deshacer. Si solo quieres que no pueda entrar, "
                "mejor desmarca la casilla 'Activo' en vez de eliminar."
            )
            c1, c2 = st.columns(2)
            if c1.button("Sí, eliminar definitivamente", key=f"confirm_yes_{u['id_usuario']}"):
                eliminar_usuario(u["id_usuario"])
                del st.session_state[f"confirmar_del_{u['id_usuario']}"]
                st.rerun()
            if c2.button("Cancelar", key=f"confirm_no_{u['id_usuario']}"):
                del st.session_state[f"confirmar_del_{u['id_usuario']}"]
                st.rerun()

        if (nuevo_nombre != u["nombre"]) or (nuevo_rol != u["rol"]):
            actualizar_usuario(u["id_usuario"], nuevo_nombre, nuevo_rol)
            st.rerun()
        if activo != bool(u.get("activo", True)):
            set_usuario_activo(u["id_usuario"], activo)
            st.rerun()

with tab_crear_usuario:
    st.subheader("Registrar un usuario nuevo")
    with st.form("crear_usuario_form", clear_on_submit=True):
        nombre = st.text_input("Nombre completo *")
        correo = st.text_input("Correo *")
        rol = st.selectbox("Rol *", ["TECNICO", "TECNICO_B", "TECNICO_MONTAJE", "PLANEADOR", "AUDITOR"])
        enviado = st.form_submit_button("Crear usuario")

    if enviado:
        if not nombre or not correo:
            st.error("Nombre y correo son obligatorios.")
        else:
            resultado = crear_usuario(nombre, correo, rol)
            st.success(f"Usuario creado: {resultado['id_usuario']} — {resultado['nombre']}")

with tab_db:
    st.subheader("Explorador de base de datos")
    st.caption(
        "Solo lectura: puedes ver el contenido de cualquier tabla y correr "
        "consultas SELECT. No se permite insertar, editar ni borrar desde aquí "
        "— eso protege los datos de un error de tecleo."
    )

    sub_tablas, sub_sql = st.tabs(["Ver tablas", "Consulta SQL personalizada"])

    with sub_tablas:
        tablas = list_tables()
        tabla_sel = st.selectbox("Tabla", tablas)
        if tabla_sel:
            try:
                total = get_table_row_count(tabla_sel)
                st.caption(f"{total} fila(s) en total. Mostrando hasta 200.")
                filas = get_table_preview(tabla_sel, limit=200)
                if filas:
                    st.dataframe(filas, use_container_width=True, hide_index=True)
                else:
                    st.info("La tabla está vacía.")
            except Exception as e:
                st.error(f"Error consultando la tabla: {e}")

    with sub_sql:
        st.caption("Ejemplo: SELECT * FROM ot WHERE prioridad = 'ALTA' ORDER BY fecha DESC")
        sql_input = st.text_area("Consulta SQL (solo SELECT)", height=100,
                                   placeholder="SELECT * FROM activos WHERE tipo = 'MOLDE'")
        if st.button("▶ Ejecutar consulta"):
            if not sql_input.strip():
                st.warning("Escribe una consulta primero.")
            else:
                try:
                    resultado = run_readonly_query(sql_input)
                    if resultado:
                        st.success(f"{len(resultado)} fila(s) devueltas.")
                        st.dataframe(resultado, use_container_width=True, hide_index=True)
                    else:
                        st.info("La consulta no devolvió filas.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error en la consulta: {e}")

with tab_jerarquia:
    st.subheader("Jerarquía técnica y clasificación ISO 14224")
    st.caption(
        "ISO 14224 clasifica cada nivel del equipo como Unidad de equipo, "
        "Subunidad, Componente o Ítem mantenible. Esto es adicional al tipo "
        "(Sistema/Subsistema/Ítem/Parte) que ya usa la jerarquía existente."
    )

    sub_nodos, sub_crear_nodo, sub_tipos = st.tabs(
        ["Nodos existentes", " Crear nodo", "Catálogo de tipos de activo"]
    )

    with sub_nodos:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["TODOS"] + TIPOS_JERARQUIA)
        nodos = list_nodos(tipo=None if filtro_tipo == "TODOS" else filtro_tipo)

        if not nodos:
            st.info("No hay nodos con ese filtro.")
        else:
            for n in nodos:
                with st.expander(f"{n['nombre']} ({n.get('tipo', '—')}) — {n.get('clase_iso14224') or 'sin clasificar'}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_e = st.text_input("Nombre", value=n["nombre"], key=f"jn_{n['id_activo']}")
                        tipo_e = st.selectbox("Tipo", TIPOS_JERARQUIA,
                                                index=TIPOS_JERARQUIA.index(n["tipo"]) if n.get("tipo") in TIPOS_JERARQUIA else 0,
                                                key=f"jt_{n['id_activo']}")
                    with col2:
                        clase_actual = n.get("clase_iso14224")
                        clase_e = st.selectbox(
                            "Clase ISO 14224", ["(sin clasificar)"] + CLASES_ISO14224,
                            index=(CLASES_ISO14224.index(clase_actual) + 1) if clase_actual in CLASES_ISO14224 else 0,
                            key=f"jc_{n['id_activo']}",
                        )

                    bcol1, bcol2 = st.columns(2)
                    if bcol1.button("Guardar", key=f"jsave_{n['id_activo']}"):
                        clase_final = None if clase_e == "(sin clasificar)" else clase_e
                        actualizar_nodo(n["id_activo"], nombre_e, tipo_e, clase_final)
                        st.success("Actualizado.")
                        st.rerun()
                    if bcol2.button("Desactivar", key=f"jdeact_{n['id_activo']}"):
                        desactivar_nodo(n["id_activo"])
                        st.warning("Nodo desactivado.")
                        st.rerun()

    with sub_crear_nodo:
        st.write("Crear un nodo nuevo en la jerarquía técnica.")
        with st.form("crear_nodo_form", clear_on_submit=True):
            nombre_nuevo = st.text_input("Nombre *")
            tipo_nuevo = st.selectbox("Tipo *", TIPOS_JERARQUIA)
            padre_opciones = [{"id_activo": None, "nombre": "— Ninguno (raíz) —"}] + list_nodos()
            padre_nuevo = st.selectbox("Nodo padre", padre_opciones, format_func=lambda p: p["nombre"])
            clase_nueva = st.selectbox("Clase ISO 14224", ["(sin clasificar)"] + CLASES_ISO14224)
            enviado = st.form_submit_button("Crear nodo")

        if enviado:
            if not nombre_nuevo:
                st.error("El nombre es obligatorio.")
            else:
                clase_final = None if clase_nueva == "(sin clasificar)" else clase_nueva
                padre_id = padre_nuevo.get("id_activo") if isinstance(padre_nuevo, dict) else None
                resultado = crear_nodo(nombre_nuevo, tipo_nuevo, padre_id, clase_final)
                st.success(f"Nodo creado: {resultado['id_activo']} — {resultado['nombre']}")

    with sub_tipos:
        st.write("Catálogo de tipos de activo (estandariza lo que antes era texto libre).")
        tipos = list_tipos_activo()
        if tipos:
            st.dataframe(tipos, use_container_width=True, hide_index=True)
        else:
            st.info("No hay tipos de activo registrados.")

        st.divider()
        with st.form("crear_tipo_activo_form", clear_on_submit=True):
            nombre_tipo = st.text_input("Nombre del tipo *")
            clase_tipo = st.selectbox("Clase ISO 14224 *", CLASES_ISO14224)
            descripcion_tipo = st.text_input("Descripción")
            enviado_tipo = st.form_submit_button("Crear tipo de activo")

        if enviado_tipo:
            if not nombre_tipo:
                st.error("El nombre es obligatorio.")
            else:
                resultado = crear_tipo_activo(nombre_tipo, clase_tipo, descripcion_tipo)
                st.success(f"Tipo de activo creado: {resultado['nombre']}")

with tab_activos_masivo:
    st.subheader("Gestión masiva de activos")
    st.warning(
        "Exclusivo de Admin. Útil para limpiar cargas de prueba o datos "
        "erróneos. El borrado definitivo NO se puede deshacer — si solo "
        "quieres que dejen de aparecer en los módulos, usa 'Desactivar "
        "masivamente' en vez de eliminar."
    )

    busqueda_masiva = st.text_input("Filtrar por tag, nombre o ID (para achicar la lista)")
    todos_los_activos = list_activos_todos(solo_activos=True)

    if busqueda_masiva:
        b = busqueda_masiva.lower()
        todos_los_activos = [
            a for a in todos_los_activos
            if b in (a.get("nombre") or "").lower()
            or b in (a.get("id_activo") or "").lower()
            or b in (a.get("tag") or "").lower()
        ]

    st.caption(f"{len(todos_los_activos)} activo(s) coinciden con el filtro actual.")

    seleccionar_todos = st.checkbox("Seleccionar TODOS los que coinciden con el filtro de arriba")

    opciones = {
        f"{(a.get('tag') or a['id_activo'])} — {a.get('nombre', '—')}": a["id_activo"]
        for a in todos_los_activos
    }

    if seleccionar_todos:
        seleccionados_labels = list(opciones.keys())
        st.multiselect("Activos seleccionados", list(opciones.keys()),
                         default=seleccionados_labels, key="ms_activos_todos", disabled=True)
    else:
        seleccionados_labels = st.multiselect("Selecciona los activos", list(opciones.keys()))

    ids_seleccionados = [opciones[lbl] for lbl in seleccionados_labels]

    if ids_seleccionados:
        st.write(f"**{len(ids_seleccionados)} activo(s) seleccionado(s).**")

        st.divider()
        st.write("** Editar un campo en lote** (aplica el mismo valor a todos los seleccionados)")
        col_campo, col_valor, col_btn = st.columns([1, 2, 1])
        with col_campo:
            campo_masivo = st.selectbox("Campo", ["zona", "tipoactivo", "familia", "fabricante"])
        with col_valor:
            valor_masivo = st.text_input("Nuevo valor para todos los seleccionados")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Aplicar a todos"):
                if not valor_masivo:
                    st.error("Escribe un valor.")
                else:
                    total_editados = editar_campo_bulk(ids_seleccionados, campo_masivo, valor_masivo)
                    st.success(f"{total_editados} activo(s) actualizado(s) con {campo_masivo} = '{valor_masivo}'.")
                    st.rerun()

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Desactivar seleccionados (reversible)"):
                for id_act in ids_seleccionados:
                    desactivar_activo(id_act)
                st.success(f"{len(ids_seleccionados)} activo(s) desactivado(s).")
                st.rerun()

        with col2:
            if st.button("Eliminar DEFINITIVAMENTE", type="primary"):
                st.session_state["confirmar_borrado_masivo"] = True

        if st.session_state.get("confirmar_borrado_masivo"):
            st.error(
                f"¿Seguro que quieres borrar DEFINITIVAMENTE estos "
                f"{len(ids_seleccionados)} activo(s)? Esta acción no se puede deshacer."
            )
            c1, c2 = st.columns(2)
            if c1.button("Sí, borrar definitivamente", key="confirm_bulk_delete_yes"):
                total = eliminar_activos_bulk(ids_seleccionados)
                del st.session_state["confirmar_borrado_masivo"]
                st.success(f"{total} activo(s) eliminado(s) definitivamente.")
                st.rerun()
            if c2.button("Cancelar", key="confirm_bulk_delete_no"):
                del st.session_state["confirmar_borrado_masivo"]
                st.rerun()

with tab_subfunciones:
    st.subheader("Permisos por sub-función (dentro de cada módulo)")
    st.caption(
        "Control más fino que 'Módulos de la app': aquí prendes/apagas "
        "pestañas o funciones ESPECÍFICAS dentro de un módulo, y eliges "
        "qué roles las ven. Ej: dejar 'Cargar CSV masivo' solo para "
        "Planeador dentro del módulo Activos, sin apagar todo el módulo."
    )

    modulo_elegido = st.selectbox(
        "Módulo", list(SUBFEATURES_CATALOGO.keys()),
        format_func=lambda k: next((m["label"] for m in MODULOS_DISPONIBLES if m["key"] == k), k),
        key="modulo_subfeatures",
    )

    subfeatures_full = get_subfeatures_full(modulo_elegido)
    catalogo_modulo = SUBFEATURES_CATALOGO.get(modulo_elegido, [])

    for sf in catalogo_modulo:
        key = sf["key"]
        info = subfeatures_full.get(key, {"activo": True, "roles": ROLES_DISPONIBLES})

        st.markdown(f"**{sf['label']}**")
        col1, col2 = st.columns([1, 3])
        with col1:
            nuevo_activo_sf = st.toggle("Activo", value=info["activo"], key=f"sfflag_{modulo_elegido}_{key}")
        with col2:
            nuevos_roles_sf = st.multiselect(
                "Visible para estos roles", ROLES_DISPONIBLES,
                default=info["roles"], key=f"sfroles_{modulo_elegido}_{key}",
                label_visibility="collapsed",
            )

        if nuevo_activo_sf != info["activo"] or set(nuevos_roles_sf) != set(info["roles"]):
            set_subfeature_full(modulo_elegido, key, nuevo_activo_sf, nuevos_roles_sf)
            st.success(f"'{sf['label']}' actualizado.")
            st.rerun()
        st.divider()
