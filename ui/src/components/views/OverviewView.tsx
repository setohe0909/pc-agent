import { Database, Brain, Network } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

function StateBadge({ state }: { state: string }) {
  const variant = state === "healthy" ? "default" : state === "offline" ? "destructive" : "secondary";
  return <Badge variant={variant} className="uppercase text-[10px]">{state}</Badge>;
}

export function OverviewView({ data }: { data: any }) {
  const { status, config, sources, supabase, mentis } = data;

  const services = status?.services || [];
  const healthy = services.filter((s: any) => s.state === "healthy").length;
  const sourcesList = sources?.sources || [];
  const discordConfigured = config?.discord ? [
    config.discord.requests_channel_id,
    config.discord.notifications_channel_id,
    config.discord.status_channel_id,
  ].filter(Boolean).length : 0;

  return (
    <div className="grid gap-6">
      <section className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardDescription>Servicios healthy</CardDescription>
              <CardTitle className="text-2xl">{healthy}/{services.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardDescription>Fuentes activas</CardDescription>
              <CardTitle className="text-2xl">{sourcesList.filter((s:any)=>s.enabled).length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardDescription>Discord</CardDescription>
              <CardTitle className="text-2xl">{discordConfigured}/3 canales</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardDescription>Embedding</CardDescription>
              <CardTitle className="text-2xl text-base">{config?.integrations?.supabase?.embedding_model || "N/A"}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Separator />

        <div>
          <h3 className="text-lg font-medium mb-4">Estado de Servicios</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((s: any) => (
              <Card key={s.name}>
                <CardHeader className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <CardTitle className="text-base">{s.name}</CardTitle>
                    <StateBadge state={s.state} />
                  </div>
                  <CardDescription className="text-xs break-words">{s.detail}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Database className="w-5 h-5"/> Supabase PGVector</CardTitle>
              <CardDescription>Vector store público para conocimiento.</CardDescription>
            </CardHeader>
            <CardContent>
              {supabase ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Estado</span>
                    <StateBadge state={supabase.supabase.knowledge_schema_ready ? "healthy" : supabase.supabase.reachable ? "degraded" : "offline"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Detalle</span>
                    <span className="truncate max-w-[150px]">{supabase.supabase.detail}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">REST Disponible</span>
                    <span>{supabase.supabase.rest_available ? "Sí" : "No"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-muted-foreground">Verificando...</div>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Brain className="w-5 h-5"/> MentisDB</CardTitle>
              <CardDescription>Memoria operacional del asistente.</CardDescription>
            </CardHeader>
            <CardContent>
              {mentis ? (
                <div className="space-y-2 text-sm">
                   <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Estado</span>
                    <StateBadge state={config?.integrations?.mentis_enabled ? (mentis.mentis.reachable ? "healthy" : "offline") : "unknown"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Lectura</span>
                    <span>{mentis.mentis.can_read ? "Sí" : "No"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Escritura</span>
                    <span>{mentis.mentis.can_write ? "Sí" : "No"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-muted-foreground">Verificando...</div>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Network className="w-5 h-5"/> Langfuse</CardTitle>
              <CardDescription>Observabilidad y traces.</CardDescription>
            </CardHeader>
            <CardContent>
              {config ? (
                <div className="space-y-2 text-sm">
                   <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Estado</span>
                    <StateBadge state={config.integrations.langfuse_enabled ? "healthy" : "unknown"} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Host</span>
                    <span className="truncate max-w-[150px]">{config.integrations.langfuse || "N/A"}</span>
                  </div>
                </div>
              ) : <div className="text-sm text-muted-foreground">Verificando...</div>}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
