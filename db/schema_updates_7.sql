-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 7
-- Permisos granulares: no solo módulos completos, sino cada
-- pestaña/función DENTRO de un módulo (ej: dentro de Activos,
-- prender/apagar "Cargar CSV masivo" solo para Planeador).
-- =========================================================

CREATE TABLE IF NOT EXISTS sub_feature_flags (
    modulo_key VARCHAR(50) NOT NULL,
    sub_feature_key VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    roles_permitidos TEXT DEFAULT 'TODOS',
    PRIMARY KEY (modulo_key, sub_feature_key)
);

GRANT ALL PRIVILEGES ON TABLE sub_feature_flags TO "Admin";
