"""
db/factory.py
=============
Punto ÚNICO donde se decide qué motor de base de datos se está usando.

Cuando migres de motor en el futuro (ej: Cloud SQL -> Firestore, o
Cloud SQL -> otro proveedor), este es el ÚNICO archivo que cambia.
`services/*` y las páginas de Streamlit siguen llamando a
`get_connector()` sin saber qué hay detrás.

Uso:
    from db.factory import get_connector
    db = get_connector()
    activos = db.fetch_all("activos", where={"activo": True})
"""

from functools import lru_cache

from config.settings import get_settings
from db.base import DBConnector


@lru_cache(maxsize=1)
def get_connector() -> DBConnector:
    settings = get_settings()
    engine = settings.get("db_engine", "gcp_cloudsql")

    if engine == "gcp_cloudsql":
        from db.gcp_connector import GCPCloudSQLConnector
        connector = GCPCloudSQLConnector(settings["gcp_cloudsql"])

    # --- Espacio reservado para futuros motores ---
    # elif engine == "firestore":
    #     from db.firestore_connector import FirestoreConnector
    #     connector = FirestoreConnector(settings["firestore"])
    #
    # elif engine == "bigquery":
    #     from db.bigquery_connector import BigQueryConnector
    #     connector = BigQueryConnector(settings["bigquery"])

    else:
        raise ValueError(f"Motor de base de datos no soportado: {engine}")

    connector.connect()
    return connector
