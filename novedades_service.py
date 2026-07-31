-- =========================================================
-- CMMS FLA-EICE - SCHEMA POSTGRESQL (Cloud SQL)
-- Generado a partir de la estructura real del Google Sheet (CMMS_DB.xlsx)
-- Mantenimiento Linea 3 Envasado
-- NOTA: los ID_* se dejan como VARCHAR porque en el Sheet actual
-- son codigos manuales (ej: 'EQ-001'), no autoincrementales.
-- Ajustar a SERIAL/UUID si se decide normalizar en el futuro.
-- =========================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    correo TEXT,
    rol TEXT,
    activo BOOLEAN
);

CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS activos (
    id_activo VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    tipo TEXT,
    padre_id TEXT,
    activo BOOLEAN,
    tipoactivo TEXT,
    fabricante TEXT,
    ubicacion TEXT,
    peso NUMERIC,
    infotecnica TEXT,
    ciclosactuales NUMERIC,
    ciclos_ult_mant NUMERIC,
    frecuencia_mant NUMERIC,
    ciclos_desde_mant NUMERIC,
    ciclos_para_mant NUMERIC,
    familia TEXT,
    ultimo_alistamiento TEXT,
    gancho TEXT,
    botadores TEXT,
    puentes_agua TEXT,
    puentes_aire TEXT,
    chapetas TEXT,
    manipulador TEXT,
    atemperador TEXT,
    accesorios TEXT,
    tip TEXT,
    version_actual TEXT
);

CREATE TABLE IF NOT EXISTS jerarquia_tecnica (
    id_activo VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    tipo TEXT,
    padre_id TEXT,
    activo BOOLEAN
);

CREATE TABLE IF NOT EXISTS averias (
    id_averia VARCHAR(50) PRIMARY KEY,
    descripcion TEXT,
    item_id TEXT,
    activo BOOLEAN,
    item_mantenible TEXT
);

CREATE TABLE IF NOT EXISTS soluciones_averia (
    id_solucion VARCHAR(50) PRIMARY KEY,
    descripcion TEXT,
    averia_id TEXT,
    activo BOOLEAN,
    descripcion_averia TEXT
);

CREATE TABLE IF NOT EXISTS novedades (
    id_nov VARCHAR(50) PRIMARY KEY,
    fecha TIMESTAMP,
    zona TEXT,
    tecnico_id TEXT,
    equipo_id TEXT,
    sistema_id TEXT,
    subsistema_id TEXT,
    item_id TEXT,
    descripcion TEXT,
    prioridad TEXT,
    tiempo_empleado_min NUMERIC,
    maquina TEXT,
    resuelto BOOLEAN,
    estado TEXT,
    creado_por TEXT,
    creado_en TIMESTAMP,
    ot_id TEXT
);

CREATE TABLE IF NOT EXISTS nov_detalle (
    id_detalle VARCHAR(50) PRIMARY KEY,
    id_nov VARCHAR(50),
    sistema_id TEXT,
    subsistema_id TEXT,
    item_id TEXT,
    averia_id TEXT,
    id_solucion VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS nov_evidencias (
    id_evidencia VARCHAR(50) PRIMARY KEY,
    id_nov VARCHAR(50),
    file_id TEXT,
    file_url TEXT,
    nombre_archivo TEXT,
    mime_type TEXT,
    subido_en TIMESTAMP
);

CREATE TABLE IF NOT EXISTS causas_falla (
    id_causa VARCHAR(50) PRIMARY KEY,
    descripcion TEXT,
    activo BOOLEAN
);

CREATE TABLE IF NOT EXISTS ot (
    id_ot VARCHAR(50) PRIMARY KEY,
    fecha TIMESTAMP,
    creacion_nov TEXT,
    origen_id TEXT,
    equipo_id TEXT,
    sistema_id TEXT,
    subsistema_id TEXT,
    item_id TEXT,
    prioridad TEXT,
    planeador_id TEXT,
    tecnico_asignador_id TEXT,
    estado TEXT,
    descripcion_solicitud TEXT,
    descripcion_trabajo TEXT,
    causa_id TEXT,
    causa_otro_texto TEXT,
    causa_normalizada_id TEXT,
    solicita_cierre BOOLEAN,
    solicita_cierre_por TEXT,
    solicita_cierre_en TIMESTAMP,
    cerrada_por TEXT,
    cerrada_en TIMESTAMP,
    folder_id TEXT,
    pdf_file_id TEXT,
    tipo_actividad TEXT,
    fecha_estimada TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ot_tiempos (
    id_tiempo VARCHAR(50) PRIMARY KEY,
    ot_id TEXT,
    tecnico_id TEXT,
    minutos NUMERIC,
    comentario TEXT,
    creado_en TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ot_repuestos (
    id_ot_rep VARCHAR(50) PRIMARY KEY,
    ot_id TEXT,
    repuesto_id TEXT,
    cantidad NUMERIC,
    observacion TEXT,
    creado_en TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ot_evidencias (
    id_evidencia VARCHAR(50) PRIMARY KEY,
    ot_id TEXT,
    file_id TEXT,
    file_url TEXT,
    nombre TEXT,
    mime_type TEXT,
    subido_en TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repuestos (
    id_repuesto VARCHAR(50) PRIMARY KEY,
    nombre_repuesto TEXT,
    categoria TEXT,
    stock NUMERIC,
    stock_minimo NUMERIC
);

CREATE TABLE IF NOT EXISTS param_chequeos (
    categoria TEXT PRIMARY KEY,
    actividad_chequeo TEXT,
    tipo TEXT
);

CREATE TABLE IF NOT EXISTS param_versiones (
    id_activo VARCHAR(50) PRIMARY KEY,
    version_disponible TEXT,
    unds NUMERIC
);

CREATE TABLE IF NOT EXISTS historial_versiones (
    id_registro VARCHAR(50) PRIMARY KEY,
    fecha TIMESTAMP,
    id_activo VARCHAR(50),
    version_anterior TEXT,
    version_nueva TEXT,
    id_ot VARCHAR(50),
    tecnico TEXT
);

CREATE TABLE IF NOT EXISTS docs (
    id_doc VARCHAR(50) PRIMARY KEY,
    nombre TEXT,
    codigo TEXT,
    version TEXT,
    estado TEXT,
    file_id TEXT,
    file_url TEXT,
    creado_por TEXT,
    creado_en TIMESTAMP
);

CREATE TABLE IF NOT EXISTS maquiladores (
    id_maquilador VARCHAR(50) PRIMARY KEY,
    nombre_empresa TEXT,
    contacto_nombre TEXT,
    contacto_telefono TEXT,
    estado TEXT
);

CREATE TABLE IF NOT EXISTS maquilas (
    id_registro VARCHAR(50) PRIMARY KEY,
    molde_id TEXT,
    perifericos_id TEXT,
    maquilador_id TEXT,
    fecha_registro TIMESTAMP,
    tipo_movimiento TEXT,
    orden_produccion TEXT,
    unidades_inyectadas NUMERIC,
    observaciones TEXT,
    registrado_por TEXT
);

CREATE TABLE IF NOT EXISTS nodisponibles (
    id_ot VARCHAR(50) PRIMARY KEY,
    id_activo VARCHAR(50),
    nombre_molde TEXT,
    tecnico_asignado TEXT,
    estado_ot TEXT,
    fecha_estimada TIMESTAMP,
    ultima_actualizacion TEXT
);

CREATE TABLE IF NOT EXISTS alistamiento (
    id_alis VARCHAR(50) PRIMARY KEY,
    fecha_registro TIMESTAMP,
    fecha_alis TIMESTAMP,
    molde_id TEXT,
    molde_nombre TEXT,
    tecnico_id TEXT,
    tecnico_nombre TEXT,
    tiempo_minutos NUMERIC,
    actividades_realizadas TEXT,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS montajes (
    id_montaje VARCHAR(50) PRIMARY KEY,
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    minutos_totales NUMERIC,
    estado TEXT,
    molde_id TEXT,
    molde_nombre TEXT,
    inyectora_id TEXT,
    inyectora_nombre TEXT,
    tecnico_id TEXT,
    tecnico_nombre TEXT,
    estado_alistamiento TEXT,
    observaciones_inicio TEXT,
    observaciones_fin TEXT,
    molde_baja_id TEXT,
    molde_baja_nombre TEXT,
    eventos_fallas TEXT,
    tiempo_eventos_min NUMERIC
);

CREATE TABLE IF NOT EXISTS tareas_programadas (
    id VARCHAR(50) PRIMARY KEY,
    fecha TIMESTAMP,
    titulo TEXT,
    descripcion TEXT,
    categoria TEXT,
    responsable TEXT,
    estado TEXT
);
