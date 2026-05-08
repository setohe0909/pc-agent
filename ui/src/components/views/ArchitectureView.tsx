export function ArchitectureView() {
  return (
    <div className="space-y-6">
      <div className="bg-card border rounded-lg p-6">
        <h3 className="text-lg font-medium mb-2">Arquitectura Docker</h3>
        <p className="text-muted-foreground mb-6">Mapa mental del sistema: entrada, orquestación, conocimiento, memoria y observabilidad.</p>
        
        <div className="grid gap-6">
          <div className="border rounded-lg p-4 bg-background">
            <h4 className="font-semibold mb-3">Entradas Externas</h4>
            <div className="flex flex-wrap gap-4">
              <div className="bg-secondary text-secondary-foreground px-4 py-3 rounded border text-sm font-medium text-center min-w-[120px]">Discord</div>
              <div className="bg-secondary text-secondary-foreground px-4 py-3 rounded border text-sm font-medium text-center min-w-[120px]">UI Web</div>
              <div className="bg-secondary text-secondary-foreground px-4 py-3 rounded border text-sm font-medium text-center min-w-[120px]">Fuentes RSS / Web</div>
            </div>
          </div>
          
          <div className="flex justify-center -my-2 relative z-10">
            <div className="bg-background border border-dashed rounded-full px-4 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Solicitudes · Configuración · Ingestión
            </div>
          </div>

          <div className="border border-primary/30 rounded-lg p-4 bg-primary/5">
            <h4 className="font-semibold mb-3">Servicios Docker Principales</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-background border border-primary/20 px-3 py-4 rounded text-center">
                <div className="font-bold text-sm">ui</div>
                <div className="text-[10px] text-muted-foreground">nginx</div>
              </div>
              <div className="bg-background border border-primary/20 px-3 py-4 rounded text-center">
                <div className="font-bold text-sm">control-api</div>
                <div className="text-[10px] text-muted-foreground">FastAPI</div>
              </div>
              <div className="bg-background border border-primary/20 px-3 py-4 rounded text-center">
                <div className="font-bold text-sm">assistant-runtime</div>
                <div className="text-[10px] text-muted-foreground">decision gate</div>
              </div>
              <div className="bg-background border border-primary/20 px-3 py-4 rounded text-center">
                <div className="font-bold text-sm">discord-bot</div>
                <div className="text-[10px] text-muted-foreground">commands</div>
              </div>
              <div className="bg-background border border-primary/20 px-3 py-4 rounded text-center">
                <div className="font-bold text-sm">ingestion-worker</div>
                <div className="text-[10px] text-muted-foreground">crons</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
            <div className="border rounded-lg p-4 bg-background">
              <h4 className="font-semibold mb-3 text-sm">Conocimiento y Memoria</h4>
              <div className="space-y-3">
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">Supabase remoto</div>
                  <div className="text-[10px] text-muted-foreground">pgvector publico</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">supabase-vector-db</div>
                  <div className="text-[10px] text-muted-foreground">pgvector local</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">MentisDB</div>
                  <div className="text-[10px] text-muted-foreground">memoria operativa</div>
                </div>
              </div>
            </div>

            <div className="border rounded-lg p-4 bg-background">
              <h4 className="font-semibold mb-3 text-sm">Modelos y Embeddings</h4>
              <div className="space-y-3">
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">Ollama</div>
                  <div className="text-[10px] text-muted-foreground">mxbai-embed-large</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">LLM Router</div>
                  <div className="text-[10px] text-muted-foreground">Gemini/GPT</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">Open-Claw</div>
                  <div className="text-[10px] text-muted-foreground">assistant runtime</div>
                </div>
              </div>
            </div>

            <div className="border rounded-lg p-4 bg-background">
              <h4 className="font-semibold mb-3 text-sm">Observabilidad</h4>
              <div className="space-y-3">
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">Langfuse Web</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="font-bold text-sm">Langfuse Worker</div>
                </div>
                <div className="bg-secondary border px-3 py-3 rounded text-center">
                  <div className="text-xs text-muted-foreground font-medium">Postgres · ClickHouse · Valkey · MinIO</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
