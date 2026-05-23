# Coder Web Sub-Agent

Coder Web ejecuta tareas web en modo produccion: genera un paquete de archivos,
crea branch, hace commit atomico, abre Pull Request, adjunta workflow de
validacion y deja una ruta de rollback. No devuelve repositorios ni cambios
ficticios.

## Capacidades

- Generacion de archivos reales para React/TypeScript, Tailwind y stacks web configurados.
- GitHub: repositorio destino o repositorio nuevo, branch aislado, commit via Git Data API y Pull Request.
- Validacion: workflow `.github/workflows/coder-web-validate.yml` con install, lint, test y build cuando hay `package.json`.
- Preview deploy: webhook configurable con `CODER_WEB_PREVIEW_DEPLOY_HOOK_URL` o `coder_web_preview_deploy_hook_url`.
- Linear: acepta `linear_issue_id`, lee el brief con `LINEAR_API_KEY` y comenta el PR/preview en el issue.
- Assets: adjuntos de Discord se versionan en `public/coder-web-assets/`.
- Rollback: cerrar PR y borrar branch; el plan queda registrado en el resultado y en el run log.
- Auditoria local: logs JSON en `CODER_WEB_RUN_LOG_DIR` o `/tmp/pc-agent-coder-web-runs`.

## Comandos

| Comando | Uso |
| --- | --- |
| `!coder-web <descripcion>` | Genera branch, commit y PR real. |
| `!coder-web --repo owner/repo <descripcion>` | Aplica el cambio sobre un repo existente. |
| `!coder-web --linear <issue_id> --repo owner/repo` | Ejecuta una tarea asignada desde Linear. |
| `!coder-web --branch feature/nombre <descripcion>` | Usa una rama base sugerida. |
| `!coder-web --preview-required <descripcion>` | Falla si no hay webhook de preview configurado. |
| `!coder-web memory` | Muestra memoria del agente. |
| `!coder-web memory --clean` | Solicita borrar memoria del dia. |

## Configuracion Requerida

```text
GITHUB_TOKEN=
GITHUB_OWNER=
CODER_WEB_PRIVATE_REPO=true
CODER_WEB_PREVIEW_DEPLOY_HOOK_URL=
LINEAR_API_KEY=
```

Tambien puede configurarse desde el Admin UI:

- `github_token`
- `github_org`
- `coder_web_repository`
- `coder_web_private_repo`
- `coder_web_preview_deploy_hook_url`
- `linear_api_key`

## Flujo Productivo

1. Coder Web recibe prompt, adjuntos y opcionalmente `linear_issue_id`.
2. Si hay Linear configurado, carga titulo, descripcion, assignee, team y URL.
3. El LLM genera plan y archivos obligatoriamente; si no hay `package.json`, la tarea falla.
4. GitHub verifica permisos de escritura sobre el repo destino.
5. Se crea branch aislado y commit atomico con archivos, assets, runbook y workflow CI.
6. Se abre PR para revision humana.
7. Se dispara preview hook si esta configurado o si la tarea lo exige.
8. Se comenta el resultado en Linear cuando hay issue y API key.
9. Se registra run log y se devuelve rollback.
