# Marketer WhatsApp Outreach (OpenWA)

Este modulo agrega una base segura para que `!marketer` pueda trabajar con contactos WhatsApp y campanas creadas desde la UI.

## Viabilidad

OpenWA es viable como adapter externo porque ofrece REST API, multi-session, webhooks, API key auth, bulk messaging, rate limiting y audit logging. En PC Agent no debe conectarse directo desde el dominio: se integra como adapter reemplazable detras de casos de uso.

## Estado Actual

- UI: pestaña WhatsApp para crear contactos opt-in y campanas draft.
- Supabase: tablas `whatsapp_contacts` y `whatsapp_campaigns` con RLS de service role.
- Control API: endpoints `/marketing/whatsapp`, `/marketing/whatsapp/contacts` y `/marketing/whatsapp/campaigns`.
- Marketer: `!marketer whatsapp` consulta contactos/campanas y resume el estado.
- Discord: `!marketer whatsapp send <campaign_id>` muestra botones de aprobar/denegar en el hilo del Marketer y solo marca la campana como `queued` si un aprobador confirma.
- Fallback Discord: `!marketer whatsapp approve <campaign_id>` o `!marketer whatsapp deny <campaign_id>`.
- OpenWA gateway: adapter HTTP preparado para `send-text`, sin envio masivo automatico.

## Guardrails

- Solo contactos con `consent_status=opted_in`.
- Las campanas se crean como `draft` y requieren aprobacion antes de cualquier envio.
- No se hace bulk send automaticamente.
- El siguiente paso debe incluir rate limits, opt-out, webhooks de delivery/read y auditoria por mensaje.
