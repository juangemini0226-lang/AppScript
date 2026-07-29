# CMMS FLA-EICE — Línea 3 Envasado (Streamlit + Google Cloud SQL)

Migración del CMMS original (Google Apps Script + Google Sheets) a
Streamlit + PostgreSQL en Google Cloud, manteniendo las mismas
funcionalidades.

- **Documentación completa de arquitectura y estado de la migración:**
  ver [`DOCUMENTATION.md`](./DOCUMENTATION.md).
- **Instrucciones detalladas para continuar el desarrollo (para otra
  IA o para ti mismo en otra sesión):** ver [`NEXT_STEPS.md`](./NEXT_STEPS.md).

## Arranque rápido

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # y completa tus credenciales
streamlit run app.py
```

## Estructura

Ver el árbol completo y la explicación de cada carpeta en
`DOCUMENTATION.md`, sección 3.
