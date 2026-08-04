"""
utils/tabs.py
===============
Helper para que cada página construya sus pestañas (tabs) dinámicamente,
mostrando solo las que Admin dejó activas para el rol del usuario actual.

Uso en una página:

    from utils.tabs import build_tabs

    tabs = build_tabs("activos", usuario["rol"])
    # tabs es un dict {"crear_activo": <contexto del tab>, ...}
    # solo con las llaves que el rol puede ver

    if "crear_activo" in tabs:
        with tabs["crear_activo"]:
            ... contenido ...

Si ninguna sub-función está visible para el rol, se muestra un aviso
en vez de una lista vacía de pestañas (Streamlit no permite st.tabs([])).
"""

import streamlit as st

from services.admin_service import visible_subfeatures


def build_tabs(modulo_key: str, rol: str) -> dict:
    disponibles = visible_subfeatures(modulo_key, rol)

    if not disponibles:
        st.warning(
            "No tienes ninguna función habilitada en este módulo. "
            "Pídele a un Planeador/Auditor que revise Admin → Módulos de la app."
        )
        return {}

    etiquetas = [sf["label"] for sf in disponibles]
    tabs_streamlit = st.tabs(etiquetas)
    return {sf["key"]: tab for sf, tab in zip(disponibles, tabs_streamlit)}
