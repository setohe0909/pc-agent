# Trend Discovery Engine (Motor de Descubrimiento de Tendencias)

Este módulo permite identificar tendencias emergentes en Instagram y TikTok para que la marca pueda actuar rápidamente y aumentar su alcance orgánico.

## Funcionalidad
El agente monitorea el ecosistema digital para detectar sonidos, hashtags y formatos de video que están ganando tracción (Viral Potential).

- **Comando**: `!marketer trends`
- **Output**:
    - Listado de tendencias detectadas con su porcentaje de crecimiento estimado.
    - Sugerencias creativas generadas por IA para adaptar esas tendencias a la marca específica.

## Implementación Técnica
- **Workflow**: `MarketingWorkflow._monitor_trends()`
- **Lógica**: Actualmente simula la detección de tendencias y utiliza el LLM para generar ideas de contenido contextualizadas. 
- **Integración**: Este módulo está diseñado para ser llamado periódicamente por el `ingestion-worker` para enviar alertas proactivas.

## Beneficios
- Permite a la marca ser "pionera" en tendencias antes de que se saturen.
- Automatiza la fase de ideación creativa, ahorrando horas de navegación en redes sociales.
