-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 6
-- Mapa de planta con imagen real de fondo + zonas dibujadas.
-- =========================================================

-- Imagen de fondo del mapa (una sola, fila única con id=1). Se guarda
-- en base64 dentro de la base — sencillo y suficiente para una imagen
-- de plano de planta (evita montar un bucket de almacenamiento aparte
-- solo para esto).
CREATE TABLE IF NOT EXISTS planta_imagen (
    id INTEGER PRIMARY KEY DEFAULT 1,
    imagen_base64 TEXT,
    imagen_mime TEXT,
    actualizado_en TIMESTAMP,
    CONSTRAINT solo_una_fila CHECK (id = 1)
);

-- Zonas rectangulares dibujadas sobre la imagen (coordenadas en
-- porcentaje 0-100 del ancho/alto de la imagen, para que funcionen
-- sin importar el tamaño real del archivo subido).
CREATE TABLE IF NOT EXISTS zonas_planta (
    id_zona VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    x1 NUMERIC,
    y1 NUMERIC,
    x2 NUMERIC,
    y2 NUMERIC,
    color TEXT DEFAULT '#3B6E8F'
);

GRANT ALL PRIVILEGES ON TABLE planta_imagen TO "Admin";
GRANT ALL PRIVILEGES ON TABLE zonas_planta TO "Admin";
