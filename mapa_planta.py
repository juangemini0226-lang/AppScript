# ==========================================================================
# COPIA este archivo como "secrets.toml" (mismo folder) para desarrollo,
# o pega este mismo contenido en Streamlit Community Cloud -> Settings ->
# Secrets si despliegas ahí.
#
# NUNCA subas secrets.toml real a GitHub. Este archivo .example SÍ se sube,
# el real debe estar en .gitignore.
# ==========================================================================

db_engine = "gcp_cloudsql"

[gcp_cloudsql]
instance_connection_name = "tu-proyecto-gcp:us-central1:cmms-instance"
db_user = "cmms_app"
db_pass = "CAMBIA_ESTA_CLAVE"
db_name = "cmms_flaeice"
ip_type = "PUBLIC"   # usa "PRIVATE" si conectas desde una VPC (Cloud Run/GCE)

# Opcional: solo necesario si NO corres en GCP (ej. Streamlit Community Cloud)
# y por lo tanto no tienes Application Default Credentials.
# Pega aquí el JSON completo de la Service Account (rol: Cloud SQL Client).
[gcp_cloudsql.credentials_json]
type = "service_account"
project_id = "tu-proyecto-gcp"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "cmms-app@tu-proyecto-gcp.iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"

[app]
empresa = "FLA-EICE"
linea = "Línea 3 - Envasado"
timezone = "America/Bogota"
