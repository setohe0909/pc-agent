# Sub-Agente: !picture (Image Generator)

El sub-agente `!picture` es un especialista en creación de contenido visual diseñado para trabajar en conjunto con el equipo de marketing y redacción. Utiliza modelos de difusión de última generación (DALL-E 3) integrados en un flujo de trabajo de **LangGraph**.

## Capacidades Principales

1.  **Generación Contextual**: No solo genera imágenes basadas en prompts aislados; utiliza la **Memoria Proactiva** para inyectar preferencias estéticas, paletas de colores de la marca y estilos recurrentes.
2.  **Visión Multimodal**: Capacidad de analizar imágenes adjuntas por el usuario para:
    *   Extraer estilos artísticos.
    *   Describir composiciones para recrearlas.
    *   Asegurar coherencia visual con activos existentes.
3.  **Aislamiento en Hilos**: Para mantener el orden, cada solicitud de imagen se procesa en un hilo de Discord, donde el agente muestra el progreso y el prompt final utilizado.

## Guía de Comandos

### `!picture <petición>`
Genera una imagen. Puedes ser tan vago o específico como quieras.
*   *Ejemplo vago*: `!picture un café moderno` (El agente usará la memoria para decidir el estilo).
*   *Ejemplo con imagen*: Envía una foto de un logo y escribe `!picture crea un fondo de pantalla para móvil basado en este estilo`.

### `!picture memory`
Muestra qué ha aprendido el agente sobre tus preferencias visuales. Estos aprendizajes se consolidan diariamente.

### `!picture memory --clean`
Limpia la memoria operativa del agente de imágenes. Útil si quieres cambiar radicalmente de dirección creativa y no quieres que el agente se vea influenciado por estilos pasados.

## Detalles Técnicos (v0.4.0)

*   **Workflow**: `PictureGraph` (LangGraph).
*   **LLM Provider**: DALL-E 3 (via OpenAI/LiteLLM).
*   **Storage**: Las referencias de estilo se guardan en la tabla `mentis_memory` de Supabase bajo la categoría `picture_style`.
*   **Output**: Formato PNG (vía URL de CDN).

## Integración con otros Agentes
El Picture Agent puede ser invocado internamente por el `!marketer` en futuras versiones para ilustrar planes de campaña o por el `!writer` para generar portadas de blog.
