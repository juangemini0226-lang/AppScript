"""
app_pages/mapa_planta.py
==========================
Mapa 2D de planta para ubicar visualmente activos (moldes, equipos).

ALCANCE DE ESTA PRIMERA VERSIÓN (léelo antes de esperar drag&drop):
Streamlit no soporta arrastrar-y-soltar de forma nativa — se necesitaría
un componente personalizado en JavaScript para eso (posible, pero es
un desarrollo aparte, no algo que se arma en una función de servicio).

Lo que SÍ hace esta versión: cada activo tiene una posición (X, Y) en
porcentaje (0-100) sobre un lienzo rectangular que representa la
planta. La ubicas escribiendo o ajustando los números con un slider, y
el mapa se dibuja como SVG con un punto y una etiqueta por activo. Es
"clic para ubicar" en vez de "arrastrar", pero cumple el objetivo de
ver de un vistazo dónde está cada molde/equipo en la planta.

Si más adelante quieres arrastrar de verdad, es una mejora de una sola
pieza (un componente HTML/JS que reporte la posición del mouse) sin
tocar el resto de la arquitectura.
"""

import streamlit as st

from services.activos_service import list_activos_todos, actualizar_activo

if "usuario" not in st.session_state:
    st.warning("Inicia sesión desde la página principal.")
    st.stop()

st.title("🗺️ Mapa de planta")

tab_mapa, tab_ubicar = st.tabs(["Ver mapa", "📍 Ubicar activo"])

activos = list_activos_todos(solo_activos=True)
activos_con_pos = [a for a in activos if a.get("pos_x") is not None and a.get("pos_y") is not None]

with tab_mapa:
    if not activos_con_pos:
        st.info(
            "Todavía no hay activos con posición asignada. Ve a la pestaña "
            "'📍 Ubicar activo' para empezar a colocarlos en el mapa."
        )
    else:
        ancho, alto = 900, 500
        puntos_svg = ""
        for a in activos_con_pos:
            x = float(a["pos_x"]) / 100 * ancho
            y = float(a["pos_y"]) / 100 * alto
            puntos_svg += f"""
                <g>
                    <circle cx="{x}" cy="{y}" r="9" fill="#e74c3c" stroke="white" stroke-width="2" />
                    <text x="{x + 12}" y="{y + 4}" font-size="12" fill="#333">{a['nombre']}</text>
                </g>
            """

        svg = f"""
        <svg width="100%" viewBox="0 0 {ancho} {alto}" style="background:#f4f4f4;border:1px solid #ddd;border-radius:8px;">
            <defs>
                <pattern id="grid" width="45" height="45" patternUnits="userSpaceOnUse">
                    <path d="M 45 0 L 0 0 0 45" fill="none" stroke="#e0e0e0" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            {puntos_svg}
        </svg>
        """
        st.markdown(svg, unsafe_allow_html=True)
        st.caption(f"{len(activos_con_pos)} activo(s) ubicados en el mapa.")

with tab_ubicar:
    st.write("Elige un activo y ajusta su posición en el plano (0 = izquierda/arriba, 100 = derecha/abajo).")
    if not activos:
        st.info("No hay activos registrados todavía.")
    else:
        activo_sel = st.selectbox("Activo", activos, format_func=lambda a: a.get("nombre", a.get("id_activo")))
        if activo_sel:
            col1, col2 = st.columns(2)
            with col1:
                nuevo_x = st.slider("Posición horizontal (X)", 0, 100,
                                      int(activo_sel.get("pos_x") or 50))
            with col2:
                nuevo_y = st.slider("Posición vertical (Y)", 0, 100,
                                      int(activo_sel.get("pos_y") or 50))

            # Vista previa en vivo mientras ajustas
            ancho, alto = 900, 300
            x_prev = nuevo_x / 100 * ancho
            y_prev = nuevo_y / 100 * alto
            st.markdown(f"""
            <svg width="100%" viewBox="0 0 {ancho} {alto}" style="background:#f4f4f4;border:1px solid #ddd;border-radius:8px;">
                <circle cx="{x_prev}" cy="{y_prev}" r="10" fill="#3498db" stroke="white" stroke-width="2" />
                <text x="{x_prev + 14}" y="{y_prev + 4}" font-size="12" fill="#333">{activo_sel.get('nombre', '')}</text>
            </svg>
            """, unsafe_allow_html=True)

            if st.button("💾 Guardar posición"):
                actualizar_activo(activo_sel["id_activo"], {"pos_x": nuevo_x, "pos_y": nuevo_y})
                st.success(f"Posición guardada para {activo_sel['nombre']}.")
                st.rerun()
