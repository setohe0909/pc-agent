import type { LucideIcon } from "lucide-react";
import { Activity, Box, Brain, Database, Globe, Layers, Megaphone, MessageSquare, Network, PenTool, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const systemStats = [
  { label: "Contenedores", value: "14", detail: "Docker compose" },
  { label: "Red", value: "Bridge", detail: "assistant-network" },
  { label: "Runtime", value: "8100", detail: "assistant-runtime" },
  { label: "Control", value: "8000", detail: "FastAPI" },
];

const layers: Array<{
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  components: Array<{ name: string; badge?: string; description: string; endpoint?: string }>;
}> = [
  {
    id: "01",
    title: "Gateway",
    description: "Entradas humanas y superficies administrativas.",
    icon: MessageSquare,
    components: [
      {
        name: "Discord Bot",
        badge: "Python / Nextcord",
        description: "Recibe comandos, crea threads por subagente y envía payloads al runtime.",
        endpoint: "assistant-runtime:8100",
      },
      {
        name: "Control UI & API",
        badge: "React + FastAPI",
        description: "Gestiona estado, configuración, memoria y monitoreo visual.",
        endpoint: "control-api:8000",
      },
    ],
  },
  {
    id: "02",
    title: "Lógica distribuida",
    description: "Orquestación, ingestión y control operacional.",
    icon: Server,
    components: [
      {
        name: "assistant-runtime",
        badge: "Orquestador",
        description: "Consulta memoria, llama LLMs y delega tareas a workflows especializados.",
      },
      {
        name: "ingestion-worker",
        badge: "Crons",
        description: "Recolecta fuentes externas, genera embeddings y ejecuta consolidación.",
      },
      {
        name: "control-api",
        badge: "Admin API",
        description: "Centraliza Supabase, runtime config, memoria y auditoría para la UI.",
      },
    ],
  },
  {
    id: "03",
    title: "Sub-agentes",
    description: "Especialización por dominio y memoria de contexto.",
    icon: Layers,
    components: [
      { name: "Marketer", badge: "Social", description: "Analiza tendencias, imágenes, leads y campañas." },
      { name: "Writer", badge: "Obsidian", description: "Genera blogs, storytelling y contenido persistido en vault." },
      { name: "Picture", badge: "Vision", description: "Genera y edita imágenes con memoria de estilo." },
      { name: "Coder Web", badge: "Pilot", description: "Prepara repos, arquitectura y aprendizajes web." },
      { name: "Trader", badge: "Execution", description: "Cruza señales de mercado con control humano." },
    ],
  },
  {
    id: "04",
    title: "Persistencia",
    description: "Memoria, vectores, documentos y datos comerciales.",
    icon: Database,
    components: [
      { name: "Supabase pgvector", badge: "RAG", description: "Conocimiento vectorial y almacenamiento de largo plazo." },
      { name: "Mentis memory", badge: "LTM / STM", description: "Fragmentos por agente y consolidaciones evolutivas." },
      { name: "Obsidian Vault", badge: "Docs", description: "Salida editorial persistida en volumen compartido." },
      { name: "Marketing CRM", badge: "Leads", description: "Contactos, campañas y auditoría comercial." },
    ],
  },
  {
    id: "05",
    title: "Observabilidad",
    description: "Trazas, costos y telemetría del stack de IA.",
    icon: ShieldCheck,
    components: [
      { name: "Langfuse Web", description: "Panel de trazas y sesiones." },
      { name: "Langfuse Worker", description: "Procesamiento asíncrono de eventos." },
      { name: "ClickHouse", description: "Analítica de alta cardinalidad." },
      { name: "Postgres / Valkey", description: "Persistencia y cache del stack Langfuse." },
    ],
  },
  {
    id: "06",
    title: "APIs externas",
    description: "Modelos, scraping, mercados y medios.",
    icon: Globe,
    components: [
      { name: "Gemini / OpenAI / Together", description: "LLMs y visión." },
      { name: "Ollama", description: "Embeddings y modelos locales." },
      { name: "Tavily", description: "Investigación y señales externas." },
      { name: "Kalshi", description: "Mercados predictivos y orderbooks." },
    ],
  },
];

const agentIcons: Record<string, LucideIcon> = {
  Marketer: Megaphone,
  Writer: PenTool,
  Picture: Brain,
  "Coder Web": Box,
  Trader: Activity,
};

export function ArchitectureView() {
  return (
    <div className="space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Network className="size-5" />
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-semibold tracking-tight text-neutral-950">Arquitectura PC Agent</h2>
                <Badge className="rounded-full bg-emerald-600 text-white">Online</Badge>
              </div>
              <p className="mt-1 text-sm leading-6 text-neutral-500">Mapa Clean/Hexagonal de servicios, puertos, persistencia y subagentes.</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:min-w-[520px]">
            {systemStats.map((stat) => (
              <div key={stat.label} className="rounded-[8px] border border-neutral-200 bg-neutral-50 px-3 py-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-neutral-400">{stat.label}</p>
                <p className="mt-1 text-sm font-semibold text-neutral-950">{stat.value}</p>
                <p className="text-xs text-neutral-500">{stat.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          {layers.map((layer) => {
            const Icon = layer.icon;
            return (
              <Card key={layer.id} className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
                <CardHeader className="border-b border-neutral-200 px-5 py-4">
                  <div className="flex items-start gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
                      <Icon className="size-4" />
                    </span>
                    <div>
                      <CardTitle className="text-base font-semibold text-neutral-950">
                        {layer.id}. {layer.title}
                      </CardTitle>
                      <CardDescription className="mt-1 text-sm text-neutral-500">{layer.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="grid gap-3 p-5 md:grid-cols-2 xl:grid-cols-3">
                  {layer.components.map((component) => {
                    const AgentIcon = agentIcons[component.name];
                    return (
                      <div key={component.name} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                        <div className="mb-3 flex items-center justify-between gap-3">
                          <div className="flex min-w-0 items-center gap-2">
                            {AgentIcon ? <AgentIcon className="size-4 shrink-0 text-[#168a5b]" /> : <Box className="size-4 shrink-0 text-neutral-500" />}
                            <p className="truncate text-sm font-semibold text-neutral-950">{component.name}</p>
                          </div>
                          {component.badge ? (
                            <span className="shrink-0 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-neutral-500 ring-1 ring-neutral-200">
                              {component.badge}
                            </span>
                          ) : null}
                        </div>
                        <p className="text-xs leading-5 text-neutral-500">{component.description}</p>
                        {component.endpoint ? (
                          <code className="mt-3 block rounded-[6px] bg-neutral-950 px-2 py-1 text-xs text-neutral-100">{component.endpoint}</code>
                        ) : null}
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })}
        </div>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <RefreshCw className="size-4 text-[#3ecf8e]" />
                Flujo principal
              </CardTitle>
              <CardDescription className="text-sm leading-6">Discord o UI envían solicitudes al runtime/API; los workflows consultan memoria y persisten resultados en Supabase.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {["Gateway", "Runtime", "Sub-agente", "Memoria", "Observabilidad"].map((step, index) => (
                <div key={step} className="flex items-center gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
                  <span className="flex size-6 items-center justify-center rounded-full bg-neutral-950 text-xs text-white">{index + 1}</span>
                  <span className="text-sm font-medium text-neutral-800">{step}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <ShieldCheck className="size-4 text-emerald-600" />
                Guardrails
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-neutral-600">
              <p>Trading requiere canal autorizado, límite operativo y aprobación humana.</p>
              <p>Credenciales se gestionan desde Runtime Settings y no se muestran en claro.</p>
              <p>Memoria por subagente queda separada por categoría para auditoría y contexto.</p>
            </CardContent>
          </Card>
        </aside>
      </section>
    </div>
  );
}
