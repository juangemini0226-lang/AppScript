"""
services/qr_service.py
=========================
Genera códigos QR con la información de un activo — para imprimir
etiquetas físicas y pegarlas en moldes/equipos. Al escanear con
cualquier cámara de celular, se lee el texto directamente (no depende
de que el celular tenga la app instalada ni de conexión a internet).
"""

import io
import zipfile

import qrcode


def _texto_qr(activo: dict) -> str:
    """Construye el bloque de texto que va codificado en el QR."""
    lineas = [
        f"TAG: {activo.get('tag') or activo['id_activo']}",
        f"Nombre: {activo.get('nombre', '—')}",
        f"Tipo: {activo.get('tipo', '—')}",
    ]
    if activo.get("familia"):
        lineas.append(f"Familia: {activo['familia']}")
    if activo.get("fabricante"):
        lineas.append(f"Fabricante: {activo['fabricante']}")
    if activo.get("zona"):
        lineas.append(f"Zona: {activo['zona']}")
    lineas.append(f"ID interno: {activo['id_activo']}")
    return "\n".join(lineas)


def generar_qr_png(activo: dict) -> bytes:
    """Devuelve los bytes de un PNG con el QR de un solo activo."""
    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data(_texto_qr(activo))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generar_qr_lote_zip(activos: list[dict]) -> bytes:
    """
    Genera un .zip con un PNG de QR por cada activo, nombrado por su
    tag — para imprimir etiquetas de muchos moldes de una sola vez.
    """
    buffer_zip = io.BytesIO()
    with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for activo in activos:
            png_bytes = generar_qr_png(activo)
            nombre_archivo = f"QR_{(activo.get('tag') or activo['id_activo'])}.png"
            nombre_archivo = "".join(c for c in nombre_archivo if c.isalnum() or c in "._-")
            zf.writestr(nombre_archivo, png_bytes)
    return buffer_zip.getvalue()
