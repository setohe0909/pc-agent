# Lead Qualification (Cualificación de Leads)

Este módulo permite al sub-agente `!marketer` analizar las interacciones en redes sociales (Instagram y TikTok) para identificar usuarios con alta intención de compra.

## Funcionalidad
El agente utiliza modelos de lenguaje (LLM) para evaluar el contenido de los comentarios y asignarles una puntuación de intención.

- **Comando**: `!marketer qualify`
- **Lógica de Análisis**:
    - **Puntuación (0-10)**: Indica el nivel de interés detectado.
    - **Categoría**: 
        - `curious`: Preguntas generales sin intención clara.
        - `interested`: Muestra interés en el producto o diseño.
        - `hot`: Preguntas específicas sobre precio, disponibilidad o cómo comprar.
    - **Notificación**: Actualmente muestra un resumen detallado en Discord de los leads que superan el umbral de intención (7/10).

## Implementación Técnica
- **Workflow**: `MarketingWorkflow._qualify_leads()`
- **Puerto de Marketing**: Consume `MarketingPort.get_comments()`.
- **Análisis**: Se realiza un prompt estructurado al LLM para obtener la clasificación en formato JSON.

## Próximos Pasos
- Integración con CRM para guardar automáticamente los leads detectados.
- Notificaciones en tiempo real vía webhooks a canales específicos de ventas.
