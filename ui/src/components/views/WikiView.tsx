import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Globe, Megaphone, PenTool, Brain, ShieldCheck } from "lucide-react";

export function WikiView() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1. Arranque v0.5.0</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Levanta el ecosistema de agentes autónomos con Docker Compose.</CardDescription>
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
          <CardDescription className="mb-4">Define URLs de servicios. Para Obsidian usa el puerto 3010 y el volumen compartido /vault.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            RT: 8100 · Obsidian: 3010 · LF: 3000
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

          <section className="space-y-4">
            <h3 className="text-xl font-semibold text-primary">Diccionario de Comandos (Discord)</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-muted/30">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Activity className="h-4 w-4" /> Sistemas
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!status</strong></p>
                  <p className="text-muted-foreground">Muestra el estado de salud de todos los microservicios (Ollama, API, Runtime, DB).</p>
                </CardContent>
              </Card>

              <Card className="bg-muted/30">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Globe className="h-4 w-4" /> Inteligencia
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!ask [pregunta]</strong></p>
                  <p className="text-muted-foreground">Consulta rápida al asistente usando el contexto actual.</p>
                  <p><strong>!research [tema]</strong></p>
                  <p className="text-muted-foreground">Búsqueda profunda en fuentes externas y memoria vectorial (RAG).</p>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-primary/20">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2 text-primary">
                    <ShieldCheck className="h-4 w-4" /> Trading Live (Demo)
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!approve_trade [instrucción]</strong></p>
                  <p className="text-muted-foreground">Inicia el flujo de ejecución en Kalshi Live (Modo Demo).</p>
                  <div className="bg-background/50 p-2 rounded mt-2 font-mono text-[10px]">
                    Límite de seguridad: $10.00 USD por operación.
                  </div>
                  <ul className="list-disc pl-4 mt-2 text-muted-foreground">
                    <li>Validación de balance en tiempo real.</li>
                    <li>Requiere aprobación dual (Humano + Crítico).</li>
                    <li>Registro de auditoría en Supabase.</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-pink-500/20">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2 text-pink-500">
                    <Megaphone className="h-4 w-4" /> Marketing (LangGraph + Vision)
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!marketer [petición con imagen]</strong></p>
                  <p className="text-muted-foreground">Analiza imágenes con <strong>Gemini Vision</strong> y planifica campañas autónomas.</p>
                  <p><strong>!marketer qualify</strong></p>
                  <p className="text-muted-foreground"><strong>Lead Auto-Pilot:</strong> Detecta y guarda leads automáticamente en el CRM.</p>
                  <p><strong>!marketer plan [tema]</strong></p>
                  <p className="text-muted-foreground">Flujo con <strong>Agente Crítico</strong> y refinamiento de voz de marca.</p>
                  <div className="bg-pink-500/10 p-2 rounded text-[10px] text-pink-400">
                    Nodos: Intent → Vision → Critic → Voice → Execution
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-indigo-500/20">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2 text-indigo-500">
                    <PenTool className="h-4 w-4" /> Writer Sub-Agent (Obsidian)
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!writer blog [es/en] [tema]</strong></p>
                  <p className="text-muted-foreground">Genera un blog optimizado y lo guarda en la carpeta /Blog de Obsidian.</p>
                  <p><strong>!writer story [es/en] [tema]</strong></p>
                  <p className="text-muted-foreground">Genera una narrativa de marca y la guarda en /Story-telling.</p>
                  <p><strong>!writer [mensaje]</strong></p>
                  <p className="text-muted-foreground">Chat directo con el redactor para lluvia de ideas creativa.</p>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-amber-500/20">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2 text-amber-500">
                    <Brain className="h-4 w-4" /> Inteligencia Proactiva
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!memory</strong></p>
                  <p className="text-muted-foreground">Ver tendencias y memorias operativas del día.</p>
                  <p><strong>!run consolidation</strong></p>
                  <p className="text-muted-foreground">Fuerza la <strong>Consolidación Diaria</strong> de aprendizajes.</p>
                  <p><strong>!memory --clean</strong></p>
                  <p className="text-muted-foreground">Limpia la memoria operativa (MentisDB).</p>
                </CardContent>
              </Card>
            </div>
          </section>
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
          <CardTitle className="text-lg">5. Supabase & CRM</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Almacenamiento vectorial y base de datos de leads calificados por la IA.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            knowledge · mentis_memory · marketing_leads
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
