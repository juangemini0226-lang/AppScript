-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 2: visibilidad de módulos por rol
-- Corre esto UNA vez, además de schema.sql y schema_updates.sql
-- =========================================================

ALTER TABLE feature_flags
    ADD COLUMN IF NOT EXISTS roles_permitidos TEXT DEFAULT 'TODOS';

-- Deja explícito que, por defecto, todos los módulos existentes
-- siguen siendo visibles para todos los roles (comportamiento actual).
UPDATE feature_flags SET roles_permitidos = 'TODOS' WHERE roles_permitidos IS NULL;

GRANT ALL PRIVILEGES ON TABLE feature_flags TO "Admin";
