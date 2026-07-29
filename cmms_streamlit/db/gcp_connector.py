"""
db/gcp_connector.py
====================
Implementación de DBConnector para Google Cloud SQL (PostgreSQL),
usando el Cloud SQL Python Connector (conexión segura sin exponer IP
pública / sin manejar certificados a mano) + SQLAlchemy como capa SQL.

Esta es la ÚNICA pieza del proyecto que sabe que la base es Postgres
y que vive en GCP. Si mañana migras de motor, este archivo se reemplaza
y `services/*` no se entera.

Requiere en requirements.txt:
    cloud-sql-python-connector[pg8000]
    sqlalchemy

Requiere credenciales:
    - En Streamlit Community Cloud: variables en `st.secrets` (ver
      .streamlit/secrets.toml.example) con el JSON de la Service Account.
    - En Cloud Run / GCE: Application Default Credentials (no hace falta
      JSON, usa la identidad del servicio).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes

from db.base import DBConnector


class GCPCloudSQLConnector(DBConnector):

    def __init__(self, settings: dict):
        """
        settings esperado (ver config/settings.py):
            instance_connection_name: "proyecto:region:instancia"
            db_user, db_pass, db_name
            credentials_json (opcional, dict): si no está, se usan ADC
            ip_type: "PUBLIC" | "PRIVATE"  (default PUBLIC)
        """
        self.settings = settings
        self._connector: Optional[Connector] = None
        self._engine: Optional[sqlalchemy.engine.Engine] = None

    # ------------------------------------------------------------------
    def connect(self) -> None:
        if self._engine is not None:
            return  # ya conectado

        creds_json = self.settings.get("credentials_json")
        if creds_json:
            # Streamlit Cloud / entorno sin ADC: se pasa la Service Account
            # como variable de entorno temporal para que el connector la use.
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = json.dumps(creds_json)

        ip_type = IPTypes.PRIVATE if self.settings.get("ip_type") == "PRIVATE" else IPTypes.PUBLIC
        self._connector = Connector(ip_type=ip_type)

        def getconn():
            return self._connector.connect(
                self.settings["instance_connection_name"],
                "pg8000",
                user=self.settings["db_user"],
                password=self.settings["db_pass"],
                db=self.settings["db_name"],
            )

        self._engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
        if self._connector is not None:
            self._connector.close()
            self._connector = None

    # ------------------------------------------------------------------
    def _ensure_conn(self):
        if self._engine is None:
            self.connect()
        return self._engine

    @staticmethod
    def _where_clause(where: Optional[dict]) -> tuple[str, dict]:
        if not where:
            return "", {}
        parts = [f"{k} = :w_{k}" for k in where.keys()]
        params = {f"w_{k}": v for k, v in where.items()}
        return " WHERE " + " AND ".join(parts), params

    def fetch_all(self, table: str, where: Optional[dict] = None,
                   order_by: Optional[str] = None,
                   limit: Optional[int] = None) -> list[dict]:
        engine = self._ensure_conn()
        where_sql, params = self._where_clause(where)
        query = f"SELECT * FROM {table}{where_sql}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {int(limit)}"
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query), params)
            return [dict(row._mapping) for row in result]

    def fetch_one(self, table: str, where: dict) -> Optional[dict]:
        rows = self.fetch_all(table, where=where, limit=1)
        return rows[0] if rows else None

    def insert(self, table: str, data: dict) -> Any:
        engine = self._ensure_conn()
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING *"
        with engine.begin() as conn:
            result = conn.execute(sqlalchemy.text(query), data)
            row = result.fetchone()
            return dict(row._mapping) if row else None

    def update(self, table: str, where: dict, data: dict) -> int:
        engine = self._ensure_conn()
        set_sql = ", ".join(f"{k} = :set_{k}" for k in data.keys())
        where_sql, where_params = self._where_clause(where)
        params = {f"set_{k}": v for k, v in data.items()}
        params.update(where_params)
        query = f"UPDATE {table} SET {set_sql}{where_sql}"
        with engine.begin() as conn:
            result = conn.execute(sqlalchemy.text(query), params)
            return result.rowcount

    def delete(self, table: str, where: dict) -> int:
        engine = self._ensure_conn()
        where_sql, params = self._where_clause(where)
        query = f"DELETE FROM {table}{where_sql}"
        with engine.begin() as conn:
            result = conn.execute(sqlalchemy.text(query), params)
            return result.rowcount

    def execute_raw(self, query: str, params: Optional[dict] = None) -> list[dict]:
        engine = self._ensure_conn()
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return []
