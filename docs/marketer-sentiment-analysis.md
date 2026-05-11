# Sentiment Analysis & Crisis Management (Análisis de Sentimiento)

Este módulo permite monitorear la salud de la reputación de la marca analizando el tono de las interacciones de los usuarios.

## Funcionalidad
El agente procesa los comentarios recientes para clasificar el sentimiento general y detectar posibles crisis de reputación.

- **Comando**: `!marketer sentiment`
- **Categorías de Sentimiento**:
    - **Positivo**: Comentarios de apoyo, satisfacción o elogios.
    - **Neutral**: Preguntas informativas o comentarios sin carga emocional clara.
    - **Negativo**: Quejas, críticas o ataques.
- **Gestión de Crisis**: Si el volumen de comentarios negativos supera un umbral crítico (ej: 20% o más de 2 comentarios en el set de prueba), el agente emite una alerta roja (`🚨 ALERTA DE CRISIS`).

## Implementación Técnica
- **Workflow**: `MarketingWorkflow._analyze_sentiment()`
- **Lógica**: Utiliza el LLM para una clasificación semántica del texto, y luego agrega los resultados para generar un reporte estadístico.

## Beneficios
- Permite una reacción rápida ante problemas de producto o servicio.
- Proporciona una métrica clara de la satisfacción de la comunidad.
- Automatiza la detección de "trolls" o ataques coordinados.
