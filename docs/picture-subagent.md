# Sub-Agente: !picture (Creative Image Agent)

El sub-agente `!picture` es un especialista en creación y edición de contenido visual diseñado para trabajar en conjunto con diseñadores, marketing y redacción. Usa un flujo de trabajo de **LangGraph** con intención creativa estructurada para decidir si debe generar una imagen nueva o editar un diseño existente.

## Capacidades Principales

1.  **Generación Contextual**: Genera imágenes nuevas usando memoria proactiva para inyectar preferencias estéticas, paletas de colores de marca y estilos recurrentes.
2.  **Edición Fiel de Diseños**: Cuando hay una imagen adjunta, el agente clasifica la intención como `edit`, `replace_text` o `variations` y prioriza conservar composición, logos, colores, espaciado y textos no solicitados.
3.  **Cambio de Texto en Diseños**: Para solicitudes como "cambia este texto por este otro", el flujo usa edición de imagen en vez de recreación desde cero.
4.  **Visión Multimodal**: Capacidad de analizar imágenes adjuntas por el usuario para:
    *   Extraer estilos artísticos.
    *   Describir composiciones para recrearlas.
    *   Asegurar coherencia visual con activos existentes.
5.  **Aislamiento en Hilos**: Para mantener el orden, cada solicitud de imagen se procesa en un hilo de Discord, donde el agente muestra el modo, el prompt aplicado y checks esperados.

## Guía de Comandos

### `!picture <petición>`
Genera una imagen o edita una imagen adjunta según la intención detectada.
*   *Ejemplo vago*: `!picture un café moderno` (El agente usará la memoria para decidir el estilo).
*   *Ejemplo con imagen*: Envía una foto de un logo y escribe `!picture crea un fondo de pantalla para móvil basado en este estilo`.
*   *Ejemplo de edición*: Adjunta un diseño y escribe `!picture cambia el texto "Summer Sale" por "Cyber Week"`.
*   *Ejemplo de variación*: Adjunta una pieza y escribe `!picture crea 3 versiones con look más premium conservando la composición`.

### `!marketer --free-model <petición visual>`
Atajo desde Marketing para crear o editar una pieza visual usando el proveedor gratuito/local preferido.
*   Sin imagen adjunta, usa generación local/Ollama (`OLLAMA_IMAGE_MODEL`, por defecto `x/z-image-turbo`).
*   Con imagen adjunta, intenta edición local vía `PICTURE_LOCAL_IMAGE_EDIT_URL`.
*   Ejemplo: `!marketer --free-model visual para campaña de lanzamiento con texto "Nuevo Drop"`

### `!picture memory`
Muestra qué ha aprendido el agente sobre tus preferencias visuales. Estos aprendizajes se consolidan diariamente.

### `!picture memory --clean`
Limpia la memoria operativa del agente de imágenes. Útil si quieres cambiar radicalmente de dirección creativa y no quieres que el agente se vea influenciado por estilos pasados.

## Detalles Técnicos

*   **Workflow**: `PictureGraph` (LangGraph).
*   **Dominio**: `PictureEditPlan` clasifica `generate`, `edit`, `replace_text` y `variations`.
*   **LLM Provider**: Generación vía Gemini Imagen/OpenAI; edición fiel vía `edit_image` en el puerto LLM.
*   **Configuración de edición**: `OPENAI_IMAGE_EDIT_MODEL` permite elegir el modelo de edición; por defecto usa `openai/gpt-image-1`.
*   **Proveedor local/self-hosted**: `PICTURE_IMAGE_EDIT_PROVIDER=local` envía la edición a `PICTURE_LOCAL_IMAGE_EDIT_URL` con `prompt`, `image_b64`, `image_mime`, `image_filename`, `mask_b64` y `context`. Esto permite montar un wrapper propio con InstructPix2Pix, FLUX Kontext, ComfyUI u otro backend sin tocar el core.
*   **Generación gratuita/local**: `!marketer --free-model ...` envía generación a Ollama con `OLLAMA_IMAGE_MODEL` y `OLLAMA_IMAGE_SIZE`.
*   **Validación**: máximo 4 imágenes por solicitud y 5MB por imagen. El runtime rechaza base64 inválido antes de llamar al modelo.
*   **Verificación**: si el proveedor devuelve base64, el grafo hace una revisión visual del resultado y puede marcar `needs_review`.
*   **Storage**: Las referencias de estilo se guardan en la tabla `mentis_memory` de Supabase bajo la categoría `picture_style`.
*   **Output**: URL de imagen o archivo PNG en Discord cuando el proveedor devuelve base64.

### Proveedor local esperado

Cuando uses `PICTURE_IMAGE_EDIT_PROVIDER=local`, el endpoint configurado debe aceptar:

```json
{
  "prompt": "Replace only the requested text...",
  "image_b64": "...",
  "image_mime": "image/png",
  "image_filename": "design.png",
  "mask_b64": null,
  "context": {
    "operation": "replace_text",
    "preserve": ["composition", "logos"]
  }
}
```

Y debe responder con uno de estos formatos:

```json
{ "image_url": "https://..." }
```

```json
{ "image_b64": "...", "image_mime": "image/png" }
```

## Integración con otros Agentes
El Picture Agent puede ser invocado internamente por el `!marketer` en futuras versiones para ilustrar planes de campaña o por el `!writer` para generar portadas de blog.
