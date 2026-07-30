"""
utils/ids.py
=============
Generador de IDs legibles, consistente con el patrón que ya existe en los
datos migrados (ej: OTT_DD8B56F9E0, OTE_1776698992122_0). Se usa cada vez
que el frontend crea un registro nuevo (activo, novedad, OT, usuario...).
"""

import random
import string
import time


def new_id(prefix: str) -> str:
    """
    Genera un ID tipo PREFIJO_XXXXXXXXXX (10 caracteres alfanuméricos en
    mayúscula). Prácticamente imposible de colisionar, y le sigue el
    estilo del código original (OTT_, OTE_, NOV_...).
    """
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"{prefix}_{suffix}"


def new_id_timestamp(prefix: str) -> str:
    """Alternativa basada en timestamp, para casos donde conviene poder
    ordenar por ID (ej: evidencias, tiempos)."""
    return f"{prefix}_{int(time.time() * 1000)}"
