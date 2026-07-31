"""
db/base.py
==========
Contrato de acceso a datos del CMMS.

POR QUÉ EXISTE ESTE ARCHIVO
----------------------------
Hoy la base es Google Cloud SQL (PostgreSQL). Mañana podría ser Firestore,
BigQuery, otro proveedor (AWS/Azure) o incluso volver a Sheets para pruebas.

Para que ese cambio NO obligue a tocar los `services/*` (la lógica de
negocio: activos, OT, novedades, maquilas, etc.), todo el resto del sistema
habla exclusivamente con esta interfaz (`DBConnector`), nunca con SQLAlchemy,
psycopg2 o el SDK de Google directamente.

Regla de oro del proyecto:
    services/*  -->  habla con DBConnector (esta clase)
    db/*        -->  implementa DBConnector para un motor concreto

Si el día de mañana migras de Cloud SQL a Firestore, solo se crea
`db/firestore_connector.py` que implemente esta misma interfaz y se cambia
UNA línea en `db/factory.py`. Nada más se toca.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class DBConnector(ABC):
    """Contrato mínimo que cualquier backend de datos debe implementar."""

    # ------------------------------------------------------------------
    # Ciclo de vida de la conexión
    # ------------------------------------------------------------------
    @abstractmethod
    def connect(self) -> None:
        """Abre la conexión / pool de conexiones."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Cierra la conexión / pool de conexiones."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Operaciones genéricas (equivalentes a lo que hacía Apps Script
    # leyendo/escribiendo filas de un Sheet)
    # ------------------------------------------------------------------
    @abstractmethod
    def fetch_all(self, table: str, where: Optional[dict] = None,
                   order_by: Optional[str] = None,
                   limit: Optional[int] = None) -> list[dict]:
        """
        Devuelve una lista de dicts (equivalente a getDataRange().getValues()
        ya convertido a objetos, como hacían los .gs).

        where: dict simple de igualdad, ej: {"activo": True, "tipo": "EQUIPO"}
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_one(self, table: str, where: dict) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    def insert(self, table: str, data: dict) -> Any:
        """Inserta un registro. Devuelve el id generado o insertado."""
        raise NotImplementedError

    @abstractmethod
    def update(self, table: str, where: dict, data: dict) -> int:
        """Actualiza registros que cumplan `where`. Devuelve filas afectadas."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, table: str, where: dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def execute_raw(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """
        Escape hatch para consultas complejas (joins, agregaciones) que no
        valen la pena modelar en los métodos genéricos de arriba.
        Úsalo con moderación: cada uso aquí es código que NO es portable
        entre motores.
        """
        raise NotImplementedError
