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
    list_usuarios, crear_usuario, actualizar_usuario, set_usuario_activo,
    list_feature_flags, set_feature_flag, MODULOS_DISPONIBLES, ROLES_DISPONIBLES,
    get_feature_flags_full, set_feature_flag_full,
    list_tables, get_table_preview, get_table_row_count, run_readonly_query,
)

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

if st.session_state["usuario"]["rol"] not in ("PLANEADOR", "AUDITOR"):
    st.error("No tienes permisos para ver esta sección.")
    st.stop()

st.title("⚙️ Administración")

tab_modulos, tab_usuarios, tab_crear_usuario, tab_db = st.tabs(
    ["Módulos de la app", "Usuarios", "➕ Crear usuario", "🗄️ Explorador de base de datos"]
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
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
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
    st.subheader("🗄️ Explorador de base de datos")
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
        if st.button("▶️ Ejecutar consulta"):
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
