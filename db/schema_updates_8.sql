-- =========================================================
-- CMMS FLA-EICE - ACTUALIZACIÓN 8
-- Roles administrables (puedes crear roles nuevos, no solo los 5
-- originales) + PINs de acceso rápido asignados por rol.
-- =========================================================

CREATE TABLE IF NOT EXISTS roles (
    rol_key VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    descripcion TEXT
);

-- Semilla con los 5 roles que ya existían, para no romper nada.
INSERT INTO roles (rol_key, nombre, descripcion) VALUES
    ('TECNICO', 'Técnico', 'Técnico de mantenimiento'),
    ('TECNICO_B', 'Técnico B', 'Técnico de mantenimiento (turno B)'),
    ('TECNICO_MONTAJE', 'Técnico de montaje', 'Técnico de montaje/alistamiento'),
    ('PLANEADOR', 'Planeador', 'Planeador de mantenimiento (administrador)'),
    ('AUDITOR', 'Auditor', 'Auditor de procesos (administrador)')
ON CONFLICT (rol_key) DO NOTHING;

-- PIN de acceso rápido por rol (para el login sin correo en planta).
-- Un PIN por rol; el nombre_generico es lo que ve el usuario logueado
-- (ej. "Técnico de turno") ya que el PIN no identifica a una persona
-- puntual, sino un rol de acceso rápido.
CREATE TABLE IF NOT EXISTS roles_pines (
    rol_key VARCHAR(50) PRIMARY KEY REFERENCES roles(rol_key),
    pin VARCHAR(10) UNIQUE NOT NULL,
    nombre_generico TEXT
);

-- Los mismos PINes que ya tenías (9999/8888/0000), para que el acceso
-- rápido siga funcionando igual justo después de aplicar este cambio.
-- Los puedes editar/cambiar después desde Admin -> Roles y PINes.
INSERT INTO roles_pines (rol_key, pin, nombre_generico) VALUES
    ('PLANEADOR', '9999', 'Planeador Master'),
    ('AUDITOR', '8888', 'Auditor de Procesos'),
    ('TECNICO', '0000', 'Técnico Operativo')
ON CONFLICT (rol_key) DO NOTHING;

GRANT ALL PRIVILEGES ON TABLE roles TO "Admin";
GRANT ALL PRIVILEGES ON TABLE roles_pines TO "Admin";
