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
1.  **Inicialización**: Normaliza payload, subcomando, fuente de datos y aprobaciones.
2.  **Análisis de Intención**: `MarketingGraph` decide si necesita dashboard, comentarios, leads, publicaciones, campaña, sentimiento, tendencias u otra acción.
3.  **Contexto y Voz**: Recupera memoria del Marketer y refina planes complejos antes de mostrarlos.
4.  **Compuerta de Aprobación**: Publicaciones, respuestas, DMs y acciones con escritura externa requieren aprobación humana y políticas de autonomía.
5.  **Ejecución**: La ruta productiva usa `ZernioAdapter` y contratos `MarketingPort`; no debe depender de datos demo en runtime.

### Comandos Interactivos
*   `!marketer`: Abre el panel de botones para acciones rápidas.
*   `!marketer memory`: Consulta los aprendizajes que el agente ha consolidado sobre tu marca.
*   `!marketer --source zernio comments --account <id>`: Lee comentarios actuales desde Zernio con trazabilidad de cuenta.
*   `!marketer post <texto> --platform <instagram|tiktok> --account <id>`: Prepara/publica contenido solo cuando exista aprobación y permisos de escritura.

## 3. Redacción Editorial (!writer)

Writer crea contenido editorial con contrato productivo:

*   `!writer blog <es|en> <tema>`: genera Markdown y lo guarda en Obsidian.
*   `!writer story <es|en> <tema>`: genera storytelling y lo guarda en Obsidian.
*   `!writer <mensaje>`: chat editorial con memoria de marca.

Si Obsidian no está disponible o no tiene permisos, Writer devuelve `writer.persistence_failed` y no reporta éxito parcial. Las imágenes externas no se insertan automáticamente; se sugieren keywords para usar assets licenciados o generados.

## 4. Generación de Imágenes (!picture)

El agente de imágenes utiliza **DALL-E 3** y memoria proactiva para generar contenido visual de alta calidad.

### Características
- **Memoria de Estilo**: El agente recuerda tus preferencias estéticas y estilos anteriores guardados en la memoria `picture`.
- **Multimodalidad**: Puedes adjuntar imágenes en Discord; el agente las analizará (Vision) y las usará como referencia para la nueva generación.
- **Hilos de Conversación**: Cada solicitud crea un hilo dedicado para no saturar el canal principal.

### Comandos
- `!picture <descripción>`: Genera una imagen basada en tu texto y contexto.
- `!picture memory`: Muestra un resumen de los estilos y preferencias guardadas.
- `!picture memory --clean`: Limpia la memoria operativa de imágenes.

## 5. Desarrollo Web (!coder-web)

El sub-agente de desarrollo web permite automatizar la creación y ajuste de plataformas e-commerce mediante repositorios de código.

### Capacidades
- **E-commerce Repo**: Crea repositorios completos con **React, TypeScript, Tailwind y Supabase**.
- **Pilot Engine**: Usa el motor Pilot para orquestar la generación de código siguiendo patrones de arquitectura limpia.

### Comandos
- `!coder-web <desc>`: Inicia un proyecto web en un hilo dedicado.
- `!coder-web memory`: Muestra contextos de proyectos previos.
- `!coder-web memory --clean`: Borra la memoria operativa de desarrollo.

## 6. Email (!email)

El sub-agente de email opera correo con enfoque Clean/Hexagonal para que el dominio no dependa de Gmail, Outlook, IMAP/SMTP ni clientes locales.

### Capacidades
- Configuracion de proveedores desde el administrador UI.
- Categorizacion por filtros, categorias y clasificacion asistida.
- Listado de emails enviados el mismo dia.
- Respuestas bulk mediante templates administrados, job aprobable y auditoria.
- Estado operacional con `!email status` y `!email --model-status`.

### Comandos
- `!email` o `!email status`: revisa proveedor, lectura, envio y templates.
- `!email sent-today`: lista enviados de hoy.
- `!email categorize <categoria>`: prepara reglas/categorizacion.
- `!email --template-<nombre> <categoria>`: prepara respuesta bulk para aprobacion con botones en Discord.
- `!email process-queued`: procesa jobs bulk aprobados en cola.

### Seguridad
Los envios masivos requieren proveedor configurado, permiso explicito de envio, aprobacion humana, rate limits, idempotencia y auditoria. Por defecto el agente genera un `job_id`; la aprobacion deja el job en cola, `!email process-queued` ejecuta el envio real y la denegacion cancela el job sin enviar correos.

La vista `Email Agent` del administrador funciona como consola operativa: muestra estado de proveedor, envio, persistencia, categorias y templates, y permite editar esa configuracion desde el mismo panel.

## 7. Inteligencia Proactiva

El sistema aprende mientras duermes:
*   **Consolidación Diaria**: Cada medianoche (UTC), el `ingestion-worker` toma todas las memorias del día y genera un resumen ejecutivo.
*   **Ejecución Manual**: Puedes forzar este proceso con `!run consolidation`.

## 7. Observabilidad

Para desarrolladores y administradores:
*   **Langfuse**: Rastrea cada llamada al LLM. Útil para depurar por qué el agente tomó una decisión.
*   **Control API**: `http://localhost:8000/status` para ver la salud del sistema.

## 8. Mejores Prácticas
*   **Contexto**: Cuanto más uses el sistema, mejor te conocerá gracias a la consolidación de memoria.
*   **Seguridad**: Nunca desactives las compuertas de aprobación para acciones que involucren APIs externas de escritura.
