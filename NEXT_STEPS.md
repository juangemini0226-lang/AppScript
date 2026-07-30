# Instrucciones de continuidad (para otra IA / otra sesión)

Este proyecto es la migración del CMMS de FLA-EICE (Línea 3 de
Envasado), que originalmente corría 100% en Google Apps Script sobre
un Google Sheet de 25 hojas, hacia una app en Streamlit con
PostgreSQL en Google Cloud SQL como base de datos.

## Qué se hizo hasta ahora

Se analizó el código fuente original completo (14 archivos `.gs` y 4
`.html`, ~12.800 líneas) y la estructura real de datos (el Excel
`CMMS_DB.xlsx`, que es un espejo del Sheet de producción con 25
tablas). Con eso se construyó el esqueleto del nuevo proyecto en
`cmms_streamlit/` con esta filosofía: separar completamente la lógica
de negocio de la base de datos, para que el usuario pueda cambiar de
motor de base de datos en el futuro sin reescribir nada de la lógica.

Concretamente se entregó: la interfaz abstracta `db/base.py`
(`DBConnector`) que define qué operaciones puede pedir cualquier parte
del sistema a la base de datos; su implementación concreta para Google
Cloud SQL en `db/gcp_connector.py`, usando el Cloud SQL Python
Connector y SQLAlchemy; un `db/factory.py` que es el único punto donde
se decide qué motor está activo; el esquema completo de PostgreSQL en
`db/schema.sql`, generado directamente a partir de las cabeceras reales
de las 25 hojas del Excel (no inventado); y un script
`db/migrate_from_sheets.py` para volcar los datos actuales del Sheet
hacia Cloud SQL usando `gspread`, pensado para correrse desde un
Codespace o un GitHub Action, porque el usuario trabaja enteramente en
línea sin entorno local.

Sobre esa base se migró un primer módulo completo de punta a punta,
como prueba de que la arquitectura funciona: `activos.gs` se portó a
`services/activos_service.py`, conservando exactamente la misma lógica
(equipos, jerarquía técnica sistema→subsistema→ítem, averías,
soluciones, consulta de ubicación de molde), y se construyó la página
`pages/1_Activos.py` en Streamlit que la consume. También se portó
`users.gs` a `services/users_service.py`, incluyendo el login por
correo con la lista de superadmins y el login rápido por PIN que se
usa en planta, y se conectó a un formulario de login en `app.py`. Las
páginas de Órdenes de Trabajo, Novedades, Maquilas y Admin se dejaron
como placeholders con un docstring explicando exactamente qué archivo
`.gs` origen hay que portar y qué patrón seguir, para que el trabajo
que falta sea mecánico y no requiera releer todo el código otra vez.
También se dejó `DOCUMENTATION.md` con la arquitectura completa, el
estado de la migración módulo por módulo, las decisiones de diseño (por
qué Postgres y no Firestore o BigQuery, por qué los IDs quedaron como
VARCHAR y no autoincrementales) y los pendientes que quedan fuera de
la base de datos, como el manejo de archivos y evidencias, que en el
original vivían en Google Drive y que en la nueva arquitectura deberían
migrar a Google Cloud Storage con la misma filosofía de abstracción que
se usó para la base de datos.

## Qué sigue

Lo siguiente que hay que hacer, en orden de prioridad, es portar los
tres módulos de negocio que faltan siguiendo exactamente el patrón que
ya existe en `activos_service.py` y `users_service.py`: primero
Órdenes de Trabajo, que es el módulo más grande y más usado
(`ot_consulta.gs` y `ot_gestion.gs`), incluyendo la generación de PDF
que habrá que reescribir con una librería Python como `reportlab` en
vez de `DocumentApp`; después Novedades (`novedades_consulta.gs`), que
es más simple pero depende de que exista ya el manejo de evidencias en
Cloud Storage; y por último Maquilas y Admin. En paralelo conviene
resolver el tema de autenticación real con Google OAuth, porque hoy el
login pide el correo por formulario en vez de detectarlo
automáticamente como hacía Apps Script con la sesión de Google. Antes
de portar cualquier módulo nuevo, quien continúe debería crear la
instancia de Cloud SQL en GCP, correr `db/schema.sql` contra ella, y
correr `db/migrate_from_sheets.py` para tener datos reales con los que
probar `pages/1_Activos.py`; eso confirma que toda la cadena
Streamlit→services→db→Cloud SQL funciona antes de invertir tiempo
portando los módulos que faltan. Todo el trabajo debe seguir haciéndose
desde GitHub (Codespaces o edición web), sin asumir un entorno local,
porque esa es la restricción de quien mantiene este proyecto.
