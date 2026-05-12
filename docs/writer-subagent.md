# Sub-Agente !writer (Storytelling & Blogs)

El sub-agente `!writer` es el responsable de la creación de contenido narrativo y estructurado para la marca. Trabaja en estrecha colaboración con el `!marketer` para utilizar tendencias e insights actuales.

## Funciones Principales

- **Generación de Blogs**: Crea artículos de formato largo optimizados para SEO basándose en un tema o idea.
- **Storytelling de Marca**: Desarrolla narrativas emocionales siguiendo estructuras como el "Viaje del Héroe".
- **Integración con Obsidian**: Guarda automáticamente cada pieza de contenido en una bóveda compartida.
- **Enriquecimiento Visual**: Busca automáticamente imágenes representativas en Unsplash basándose en el análisis del texto.

## Comandos de Discord

- `!writer blog <idioma> <tema>`: Genera un blog post. Ejemplo: `!writer blog es El futuro del minimalismo`.
- `!writer story <idioma> <tema>`: Genera una historia. Ejemplo: `!writer story en Brand origin story`.
- `!writer <mensaje>`: Conversación libre con el redactor para lluvia de ideas.

## Integración con Obsidian (Docker)

El contenido se almacena en el volumen compartido `obsidian-vault`, montado en `/vault` dentro de los contenedores.

### Estructura de Archivos
- `/vault/Blog/Titulo-Fecha.md`
- `/vault/Story-telling/Titulo-Fecha.md`

## Capas Tecnológicas

1.  **Core**: `WriterWorkflow` (Python/FastAPI).
2.  **LLM**: Gemini-Flash para generación rápida y creativa.
3.  **Storage**: Sistema de archivos local (Shared Docker Volume).
4.  **UI**: Obsidian (acceso vía KasmVNC en puerto 3010).
5.  **Visuals**: Unsplash API (Dynamic Image Source).
