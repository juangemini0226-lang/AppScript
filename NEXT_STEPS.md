# CMMS FLA-EICE — Documentación técnica

Sistema de mantenimiento (CMMS) de la Línea 3 de Envasado, FLA-EICE.
Este documento explica **qué es cada cosa, por qué está diseñada así, y
qué falta**, pensado para que cualquier persona (o IA) que retome el
proyecto no tenga que releer el Apps Script original desde cero.

## 1. De dónde viene esto

El sistema original vivía 100% en Google Apps Script:
- **Backend**: 14 archivos `.gs` (config, database, activos, users, OT,
  novedades, maquilas, PDF, admin, reportes...) operando directamente
  sobre un Google Sheet con 25 hojas.
- **Frontend**: 4 archivos `.html` (`ui.html`, `admin.html`,
  `maquilas.html`, `parametrización.html`) servidos como web app de
  Apps Script.

El Sheet (`CMMS_DB.xlsx` en este repo es una copia de su estructura)
tiene estas 25 tablas: `USUARIOS, CONFIG, ACTIVOS, JERARQUIA_TECNICA,
AVERIAS, SOLUCIONES_AVERIA, NOVEDADES, NOV_DETALLE, NOV_EVIDENCIAS,
CAUSAS_FALLA, OT, OT_TIEMPOS, OT_REPUESTOS, OT_EVIDENCIAS, REPUESTOS,
PARAM_CHEQUEOS, PARAM_VERSIONES, HISTORIAL_VERSIONES, DOCS,
MAQUILADORES, MAQUILAS, Nodisponibles, ALISTAMIENTO, MONTAJES,
TAREAS_PROGRAMADAS`.

## 2. Arquitectura nueva

```
Streamlit (UI)  →  services/*.py (lógica de negocio)  →  db/factory.py
                                                              │
                                                    DBConnector (interfaz)
                                                              │
                                                  db/gcp_connector.py
                                                  (Cloud SQL / PostgreSQL)
```

**Regla de oro**: `services/*` y las páginas de Streamlit **nunca**
importan `sqlalchemy`, `psycopg2` ni nada de Google Cloud directamente.
Solo hablan con `db.factory.get_connector()`, que devuelve un objeto que
cumple la interfaz `DBConnector` (`db/base.py`).

### Por qué esta capa de abstracción (lo que pediste explícitamente)

Hoy el destino es **Google Cloud SQL (PostgreSQL)**. Es la elección
razonable porque los datos son fuertemente relacionales (una OT tiene
tiempos, repuestos y evidencias asociadas por `OT_ID`; una novedad se
liga a equipo→sistema→subsistema→ítem). Pero si en el futuro decides
migrar (por costo, por escalar a otra nube, por pasar a Firestore para
las evidencias/fotos, etc.), el cambio se reduce a:

1. Crear `db/nuevo_motor_connector.py` implementando `DBConnector`.
2. Cambiar una línea en `db/factory.py`.

Nada en `services/` ni en `pages/` se toca. Esa es la razón de ser de
`db/base.py`.

## 3. Estructura del repo

```
cmms_streamlit/
├── app.py                     # Entrada Streamlit + login
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example   # plantilla de credenciales (NO subir la real)
├── config/
│   └── settings.py            # lee st.secrets y lo normaliza a dict
├── db/
│   ├── base.py                # interfaz DBConnector (el contrato)
│   ├── factory.py             # decide qué conector instanciar
│   ├── gcp_connector.py        # implementación Cloud SQL / PostgreSQL
│   ├── schema.sql             # DDL de las 25 tablas (generado desde el Excel real)
│   └── migrate_from_sheets.py # script de migración Sheet -> Cloud SQL (una vez)
├── services/
│   ├── activos_service.py     # ✅ migrado completo (desde activos.gs)
│   └── users_service.py       # ✅ migrado completo (desde users.gs)
└── pages/
    ├── 1_Activos.py           # ✅ funcional end-to-end
    ├── 2_Ordenes_de_Trabajo.py# ⏳ placeholder, con plan de migración en docstring
    ├── 3_Novedades.py         # ⏳ placeholder
    ├── 4_Maquilas.py          # ⏳ placeholder
    └── 5_Admin.py             # ⏳ placeholder
```

## 4. Estado de la migración (checklist)

| Módulo | Estado |
|---|---|
| Login (correo / PIN rápido) | ✅ |
| Dashboard con KPIs + accesos rápidos | ✅ |
| Activos: explorar, consultar molde, crear, listar+buscar+editar en línea | ✅ |
| Novedades: reportar, tablero, conversión directa a OT | ✅ |
| Órdenes de Trabajo: tablero Kanban, lista+detalle, crear, cambiar estado | ✅ |
| Maquilas: historial, registrar movimiento, dar de alta maquiladores | ✅ |
| Admin: usuarios (CRUD), módulos on/off **+ visibilidad por rol** | ✅ |
| Admin: explorador de base de datos (ver tablas + SQL de solo lectura) | ✅ |
| Repuestos por OT, evidencias fotográficas, PDF de cierre | ⏳ pendiente |
| Recarga de datos de `activos` (rota por los `#N/A` del Sheet original) | ⏳ pendiente |
| Autenticación real con Google OAuth (hoy: correo por formulario) | ⏳ pendiente |

## 5. Decisiones de base de datos

- **Motor**: PostgreSQL en Cloud SQL. Alternativas consideradas y por
  qué no: Firestore (NoSQL) complica los joins que ya existían de forma
  natural en el Sheet (OT↔tiempos↔repuestos↔evidencias); BigQuery es
  para analítica, no para un sistema transaccional con formularios.
- **Tipos de columna** (`db/schema.sql`): los `ID_*` se dejaron como
  `VARCHAR(50)` porque hoy son códigos manuales (`EQ-001`, `MOLDE-014`),
  no autoincrementales. Si más adelante decides normalizar a
  `SERIAL`/`UUID`, es un cambio localizado en `schema.sql` +
  `migrate_from_sheets.py`.
- **Conexión**: se usa el *Cloud SQL Python Connector* (no una IP +
  contraseña sueltas) porque maneja TLS y rotación de certificados
  automáticamente, y funciona igual de bien desde Streamlit Community
  Cloud, Cloud Run o un Codespace de GitHub.

## 6. Pendientes fuera de la base de datos

1. **Archivos/evidencias** (fotos de novedades y OT, PDFs de OT,
   documentos): el original usaba `DriveApp`. La opción natural en GCP
   es **Google Cloud Storage** (un bucket, URLs firmadas). Falta un
   `storage/gcs_connector.py` con la misma filosofía de abstracción
   que `db/`.
2. **Autenticación real**: hoy `get_current_user()` recibe el email por
   formulario. Para producción conviene integrar **Google OAuth** (o
   Identity-Aware Proxy si se despliega en Cloud Run) para que el login
   sea automático como en Apps Script.
3. **Generación de PDF** (`pdf_generator.gs`): portar a `reportlab` o
   `WeasyPrint`.
4. **Envío de correos** (scopes de Gmail en `appscript.json`): usar
   `smtplib` con una cuenta de servicio SMTP, o la API de Gmail si se
   necesita mantener el remitente corporativo.

## 7. Cómo desplegar (sin entorno local, todo desde GitHub)

1. Sube este repo a GitHub.
2. Crea la instancia de Cloud SQL (PostgreSQL) desde la consola de GCP
   o Cloud Shell — no requiere nada local.
3. Corre `db/schema.sql` contra la instancia (desde Cloud Shell con
   `psql`, o desde un Codespace).
4. Corre `db/migrate_from_sheets.py` una vez para volcar los datos
   actuales del Sheet (ver instrucciones en el propio archivo).
5. Despliega en **Streamlit Community Cloud** apuntando a este repo de
   GitHub; pega el contenido de `.streamlit/secrets.toml.example`
   (con tus valores reales) en Settings → Secrets.
6. Verifica que `pages/1_Activos.py` carga datos reales — es el módulo
   ya migrado que sirve de prueba de humo de toda la arquitectura.
