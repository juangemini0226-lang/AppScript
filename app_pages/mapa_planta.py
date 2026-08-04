"""
app_pages/mapa_planta.py
==========================
Mapa de planta con una foto real como fondo (subida una vez), zonas
rectangulares dibujadas sobre ella (Bodega A, Taller, Línea 3...), y
ubicación de moldes/activos dentro de esas zonas.

ALCANCE (léelo antes de esperar arrastrar con el mouse):
Streamlit no soporta dibujar/arrastrar de forma nativa — armar eso
requeriría un componente en JavaScript aparte. Aquí las zonas se
definen con controles numéricos (posición y tamaño en % de la imagen)
con vista previa en vivo mientras ajustas los valores, y los activos
se ubican eligiendo a qué zona pertenecen (con la opción de afinar su
punto exacto dentro de ella). Es "clic y ajustar números" en vez de
"arrastrar con el mouse", pero con foto real de fondo y zonas
visibles, ya cumple el objetivo de ver de un vistazo dónde está cada
molde en la planta.
"""

import streamlit as st

from services.activos_service import list_activos_todos, actualizar_activo
from services.mapa_service import (
    get_imagen_planta, set_imagen_planta,
    list_zonas, crear_zona, actualizar_zona, eliminar_zona,
)
from utils.tabs import build_tabs

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🗺️ Mapa de planta")

usuario = st.session_state["usuario"]
tabs = build_tabs("mapa_planta", usuario["rol"])

imagen_actual = get_imagen_planta()
zonas = list_zonas()
activos = list_activos_todos(solo_activos=True)


def _fondo_html(ancho=900, alto=550):
    """HTML con la imagen de fondo (si existe) y las zonas overlay."""
    if imagen_actual and imagen_actual.get("imagen_base64"):
        src = f"data:{imagen_actual['imagen_mime']};base64,{imagen_actual['imagen_base64']}"
        fondo = f'<img src="{src}" style="width:100%;height:100%;object-fit:contain;display:block;" />'
    else:
        fondo = ""

    zonas_html = ""
    for z in zonas:
        left, top = float(z["x1"]), float(z["y1"])
        width, height = float(z["x2"]) - left, float(z["y2"]) - top
        zonas_html += f"""
        <div style="position:absolute;left:{left}%;top:{top}%;width:{width}%;height:{height}%;
                    border:2px dashed {z['color']};background:{z['color']}22;
                    display:flex;align-items:flex-start;justify-content:flex-start;">
            <span style="background:{z['color']};color:white;font-size:11px;padding:1px 6px;
                         border-radius:0 0 4px 0;">{z['nombre']}</span>
        </div>
        """

    return f"""
    <div style="position:relative;width:100%;padding-top:56%;background:#e8e8e8;
                border:1px solid #ddd;border-radius:8px;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;width:100%;height:100%;">
            {fondo}
            {zonas_html}
        </div>
    </div>
    """


if "ver_mapa" in tabs:
    with tabs["ver_mapa"]:
        if not imagen_actual:
            st.info("Todavía no has subido una foto de la planta — ve a la pestaña '🖼️ Foto de planta'.")
        else:
            st.markdown(_fondo_html(), unsafe_allow_html=True)

        activos_con_pos = [a for a in activos if a.get("pos_x") is not None and a.get("pos_y") is not None]
        if activos_con_pos:
            with st.expander(f"📋 Ver lista de ubicaciones ({len(activos_con_pos)})"):
                tabla = [{"Activo": a.get("tag") or a["nombre"], "Nombre": a["nombre"],
                           "Zona": a.get("zona") or "—", "Ubicación actual": a.get("ubicacion") or "—"}
                          for a in activos_con_pos]
                st.dataframe(tabla, use_container_width=True, hide_index=True)

if "foto_planta" in tabs:
    with tabs["foto_planta"]:
        st.subheader("Foto de la planta")
        st.caption(
            "Sube una foto o plano de la planta (una imagen general, vista de "
            "arriba si tienes una). Se usa como fondo del mapa; las zonas se "
            "dibujan encima."
        )

        if imagen_actual:
            st.success("Ya hay una imagen cargada:")
            src = f"data:{imagen_actual['imagen_mime']};base64,{imagen_actual['imagen_base64']}"
            st.markdown(f'<img src="{src}" style="max-width:100%;border-radius:8px;border:1px solid #ddd;" />',
                         unsafe_allow_html=True)

        nueva_imagen = st.file_uploader("Subir/reemplazar imagen", type=["png", "jpg", "jpeg"])
        if nueva_imagen is not None:
            if st.button("💾 Guardar esta imagen como fondo del mapa"):
                set_imagen_planta(nueva_imagen.getvalue(), nueva_imagen.type)
                st.success("Imagen guardada. Ve a 'Ver mapa' para verla.")
                st.rerun()

if "zonas" in tabs:
    with tabs["zonas"]:
        st.subheader("Zonas de la planta")
        st.caption(
            "Cada zona es un rectángulo sobre la imagen, definido en % de "
            "ancho/alto (0 = borde izquierdo/superior, 100 = borde derecho/inferior). "
            "Ajusta los números y mira la vista previa antes de guardar."
        )

        if not imagen_actual:
            st.warning("Sube primero una foto en '🖼️ Foto de planta' para poder ubicar zonas sobre ella.")

        with st.expander("➕ Crear zona nueva", expanded=not zonas):
            col1, col2 = st.columns(2)
            with col1:
                nombre_zona = st.text_input("Nombre de la zona (ej: Bodega A, Taller, Línea 3)")
                color_zona = st.color_picker("Color", value="#3B6E8F")
            with col2:
                x1 = st.slider("X inicial (%)", 0, 100, 10, key="nueva_x1")
                y1 = st.slider("Y inicial (%)", 0, 100, 10, key="nueva_y1")
                x2 = st.slider("X final (%)", 0, 100, 30, key="nueva_x2")
                y2 = st.slider("Y final (%)", 0, 100, 30, key="nueva_y2")

            # vista previa en vivo
            preview_zonas_html = f"""
            <div style="position:absolute;left:{min(x1,x2)}%;top:{min(y1,y2)}%;
                        width:{abs(x2-x1)}%;height:{abs(y2-y1)}%;
                        border:2px dashed {color_zona};background:{color_zona}33;"></div>
            """
            fondo_src = ""
            if imagen_actual:
                src = f"data:{imagen_actual['imagen_mime']};base64,{imagen_actual['imagen_base64']}"
                fondo_src = f'<img src="{src}" style="width:100%;height:100%;object-fit:contain;" />'
            st.markdown(f"""
            <div style="position:relative;width:100%;padding-top:56%;background:#e8e8e8;
                        border:1px solid #ddd;border-radius:8px;overflow:hidden;">
                <div style="position:absolute;top:0;left:0;width:100%;height:100%;">
                    {fondo_src}
                    {preview_zonas_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💾 Crear esta zona"):
                if not nombre_zona:
                    st.error("Ponle un nombre a la zona.")
                else:
                    crear_zona(nombre_zona, x1, y1, x2, y2, color_zona)
                    st.success(f"Zona '{nombre_zona}' creada.")
                    st.rerun()

        if zonas:
            st.divider()
            st.write("**Zonas existentes:**")
            for z in zonas:
                with st.expander(f"🟦 {z['nombre']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_e = st.text_input("Nombre", value=z["nombre"], key=f"zn_{z['id_zona']}")
                        color_e = st.color_picker("Color", value=z.get("color") or "#3B6E8F", key=f"zc_{z['id_zona']}")
                    with col2:
                        x1_e = st.slider("X inicial (%)", 0, 100, int(z["x1"]), key=f"zx1_{z['id_zona']}")
                        y1_e = st.slider("Y inicial (%)", 0, 100, int(z["y1"]), key=f"zy1_{z['id_zona']}")
                        x2_e = st.slider("X final (%)", 0, 100, int(z["x2"]), key=f"zx2_{z['id_zona']}")
                        y2_e = st.slider("Y final (%)", 0, 100, int(z["y2"]), key=f"zy2_{z['id_zona']}")

                    bcol1, bcol2 = st.columns(2)
                    if bcol1.button("💾 Guardar cambios", key=f"zsave_{z['id_zona']}"):
                        actualizar_zona(z["id_zona"], nombre_e, x1_e, y1_e, x2_e, y2_e, color_e)
                        st.success("Zona actualizada.")
                        st.rerun()
                    if bcol2.button("🗑️ Eliminar zona", key=f"zdel_{z['id_zona']}"):
                        eliminar_zona(z["id_zona"])
                        st.warning("Zona eliminada.")
                        st.rerun()

if "ubicar_activo" in tabs:
    with tabs["ubicar_activo"]:
        st.write("Elige un activo, asígnalo a una zona, y afina su punto exacto dentro de ella si quieres.")
        if not activos:
            st.info("No hay activos registrados todavía.")
        elif not zonas:
            st.warning("Crea al menos una zona primero, en la pestaña '🟦 Zonas'.")
        else:
            busqueda_ubicar = st.text_input("🔍 Buscar activo por tag, nombre o ID", key="busq_ubicar")
            activos_filtrados = activos
            if busqueda_ubicar:
                b = busqueda_ubicar.lower()
                activos_filtrados = [a for a in activos if b in (a.get("nombre") or "").lower()
                                       or b in (a.get("id_activo") or "").lower()
                                       or b in (a.get("tag") or "").lower()]

            if not activos_filtrados:
                st.warning("No hay activos que coincidan con la búsqueda.")
            else:
                activo_sel = st.selectbox("Activo", activos_filtrados,
                                            format_func=lambda a: f"{a.get('tag') or a.get('nombre', '—')} ({a.get('id_activo', '—')})")
                if activo_sel:
                    zona_actual_nombre = activo_sel.get("zona")
                    zona_idx = next((i for i, z in enumerate(zonas) if z["nombre"] == zona_actual_nombre), 0)
                    zona_sel = st.selectbox("Zona", zonas, index=zona_idx, format_func=lambda z: z["nombre"])

                    st.caption("Punto exacto dentro de la zona (0% = esquina superior izquierda de la zona, 100% = esquina inferior derecha).")
                    col1, col2 = st.columns(2)
                    with col1:
                        pos_relativa_x = st.slider("Posición horizontal dentro de la zona", 0, 100, 50)
                    with col2:
                        pos_relativa_y = st.slider("Posición vertical dentro de la zona", 0, 100, 50)

                    # convertir posición relativa a la zona -> posición absoluta en el mapa completo
                    x1, y1, x2, y2 = float(zona_sel["x1"]), float(zona_sel["y1"]), float(zona_sel["x2"]), float(zona_sel["y2"])
                    pos_x_absoluta = x1 + (x2 - x1) * (pos_relativa_x / 100)
                    pos_y_absoluta = y1 + (y2 - y1) * (pos_relativa_y / 100)

                    fondo_src = ""
                    if imagen_actual:
                        src = f"data:{imagen_actual['imagen_mime']};base64,{imagen_actual['imagen_base64']}"
                        fondo_src = f'<img src="{src}" style="width:100%;height:100%;object-fit:contain;" />'
                    zonas_preview = "".join(
                        f'<div style="position:absolute;left:{z["x1"]}%;top:{z["y1"]}%;'
                        f'width:{float(z["x2"])-float(z["x1"])}%;height:{float(z["y2"])-float(z["y1"])}%;'
                        f'border:2px dashed {z["color"]};background:{z["color"]}22;"></div>'
                        for z in zonas
                    )
                    st.markdown(f"""
                    <div style="position:relative;width:100%;padding-top:56%;background:#e8e8e8;
                                border:1px solid #ddd;border-radius:8px;overflow:hidden;">
                        <div style="position:absolute;top:0;left:0;width:100%;height:100%;">
                            {fondo_src}
                            {zonas_preview}
                            <div style="position:absolute;left:{pos_x_absoluta}%;top:{pos_y_absoluta}%;
                                        width:14px;height:14px;margin-left:-7px;margin-top:-7px;
                                        border-radius:50%;background:#E8A43B;border:2px solid white;
                                        box-shadow:0 0 0 2px #1E2530;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("💾 Guardar ubicación"):
                        actualizar_activo(activo_sel["id_activo"], {
                            "zona": zona_sel["nombre"],
                            "ubicacion": zona_sel["nombre"],
                            "pos_x": pos_x_absoluta, "pos_y": pos_y_absoluta,
                        })
                        st.success(f"'{activo_sel.get('tag') or activo_sel['nombre']}' ubicado en {zona_sel['nombre']}.")
                        st.rerun()
