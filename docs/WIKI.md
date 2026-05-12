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

## 3. Inteligencia Proactiva

El sistema aprende mientras duermes:
*   **Consolidación Diaria**: Cada medianoche (UTC), el `ingestion-worker` toma todas las memorias del día y genera un resumen ejecutivo.
*   **Ejecución Manual**: Puedes forzar este proceso con `!run consolidation`.

## 4. Observabilidad

Para desarrolladores y administradores:
*   **Langfuse**: Rastrea cada llamada al LLM. Útil para depurar por qué el agente tomó una decisión.
*   **Control API**: `http://localhost:8000/status` para ver la salud del sistema.

## 5. Mejores Prácticas
*   **Contexto**: Cuanto más uses el sistema, mejor te conocerá gracias a la consolidación de memoria.
*   **Seguridad**: Nunca desactives las compuertas de aprobación para acciones que involucren APIs externas de escritura.
