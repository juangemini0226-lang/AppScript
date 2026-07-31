-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 3
-- Jerarquía técnica clasificada por ISO 14224 + catálogo de tipos de
-- activo + coordenadas para el mapa 2D de planta.
-- Corre esto UNA vez, además de las actualizaciones anteriores.
-- =========================================================

-- Clasificación ISO 14224 sobre cada nodo de la jerarquía técnica
-- (Unidad de equipo / Subunidad / Componente / Ítem mantenible).
ALTER TABLE jerarquia_tecnica
    ADD COLUMN IF NOT EXISTS clase_iso14224 TEXT;

-- Catálogo editable de tipos de activo (antes era texto libre en
-- ACTIVOS.tipoactivo / familia). Permite estandarizar nomenclatura.
CREATE TABLE IF NOT EXISTS tipos_activo (
    id_tipo VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    clase_iso14224 TEXT,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

-- Semilla inicial basada en categorías típicas ISO 14224 para equipos
-- de planta plástica/inyección — el admin puede editar esto después.
INSERT INTO tipos_activo (id_tipo, nombre, clase_iso14224, descripcion) VALUES
    ('TA_MOLDE', 'Molde', 'Unidad de equipo', 'Molde de inyección'),
    ('TA_INYECTORA', 'Inyectora', 'Unidad de equipo', 'Máquina inyectora'),
    ('TA_SOPLADORA', 'Sopladora', 'Unidad de equipo', 'Máquina sopladora'),
    ('TA_PERIFERICO', 'Periférico', 'Subunidad', 'Equipo auxiliar (robot, atemperador, etc.)')
ON CONFLICT (id_tipo) DO NOTHING;

-- Coordenadas en el plano 2D de planta (0-100, porcentaje del ancho y
-- alto del lienzo), para ubicar visualmente moldes/equipos.
ALTER TABLE activos
    ADD COLUMN IF NOT EXISTS pos_x NUMERIC,
    ADD COLUMN IF NOT EXISTS pos_y NUMERIC;

GRANT ALL PRIVILEGES ON TABLE tipos_activo TO "Admin";
GRANT ALL PRIVILEGES ON TABLE jerarquia_tecnica TO "Admin";
GRANT ALL PRIVILEGES ON TABLE activos TO "Admin";
