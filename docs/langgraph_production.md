# MarketingGraph En Produccion

`MarketingGraph` es la ruta productiva del sub-agente `!marketer`. Reemplaza el despachador legacy basado en `MarketingWorkflow` para que el flujo tenga estado, pasos observables y compuertas de aprobacion humana.

## Estado Del Grafo

El estado principal vive en `MarketingState` e incluye:

- `prompt`: instruccion original.
- `images`: imagenes adjuntas para analisis visual.
- `sub_command`: accion solicitada o detectada.
- `payload`: opciones operativas como `data_source`, `account_id`, `platform`, `is_approved` o `scheduled_for`.
- `context`: memoria recuperada para la marca.
- `suggested_action`: herramienta detectada por comando directo o tool calling.
- `tool_results`: resultado de la accion ejecutada.
- `requires_approval`: indica si debe pasar por humano.
- `final_message`: mensaje listo para Discord/UI.
- `errors`: errores capturados durante el flujo.

## Nodos Actuales

1. `initialize`: normaliza payload, subcomando y aprobacion.
2. `analyze_image`: analiza imagenes adjuntas cuando existen.
3. `retrieve_context`: recupera memoria del Marketer.
4. `analyze_intent`: detecta accion por comando directo o tool calling.
5. `critic_node`: revisa planes complejos.
6. `brand_voice_refiner`: ajusta tono de marca.
7. `human_approval`: devuelve `requires_approval` cuando una accion sensible no esta aprobada.
8. `execute_tool`: ejecuta la accion sobre `MarketingAutomationService` o `MarketingPort`.
9. `finalize`: normaliza la respuesta final.

## Adapter Productivo

En runtime, `MarketingGraph` se instancia con `ZernioAdapter`. El contrato `MarketingPort` declara las capacidades usadas en produccion:

- cuentas conectadas
- comentarios
- respuestas y DMs
- dashboard y reportes
- top content, audiencia, alertas y mejores horarios
- leads
- drafts de campana y posts
- runs de automatizacion
- idempotencia
- publicacion y programacion de posts

## Aprobaciones

Las acciones con escritura externa usan `AutonomyPolicy`:

- modo asistido por defecto
- `MARKETER_AUTOMATION_ENABLED` controla si la automatizacion esta activa
- `MARKETER_ALLOW_WRITES=false` bloquea escrituras reales aunque exista aprobacion
- `is_approved=true` es requerido para publicar, programar, responder o enviar DMs

## Validacion

```bash
services/assistant-runtime/venv/bin/python -m unittest services/assistant-runtime/test_marketing_graph_regression.py
services/assistant-runtime/venv/bin/python -m unittest services/assistant-runtime/test_marketing_automation.py
```

Estas pruebas cubren comandos explicitos, dashboard, comentarios Zernio, publicaciones con media/account, aprobaciones, drafts, idempotencia y compatibilidad con errores del runtime.
