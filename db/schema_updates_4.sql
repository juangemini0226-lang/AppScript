-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 4
-- Columna 'tag' para identificar activos por su etiqueta física
-- (como los llaman en planta), independiente del id_activo interno.
-- =========================================================

ALTER TABLE activos
    ADD COLUMN IF NOT EXISTS tag TEXT;

GRANT ALL PRIVILEGES ON TABLE activos TO "Admin";
