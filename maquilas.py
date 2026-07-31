"""
app_pages/activos.py
======================
Consulta de jerarquía técnica + creación de activos nuevos desde el
frontend (planta, equipo o molde), sin tocar el Sheet ni la base a mano.
"""

import io

import streamlit as st
import pandas as pd

from services.activos_service import (
    get_equipos, get_sistemas_simple, get_subsistemas_simple, get_items_simple,
    get_averias_simple, get_soluciones_simple, consultar_ubicacion_molde,
    list_activos_todos, crear_activo, actualizar_activo, desactivar_activo,
    crear_activos_bulk, exportar_activos_para_ubicacion, importar_ubicaciones_bulk,
)

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🏭 Activos y jerarquía técnica")

tab_jerarquia, tab_molde, tab_crear, tab_csv, tab_ubicaciones, tab_listado = st.tabs(
    ["Explorar jerarquía", "Consultar molde", "➕ Crear activo", "📤 Cargar CSV masivo",
     "📍 Plantilla de ubicaciones", "Listado completo"]
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
    molde_id = st.text_input("Tag del molde (el código con el que lo llaman en planta)")
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
            tag = st.text_input("Tag / código de planta (como lo llaman)")
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
                "nombre": nombre, "tag": tag or None, "tipo": tipo, "fabricante": fabricante or None,
                "ubicacion": ubicacion or None, "familia": familia or None,
                "peso": peso or None, "padre_id": padre_id,
            })
            st.success(f"Activo creado: {resultado['id_activo']} — {resultado['nombre']}")

with tab_csv:
    st.subheader("Cargar activos desde un CSV")
    st.caption(
        "Sube un archivo CSV con tus activos, elige qué columna de tu archivo "
        "corresponde a cada campo del sistema, revisa la vista previa, y confirma "
        "la carga. Los activos creados quedan editables normalmente en 'Listado completo'."
    )

    archivo = st.file_uploader("Archivo CSV", type=["csv"])

    if archivo is not None:
        try:
            # Detecta separador automáticamente (coma o punto y coma, común en exports de Excel en español)
            df = pd.read_csv(archivo, sep=None, engine="python")
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")
            df = None

        if df is not None:
            st.write(f"**{len(df)} filas encontradas.** Vista previa:")
            st.dataframe(df.head(10), use_container_width=True)

            st.divider()
            st.write("**Paso 2: elige qué columna de tu CSV corresponde a cada campo**")

            columnas_csv = ["(no usar)"] + list(df.columns)

            campos_sistema = [
                ("nombre", "Nombre del activo *", True),
                ("tag", "Tag / código con el que lo llaman en planta", False),
                ("tipo", "Tipo (PLANTA/EQUIPO/MOLDE)", False),
                ("tipoactivo", "Tipo de activo (ej: MOLDE, INYECTORA)", False),
                ("fabricante", "Fabricante", False),
                ("ubicacion", "Ubicación física", False),
                ("familia", "Familia", False),
                ("peso", "Peso", False),
            ]

            mapeo = {}
            col_izq, col_der = st.columns(2)
            for i, (campo, etiqueta, obligatorio) in enumerate(campos_sistema):
                destino = col_izq if i % 2 == 0 else col_der
                with destino:
                    # intenta adivinar la columna por coincidencia de nombre
                    sugerida = next((c for c in df.columns if campo.lower() in c.lower()), "(no usar)")
                    idx_default = columnas_csv.index(sugerida) if sugerida in columnas_csv else 0
                    seleccion = st.selectbox(
                        f"{etiqueta}{' (obligatorio)' if obligatorio else ''}",
                        columnas_csv, index=idx_default, key=f"map_{campo}",
                    )
                    mapeo[campo] = None if seleccion == "(no usar)" else seleccion

            tipo_fijo = None
            if not mapeo.get("tipo"):
                tipo_fijo = st.selectbox(
                    "No mapeaste una columna de 'Tipo' — ¿qué tipo usamos para TODAS las filas?",
                    ["EQUIPO", "MOLDE", "PLANTA"],
                )

            if not mapeo.get("nombre"):
                st.warning("Debes mapear al menos la columna de Nombre para poder importar.")
            else:
                st.divider()
                st.write("**Paso 3: vista previa de lo que se va a crear**")

                filas_a_crear = []
                for _, fila in df.iterrows():
                    dato = {
                        "nombre": str(fila[mapeo["nombre"]]).strip() if pd.notna(fila[mapeo["nombre"]]) else None,
                        "tipo": (str(fila[mapeo["tipo"]]).strip().upper() if mapeo.get("tipo") and pd.notna(fila[mapeo["tipo"]]) else tipo_fijo),
                    }
                    for campo in ["tipoactivo", "fabricante", "ubicacion", "familia", "peso", "tag"]:
                        col = mapeo.get(campo)
                        valor = fila[col] if col and pd.notna(fila[col]) else None
                        if campo == "peso" and valor is not None:
                            try:
                                valor = float(str(valor).replace(",", "."))
                            except ValueError:
                                valor = None
                        else:
                            valor = str(valor).strip() if valor is not None else None
                        dato[campo] = valor
                    filas_a_crear.append(dato)

                st.dataframe(pd.DataFrame(filas_a_crear).head(10), use_container_width=True)
                st.caption(f"Se crearán {len(filas_a_crear)} activo(s) en total.")

                if st.button(f"✅ Confirmar e importar {len(filas_a_crear)} activo(s)", type="primary"):
                    with st.spinner("Importando..."):
                        resultado = crear_activos_bulk(filas_a_crear)
                    st.success(f"{len(resultado['exitosos'])} activo(s) creado(s) correctamente.")
                    if resultado["errores"]:
                        st.error(f"{len(resultado['errores'])} fila(s) con error:")
                        st.dataframe(pd.DataFrame(resultado["errores"]), use_container_width=True)
                    else:
                        st.balloons()

with tab_ubicaciones:
    st.subheader("📍 Plantilla de ubicaciones de moldes/activos")
    st.markdown("""
    **Cómo funciona:**
    1. Descarga la plantilla — trae los activos ya registrados (Tag y Nombre)
       para que solo llenes **Zona** y **Ubicación**.
    2. La **Zona** es la ubicación *permanente* asignada al molde
       (ej: "Bodega A - Estante 3"). La **Ubicación** es donde está
       *ahora mismo* — normalmente igual a la zona, salvo cuando el
       molde está en una Orden de Trabajo en ejecución/en espera, caso
       en el que el sistema la cambia sola a "TALLER" y la regresa a
       la zona automáticamente al cerrar la OT.
    3. Llena el Excel (agrega filas nuevas si quieres registrar
       ubicaciones de activos que aún no existen — necesitan tener el
       mismo Tag que uses luego para crearlos).
    4. Súbelo aquí abajo para aplicar los cambios de una vez.

    Esto normalmente se hace una sola vez para la carga inicial —
    después, los técnicos editan la ubicación de un molde puntual
    directamente desde 'Listado completo' o el Mapa de planta.
    """)

    st.divider()
    st.write("**Paso 1: descarga la plantilla**")

    datos_actuales = exportar_activos_para_ubicacion()
    df_plantilla = pd.DataFrame(datos_actuales) if datos_actuales else pd.DataFrame(
        columns=["Tag", "Nombre", "Zona", "Ubicacion"]
    )

    buffer = io.BytesIO()
    df_plantilla.to_excel(buffer, index=False, sheet_name="Ubicaciones")
    buffer.seek(0)

    st.download_button(
        "⬇️ Descargar plantilla de ubicaciones (Excel)",
        data=buffer,
        file_name="plantilla_ubicaciones_activos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.caption(f"La plantilla trae {len(datos_actuales)} activo(s) ya registrados.")

    st.divider()
    st.write("**Paso 2: sube el Excel ya lleno**")

    archivo_ubicaciones = st.file_uploader("Excel de ubicaciones (.xlsx)", type=["xlsx"], key="upload_ubicaciones")

    if archivo_ubicaciones is not None:
        try:
            df_subido = pd.read_excel(archivo_ubicaciones)
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")
            df_subido = None

        if df_subido is not None:
            columnas_necesarias = {"Tag", "Zona", "Ubicacion"}
            if not columnas_necesarias.issubset(set(df_subido.columns)):
                st.error(f"El archivo debe tener las columnas: {', '.join(columnas_necesarias)}")
            else:
                st.write("Vista previa:")
                st.dataframe(df_subido.head(10), use_container_width=True)

                if st.button(f"✅ Aplicar {len(df_subido)} ubicación(es)", type="primary"):
                    filas = df_subido.fillna("").to_dict("records")
                    with st.spinner("Actualizando ubicaciones..."):
                        resultado = importar_ubicaciones_bulk(filas)
                    st.success(f"{len(resultado['actualizados'])} activo(s) actualizado(s).")
                    if resultado["no_encontrados"]:
                        st.warning(
                            f"{len(resultado['no_encontrados'])} tag(s) no encontrados en la base "
                            "(revisa que coincidan exactamente con el Tag registrado):"
                        )
                        st.write(", ".join(resultado["no_encontrados"]))

with tab_listado:
    st.subheader("Listado completo — edición rápida")
    busqueda = st.text_input("🔍 Buscar por tag, nombre o ID")

    activos = list_activos_todos(solo_activos=True)
    if busqueda:
        b = busqueda.lower()
        activos = [a for a in activos if b in (a.get("nombre") or "").lower()
                   or b in (a.get("id_activo") or "").lower()
                   or b in (a.get("tag") or "").lower()]

    if not activos:
        st.info("No hay activos que coincidan.")
    else:
        st.caption(f"{len(activos)} resultado(s). Expande una fila para editarla.")
        for a in activos:
            etiqueta_visible = a.get("tag") or a["id_activo"]
            with st.expander(f"{etiqueta_visible} — {a.get('nombre', '—')} ({a.get('tipo', '—')})"):
                col1, col2 = st.columns(2)
                with col1:
                    tag_e = st.text_input("Tag / código de planta", value=a.get("tag") or "", key=f"edtag_{a['id_activo']}")
                    nombre_e = st.text_input("Nombre", value=a.get("nombre", ""), key=f"edn_{a['id_activo']}")
                    ubicacion_e = st.text_input("Ubicación", value=a.get("ubicacion") or "", key=f"edu_{a['id_activo']}")
                with col2:
                    fabricante_e = st.text_input("Fabricante", value=a.get("fabricante") or "", key=f"edf_{a['id_activo']}")
                    familia_e = st.text_input("Familia", value=a.get("familia") or "", key=f"edfam_{a['id_activo']}")
                    st.caption(f"ID interno: `{a['id_activo']}` (no editable)")

                bcol1, bcol2 = st.columns(2)
                if bcol1.button("💾 Guardar cambios", key=f"save_{a['id_activo']}"):
                    actualizar_activo(a["id_activo"], {
                        "tag": tag_e or None, "nombre": nombre_e, "ubicacion": ubicacion_e or None,
                        "fabricante": fabricante_e or None, "familia": familia_e or None,
                    })
                    st.success("Actualizado.")
                    st.rerun()
                if bcol2.button("🗑️ Desactivar", key=f"deact_{a['id_activo']}"):
                    desactivar_activo(a["id_activo"])
                    st.warning("Activo desactivado.")
                    st.rerun()
