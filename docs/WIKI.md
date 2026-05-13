# Wiki de PC Agent

Bienvenido a la Wiki oficial de PC Agent. Este documento sirve como referencia completa para operar y entender el sistema.

## 1. Arquitectura de Agentes

PC Agent no es un simple bot; es un sistema de microservicios coordinados:

*   **LangGraph**: El "cerebro" que maneja el estado de las conversaciones. Permite flujos no lineales y pausas para aprobación humana.
*   **Native Tool Calling**: Los agentes tienen acceso a herramientas (functions) que invocan según la necesidad del usuario.
*   **Memoria Multinivel**:
    *   *Short-term*: MentisDB (rápida, volátil).
    *   *Mid-term*: Supabase `mentis_memory` (historial del día).
    *   *Long-term*: Conocimiento consolidado (aprendizajes proactivos).

## 2. Operación de Marketing (!marketer)

El agente de marketing es el más avanzado actualmente.

### Flujo de Trabajo
1.  **Análisis de Intención**: El LLM decide si necesitas `qualify_leads`, `monitor_trends`, `analyze_sentiment` o un `plan_campaign`.
2.  **Compuerta de Aprobación**: Para acciones críticas (como generar un plan costoso), el agente enviará una solicitud de aprobación a Discord.
3.  **Ejecución**: Una vez aprobado, el agente interactúa con las APIs de redes sociales (vía adapters).

### Comandos Interactivos
*   `!marketer`: Abre el panel de botones para acciones rápidas.
*   `!marketer memory`: Consulta los aprendizajes que el agente ha consolidado sobre tu marca.

## 3. Generación de Imágenes (!picture)

El agente de imágenes utiliza **DALL-E 3** y memoria proactiva para generar contenido visual de alta calidad.

### Características
- **Memoria de Estilo**: El agente recuerda tus preferencias estéticas y estilos anteriores guardados en la memoria `picture`.
- **Multimodalidad**: Puedes adjuntar imágenes en Discord; el agente las analizará (Vision) y las usará como referencia para la nueva generación.
- **Hilos de Conversación**: Cada solicitud crea un hilo dedicado para no saturar el canal principal.

### Comandos
- `!picture <descripción>`: Genera una imagen basada en tu texto y contexto.
- `!picture memory`: Muestra un resumen de los estilos y preferencias guardadas.
- `!picture memory --clean`: Limpia la memoria operativa de imágenes.

## 4. Desarrollo Web (!coder-web)

El sub-agente de desarrollo web permite automatizar la creación y ajuste de plataformas e-commerce.

### Capacidades
- **E-commerce Repo**: Crea repositorios completos con **React, TypeScript, Tailwind y Supabase**.
- **Wix Automator**: Ajusta interfaces en Wix mediante su API, permitiendo versionado y cambios rápidos.
- **Pilot Engine**: Usa el motor Pilot para orquestar la generación de código siguiendo patrones de arquitectura limpia.

### Comandos
- `!coder-web <desc>`: Inicia un proyecto web en un hilo dedicado.
- `!coder-web memory`: Muestra contextos de proyectos previos.
- `!coder-web memory --clean`: Borra la memoria operativa de desarrollo.

## 5. Inteligencia Proactiva

El sistema aprende mientras duermes:
*   **Consolidación Diaria**: Cada medianoche (UTC), el `ingestion-worker` toma todas las memorias del día y genera un resumen ejecutivo.
*   **Ejecución Manual**: Puedes forzar este proceso con `!run consolidation`.

## 6. Observabilidad

Para desarrolladores y administradores:
*   **Langfuse**: Rastrea cada llamada al LLM. Útil para depurar por qué el agente tomó una decisión.
*   **Control API**: `http://localhost:8000/status` para ver la salud del sistema.

## 7. Mejores Prácticas
*   **Contexto**: Cuanto más uses el sistema, mejor te conocerá gracias a la consolidación de memoria.
*   **Seguridad**: Nunca desactives las compuertas de aprobación para acciones que involucren APIs externas de escritura.
