# Sub-Agente !writer (Storytelling & Blogs)

El sub-agente `!writer` es el responsable de la creación de contenido narrativo y estructurado para la marca. Trabaja en estrecha colaboración con el `!marketer` para utilizar tendencias e insights actuales.

## Funciones Principales

- **Generación de Blogs**: Crea artículos de formato largo optimizados para SEO basándose en un tema o idea.
- **Storytelling de Marca**: Desarrolla narrativas emocionales siguiendo estructuras como el "Viaje del Héroe".
- **Integración con Obsidian**: Guarda automáticamente cada pieza de contenido en una bóveda compartida.
- **Contrato de producción**: Valida acciones soportadas, rechaza prompts vacíos y devuelve errores estructurados cuando falla la persistencia.
- **Registro operativo**: Guarda un resumen de cada ejecución en memoria para auditoría y continuidad editorial.
- **Assets seguros**: Sugiere keywords visuales, pero no inserta imágenes externas no licenciadas como si fueran assets listos para publicar.

## Comandos de Discord

- `!writer blog <idioma> <tema>`: Genera un blog post. Ejemplo: `!writer blog es El futuro del minimalismo`.
- `!writer story <idioma> <tema>`: Genera una historia. Ejemplo: `!writer story en Brand origin story`.
- `!writer storytelling <idioma> <tema>`: Alias explícito para storytelling.
- `!writer <mensaje>`: Conversación libre con el redactor para lluvia de ideas.

## Contrato de Respuesta

Todas las acciones devuelven un resultado con:

- `status`: `success` o `error`.
- `message`: respuesta legible para Discord/UI.
- `command`: acción ejecutada cuando aplica.
- `content`: contenido generado.
- `artifact`: ruta relativa del Markdown guardado en Obsidian cuando aplica.
- `metadata`: idioma y keywords visuales sugeridas.

Errores esperados:

- `writer.empty_prompt`: no se recibió tema o instrucción editorial.
- `writer.unsupported_action`: el subcomando no está soportado.
- `writer.persistence_failed`: el contenido se generó, pero no pudo guardarse en Obsidian. En producción no se reporta como éxito.

## Integración con Obsidian (Docker)

El contenido se almacena en el volumen compartido `obsidian-vault`, montado en `/vault` dentro de los contenedores.

### Estructura de Archivos
- `/vault/Blog/titulo-fecha-hora.md`
- `/vault/Story-telling/titulo-fecha-hora.md`

## Capas Tecnológicas

1.  **Core**: `WriterWorkflow` (Python/FastAPI).
2.  **LLM**: Gemini-Flash para generación rápida y creativa.
3.  **Storage**: Sistema de archivos local (Shared Docker Volume).
4.  **UI**: Obsidian (acceso vía KasmVNC en puerto 3010).
5.  **Memoria**: `MemoryPort.save_interaction()` registra preview, comando y artefacto.
6.  **Visuals**: Keywords sugeridas para buscar o generar assets con licencia antes de publicar.

## Validación

Pruebas principales:

```bash
services/assistant-runtime/venv/bin/python -m unittest services/assistant-runtime/test_writer_workflow.py
```

Estas pruebas cubren chat, blog, error de persistencia y comandos inválidos.
