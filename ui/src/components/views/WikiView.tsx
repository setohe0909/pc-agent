import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Globe, LayoutGrid, Megaphone, PenTool, Files } from "lucide-react";

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
                    <LayoutGrid className="h-4 w-4" /> Trading Pro (Dual Agent)
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!approve_trade [instrucción]</strong></p>
                  <p className="text-muted-foreground">Inicia el flujo de ejecución real en Kalshi.</p>
                  <div className="bg-background/50 p-2 rounded mt-2 font-mono text-[10px]">
                    Ej: !approve_trade Compra 5 contratos YES en el mercado de tasas de la FED
                  </div>
                  <ul className="list-disc pl-4 mt-2 text-muted-foreground">
                    <li>Pasa por validación de balance.</li>
                    <li>Requiere aprobación del Agente Crítico.</li>
                    <li>Genera Embed visual en Discord.</li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-muted/30 border-pink-500/20">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2 text-pink-500">
                    <Megaphone className="h-4 w-4" /> Marketing Sub-Agent
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!marketer memory</strong></p>
                  <p className="text-muted-foreground">Muestra los aprendizajes y hallazgos recientes del sub-agente.</p>
                  <p><strong>!marketer respond</strong></p>
                  <p className="text-muted-foreground">Responde comentarios en Instagram con un tono empático.</p>
                  <p><strong>!marketer qualify</strong></p>
                  <p className="text-muted-foreground">Analiza interacciones para detectar leads de alta intención (Hot Leads).</p>
                  <p><strong>!marketer magnet</strong></p>
                  <p className="text-muted-foreground">Envía recursos (guías, catálogos) automáticamente por DM basado en palabras clave.</p>
                  <p><strong>!marketer funnel [tema]</strong></p>
                  <p className="text-muted-foreground">Diseña una estrategia de embudo de ventas (TOFU, MOFU, BOFU).</p>
                  <p><strong>!marketer trends</strong></p>
                  <p className="text-muted-foreground">Detecta tendencias virales en TikTok/IG y sugiere contenido adaptado.</p>
                  <p><strong>!marketer sentiment</strong></p>
                  <p className="text-muted-foreground">Analiza el tono de la comunidad y alerta sobre posibles crisis de reputación.</p>
                  <p><strong>!marketer collab [marca]</strong></p>
                  <p className="text-muted-foreground">Identifica micro-influencers y marcas para colaboraciones estratégicas.</p>
                  <p><strong>!marketer plan [tema]</strong></p>
                  <p className="text-muted-foreground">Planifica campañas basadas en tendencias e insights de diseño.</p>
                  <p><strong>!marketer research [competidor]</strong></p>
                  <p className="text-muted-foreground">Analiza la competencia y propone estrategias de superación.</p>
                  <p><strong>!marketer-status</strong></p>
                  <p className="text-muted-foreground">Verifica conexión con Instagram Business y TikTok API.</p>
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
                    <Camera className="h-4 w-4" /> Picture Sub-Agent (DALL-E 3)
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-xs space-y-2">
                  <p><strong>!picture [descripción]</strong></p>
                  <p className="text-muted-foreground">Genera una imagen usando memoria proactiva y hilos de conversación.</p>
                  <p><strong>!picture memory</strong></p>
                  <p className="text-muted-foreground">Ver estilos y preferencias visuales consolidadas.</p>
                  <p><strong>!picture memory --clean</strong></p>
                  <p className="text-muted-foreground">Limpia la memoria operativa de imágenes.</p>
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
