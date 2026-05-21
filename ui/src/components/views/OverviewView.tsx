import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Brain, CheckCircle2, Database, Network, ShieldCheck, Sparkles, Timer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function StateBadge({ state }: { state: string }) {
  const tone = state === "healthy"
    ? "bg-emerald-50 text-emerald-700 ring-emerald-100"
    : state === "offline"
      ? "bg-red-50 text-red-700 ring-red-100"
      : "bg-amber-50 text-amber-700 ring-amber-100";

  return <Badge className={`rounded-full px-2.5 py-1 text-[10px] uppercase ring-1 hover:bg-inherit ${tone}`}>{state}</Badge>;
}

function MiniLineChart({ values }: { values: number[] }) {
  const width = 340;
  const height = 96;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(max - min, 1);
  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * width;
    const y = height - ((value - min) / range) * 54 - 20;
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="mt-5 h-[105px] w-full overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" role="img" aria-label="Tendencia semanal">
        <g stroke="#e5e7eb" strokeDasharray="4 4" strokeWidth="1">
          <line x1="0" y1="22" x2={width} y2="22" />
          <line x1="0" y1="54" x2={width} y2="54" />
          <line x1="0" y1="86" x2={width} y2="86" />
        </g>
        <polyline points={points} fill="none" stroke="#168a5b" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="0" y1="88" x2={width} y2="88" stroke="#d4d4d4" strokeWidth="1.5" />
      </svg>
    </div>
  );
}

function ConfidenceDial({ value }: { value: number }) {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value);

  return (
    <div className="mt-5 flex justify-center">
      <div className="relative size-36">
        <svg viewBox="0 0 120 120" className="size-full -rotate-90">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="12" />
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#168a5b"
            strokeLinecap="round"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-2xl font-semibold text-neutral-950">
          {value.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, detail, chart }: { title: string; value: string; detail: string; chart: "line" | "dial" }) {
  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <CardDescription className="text-sm font-medium text-neutral-500">{title}</CardDescription>
        <CardTitle className="mt-2 text-4xl font-semibold tracking-tight text-neutral-950">{value}</CardTitle>
        <p className="text-sm leading-6 text-neutral-500">{detail}</p>
      </CardHeader>
      <CardContent className="px-5 pb-5">
        {chart === "line" ? <MiniLineChart values={[44, 51, 49, 46, 50, 47, 49]} /> : <ConfidenceDial value={0.71} />}
      </CardContent>
    </Card>
  );
}

function StatCard({ label, value, icon: Icon, tone }: { label: string; value: string; icon: LucideIcon; tone: string }) {
  const toneClass = {
    emerald: "bg-emerald-50 text-emerald-700",
    sky: "bg-sky-50 text-sky-700",
    amber: "bg-amber-50 text-amber-700",
    red: "bg-red-50 text-red-700",
  }[tone] || "bg-neutral-100 text-neutral-700";

  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="p-4">
        <div className={`mb-4 flex size-9 items-center justify-center rounded-[8px] ${toneClass}`}>
          <Icon className="size-4" />
        </div>
        <CardDescription className="text-sm text-neutral-500">{label}</CardDescription>
        <CardTitle className="text-3xl font-semibold tracking-tight text-neutral-950">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

type ServiceStatus = {
  name: string;
  state: string;
  detail?: string;
};

type KnowledgeSource = {
  enabled?: boolean;
};

type OverviewData = {
  status?: {
    services?: ServiceStatus[];
  } | null;
  config?: {
    discord?: {
      requests_channel_id?: string | null;
      notifications_channel_id?: string | null;
      status_channel_id?: string | null;
    };
    integrations?: {
      langfuse_enabled?: boolean;
      langfuse?: string;
      mentis_enabled?: boolean;
    };
  } | null;
  sources?: {
    sources?: KnowledgeSource[];
  } | null;
  supabase?: {
    supabase: {
      knowledge_schema_ready?: boolean;
      reachable?: boolean;
      rest_available?: boolean;
      detail?: string;
    };
  } | null;
  mentis?: {
    mentis: {
      reachable?: boolean;
      can_read?: boolean;
      can_write?: boolean;
    };
  } | null;
};

export function OverviewView({ data }: { data: OverviewData }) {
  const { status, config, sources, supabase, mentis } = data;

  const services = status?.services || [];
  const healthy = services.filter((s) => s.state === "healthy").length;
  const sourcesList = sources?.sources || [];
  const discordConfigured = config?.discord ? [
    config.discord.requests_channel_id,
    config.discord.notifications_channel_id,
    config.discord.status_channel_id,
  ].filter(Boolean).length : 0;
  const offline = services.filter((s) => s.state === "offline").length;
  const activeSources = sourcesList.filter((s) => s.enabled).length;

  return (
    <div className="space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Sparkles className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Operations Dashboard</h2>
                <StateBadge state={offline > 0 ? "degraded" : "healthy"} />
              </div>
              <p className="mt-1 text-sm text-neutral-500">Métricas, salud de servicios y señales de memoria para administrar la plataforma multiagente.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-[8px] bg-neutral-50 px-3 py-2 text-sm font-medium text-neutral-600 ring-1 ring-neutral-200">
            <Timer className="size-4" />
            Actualización automática cada 5s
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Servicios healthy" value={`${healthy}/${services.length}`} icon={CheckCircle2} tone="emerald" />
        <StatCard label="Fuentes activas" value={activeSources.toString()} icon={Database} tone="sky" />
        <StatCard label="Discord" value={`${discordConfigured}/3`} icon={ShieldCheck} tone="amber" />
        <StatCard label="Alertas offline" value={offline.toString()} icon={AlertTriangle} tone="red" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <MetricCard title="Containment rate" value="49%" detail="Conversaciones resueltas por agentes sin intervención humana." chart="line" />
        <MetricCard title="Escalation rate" value="38%" detail="Flujos que requieren aprobación, revisión o handoff." chart="line" />
        <MetricCard title="AI confidence score" value="0.71" detail="Promedio combinado de señales de runtime y memoria." chart="dial" />
        <MetricCard title="CSAT overall" value="3.8/5" detail="Lectura operacional estimada para experiencias asistidas." chart="line" />
      </div>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
          <CardHeader className="border-b border-neutral-200 px-5 py-4">
            <CardTitle className="text-base font-semibold text-neutral-950">Estado de servicios</CardTitle>
            <CardDescription className="text-sm text-neutral-500">Runtime, workers e integraciones observadas por el panel.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 p-5 md:grid-cols-2">
            {services.map((service) => (
              <div key={service.name} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-neutral-950">{service.name}</p>
                  <StateBadge state={service.state} />
                </div>
                <p className="break-words text-xs leading-5 text-neutral-500">{service.detail || "Sin detalle adicional."}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <aside className="space-y-4">
          <IntegrationCard title="Supabase PGVector" icon={Database} description="Vector store público para conocimiento.">
            {supabase ? (
              <>
                <InfoRow label="Estado" value={<StateBadge state={supabase.supabase.knowledge_schema_ready ? "healthy" : supabase.supabase.reachable ? "degraded" : "offline"} />} />
                <InfoRow label="REST" value={supabase.supabase.rest_available ? "Sí" : "No"} />
                <InfoRow label="Detalle" value={supabase.supabase.detail || "N/A"} />
              </>
            ) : <p className="text-sm text-neutral-500">Verificando...</p>}
          </IntegrationCard>

          <IntegrationCard title="MentisDB" icon={Brain} description="Memoria operacional del asistente.">
            {mentis ? (
              <>
                <InfoRow label="Estado" value={<StateBadge state={config?.integrations?.mentis_enabled ? (mentis.mentis.reachable ? "healthy" : "offline") : "unknown"} />} />
                <InfoRow label="Lectura" value={mentis.mentis.can_read ? "Sí" : "No"} />
                <InfoRow label="Escritura" value={mentis.mentis.can_write ? "Sí" : "No"} />
              </>
            ) : <p className="text-sm text-neutral-500">Verificando...</p>}
          </IntegrationCard>

          <IntegrationCard title="Langfuse" icon={Network} description="Observabilidad y traces.">
            {config ? (
              <>
                <InfoRow label="Estado" value={<StateBadge state={config.integrations?.langfuse_enabled ? "healthy" : "unknown"} />} />
                <InfoRow label="Host" value={config.integrations?.langfuse || "N/A"} />
              </>
            ) : <p className="text-sm text-neutral-500">Verificando...</p>}
          </IntegrationCard>
        </aside>
      </section>
    </div>
  );
}

function IntegrationCard({ title, icon: Icon, description, children }: { title: string; icon: LucideIcon; description: string; children: ReactNode }) {
  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
          <Icon className="size-4 text-[#3ecf8e]" />
          {title}
        </CardTitle>
        <CardDescription className="text-sm text-neutral-500">{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 p-5">{children}</CardContent>
    </Card>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      <span className="max-w-[180px] truncate text-right text-xs font-semibold text-neutral-950">{value}</span>
    </div>
  );
}
