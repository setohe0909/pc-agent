# Email Sub-Agent

El sub-agente `!email` administra flujos de correo para lectura, categorizacion y respuestas masivas controladas. Esta disenado con arquitectura hexagonal: el nucleo conoce casos de uso y reglas de seguridad, mientras Google, Outlook, IMAP/SMTP, clientes locales de PC u otros proveedores viven como adaptadores intercambiables.

## Capacidades

- Conectar proveedores desde el administrador: Google Gmail, Microsoft Outlook, IMAP/SMTP, cliente local de PC o adaptadores futuros.
- Categorizar emails por filtros, categorias y clasificacion asistida.
- Listar emails enviados el mismo dia con trazabilidad de cuenta/proveedor.
- Preparar respuestas bulk usando templates administrados.
- Consultar `status` y `--model-status` sin consumir acciones de envio.

## Comandos

| Comando | Uso |
| --- | --- |
| `!email` / `!email status` | Estado del proveedor, lectura, envio y templates. |
| `!email sent-today` | Lista emails enviados hoy. |
| `!email categorize <categoria>` | Prepara categorizacion por filtros/categoria. |
| `!email --template-<nombre> <categoria>` | Prepara respuesta bulk para emails de esa categoria. |
| `!email --model-status` | Muestra modelos usados para clasificacion, resumen y templates. |

## Diseno de Produccion

El flujo separa responsabilidades:

- `EmailWorkflow`: orquesta casos de uso del sub-agente.
- `EmailProviderPort`: define lectura de enviados, busqueda por categoria y envio bulk.
- `EmailConfigPort`: lee proveedor default y templates.
- `ConfiguredEmailProvider`: adapter de runtime que valida configuracion y delega a adaptadores reales.
- Admin UI: guarda proveedor, credenciales, permiso de envio, limites y templates.

Los envios bulk deben ejecutarse como cola aprobada, con idempotencia por email, rate limits por proveedor, auditoria, manejo de rebotes y opt-out cuando aplique. Por defecto el comando prepara un plan y solicita aprobacion antes de enviar.

## Configuracion

En `Configuracion > Email` se administra:

- Proveedor y cuenta principal.
- Credenciales OAuth para Google u Outlook.
- IMAP/SMTP para proveedores genericos.
- Bridge de cliente local para integraciones de PC.
- Permiso explicito de envio.
- Limite bulk por minuto.
- Templates JSON para `!email --template-<nombre>`.

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
