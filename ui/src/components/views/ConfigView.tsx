import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Brain,
  CheckCircle2,
  Database,
  DollarSign,
  Globe,
  LayoutGrid,
  Save,
  Server,
  SlidersHorizontal,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function ConfigView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { config } = data;
  const integrations = config?.integrations || {};
  const modelUsage = data.modelUsage;

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);

    if (payload.embedding_dimensions) payload.embedding_dimensions = Number(payload.embedding_dimensions);
    if (payload.mentis_enabled === "true") payload.mentis_enabled = true;
    if (payload.mentis_enabled === "false") payload.mentis_enabled = false;
    if (payload.langfuse_enabled === "true") payload.langfuse_enabled = true;
    if (payload.langfuse_enabled === "false") payload.langfuse_enabled = false;

    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-5">
      <div className="sticky top-0 z-20 rounded-[10px] border border-neutral-200 bg-white/95 px-5 py-4 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <LayoutGrid className="size-4" />
            </span>
            <div className="min-w-0">
              <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Centro de Configuración</h2>
              <p className="text-sm text-neutral-500">Infraestructura, modelos, datos y credenciales sensibles.</p>
            </div>
          </div>
          <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
            <Save className="size-4" />
            Guardar cambios
          </Button>
        </div>
      </div>

      <Tabs defaultValue="core" className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <TabsList className="h-auto flex-col items-stretch justify-start gap-1 rounded-[10px] border border-neutral-200 bg-white p-2 shadow-sm">
          <ConfigTab value="core" icon={Server} title="Infraestructura" description="Servicios, trazas y endpoints" />
          <ConfigTab value="ai" icon={Brain} title="Modelos e IA" description="Keys, proveedores y costos" />
          <ConfigTab value="data" icon={Database} title="Datos y RAG" description="Supabase, memoria y embeddings" />
          <ConfigTab value="trading" icon={Activity} title="Trading" description="Credenciales de ejecución" />
        </TabsList>

        <div className="min-w-0">
          <TabsContent value="core" className="mt-0 space-y-4 outline-none">
            <SettingsSection icon={Server} title="Servicios Core" description="URLs de conexión para los microservicios de Docker.">
              <Field label="Assistant Runtime URL" hint="Por defecto: http://assistant-runtime:8100">
                <Input name="open_claw_base_url" defaultValue={integrations.open_claw} placeholder="http://assistant-runtime:8100" className="config-input" />
              </Field>
              <Field label="Ollama URL" hint="Usa host.docker.internal:11434 para usar Ollama Desktop.">
                <Input name="ollama_base_url" defaultValue={integrations.ollama} placeholder="http://ollama:11434" className="config-input" />
              </Field>
            </SettingsSection>

            <SettingsSection icon={SlidersHorizontal} title="Observabilidad" description="Controla trazas y conexión con Langfuse.">
              <Field label="Estado del Servicio">
                <Select name="langfuse_enabled" defaultValue={String(integrations.langfuse_enabled)}>
                  <SelectTrigger className="config-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">Desactivado</SelectItem>
                    <SelectItem value="true">Activo (trazas habilitadas)</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Langfuse Host">
                <Input name="langfuse_host" defaultValue={integrations.langfuse} placeholder="http://langfuse-web:3000" className="config-input" />
              </Field>
            </SettingsSection>
          </TabsContent>

          <TabsContent value="ai" className="mt-0 space-y-4 outline-none">
            <SettingsSection icon={Brain} title="Proveedores de LLM" description="Configura llaves de API. Los campos vacíos no reemplazan valores guardados.">
              <SecretField label="Gemini API Key" active={integrations.gemini_api_key_configured}>
                <Input name="gemini_api_key" type="password" placeholder="AIza..." className="config-input" />
              </SecretField>
              <SecretField label="OpenAI API Key" active={integrations.openai_api_key_configured}>
                <Input name="openai_api_key" type="password" placeholder="sk-..." className="config-input" />
              </SecretField>
              <SecretField label="OpenAI Admin API Key" active={integrations.openai_admin_api_key_configured} hint="Necesaria para consultar consumo real en OpenAI Costs API.">
                <Input name="openai_admin_api_key" type="password" placeholder="sk-admin-..." className="config-input" />
              </SecretField>
              <SecretField label="Together API Key" active={integrations.together_api_key_configured}>
                <Input name="together_api_key" type="password" placeholder="tgp_..." className="config-input" />
              </SecretField>
            </SettingsSection>

            <ModelUsagePanel usage={modelUsage} />

            <SettingsSection icon={CheckCircle2} title="Langfuse Keys" description="Credenciales usadas para correlacionar ejecuciones y trazas.">
              <SecretField label="Langfuse Public Key" active={integrations.langfuse_public_key_configured}>
                <Input name="langfuse_public_key" type="password" placeholder="pk-lf-..." className="config-input" />
              </SecretField>
              <SecretField label="Langfuse Secret Key" active={integrations.langfuse_secret_key_configured}>
                <Input name="langfuse_secret_key" type="password" placeholder="sk-lf-..." className="config-input" />
              </SecretField>
            </SettingsSection>
          </TabsContent>

          <TabsContent value="data" className="mt-0 space-y-4 outline-none">
            <SettingsSection icon={Database} title="Supabase & Vector Store" description="Almacenamiento de largo plazo para conocimiento, memoria y RAG." columns={1}>
              <Field label="Supabase Project URL">
                <Input name="supabase_url" defaultValue={integrations.supabase?.url} placeholder="https://xyz.supabase.co" className="config-input" />
              </Field>
              <div className="grid gap-4 md:grid-cols-2">
                <SecretField label="Publishable Key" active={integrations.supabase?.has_publishable_key}>
                  <Input name="supabase_publishable_key" type="password" placeholder="Anon Key" className="config-input" />
                </SecretField>
                <SecretField label="Service Role Key" active={integrations.supabase?.has_service_role_key}>
                  <Input name="supabase_service_role_key" type="password" placeholder="Service Key" className="config-input" />
                </SecretField>
              </div>
              <div className="grid gap-4 border-t border-neutral-200 pt-4 md:grid-cols-2">
                <Field label="Embedding Model">
                  <Input name="embedding_model" defaultValue={integrations.supabase?.embedding_model} placeholder="mxbai-embed-large" className="config-input" />
                </Field>
                <Field label="Dimensions">
                  <Input name="embedding_dimensions" type="number" defaultValue={integrations.supabase?.embedding_dimensions} className="config-input" />
                </Field>
              </div>
            </SettingsSection>

            <SettingsSection icon={Database} title="MentisDB" description="Memoria operacional de corto plazo para agentes y subagentes.">
              <Field label="Estado">
                <Select name="mentis_enabled" defaultValue={String(integrations.mentis_enabled)}>
                  <SelectTrigger className="config-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">Desactivado</SelectItem>
                    <SelectItem value="true">Activo</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Mentis URL">
                <Input name="mentis_base_url" defaultValue={integrations.mentis} placeholder="http://mentisdb:80" className="config-input" />
              </Field>
            </SettingsSection>
          </TabsContent>

          <TabsContent value="trading" className="mt-0 space-y-4 outline-none">
            <SettingsSection
              icon={Globe}
              title="Cuenta de Kalshi"
              description="Credenciales para ejecución real de mercados de predicción."
              action={
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${integrations.kalshi_configured ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                  {integrations.kalshi_configured ? "Vinculada" : "Pendiente"}
                </span>
              }
            >
              <Field label="Username / Email">
                <Input name="kalshi_username" defaultValue={config.kalshi_username} placeholder="user@mail.com" className="config-input" />
              </Field>
              <Field label="Password">
                <Input name="kalshi_password" type="password" placeholder="••••••••" className="config-input" />
              </Field>
              <Field label="Key ID (Opcional)">
                <Input name="kalshi_key_id" defaultValue={config.kalshi_key_id} placeholder="UUID" className="config-input" />
              </Field>
            </SettingsSection>
          </TabsContent>
        </div>
      </Tabs>
    </form>
  );
}

function ConfigTab({ value, icon: Icon, title, description }: { value: string; icon: LucideIcon; title: string; description: string }) {
  return (
    <TabsTrigger
      value={value}
      className="h-auto justify-start gap-3 rounded-[8px] border border-transparent px-3 py-3 text-left data-active:border-neutral-200 data-active:bg-neutral-50 data-active:shadow-sm"
    >
      <Icon className="size-4 shrink-0 text-neutral-500" />
      <span className="min-w-0">
        <span className="block text-sm font-semibold text-neutral-900">{title}</span>
        <span className="block truncate text-xs font-normal text-neutral-500">{description}</span>
      </span>
    </TabsTrigger>
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
      <CardContent className={`grid gap-4 p-5 ${columns === 2 ? "md:grid-cols-2" : "grid-cols-1"}`}>
        {children}
      </CardContent>
    </Card>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold text-neutral-900">{label}</Label>
      {children}
      {hint ? <p className="text-xs leading-5 text-neutral-500">{hint}</p> : null}
    </div>
  );
}

function SecretField({ label, active, hint, children }: { label: string; active: boolean; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <Label className="text-sm font-semibold text-neutral-900">{label}</Label>
        <StatusBadge active={active} />
      </div>
      {children}
      {hint ? <p className="text-xs leading-5 text-neutral-500">{hint}</p> : null}
    </div>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${active ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
      {active ? "Configurado" : "Pendiente"}
    </span>
  );
}

function ModelUsagePanel({ usage }: { usage: any }) {
  const providers = usage?.providers || [];
  if (!providers.length) {
    return null;
  }

  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
          <DollarSign className="size-4 text-emerald-600" />
          Consumo y límites de modelos
        </CardTitle>
        <CardDescription className="text-sm text-neutral-500">
          {usage.period?.label || "Periodo actual"} · {usage.period?.start} a {usage.period?.end}
        </CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-3 p-5 xl:grid-cols-3">
        {providers.map((provider: any) => {
          const used = typeof provider.used === "number" ? provider.used : null;
          return (
            <div key={provider.provider} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
              <div className="mb-3 flex items-center justify-between gap-2">
                <span className="text-sm font-semibold capitalize text-neutral-900">{provider.provider}</span>
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${provider.status === "live" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                  {provider.status}
                </span>
              </div>
              <div className="text-2xl font-semibold text-neutral-950">
                {used !== null ? `$${used.toFixed(2)}` : "N/D"}
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-neutral-200">
                <div className={`h-full rounded-full ${provider.status === "live" ? "w-full bg-emerald-500" : "w-0 bg-emerald-500"}`} />
              </div>
              <p className="mt-2 text-xs font-medium text-neutral-500">
                Límite: {provider.limit !== null && provider.limit !== undefined ? provider.limit : "No disponible"}
              </p>
              <p className="mt-3 text-xs leading-relaxed text-neutral-500">{provider.detail}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
