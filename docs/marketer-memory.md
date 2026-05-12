# Marketer Memory System (MentisDB Integration)

Este módulo implementa un sistema de memoria proactiva para el sub-agente `!marketer`, permitiéndole aprender de sus interacciones pasadas y utilizar ese conocimiento para dar mejores respuestas y recomendaciones.

## Funcionalidad
El sistema utiliza **MentisDB** (almacenado en Supabase) para persistir aprendizajes clave.

- **Comando**: `!marketer memory`
- **Tipos de Memoria (Categorías)**:
    - `marketing_lead`: Registro de leads cualificados detectados.
    - `marketing_trend`: Registro de tendencias virales encontradas.
    - `marketing_insight`: Hallazgos estratégicos generales.

## Implementación Técnica
1.  **Persistencia**: Se actualizó `MentisMemoryAdapter` para incluir el método `save_memory`, que escribe en la tabla `mentis_memory`.
2.  **Contexto**: Antes de procesar cualquier comando de chat, el sub-agente consulta los últimos 5 fragmentos de memoria para ajustar su tono y recomendaciones.
3.  **Aprendizaje Automático**:
    - Al ejecutar `!marketer qualify`, se guarda automáticamente un registro del lead encontrado.
    - Al ejecutar `!marketer trends`, se guarda la tendencia detectada para futuras referencias.

## Beneficios
- **Contextualización**: El agente "recuerda" qué tendencias ha visto antes.
- **Continuidad**: Permite al usuario ver un resumen de lo que el agente ha "aprendido" durante el día.
- **Base de Conocimiento**: Acumula inteligencia sobre la audiencia y el mercado de forma automática.

## Próximos Pasos
- Implementar búsqueda semántica (vectorial) sobre la memoria del marketer para recuperar fragmentos más precisos según el prompt del usuario.
- Integrar la memoria con el sistema de planificación de campañas para que proponga ideas basadas en lo que funcionó en el pasado.
