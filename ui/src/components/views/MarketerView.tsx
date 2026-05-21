import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Brain,
  Camera,
  Megaphone,
  Music,
  Radar,
  Save,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const intelligenceNodes = [
  {
    icon: ShieldCheck,
    title: "Critic Node",
    description: "Revisa planes y campañas antes de ejecutar acciones visibles.",
  },
  {
    icon: Brain,
    title: "Voice Refiner",
    description: "Ajusta tono empático y profesional usando identidad de marca.",
  },
  {
    icon: Activity,
    title: "Lead Auto-Pilot",
    description: "Persiste prospectos calificados y señales comerciales en Supabase.",
  },
];

const operationSignals = [
  { icon: Radar, label: "Comentarios", value: "Activa", tone: "emerald" },
  { icon: Search, label: "Competencia", value: "En espera", tone: "amber" },
  { icon: Megaphone, label: "Última campaña", value: "Primavera 2026", tone: "pink" },
];

const marketingFlow = ["Escuchar", "Calificar", "Responder", "Persistir"];

export function MarketerView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { runtime } = data;
  const currentRuntime = runtime?.runtime || {};

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
              <Megaphone className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Marketer Sub-Agent Portal</h2>
                <Badge className="rounded-full bg-pink-50 text-pink-700 hover:bg-pink-50">LangGraph</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">Automatización, investigación y workflows comerciales asistidos por IA.</p>
            </div>
          </div>
          <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
            <Save className="size-4" />
            Guardar configuración
          </Button>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <SettingsSection icon={Camera} title="Instagram Business" description="Cuenta conectada para comentarios, campañas y leads.">
              <Field label="Instagram Access Token">
                <Input name="instagram_access_token" type="password" placeholder="EAAB..." defaultValue={currentRuntime.instagram_access_token} className="marketing-input" />
              </Field>
              <Field label="Instagram Account ID">
                <Input name="instagram_account_id" placeholder="1784..." defaultValue={currentRuntime.instagram_account_id} className="marketing-input" />
              </Field>
            </SettingsSection>

            <SettingsSection icon={Music} title="TikTok For Business" description="Gestión de contenido, señales virales y tendencias.">
              <Field label="TikTok API Key">
                <Input name="tiktok_api_key" type="password" placeholder="tk_..." defaultValue={currentRuntime.tiktok_api_key} className="marketing-input" />
              </Field>
              <Field label="TikTok User ID">
                <Input name="tiktok_user_id" placeholder="@username" defaultValue={currentRuntime.tiktok_user_id} className="marketing-input" />
              </Field>
            </SettingsSection>
          </div>

          <SettingsSection icon={Sparkles} title="Identidad de marca & tono" description="Define cómo debe actuar el agente cuando responde o califica." columns={3}>
            <Field label="Tipo de marca">
              <Select name="marketing_brand_type" defaultValue={currentRuntime.marketing_brand_type || "fashion"}>
                <SelectTrigger className="marketing-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="fashion">Moda / diseño</SelectItem>
                  <SelectItem value="tech">Tecnología</SelectItem>
                  <SelectItem value="food">Gastronomía</SelectItem>
                  <SelectItem value="service">Servicios</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Tono de respuesta">
              <Select name="marketing_tone" defaultValue={currentRuntime.marketing_tone || "empathetic"}>
                <SelectTrigger className="marketing-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="empathetic">Empático & positivo</SelectItem>
                  <SelectItem value="professional">Profesional & serio</SelectItem>
                  <SelectItem value="funny">Divertido & casual</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Frecuencia de sondeo">
              <Select name="marketing_poll_frequency" defaultValue={currentRuntime.marketing_poll_frequency || "daily"}>
                <SelectTrigger className="marketing-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Cada hora</SelectItem>
                  <SelectItem value="daily">Diario</SelectItem>
                  <SelectItem value="weekly">Semanal</SelectItem>
                </SelectContent>
              </Select>
            </Field>
          </SettingsSection>

          <SettingsSection icon={Target} title="LangGraph v0.5.0 Intelligence" description="Nodos autónomos para análisis crítico, voz y prospección." columns={1}>
            <div className="grid gap-3 md:grid-cols-3">
              {intelligenceNodes.map((node) => (
                <div key={node.title} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <span className="flex size-8 items-center justify-center rounded-[8px] bg-white text-neutral-800 ring-1 ring-neutral-200">
                      <node.icon className="size-4" />
                    </span>
                    <p className="text-sm font-semibold text-neutral-950">{node.title}</p>
                  </div>
                  <p className="text-xs leading-5 text-neutral-500">{node.description}</p>
                </div>
              ))}
            </div>
          </SettingsSection>
        </div>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <TrendingUp className="size-4 text-[#3ecf8e]" />
                Flujo comercial
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Ciclo operativo del agente de marketing.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 p-5">
              {marketingFlow.map((step, index) => (
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
                Estado de operaciones
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Señales activas de escucha, research y campaña.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              {operationSignals.map((signal) => (
                <StatusRow key={signal.label} {...signal} />
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
  columns = 2,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children: ReactNode;
  columns?: 1 | 2 | 3;
}) {
  const columnClass = columns === 3 ? "md:grid-cols-3" : columns === 2 ? "md:grid-cols-2" : "grid-cols-1";

  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <div className="flex min-w-0 gap-3">
          <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
            <Icon className="size-4" />
          </span>
          <div className="min-w-0">
            <CardTitle className="text-base font-semibold text-neutral-950">{title}</CardTitle>
            <CardDescription className="mt-1 text-sm text-neutral-500">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className={`grid gap-4 p-5 ${columnClass}`}>{children}</CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold text-neutral-900">{label}</Label>
      {children}
    </div>
  );
}

function StatusRow({ label, value, icon: Icon, tone }: { label: string; value: string; icon: LucideIcon; tone: string }) {
  const toneClass = {
    emerald: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    amber: "bg-amber-50 text-amber-700 ring-amber-100",
    pink: "bg-pink-50 text-pink-700 ring-pink-100",
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
