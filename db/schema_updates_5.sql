-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 5
-- 1) Corrige param_chequeos y param_versiones: su "llave única" original
--    (categoria / id_activo) en realidad se repite a propósito muchas
--    veces (varias actividades por categoría, varias versiones por
--    molde) — error mío al generar el schema. Se reemplaza por un id
--    autoincremental real, y se conservan las columnas originales.
-- 2) Agrega 'zona' a ACTIVOS: la ubicación permanente asignada al
--    molde/equipo, separada de 'ubicacion' (que puede cambiar
--    temporalmente a "TALLER" mientras hay una OT en curso).
-- =========================================================

-- --- 1) Arreglo de llaves primarias mal diseñadas ---

ALTER TABLE param_chequeos DROP CONSTRAINT IF EXISTS param_chequeos_pkey;
ALTER TABLE param_chequeos ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;

ALTER TABLE param_versiones DROP CONSTRAINT IF EXISTS param_versiones_pkey;
ALTER TABLE param_versiones ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;

-- --- 2) Zona permanente + ubicación temporal automática ---

ALTER TABLE activos
    ADD COLUMN IF NOT EXISTS zona TEXT;

-- Para los activos que ya tienen algo en 'ubicacion', se copia como
-- punto de partida a 'zona' (su ubicación permanente conocida hasta
-- ahora). Después lo pueden ajustar en la plantilla de ubicaciones.
UPDATE activos SET zona = ubicacion WHERE zona IS NULL AND ubicacion IS NOT NULL;

GRANT ALL PRIVILEGES ON TABLE param_chequeos TO "Admin";
GRANT ALL PRIVILEGES ON TABLE param_versiones TO "Admin";
GRANT ALL PRIVILEGES ON TABLE activos TO "Admin";
