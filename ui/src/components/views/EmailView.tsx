import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { AlertTriangle, CheckCircle2, Database, KeyRound, Mail, Save, Send, ShieldCheck, Tags } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const defaultCategories = [
  {
    name: "lead",
    description: "Prospectos o solicitudes comerciales entrantes.",
    filters: { labels: ["lead"], query: "newer_than:30d" },
    confidence_threshold: 0.7,
  },
  {
    name: "soporte",
    description: "Solicitudes de ayuda, errores o seguimiento operativo.",
    filters: { labels: ["support"], query: "newer_than:14d" },
    confidence_threshold: 0.75,
  },
];

export function EmailView({
  data,
  onSave,
}: {
  data: any;
  adminToken: string;
  onSave: (payload: any) => Promise<void>;
}) {
  const email = data.config?.integrations?.email || {};
  const runtime = data.runtime?.runtime || {};
  const templates = readJsonList(runtime.email_templates);
  const categories = readJsonList(runtime.email_categories);
  const jobs = data.emailJobs?.jobs || [];
  const ready = providerReady(email);
  const supabaseReady = Boolean(data.config?.integrations?.supabase?.has_service_role_key);

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload: any = Object.fromEntries(formData);

    if (payload.email_send_enabled === "true") payload.email_send_enabled = true;
    if (payload.email_send_enabled === "false") payload.email_send_enabled = false;
    if (payload.email_bulk_rate_limit) payload.email_bulk_rate_limit = Number(payload.email_bulk_rate_limit);

    Object.keys(payload).forEach((key) => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Mail className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Email Sub-Agent</h2>
                <Badge variant={ready ? "default" : "outline"}>{email.provider || "not_configured"}</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">
                Proveedores, categorías, templates y respuestas bulk con aprobación humana.
              </p>
            </div>
          </div>
          <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
            <Save className="size-4" />
            Guardar Email Agent
          </Button>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-4">
        <StatusTile icon={ShieldCheck} label="Proveedor" value={ready ? "Conectable" : "Pendiente"} tone={ready ? "emerald" : "amber"} />
        <StatusTile icon={Send} label="Envío" value={email.send_enabled ? "Con aprobación" : "Bloqueado"} tone={email.send_enabled ? "emerald" : "neutral"} />
        <StatusTile icon={Tags} label="Categorías" value={`${categories.length} configuradas`} tone={categories.length ? "sky" : "neutral"} />
        <StatusTile icon={Database} label="Persistencia" value={supabaseReady ? "Supabase" : "Archivo local"} tone={supabaseReady ? "emerald" : "amber"} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <SettingsSection
            icon={ShieldCheck}
            title="Proveedor y Permisos"
            description="Define la cuenta, el proveedor activo y el nivel permitido para respuestas masivas."
            action={<StateBadge ready={ready} />}
          >
            <Field label="Proveedor">
              <Select name="email_provider" defaultValue={email.provider || "not_configured"}>
                <SelectTrigger className="config-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="not_configured">Sin configurar</SelectItem>
                  <SelectItem value="google">Google Gmail</SelectItem>
                  <SelectItem value="outlook">Microsoft Outlook</SelectItem>
                  <SelectItem value="imap_smtp">IMAP / SMTP</SelectItem>
                  <SelectItem value="pc_client">Cliente local del PC</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Cuenta principal">
              <Input name="email_account_id" defaultValue={email.account_id || ""} placeholder="equipo@empresa.com" className="config-input" />
            </Field>
            <Field label="Permitir envío">
              <Select name="email_send_enabled" defaultValue={String(email.send_enabled || false)}>
                <SelectTrigger className="config-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Solo lectura y drafts</SelectItem>
                  <SelectItem value="true">Envío con aprobación</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Límite bulk por minuto">
              <Input name="email_bulk_rate_limit" type="number" defaultValue={email.bulk_rate_limit || 30} min={1} max={500} className="config-input" />
            </Field>
          </SettingsSection>

          <SettingsSection icon={KeyRound} title="Credenciales" description="Los campos vacíos conservan los secretos existentes.">
            <SecretField label="Google Client ID" active={email.has_google_oauth}>
              <Input name="email_google_client_id" type="password" placeholder="client-id.apps.googleusercontent.com" className="config-input" />
            </SecretField>
            <SecretField label="Google Client Secret" active={email.has_google_oauth}>
              <Input name="email_google_client_secret" type="password" placeholder="GOCSPX-..." className="config-input" />
            </SecretField>
            <SecretField label="Outlook Client ID" active={email.has_outlook_oauth}>
              <Input name="email_outlook_client_id" type="password" placeholder="Azure application client id" className="config-input" />
            </SecretField>
            <SecretField label="Outlook Client Secret" active={email.has_outlook_oauth}>
              <Input name="email_outlook_client_secret" type="password" placeholder="Azure client secret" className="config-input" />
            </SecretField>
            <Field label="Outlook Tenant ID">
              <Input name="email_outlook_tenant_id" defaultValue={email.outlook_tenant_id || ""} placeholder="common / organizations / tenant id" className="config-input" />
            </Field>
            <Field label="Cliente local bridge URL">
              <Input name="email_pc_client_bridge_url" defaultValue={email.pc_client_bridge_url || ""} placeholder="http://host.docker.internal:8765" className="config-input" />
            </Field>
            <SecretField label="Cliente local bridge token" active={email.has_pc_client_bridge}>
              <Input name="email_pc_client_bridge_token" type="password" placeholder="Token opcional del bridge local" className="config-input" />
            </SecretField>
          </SettingsSection>

          <SettingsSection icon={Mail} title="IMAP / SMTP" description="Configuración para cuentas corporativas o proveedores genéricos.">
            <Field label="IMAP Host">
              <Input name="email_imap_host" defaultValue={email.imap_host || ""} placeholder="imap.empresa.com:993" className="config-input" />
            </Field>
            <Field label="SMTP Host">
              <Input name="email_smtp_host" defaultValue={email.smtp_host || ""} placeholder="smtp.empresa.com:587" className="config-input" />
            </Field>
            <Field label="Usuario">
              <Input name="email_username" defaultValue={email.username || ""} placeholder="equipo@empresa.com" className="config-input" />
            </Field>
            <SecretField label="Password / App Password" active={email.has_imap_smtp}>
              <Input name="email_password" type="password" placeholder="••••••••" className="config-input" />
            </SecretField>
          </SettingsSection>

          <SettingsSection icon={Tags} title="Categorías" description="Reglas que el Email Agent usa para buscar candidatos y clasificar conversaciones." columns={1}>
            <textarea
              name="email_categories"
              defaultValue={formatJson(runtime.email_categories, defaultCategories)}
              className="min-h-[190px] w-full rounded-[8px] border border-neutral-200 bg-white px-3 py-2 font-mono text-xs shadow-sm outline-none focus:border-neutral-400"
              spellCheck={false}
            />
          </SettingsSection>

          <SettingsSection icon={Send} title="Templates de Respuesta" description="Plantillas disponibles para comandos como !email --template-seguimiento lead." columns={1}>
            <textarea
              name="email_templates"
              defaultValue={formatJson(runtime.email_templates, [])}
              className="min-h-[220px] w-full rounded-[8px] border border-neutral-200 bg-white px-3 py-2 font-mono text-xs shadow-sm outline-none focus:border-neutral-400"
              spellCheck={false}
            />
          </SettingsSection>
        </div>

        <aside className="space-y-5">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="text-base font-semibold text-neutral-950">Estado Operativo</CardTitle>
              <CardDescription className="text-sm text-neutral-500">Lectura rápida antes de activar envíos.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1 px-5 py-4 text-sm">
              <StatusRow label="Cuenta" value={email.account_id || "Sin cuenta"} />
              <StatusRow label="Lectura" value={ready ? "Lista" : "Pendiente"} />
              <StatusRow label="Envío" value={email.send_enabled ? "Con aprobación" : "Bloqueado"} />
              <StatusRow label="Bulk" value={`${email.bulk_rate_limit || 30}/min`} />
              <StatusRow label="Templates" value={`${templates.length}`} />
              <StatusRow label="Categorías" value={`${categories.length}`} />
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="text-base font-semibold text-neutral-950">Comandos</CardTitle>
              <CardDescription className="text-sm text-neutral-500">Vista previa del uso desde Discord.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 px-5 py-4 text-sm">
              <Command text="!email status" />
              <Command text="!email sent-today" />
              <Command text={`!email categorize ${categories[0]?.name || "lead"}`} />
              <Command text={`!email --template-${templates[0]?.name || "seguimiento"} ${templates[0]?.category || categories[0]?.name || "lead"}`} />
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                {supabaseReady ? <CheckCircle2 className="size-4 text-emerald-600" /> : <AlertTriangle className="size-4 text-amber-600" />}
                Jobs y Auditoría
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">
                {supabaseReady ? "Los jobs bulk se persistirán en Supabase." : "Sin service role, el runtime usará fallback local."}
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="text-base font-semibold text-neutral-950">Jobs Recientes</CardTitle>
              <CardDescription className="text-sm text-neutral-500">
                Aprobaciones, cola y resultados de bulk replies.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 px-5 py-4 text-sm">
              {jobs.length === 0 ? (
                <p className="text-neutral-500">{data.emailJobs?.detail || "Sin jobs registrados."}</p>
              ) : (
                jobs.slice(0, 8).map((job: any) => (
                  <div key={job.id} className="rounded-[8px] border border-neutral-200 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="truncate font-medium text-neutral-950">{job.template_name || job.id}</p>
                      <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] font-semibold text-neutral-700">
                        {job.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-neutral-500">
                      {job.category || "sin categoria"} · {job.recipient_count || 0} destinatarios
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </form>
  );
}

function SettingsSection({
  icon: Icon,
  title,
  description,
  children,
  action,
  columns = 2,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
  columns?: 1 | 2;
}) {
  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 gap-3">
            <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
              <Icon className="size-4" />
            </span>
            <div className="min-w-0">
              <CardTitle className="text-base font-semibold text-neutral-950">{title}</CardTitle>
              <CardDescription className="mt-1 text-sm text-neutral-500">{description}</CardDescription>
            </div>
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent className={columns === 1 ? "space-y-4 px-5 py-5" : "grid gap-4 px-5 py-5 md:grid-cols-2"}>
        {children}
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium text-neutral-700">{label}</Label>
      {children}
    </div>
  );
}

function SecretField({ label, active, children }: { label: string; active?: boolean; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <Label className="text-sm font-medium text-neutral-700">{label}</Label>
        <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${active ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-neutral-200 bg-neutral-50 text-neutral-500"}`}>
          {active ? "Guardado" : "Pendiente"}
        </span>
      </div>
      {children}
    </div>
  );
}

function StateBadge({ ready }: { ready: boolean }) {
  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${ready ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
      {ready ? "Proveedor listo" : "Pendiente"}
    </span>
  );
}

function StatusTile({ icon: Icon, label, value, tone }: { icon: LucideIcon; label: string; value: string; tone: "emerald" | "amber" | "sky" | "neutral" }) {
  const tones = {
    emerald: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    sky: "bg-sky-50 text-sky-700",
    neutral: "bg-neutral-100 text-neutral-700",
  };
  return (
    <div className="rounded-[10px] border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <span className={`flex size-9 items-center justify-center rounded-[8px] ${tones[tone]}`}>
          <Icon className="size-4" />
        </span>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.05em] text-neutral-500">{label}</p>
          <p className="truncate text-sm font-semibold text-neutral-950">{value}</p>
        </div>
      </div>
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-neutral-100 py-2 last:border-b-0">
      <span className="text-neutral-500">{label}</span>
      <span className="text-right font-medium text-neutral-950">{value}</span>
    </div>
  );
}

function Command({ text }: { text: string }) {
  return <code className="block rounded-[8px] bg-neutral-100 px-3 py-2 text-xs text-neutral-900">{text}</code>;
}

function providerReady(email: any) {
  if (!email.provider || email.provider === "not_configured") return false;
  if (email.provider === "google") return Boolean(email.has_google_oauth);
  if (email.provider === "outlook") return Boolean(email.has_outlook_oauth);
  if (email.provider === "imap_smtp") return Boolean(email.has_imap_smtp);
  if (email.provider === "pc_client") return Boolean(email.has_pc_client_bridge);
  return false;
}

function readJsonList(value: any) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

function formatJson(value: any, fallback: any[]) {
  const parsed = readJsonList(value);
  return JSON.stringify(parsed.length ? parsed : fallback, null, 2);
}
