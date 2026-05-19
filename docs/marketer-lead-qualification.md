# Lead Qualification (Cualificación de Leads)

Este módulo permite al sub-agente `!marketer` analizar las interacciones en redes sociales (Instagram y TikTok) para identificar usuarios con alta intención de compra.

## Funcionalidad
El agente utiliza modelos de lenguaje (LLM) para evaluar el contenido de los comentarios y asignarles una puntuación de intención.

- **Comando**: `!marketer qualify`
- **Fuente Zernio**: `!marketer --source zernio qualify --account <id>`
- **Lógica de Análisis**:
    - **Puntuación (0-10)**: Indica el nivel de interés detectado.
    - **Categoría**: 
        - `curious`: Preguntas generales sin intención clara.
        - `interested`: Muestra interés en el producto o diseño.
        - `hot`: Preguntas específicas sobre precio, disponibilidad o cómo comprar.
    - **Notificación**: muestra un resumen detallado en Discord de los leads que superan el umbral de intención.
    - **Trazabilidad**: cuando se usa Zernio, cada lead conserva metadatos de fuente, comentario, post, cuenta y URL.

## Implementación Técnica
- **Workflow**: `MarketingGraph._qualify_leads()` delega a `MarketingAutomationService.qualify_leads()`.
- **Puerto de Marketing**: consume `MarketingPort.get_comments(platform, post_id, data_source, account_id)`.
- **Adaptador Zernio**: con `data_source=zernio`, usa la Comments API de Zernio para listar publicaciones con comentarios y consultar el hilo de cada post.
- **Análisis**: la detección inicial usa señales de intención de compra y queda lista para evolucionar a scoring LLM/CRM sin acoplar el bot a Zernio.

## Próximos Pasos
- Definir scoring configurable por empresa y producto.
- Agregar deduplicación por `comment_id` para evitar guardar el mismo lead varias veces.
- Notificaciones en tiempo real vía webhooks a canales específicos de ventas.
