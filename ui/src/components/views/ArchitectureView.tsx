import { Server, Brain, Database, ShieldCheck, Activity, PenTool, Megaphone, Layout, Globe, Image as LucideImage } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function ArchitectureView() {
  return (
    <div className="space-y-8 pb-10">
      <div className="bg-card border rounded-xl p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Server className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Orquestación PC Agent Pro</h2>
            <p className="text-muted-foreground">Arquitectura multi-agente distribuida sobre Docker Stack.</p>
          </div>
        </div>

        <div className="grid gap-8 mt-8">
          {/* Capa de Interfaz y Entrada */}
          <div className="border rounded-xl p-5 bg-background shadow-sm border-indigo-500/20">
            <h4 className="font-bold mb-4 flex items-center gap-2 text-indigo-500">
              <Layout className="w-4 h-4" /> Capa de Interfaz y Gateway
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-card border text-center">
                <p className="font-bold text-sm">Discord Bot</p>
                <Badge variant="secondary" className="mt-1 text-[10px]">Command Gateway</Badge>
              </div>
              <div className="p-4 rounded-lg bg-card border text-center">
                <p className="font-bold text-sm">Control UI (8080)</p>
                <Badge variant="secondary" className="mt-1 text-[10px]">React / Nginx</Badge>
              </div>
              <div className="p-4 rounded-lg bg-card border text-center">
                <p className="font-bold text-sm">Obsidian Web (3010)</p>
                <Badge variant="secondary" className="mt-1 text-[10px]">KasmVNC Interface</Badge>
              </div>
            </div>
          </div>

          <div className="flex justify-center -my-4 relative z-10">
            <div className="bg-primary text-primary-foreground rounded-full px-6 py-1 text-xs font-bold uppercase">
              Orquestación de Solicitudes
            </div>
          </div>

          {/* Capa de Inteligencia y Sub-Agentes */}
          <div className="border-2 border-primary/30 rounded-xl p-6 bg-primary/5 shadow-inner">
            <h4 className="font-bold mb-4 flex items-center gap-2 text-primary">
              <Brain className="w-5 h-5" /> Assistant Runtime (FastAPI Engine)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-5 rounded-xl bg-background border-2 border-pink-500/30 shadow-sm">
                <Megaphone className="w-8 h-8 text-pink-500 mb-2" />
                <p className="font-bold">!marketer Agent</p>
                <p className="text-[10px] text-muted-foreground mt-1">Tendencias, Social Sentiment, Leads Qualify.</p>
              </div>
              <div className="p-5 rounded-xl bg-background border-2 border-indigo-500/30 shadow-sm">
                <PenTool className="w-8 h-8 text-indigo-500 mb-2" />
                <p className="font-bold">!writer Agent</p>
                <p className="text-[10px] text-muted-foreground mt-1">Copywriting, Storytelling, SEO, Obsidian Sync.</p>
              </div>
              <div className="p-5 rounded-xl bg-background border-2 border-green-500/30 shadow-sm">
                <Activity className="w-8 h-8 text-green-500 mb-2" />
                <p className="font-bold">Trading Core</p>
                <p className="text-[10px] text-muted-foreground mt-1">Kalshi Gateway, Risk Management, Predictions.</p>
              </div>
            </div>
          </div>

          {/* Capa de Datos y Modelos */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="border rounded-xl p-5 bg-background shadow-sm border-amber-500/20">
              <h4 className="font-bold mb-4 flex items-center gap-2 text-amber-500">
                <Database className="w-4 h-4" /> Datos y Persistencia
              </h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border">
                  <span className="text-xs font-semibold">Supabase (pgvector)</span>
                  <Badge variant="outline">Long-Term Memory</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border">
                  <span className="text-xs font-semibold">MentisDB (Social Memory)</span>
                  <Badge variant="outline">Working Store</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border border-indigo-500/30">
                  <span className="text-xs font-semibold">Obsidian Vault (Volume)</span>
                  <Badge className="bg-indigo-500">Shared Storage</Badge>
                </div>
              </div>
            </div>

            <div className="border rounded-xl p-5 bg-background shadow-sm border-blue-500/20">
              <h4 className="font-bold mb-4 flex items-center gap-2 text-blue-500">
                <Globe className="w-4 h-4" /> Modelos & API
              </h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border">
                  <span className="text-xs font-semibold">Gemini 1.5 Flash</span>
                  <Badge variant="outline" className="text-blue-500 border-blue-200">Main Reasoning</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border">
                  <span className="text-xs font-semibold">Ollama (Local)</span>
                  <Badge variant="outline">Embeddings (1024d)</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-card border border-amber-500/30">
                  <span className="text-xs font-semibold">Unsplash API</span>
                  <Badge className="bg-amber-500"><LucideImage className="w-3 h-3 mr-1" /> Dynamic Visuals</Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Capa de Observabilidad */}
          <div className="border rounded-xl p-5 bg-muted/30 border-dashed">
            <h4 className="font-bold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" /> Stack de Observabilidad (Langfuse)
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-2 rounded bg-background border text-[10px] font-bold">Langfuse Web</div>
              <div className="p-2 rounded bg-background border text-[10px] font-bold">Langfuse Worker</div>
              <div className="p-2 rounded bg-background border text-[10px] font-bold">ClickHouse DB</div>
              <div className="p-2 rounded bg-background border text-[10px] font-bold">Valkey / MinIO</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
