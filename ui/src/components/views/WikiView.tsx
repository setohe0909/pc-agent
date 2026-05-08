import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, BookOpen, Brain, Database, ShieldCheck, TerminalSquare } from "lucide-react";

export function WikiView() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Arranque</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Levanta los servicios base con Docker y abre la consola en localhost:8080.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            docker compose up --build
          </code>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2. Configuración</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">En la pestaña Configuración define URLs de assistant-runtime, MentisDB, Langfuse, Ollama y Supabase.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            http://localhost:8100 · http://localhost:9471 · http://localhost:3000
          </code>
        </CardContent>
      </Card>

      <Card className="md:col-span-2 lg:col-span-3 border-blue-500/30 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            Guía de Comandos de Discord
          </CardTitle>
          <CardDescription>Usa estos comandos en el canal de solicitudes autorizado para interactuar con el agente.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <code className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded font-bold">!status</code>
              <span className="text-sm font-medium">Salud del Sistema</span>
            </div>
            <p className="text-xs text-muted-foreground">Consulta el estado proactivo de todos los servicios (Ollama, Gemini, Supabase, Mentis). Úsalo para verificar conectividad.</p>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <code className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded font-bold">!ask [texto]</code>
              <span className="text-sm font-medium">Consulta de Conocimiento</span>
            </div>
            <p className="text-xs text-muted-foreground">Pregunta sobre cualquier tema. El agente buscará en las fuentes vectorizadas en Supabase y MentisDB para responder.</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <code className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded font-bold">!research [tema]</code>
              <span className="text-sm font-medium">Análisis de Tendencias</span>
            </div>
            <p className="text-xs text-muted-foreground">Inicia una investigación profunda sobre mercados o tendencias burstátiles. Útil para identificar oportunidades en Kalshi.</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <code className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded font-bold">!approve_trade [id]</code>
              <span className="text-sm font-medium">Ejecución de Trading</span>
            </div>
            <p className="text-xs text-muted-foreground">Autoriza una operación financiera. Solo funciona si el usuario está en la lista de Aprobadores y en el canal correcto.</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Configuración de Modelos</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Switch dinámico entre proveedores. Si no hay API Key de OpenAI, el sistema busca Ollama.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            DEFAULT_LLM_PROVIDER: gemini | openai | ollama
          </code>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">4. Conocimiento</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Agrega fuentes RSS o website. El worker descarga contenido, genera embeddings con Ollama y guarda en Supabase.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            mxbai-embed-large · 1024 dimensiones
          </code>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">5. Supabase</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">La publishable key permite lectura pública. La escritura requiere service role.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            knowledge_sources · knowledge_documents
          </code>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">6. Seguridad de trading</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">El runtime rechaza decisiones de trading si no vienen del canal Discord autorizado con aprobación.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            DISCORD_REQUESTS_CHANNEL_ID
          </code>
        </CardContent>
      </Card>
    </div>
  );
}
