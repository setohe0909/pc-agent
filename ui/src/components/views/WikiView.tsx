import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">3. Discord</CardTitle>
        </CardHeader>
        <CardContent>
          <CardDescription className="mb-4">Configura token, canales y aprobadores. Las decisiones de trading solo pasan por Discord.</CardDescription>
          <code className="bg-secondary text-secondary-foreground text-xs p-2 rounded block break-words font-mono">
            !ask · !research · !approve_trade
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
