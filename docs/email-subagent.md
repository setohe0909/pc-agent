# Email Sub-Agent

El sub-agente `!email` administra flujos de correo para lectura, categorizacion y respuestas masivas controladas. Esta disenado con arquitectura hexagonal: el nucleo conoce casos de uso y reglas de seguridad, mientras Google, Outlook, IMAP/SMTP, clientes locales de PC u otros proveedores viven como adaptadores intercambiables.

## Capacidades

- Conectar proveedores desde el administrador: Google Gmail, Microsoft Outlook, IMAP/SMTP, cliente local de PC o adaptadores futuros.
- Categorizar emails por filtros, categorias y clasificacion asistida.
- Listar emails enviados el mismo dia con trazabilidad de cuenta/proveedor.
- Preparar respuestas bulk usando templates administrados.
- Generar jobs aprobables para respuestas bulk con auditoria y estado de cola.
- Consultar `status` y `--model-status` sin consumir acciones de envio.

## Comandos

| Comando | Uso |
| --- | --- |
| `!email` / `!email status` | Estado del proveedor, lectura, envio y templates. |
| `!email sent-today` | Lista emails enviados hoy. |
| `!email categorize <categoria>` | Prepara categorizacion por filtros/categoria. |
| `!email --template-<nombre> <categoria>` | Prepara respuesta bulk para emails de esa categoria y solicita aprobacion. |
| `!email process-queued` | Procesa jobs bulk aprobados en cola. |
| `!email --model-status` | Muestra modelos usados para clasificacion, resumen y templates. |

## Diseno de Produccion

El flujo separa responsabilidades:

- `EmailWorkflow`: orquesta casos de uso del sub-agente.
- `EmailProviderPort`: define lectura de enviados, busqueda por categoria y envio bulk.
- `EmailConfigPort`: lee proveedor default y templates.
- `EmailJobRepositoryPort`: persiste jobs bulk, aprobaciones, denegaciones y auditoria.
- `ConfiguredEmailProvider`: adapter de runtime que valida configuracion y delega a adaptadores reales.
- `SupabaseEmailJobRepository`: adapter de produccion cuando existen `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`.
- `FileEmailJobRepository`: fallback local para persistir jobs en `EMAIL_JOBS_PATH` durante desarrollo.
- Admin UI: guarda proveedor, credenciales, permiso de envio, limites y templates.

Los envios bulk se ejecutan en tres pasos: primero se crea un `job_id` con preview y auditoria; luego un aprobador confirma o deniega desde Discord; finalmente un worker procesa jobs `queued` con `!email process-queued`. Solo el worker llama al proveedor con `dry_run=false`, actualiza destinatarios y marca el job como `sent`, `queued` o `failed`. El proveedor debe aplicar idempotencia por email, rate limits, opt-out, manejo de rebotes y trazabilidad por mensaje.

Los proveedores Google, Outlook e IMAP/SMTP ya no simulan envios: si no existe adapter real, el runtime responde `adapter_required`. Hoy el provider operativo end-to-end es `pc_client` mediante bridge HTTP.

## Configuracion

En `Configuracion > Email` se administra:

- Proveedor y cuenta principal.
- Credenciales OAuth para Google u Outlook.
- IMAP/SMTP para proveedores genericos.
- Bridge de cliente local para integraciones de PC.
- Permiso explicito de envio.
- Limite bulk por minuto.
- Templates JSON para `!email --template-<nombre>`.

La vista `Email Agent` del administrador tambien permite editar estos valores sin salir del sub-agente: proveedor activo, permisos de envio, credenciales, categorias, templates y estado de persistencia de jobs.

Ejemplo de template:

```json
[
  {
    "name": "seguimiento",
    "subject": "Re: {{subject}}",
    "body": "Hola {{name}}, gracias por escribirnos. Te comparto el siguiente paso...",
    "category": "lead",
    "requires_approval": true,
    "rate_limit_per_minute": 30
  }
]
```

## Contrato del Bridge Local

Cuando el proveedor es `pc_client`, el adapter llama al bridge HTTP configurado:

| Endpoint | Metodo | Uso |
| --- | --- | --- |
| `/sent?date=YYYY-MM-DD` | `GET` | Devuelve `{ "emails": [...] }` o una lista de emails enviados. |
| `/search?category=<categoria>&limit=100` | `GET` | Devuelve emails candidatos para una categoria. |
| `/bulk-replies` | `POST` | Recibe `email_ids`, `template` y `dry_run`; devuelve estado `planned` o `queued`. |

Si se configura `email_pc_client_bridge_token`, el runtime lo envia como `Authorization: Bearer <token>`.

## Persistencia y Auditoria

La migracion `20260521000100_email_agent.sql` crea:

- `email_bulk_jobs`: job aprobable con proveedor, template, categoria, estado y resultado del proveedor.
- `email_bulk_job_recipients`: destinatarios por job para idempotencia y seguimiento por mensaje.
- `email_audit_events`: eventos de preparacion, aprobacion, denegacion y errores operativos.

El runtime usa `EMAIL_JOB_REPOSITORY=auto` por defecto: selecciona Supabase si esta configurado y usa archivo local como fallback. Para forzar un modo se puede usar `EMAIL_JOB_REPOSITORY=supabase` o `EMAIL_JOB_REPOSITORY=file`.
