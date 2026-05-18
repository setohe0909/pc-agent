import { Server, Database, ShieldCheck, Activity, PenTool, Megaphone, Globe, RefreshCw, MessageSquare, Box, Network, Layers, Cpu } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function ArchitectureView() {
  return (
    <div className="space-y-8 pb-10">
      <div className="bg-card border rounded-xl p-8 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Network className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h2 className="text-3xl font-black tracking-tight">ARQUITECTURA TOTAL PC AGENT</h2>
              <p className="text-muted-foreground font-medium">Orquestación de 14 contenedores Docker, Flujos de Comunicación y Stack de IA.</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <Badge className="bg-green-500 text-white animate-pulse">SYSTEM CLUSTER: ONLINE</Badge>
            <span className="text-[10px] font-mono text-muted-foreground">Network: assistant-network (Bridge)</span>
          </div>
        </div>

        <div className="grid gap-10">
          
          {/* 01. CAPA DE ENTRADA Y GATEWAY */}
          <section className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-widest text-indigo-500 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> 01. Gateway Layer (Interacción Externa)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-6 rounded-xl bg-indigo-500/5 border-2 border-indigo-500/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2"><Badge className="bg-indigo-500">Discord Bot Service</Badge></div>
                <p className="font-bold text-lg mb-2">Discord Bot (Python/Nextcord)</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  <strong>Función:</strong> Interfaz humana principal. Recibe comandos (!writer, !marketer, !trade) via WebSockets desde Discord Gateway.<br/>
                  <strong>Comunicación:</strong> Actúa como cliente HTTP enviando el payload al <code className="bg-indigo-100 text-indigo-700 px-1 rounded">assistant-runtime:8100</code>.
                </p>
              </div>
              <div className="p-6 rounded-xl bg-indigo-500/5 border-2 border-indigo-500/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2"><Badge className="bg-indigo-500">Admin Gateway</Badge></div>
                <p className="font-bold text-lg mb-2">Control UI & API (React + FastAPI)</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  <strong>Función:</strong> Gestión de estado, configuración y monitoreo visual.<br/>
                  <strong>Comunicación:</strong> La UI consume la <code className="bg-indigo-100 text-indigo-700 px-1 rounded">control-api:8000</code>, que persiste cambios en MentisDB y lee logs de contenedores.
                </p>
              </div>
            </div>
          </section>

          {/* 02. CAPA DE LÓGICA Y ORQUESTACIÓN */}
          <section className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-widest text-primary flex items-center gap-2">
              <Cpu className="w-4 h-4" /> 02. Logic Layer (Procesamiento Distribuido)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-primary/5 border-2 border-primary/20">
                <div className="flex items-center gap-2 mb-3">
                  <Box className="w-5 h-5 text-primary" />
                  <p className="font-black text-sm">assistant-runtime</p>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  <strong>El Orquestador:</strong> Recibe solicitudes del Bot, consulta la memoria (Supabase) y delega tareas a los sub-agentes.<br/>
                  <strong>Comunicación:</strong> Bridge central entre LLMs (Gemini/Ollama) y servicios de persistencia.
                </p>
              </div>
              <div className="p-4 rounded-xl bg-amber-500/5 border-2 border-amber-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <RefreshCw className="w-5 h-5 text-amber-500" />
                  <p className="font-black text-sm">ingestion-worker</p>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  <strong>El Recolector (Crons):</strong> Ejecuta tareas programadas cada 15m. Consume <strong>Tavily API</strong> para noticias y <strong>Kalshi API</strong> para mercados.<br/>
                  <strong>Acción:</strong> Genera embeddings vía Ollama y los guarda en Supabase.
                </p>
              </div>
              <div className="p-4 rounded-xl bg-green-500/5 border-2 border-green-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <Server className="w-5 h-5 text-green-500" />
                  <p className="font-black text-sm">control-api</p>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  <strong>El Puente de Datos:</strong> Centraliza el acceso a MentisDB para la UI y gestiona el ciclo de vida de los tokens de las APIs externas.
                </p>
              </div>
            </div>
          </section>

          {/* 03. SUB-AGENTES ESPECIALIZADOS */}
          <section className="space-y-4 bg-muted/30 p-6 rounded-2xl border border-dashed">
            <h3 className="text-xs font-black uppercase tracking-widest flex items-center gap-2">
              <Layers className="w-4 h-4" /> 03. Agent Layer (Especialización)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2"><Megaphone className="w-4 h-4 text-pink-500" /><p className="font-bold text-xs">!marketer (Social)</p></div>
                <p className="text-[10px] text-muted-foreground">Analiza tendencias de Tavily en MentisDB para gestionar Instagram/TikTok y cualificar leads.</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2"><PenTool className="w-4 h-4 text-indigo-500" /><p className="font-bold text-xs">!writer (Obsidian)</p></div>
                <p className="text-[10px] text-muted-foreground">Genera blogs optimizados sincronizando con el contenedor de Obsidian via Shared Volume.</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2"><Activity className="w-4 h-4 text-green-500" /><p className="font-bold text-xs">Trader (Execution)</p></div>
                <p className="text-[10px] text-muted-foreground">Cruza insights de Tavily con el Orderbook de Kalshi para proponer trades automáticos en Discord.</p>
              </div>
            </div>
          </section>

          {/* 04. PERSISTENCIA Y VOLÚMENES */}
          <section className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-widest text-amber-600 flex items-center gap-2">
              <Database className="w-4 h-4" /> 04. Persistence Layer (Storage Mesh)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border bg-background">
                <p className="text-[10px] font-bold text-amber-600 mb-2">SUPABASE (pgvector)</p>
                <p className="text-[10px] text-muted-foreground">Base de datos de largo plazo para RAG. Dockerizado o remoto.</p>
              </div>
              <div className="p-4 rounded-xl border bg-background border-indigo-500/30">
                <p className="text-[10px] font-bold text-indigo-500 mb-2">OBSIDIAN / VAULT</p>
                <p className="text-[10px] text-muted-foreground">Persistencia física de documentos. Contenedor visual en puerto 3010 y volumen montado en <code className="text-[9px]">/vault</code>.</p>
              </div>
              <div className="p-4 rounded-xl border bg-background">
                <p className="text-[10px] font-bold text-blue-500 mb-2">MENTISDB (Valkey)</p>
                <p className="text-[10px] text-muted-foreground">Memoria social y operativa de baja latencia para insights diarios.</p>
              </div>
            </div>
          </section>

          {/* 05. OBSERVABILIDAD (LANGFUSE STACK) */}
          <section className="p-6 rounded-[8px] border border-green-200 bg-green-50 text-slate-950 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2 text-green-800">
                <ShieldCheck className="w-5 h-5 text-green-600" /> 05. Observability (Langfuse 5-Container Stack)
              </h3>
              <Badge variant="outline" className="border-green-300 text-green-800">Full Traceability</Badge>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="p-2 border border-green-200 bg-white rounded text-center"><p className="text-[9px] font-black">LF Web</p></div>
              <div className="p-2 border border-green-200 bg-white rounded text-center"><p className="text-[9px] font-black">LF Worker</p></div>
              <div className="p-2 border border-green-200 bg-white rounded text-center"><p className="text-[9px] font-black">ClickHouse</p></div>
              <div className="p-2 border border-green-200 bg-white rounded text-center"><p className="text-[9px] font-black">Postgres (LF)</p></div>
              <div className="p-2 border border-green-200 bg-white rounded text-center"><p className="text-[9px] font-black">Valkey Cache</p></div>
            </div>
            <p className="text-[9px] text-green-800 mt-2 italic text-center">Monitorea costos, latencia y trazas de cada llamada a Gemini/Ollama.</p>
          </section>

          {/* 06. APIS DE TERCEROS */}
          <section className="space-y-4">
            <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
              <Globe className="w-4 h-4" /> 06. External Cloud Mesh (APIs & LLMs)
            </h3>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">Gemini 1.5 (Cerebro)</Badge>
              <Badge variant="secondary">Ollama (Embeddings Locales)</Badge>
              <Badge className="bg-orange-500 text-white">Tavily (Scraping AI)</Badge>
              <Badge className="bg-blue-600 text-white">Kalshi (Predictive Markets)</Badge>
              <Badge className="bg-pink-600 text-white">Instagram Graph</Badge>
              <Badge className="bg-teal-500 text-white">Unsplash (Media)</Badge>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
