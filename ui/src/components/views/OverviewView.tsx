import { AlertTriangle, Brain, CheckCircle2, Database, Network, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function StateBadge({ state }: { state: string }) {
  const variant = state === "healthy" ? "default" : state === "offline" ? "destructive" : "secondary";
  const tone = state === "healthy"
    ? "bg-[#159947] text-white"
    : state === "offline"
      ? "bg-red-100 text-red-700"
      : "bg-amber-100 text-amber-700";

  return <Badge variant={variant} className={`rounded-[4px] px-2 uppercase text-[10px] ${tone}`}>{state}</Badge>;
}

function MiniLineChart({ values }: { values: number[] }) {
  const width = 340;
  const height = 110;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(max - min, 1);
  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * width;
    const y = height - ((value - min) / range) * 64 - 24;
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="mt-5 h-[120px] w-full overflow-hidden">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" role="img" aria-label="Tendencia semanal">
        <g stroke="#d7e0e6" strokeDasharray="4 4" strokeWidth="1">
          <line x1="0" y1="22" x2={width} y2="22" />
          <line x1="0" y1="58" x2={width} y2="58" />
          <line x1="0" y1="94" x2={width} y2="94" />
        </g>
        <g stroke="#e8eef2" strokeWidth="1">
          {[0, 1, 2, 3, 4, 5, 6].map((tick) => (
            <line key={tick} x1={(tick / 6) * width} y1="12" x2={(tick / 6) * width} y2="98" />
          ))}
        </g>
        <polyline points={points} fill="none" stroke="#4a9bd0" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="0" y1="98" x2={width} y2="98" stroke="#8b969f" strokeWidth="2" />
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
      <div className="relative size-40">
        <svg viewBox="0 0 120 120" className="size-full -rotate-90">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="#e4e9ec" strokeWidth="12" />
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#1688d8"
            strokeLinecap="round"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-3xl font-medium text-slate-950">
          {value.toFixed(2)}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  detail,
  chart,
}: {
  title: string;
  value: string;
  detail: string;
  chart: "line" | "dial";
}) {
  return (
    <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
      <CardHeader className="p-6 pb-2">
        <CardDescription className="text-base font-medium text-slate-700">{title}</CardDescription>
        <CardTitle className="mt-3 text-4xl font-medium text-slate-950">{value}</CardTitle>
        <p className="text-sm text-slate-500">{detail}</p>
      </CardHeader>
      <CardContent className="px-6 pb-6">
        {chart === "line" ? <MiniLineChart values={[44, 51, 49, 46, 50, 47, 49]} /> : <ConfidenceDial value={0.71} />}
      </CardContent>
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
    <div className="space-y-8">
      <section>
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-slate-950">Overview</h2>
          <div className="text-sm text-slate-500">Actualización automática cada 5s</div>
        </div>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader className="p-5">
              <div className="mb-4 flex size-11 items-center justify-center rounded-[8px] bg-[#edf8f1] text-[#159947]">
                <CheckCircle2 className="size-5" />
              </div>
              <CardDescription className="text-slate-500">Servicios healthy</CardDescription>
              <CardTitle className="text-4xl font-medium text-slate-950">{healthy}/{services.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader className="p-5">
              <div className="mb-4 flex size-11 items-center justify-center rounded-[8px] bg-[#eef7fd] text-[#1688d8]">
                <Database className="size-5" />
              </div>
              <CardDescription className="text-slate-500">Fuentes activas</CardDescription>
              <CardTitle className="text-4xl font-medium text-slate-950">{activeSources}</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader className="p-5">
              <div className="mb-4 flex size-11 items-center justify-center rounded-[8px] bg-[#fff8e8] text-[#d88716]">
                <ShieldCheck className="size-5" />
              </div>
              <CardDescription className="text-slate-500">Discord</CardDescription>
              <CardTitle className="text-4xl font-medium text-slate-950">{discordConfigured}/3</CardTitle>
            </CardHeader>
          </Card>
          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader className="p-5">
              <div className="mb-4 flex size-11 items-center justify-center rounded-[8px] bg-[#fff1f1] text-red-600">
                <AlertTriangle className="size-5" />
              </div>
              <CardDescription className="text-slate-500">Alertas offline</CardDescription>
              <CardTitle className="text-4xl font-medium text-slate-950">{offline}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
          <MetricCard title="Containment rate" value="49%" detail="Conversaciones resueltas por agentes sin intervención humana" chart="line" />
          <MetricCard title="Escalation rate" value="38%" detail="Flujos que requieren aprobación, revisión o handoff" chart="line" />
          <MetricCard title="AI confidence score (avg)" value="0.71" detail="Promedio combinado de señales de runtime y memoria" chart="dial" />
          <MetricCard title="CSAT - overall" value="3.8/5" detail="Lectura operacional estimada para experiencias asistidas" chart="line" />
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-slate-950">Estado de Servicios</h2>
          <StateBadge state={offline > 0 ? "degraded" : "healthy"} />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {services.map((s) => (
              <Card key={s.name} className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
                <CardHeader className="p-5">
                  <div className="flex items-center justify-between mb-2">
                    <CardTitle className="text-base text-slate-950">{s.name}</CardTitle>
                    <StateBadge state={s.state} />
                  </div>
                  <CardDescription className="text-xs break-words text-slate-500">{s.detail}</CardDescription>
                </CardHeader>
              </Card>
            ))}
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-950"><Database className="w-5 h-5"/> Supabase PGVector</CardTitle>
              <CardDescription className="text-slate-500">Vector store público para conocimiento.</CardDescription>
            </CardHeader>
            <CardContent>
              {supabase ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Estado</span>
                    <StateBadge state={supabase.supabase.knowledge_schema_ready ? "healthy" : supabase.supabase.reachable ? "degraded" : "offline"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Detalle</span>
                    <span className="truncate max-w-[150px]">{supabase.supabase.detail}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">REST Disponible</span>
                    <span>{supabase.supabase.rest_available ? "Sí" : "No"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-slate-500">Verificando...</div>}
            </CardContent>
          </Card>

          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-950"><Brain className="w-5 h-5"/> MentisDB</CardTitle>
              <CardDescription className="text-slate-500">Memoria operacional del asistente.</CardDescription>
            </CardHeader>
            <CardContent>
              {mentis ? (
                <div className="space-y-2 text-sm">
                   <div className="flex justify-between items-center">
                    <span className="text-slate-500">Estado</span>
                    <StateBadge state={config?.integrations?.mentis_enabled ? (mentis.mentis.reachable ? "healthy" : "offline") : "unknown"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Lectura</span>
                    <span>{mentis.mentis.can_read ? "Sí" : "No"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Escritura</span>
                    <span>{mentis.mentis.can_write ? "Sí" : "No"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-slate-500">Verificando...</div>}
            </CardContent>
          </Card>

          <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-950"><Network className="w-5 h-5"/> Langfuse</CardTitle>
              <CardDescription className="text-slate-500">Observabilidad y traces.</CardDescription>
            </CardHeader>
            <CardContent>
              {config ? (
                <div className="space-y-2 text-sm">
                   <div className="flex justify-between items-center">
                    <span className="text-slate-500">Estado</span>
                    <StateBadge state={config.integrations?.langfuse_enabled ? "healthy" : "unknown"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Host</span>
                    <span className="truncate max-w-[150px]">{config.integrations?.langfuse || "N/A"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-slate-500">Verificando...</div>}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
