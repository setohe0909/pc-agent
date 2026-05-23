import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Boxes,
  CheckCircle2,
  Code,
  Database,
  GitBranch,
  Globe2,
  Layout,
  Rocket,
  Save,
  Shield,
  Terminal,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const pilotCapabilities = [
  {
    icon: Layout,
    title: "Layout Builder",
    description: "Genera interfaces responsivas con Tailwind y componentes reutilizables.",
  },
  {
    icon: Database,
    title: "Supabase Architect",
    description: "Propone tablas, políticas RLS y flujos de datos para nuevos módulos.",
  },
  {
    icon: Shield,
    title: "Version Control",
    description: "Mantiene cambios trazables antes de pasar a revisión humana.",
  },
];

const pilotFlow = ["Brief", "Scaffold", "Review", "Deploy"];

const monitorItems = [
  { label: "GitHub Writes", value: "Branch + PR", icon: Zap, tone: "emerald" },
  { label: "Linear Intake", value: "Issue linked", icon: Database, tone: "sky" },
  { label: "CI/CD Pipelines", value: "PR checks", icon: Globe2, tone: "violet" },
];

const terminalLines = [
  "[SYSTEM] Production adapter initialized.",
  "[GITHUB] Branch, commit and pull request required.",
  "[LINEAR] Issue comments enabled when API key is configured.",
  "[PREVIEW] Deploy hook required for preview_required tasks.",
];

export function CoderWebView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { runtime } = data;
  const currentRuntime = runtime?.runtime || {};
  const secrets = currentRuntime.secrets || {};
  const coderWebConfig = data.config?.integrations?.coder_web || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);

    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-5 pb-10">
      <section className="sticky top-0 z-20 rounded-[10px] border border-neutral-200 bg-white/95 px-5 py-4 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Code className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Coder Web Agent</h2>
                <Badge className="rounded-full bg-blue-50 text-blue-700 hover:bg-blue-50">Pilot</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">Experiencias web, e-commerce y despliegues asistidos por subagentes.</p>
            </div>
          </div>
          <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
            <Save className="size-4" />
            Guardar cambios
          </Button>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <SettingsSection
            icon={GitBranch}
            title="GitHub Repository Control"
            description="Credenciales y destino para crear, actualizar y publicar proyectos React/TS."
            action={
              <div className="flex flex-wrap justify-end gap-2">
                <ConfigBadge configured={Boolean(secrets.github_token || coderWebConfig.has_github_auth)} label="GitHub" />
                <ConfigBadge configured={Boolean(secrets.linear_api_key || coderWebConfig.has_linear_api_key)} label="Linear" />
                <ConfigBadge configured={Boolean(secrets.coder_web_preview_deploy_hook_url || coderWebConfig.has_preview_hook)} label="Preview" />
              </div>
            }
          >
            <Field label="GitHub Personal Token" hint="Solo se actualiza si escribes un nuevo token.">
              <Input
                name="github_token"
                type="password"
                placeholder={secrets.github_token ? "Token existente protegido" : "ghp_..."}
                className="coder-input"
              />
            </Field>
            <Field label="GitHub Organization / User" hint="Owner por defecto para repositorios nuevos.">
              <Input
                name="github_org"
                placeholder="tu-org"
                defaultValue={currentRuntime.github_org || ""}
                className="coder-input"
              />
            </Field>
            <Field label="Repositorio destino" hint="Opcional. Si está vacío, Coder Web crea un repo nuevo en el owner configurado.">
              <Input
                name="coder_web_repository"
                placeholder="owner/repo"
                defaultValue={currentRuntime.coder_web_repository || ""}
                className="coder-input"
              />
            </Field>
            <Field label="Linear API Key" hint="Permite comentar PRs en issues asignados desde Linear.">
              <Input
                name="linear_api_key"
                type="password"
                placeholder={secrets.linear_api_key ? "Key existente protegida" : "lin_api_..."}
                className="coder-input"
              />
            </Field>
            <Field label="Preview deploy hook" hint="Webhook de Vercel/Netlify/CI para generar preview por PR.">
              <Input
                name="coder_web_preview_deploy_hook_url"
                type="password"
                placeholder={secrets.coder_web_preview_deploy_hook_url ? "Hook existente protegido" : "https://api.vercel.com/v1/integrations/deploy/..."}
                className="coder-input"
              />
            </Field>
            <Field label="Privacidad de repos nuevos">
              <Select name="coder_web_private_repo" defaultValue={String(currentRuntime.coder_web_private_repo ?? true)}>
                <SelectTrigger className="coder-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Privado</SelectItem>
                  <SelectItem value="false">Público</SelectItem>
                </SelectContent>
              </Select>
            </Field>
          </SettingsSection>

          <SettingsSection
            icon={Terminal}
            title="Stack & preferencias de desarrollo"
            description="Define el comportamiento base para nuevos proyectos y cambios asistidos."
          >
            <Field label="Stack principal">
              <Select name="coder_web_stack" defaultValue={currentRuntime.coder_web_stack || "react-ts"}>
                <SelectTrigger className="coder-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="react-ts">React/TS + Tailwind + Supabase</SelectItem>
                  <SelectItem value="nextjs">Next.js + Tailwind + Prisma</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Nivel de autonomía">
              <Select name="coder_web_autonomy" defaultValue={currentRuntime.coder_web_autonomy || "human-in-loop"}>
                <SelectTrigger className="coder-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="full">Total (auto-deploy)</SelectItem>
                  <SelectItem value="human-in-loop">Revisión requerida</SelectItem>
                  <SelectItem value="draft">Solo borradores</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Prioridad de performance">
              <Select name="coder_web_perf" defaultValue={currentRuntime.coder_web_perf || "high"}>
                <SelectTrigger className="coder-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">Máxima (SEO & speed)</SelectItem>
                  <SelectItem value="balanced">Balanceada</SelectItem>
                  <SelectItem value="dev">Desarrollo rápido</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <div className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
              <p className="text-sm font-semibold text-neutral-950">Modo de entrega</p>
              <p className="mt-1 text-xs leading-5 text-neutral-500">
                El piloto siempre prepara branch, commit, pull request, checks y rollback antes de tocar ambientes productivos.
              </p>
              <code className="mt-3 block rounded-[6px] bg-neutral-950 px-3 py-2 text-xs text-neutral-100">
                branch: feature/coder-web-pilot
              </code>
            </div>
          </SettingsSection>

          <SettingsSection icon={Boxes} title="Pilot AI Engine" description="Bloques de ejecución disponibles para diseño, datos y control de cambios." columns={1}>
            <div className="grid gap-3 md:grid-cols-3">
              {pilotCapabilities.map((capability) => (
                <div key={capability.title} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex size-8 items-center justify-center rounded-[8px] bg-white text-neutral-800 ring-1 ring-neutral-200">
                      <capability.icon className="size-4" />
                    </span>
                    <p className="text-sm font-semibold text-neutral-950">{capability.title}</p>
                  </div>
                  <p className="text-xs leading-5 text-neutral-500">{capability.description}</p>
                </div>
              ))}
            </div>
          </SettingsSection>
        </div>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <Rocket className="size-4 text-[#3ecf8e]" />
                Flujo Pilot
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">De una solicitud a una rama lista para revisión.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 p-5">
              {pilotFlow.map((step, index) => (
                <div key={step} className="flex items-center gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
                  <span className="flex size-6 items-center justify-center rounded-full bg-neutral-950 text-xs text-white">{index + 1}</span>
                  <span className="text-sm font-medium text-neutral-800">{step}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <Activity className="size-4 text-[#3ecf8e]" />
                Pilot Monitor
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Estado operativo de generación, datos y despliegue.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              {monitorItems.map((item) => (
                <StatusRow key={item.label} {...item} />
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-neutral-950 text-white shadow-sm">
            <CardHeader className="border-b border-white/10 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <GitBranch className="size-4 text-[#3ecf8e]" />
                Live Trace
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-5 font-mono text-xs text-neutral-300">
              {terminalLines.map((line) => (
                <p key={line}>
                  <span className="text-[#3ecf8e]">{">"}</span> {line}
                </p>
              ))}
            </CardContent>
          </Card>
        </aside>
      </section>
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

function ConfigBadge({ configured, label }: { configured: boolean; label: string }) {
  return configured ? (
    <Badge className="rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
      <CheckCircle2 className="mr-1 size-3" />
      {label}
    </Badge>
  ) : (
    <Badge className="rounded-full bg-neutral-100 text-neutral-500 hover:bg-neutral-100">
      {label}
    </Badge>
  );
}

function StatusRow({ label, value, icon: Icon, tone }: { label: string; value: string; icon: LucideIcon; tone: string }) {
  const toneClass = {
    emerald: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    sky: "bg-sky-50 text-sky-700 ring-sky-100",
    violet: "bg-violet-50 text-violet-700 ring-violet-100",
  }[tone] || "bg-neutral-50 text-neutral-700 ring-neutral-100";

  return (
    <div className="flex items-center justify-between gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
      <div className="flex items-center gap-2">
        <span className={`flex size-7 items-center justify-center rounded-[7px] ring-1 ${toneClass}`}>
          <Icon className="size-3.5" />
        </span>
        <span className="text-sm font-medium text-neutral-700">{label}</span>
      </div>
      <span className="text-xs font-semibold text-neutral-950">{value}</span>
    </div>
  );
}
