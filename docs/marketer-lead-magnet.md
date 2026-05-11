# Lead Magnet Automation ("Comment-to-DM")

Este módulo automatiza la entrega de recursos gratuitos (lead magnets) a los usuarios que interactúan con palabras clave específicas en los comentarios.

## Funcionalidad
El agente monitorea los comentarios en busca de disparadores (triggers) predefinidos y responde automáticamente enviando un mensaje directo (DM) con el recurso solicitado.

- **Comando**: `!marketer magnet`
- **Disparadores (Triggers) Actuales**:
    - `GUIA`: Envía un enlace a la "Guía de Estilo".
    - `INFO`: Envía un enlace al "Catálogo 2026".
- **Valor**: Aumenta la conversión de seguidores a leads y automatiza tareas repetitivas de atención al cliente.

## Implementación Técnica
- **Workflow**: `MarketingWorkflow._process_lead_magnets()`
- **Puerto de Marketing**: 
    - `get_comments()`: Para leer los comentarios.
    - `send_dm()`: Para enviar la respuesta privada.
- **Lógica**: Comparación de texto (insensible a mayúsculas) para identificar los triggers.

## Próximos Pasos
- Configuración dinámica de magnets desde el portal administrativo.
- Registro de qué usuario recibió qué magnet para evitar envíos duplicados.
