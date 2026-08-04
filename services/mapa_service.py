"""
services/mapa_service.py
===========================
Imagen de fondo del mapa de planta (foto real, subida una vez) +
zonas rectangulares dibujadas sobre ella. Streamlit no soporta
arrastrar-y-dibujar de forma nativa, así que las zonas se definen con
coordenadas en porcentaje (0-100) mediante campos numéricos, con
vista previa en vivo mientras se ajustan — no es "dibujar con el
mouse", pero cumple el objetivo de ubicar zonas sobre una foto real.
"""

import base64

from utils.ids import new_id
from db.factory import get_connector


def get_imagen_planta() -> dict | None:
    db = get_connector()
    return db.fetch_one("planta_imagen", where={"id": 1})


def set_imagen_planta(bytes_imagen: bytes, mime: str) -> None:
    from datetime import datetime
    db = get_connector()
    b64 = base64.b64encode(bytes_imagen).decode("utf-8")
    existente = db.fetch_one("planta_imagen", where={"id": 1})
    data = {"imagen_base64": b64, "imagen_mime": mime, "actualizado_en": datetime.now()}
    if existente:
        db.update("planta_imagen", where={"id": 1}, data=data)
    else:
        db.insert("planta_imagen", {"id": 1, **data})


def list_zonas() -> list[dict]:
    db = get_connector()
    return db.fetch_all("zonas_planta", order_by="nombre")


def crear_zona(nombre: str, x1: float, y1: float, x2: float, y2: float, color: str) -> dict:
    db = get_connector()
    registro = {
        "id_zona": new_id("ZON"),
        "nombre": nombre,
        "x1": min(x1, x2), "y1": min(y1, y2),
        "x2": max(x1, x2), "y2": max(y1, y2),
        "color": color,
    }
    return db.insert("zonas_planta", registro)


def actualizar_zona(id_zona: str, nombre: str, x1: float, y1: float, x2: float, y2: float, color: str) -> int:
    db = get_connector()
    return db.update("zonas_planta", where={"id_zona": id_zona}, data={
        "nombre": nombre,
        "x1": min(x1, x2), "y1": min(y1, y2),
        "x2": max(x1, x2), "y2": max(y1, y2),
        "color": color,
    })


def eliminar_zona(id_zona: str) -> int:
    db = get_connector()
    return db.delete("zonas_planta", where={"id_zona": id_zona})
