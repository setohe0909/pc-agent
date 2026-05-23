# Sales Funnel Generator (Generador de Funnels)

Este módulo permite diseñar estrategias de contenido estructuradas siguiendo las etapas del embudo de ventas (Funnel).

## Funcionalidad
El agente genera una propuesta estratégica dividida en tres fases clave para maximizar la conversión.

- **Comando**: `!marketer funnel [tema/marca]`
- **Etapas del Embudo**:
    1. **TOFU (Top of Funnel)**: Contenido de descubrimiento y atracción (viralidad).
    2. **MOFU (Middle of Funnel)**: Contenido de consideración y construcción de autoridad/confianza.
    3. **BOFU (Bottom of Funnel)**: Contenido de conversión y cierre de ventas.

## Implementación Técnica
- **Workflow**: `MarketingGraph._generate_funnel()`
- **Lógica**: Utiliza un prompt estructurado enviado al LLM para organizar las ideas de contenido en una jerarquía lógica de marketing.
- **Producción**: es una acción de estrategia y no ejecuta publicaciones, DMs ni cambios externos por sí sola.

## Beneficios
- Asegura que no todo el contenido sea de venta directa (lo cual agota a la audiencia).
- Proporciona una hoja de ruta clara para el crecimiento de seguidores y la captación de leads.
