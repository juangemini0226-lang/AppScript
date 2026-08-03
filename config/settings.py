"""
config/settings.py
===================
Lee la configuración desde `st.secrets` (Streamlit Cloud / local) y la
expone como un dict plano para que el resto de la app (sobre todo
db/factory.py) no dependa directamente de Streamlit.

En Streamlit Community Cloud: Settings -> Secrets, pegas el TOML
(ver .streamlit/secrets.toml.example en la raíz del proyecto).
"""

from functools import lru_cache

import streamlit as st


@lru_cache(maxsize=1)
def get_settings() -> dict:
    s = st.secrets

    return {
        # Selector de motor de base de datos. Ver db/factory.py
        "db_engine": s.get("db_engine", "gcp_cloudsql"),

        "gcp_cloudsql": {
            "instance_connection_name": s["gcp_cloudsql"]["instance_connection_name"],
            "db_user": s["gcp_cloudsql"]["db_user"],
            "db_pass": s["gcp_cloudsql"]["db_pass"],
            "db_name": s["gcp_cloudsql"]["db_name"],
            "ip_type": s["gcp_cloudsql"].get("ip_type", "PUBLIC"),
            # Service account completa en JSON, solo si no usas ADC.
            "credentials_json": dict(s["gcp_cloudsql"]["credentials_json"])
                if "credentials_json" in s["gcp_cloudsql"] else None,
        },

        "app": {
            "empresa": s.get("app", {}).get("empresa", "FLA-EICE"),
            "linea": s.get("app", {}).get("linea", "Línea 3 - Envasado"),
            "timezone": s.get("app", {}).get("timezone", "America/Bogota"),
        },
    }
