import type { LucideIcon } from "lucide-react";
import { Activity, BookOpen, Brain, CheckCircle2, Database, Globe, Megaphone, PenTool, ShieldCheck, Terminal } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const quickStart = [
  {
    title: "Arranque",
    description: "Levanta el ecosistema de agentes autónomos con Docker Compose.",
    command: "docker compose up -d --build",
  },
  {
    title: "Puertos base",
    description: "Servicios principales expuestos para operación local y contenedores.",
    command: "Runtime 8100 · Control API 8000 · Obsidian 3010 · Langfuse 3000",
  },
  {
    title: "Modelos",
    description: "El runtime prioriza proveedores configurados y cae a Ollama cuando aplica.",
    command: "gemini | openai | ollama | together",
  },
];

const commandGroups: Array<{
  title: string;
  icon: LucideIcon;
  tone: string;
  commands: Array<{ command: string; title: string; description: string; note?: string }>;
}> = [
  {
    title: "Sistema",
    icon: Activity,
    tone: "text-emerald-700 bg-emerald-50",
    commands: [
      { command: "!status", title: "Salud del sistema", description: "Muestra conectividad de Ollama, API, Runtime, Supabase y Mentis." },
      { command: "!memory", title: "Memoria operativa", description: "Lista tendencias y aprendizajes recientes guardados en MentisDB." },
      { command: "!run consolidation", title: "Consolidación diaria", description: "Fuerza la síntesis de memoria de largo plazo." },
    ],
  },
  {
    title: "Inteligencia",
    icon: Globe,
    tone: "text-blue-700 bg-blue-50",
    commands: [
      { command: "!ask [pregunta]", title: "Consulta RAG", description: "Responde usando fuentes vectorizadas y memoria disponible." },
      { command: "!research [tema]", title: "Investigación profunda", description: "Busca fuentes externas y sintetiza oportunidades o riesgos." },
    ],
  },
  {
    title: "Marketing",
    icon: Megaphone,
    tone: "text-pink-700 bg-pink-50",
    commands: [
      { command: "!marketer [petición]", title: "Campaña asistida", description: "Planifica campañas con contexto, memoria y análisis visual." },
      { command: "!marketer qualify", title: "Lead auto-pilot", description: "Detecta leads y los persiste en CRM." },
      { command: "!marketer plan [tema]", title: "Plan editorial", description: "Genera estrategia con crítica y voz de marca." },
    ],
  },
  {
    title: "Sub-agentes",
    icon: PenTool,
    tone: "text-indigo-700 bg-indigo-50",
    commands: [
      { command: "!writer blog [es/en] [tema]", title: "Blog en Obsidian", description: "Crea contenido optimizado y lo guarda en el vault." },
      { command: "!picture memory", title: "Memoria visual", description: "Consulta aprendizajes de estilo del agente de imágenes." },
      { command: "!coder-web memory", title: "Memoria web", description: "Revisa aprendizajes del subagente de desarrollo web." },
    ],
  },
  {
    title: "Trading",
    icon: ShieldCheck,
    tone: "text-amber-700 bg-amber-50",
    commands: [
      {
        command: "!approve_trade [instrucción]",
        title: "Ejecución controlada",
        description: "Inicia flujo de Kalshi con límites, auditoría y aprobación humana.",
        note: "Límite operativo: $10 USD por operación.",
      },
    ],
  },
];

const dataNotes = [
  { label: "Vector store", value: "Supabase pgvector · mxbai-embed-large · 1024 dims" },
  { label: "Memoria", value: "mentis_memory · memoria por agente y consolidaciones" },
  { label: "CRM", value: "marketing_leads · señales calificadas por IA" },
  { label: "Seguridad", value: "Canal Discord autorizado + aprobación para trading" },
];

export function WikiView() {
  return (
    <div className="space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <BookOpen className="size-5" />
            </span>
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-neutral-950">Manual Operativo</h2>
              <p className="mt-1 text-sm text-neutral-500">Arranque, comandos de Discord y referencias rápidas para operar PC Agent.</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:min-w-[520px]">
            {dataNotes.map((item) => (
              <div key={item.label} className="rounded-[8px] border border-neutral-200 bg-neutral-50 px-3 py-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-neutral-400">{item.label}</p>
                <p className="mt-1 line-clamp-2 text-xs font-medium leading-5 text-neutral-700">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {quickStart.map((item, index) => (
          <Card key={item.title} className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <span className="flex size-6 items-center justify-center rounded-full bg-neutral-100 text-xs text-neutral-500">{index + 1}</span>
                {item.title}
              </CardTitle>
              <CardDescription className="text-sm leading-6 text-neutral-500">{item.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <code className="block rounded-[8px] bg-neutral-950 px-3 py-2 text-xs font-medium leading-5 text-neutral-100">
                {item.command}
              </code>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
          <CardHeader className="border-b border-neutral-200 px-5 py-4">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
              <Terminal className="size-4 text-[#3ecf8e]" />
              Diccionario de comandos
            </CardTitle>
            <CardDescription className="text-sm text-neutral-500">Comandos agrupados por workflow para encontrarlos rápido durante operación.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-5 lg:grid-cols-2">
            {commandGroups.map((group) => {
              const Icon = group.icon;
              return (
                <div key={group.title} className="rounded-[10px] border border-neutral-200 bg-neutral-50 p-4">
                  <div className="mb-4 flex items-center gap-2">
                    <span className={`flex size-8 items-center justify-center rounded-[8px] ${group.tone}`}>
                      <Icon className="size-4" />
                    </span>
                    <h3 className="text-sm font-semibold text-neutral-950">{group.title}</h3>
                  </div>
                  <div className="space-y-3">
                    {group.commands.map((item) => (
                      <div key={item.command} className="rounded-[8px] border border-neutral-200 bg-white p-3">
                        <code className="rounded-[6px] bg-neutral-100 px-2 py-1 text-xs font-semibold text-neutral-900">{item.command}</code>
                        <p className="mt-2 text-sm font-semibold text-neutral-950">{item.title}</p>
                        <p className="mt-1 text-xs leading-5 text-neutral-500">{item.description}</p>
                        {item.note ? <p className="mt-2 rounded-[6px] bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">{item.note}</p> : null}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <Brain className="size-4 text-[#3ecf8e]" />
                Memoria y conocimiento
              </CardTitle>
              <CardDescription className="text-sm leading-6">
                El worker descarga fuentes, genera embeddings y guarda señales en Supabase. MentisDB sostiene memoria operativa y consolidaciones.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <Database className="size-4 text-[#3ecf8e]" />
                Tablas clave
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {["knowledge_documents", "mentis_memory", "marketing_leads", "whatsapp_campaigns"].map((table) => (
                <div key={table} className="flex items-center gap-2 rounded-[8px] bg-neutral-50 px-3 py-2">
                  <CheckCircle2 className="size-4 text-emerald-600" />
                  <code className="text-xs font-semibold text-neutral-800">{table}</code>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
