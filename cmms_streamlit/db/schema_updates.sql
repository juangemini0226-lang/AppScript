-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN DE SCHEMA (reconstrucción)
-- Corre esto una sola vez, ADEMÁS del schema.sql original.
-- =========================================================

-- Controla qué módulos ve cada usuario, editable desde la página Admin.
CREATE TABLE IF NOT EXISTS feature_flags (
    feature_key VARCHAR(50) PRIMARY KEY,
    activo BOOLEAN DEFAULT TRUE,
    descripcion TEXT
);

-- Semilla inicial: todos los módulos encendidos por defecto.
INSERT INTO feature_flags (feature_key, activo, descripcion) VALUES
    ('activos', TRUE, 'Módulo de Activos'),
    ('ordenes_trabajo', TRUE, 'Módulo de Órdenes de Trabajo'),
    ('novedades', TRUE, 'Módulo de Novedades'),
    ('maquilas', TRUE, 'Módulo de Maquilas')
ON CONFLICT (feature_key) DO NOTHING;

-- Otorga permisos al usuario de aplicación (ajusta "Admin" si tu
-- usuario de base de datos tiene otro nombre).
GRANT ALL PRIVILEGES ON TABLE feature_flags TO "Admin";
