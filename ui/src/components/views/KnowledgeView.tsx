import type { FormEvent } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { addKnowledgeSource, saveIngestionSchedule, triggerIngestionRun } from "@/lib/api";

function StateBadge({ state }: { state: string }) {
  const variant = state === "healthy" ? "default" : state === "offline" ? "destructive" : "secondary";
  return <Badge variant={variant} className="uppercase text-[10px]">{state}</Badge>;
}

export function KnowledgeView({ data, adminToken, onRefresh }: { data: any, adminToken: string, onRefresh: () => void }) {
  const { sources, ingestion } = data;
  const sourcesList = sources?.sources || [];
  const schedule = ingestion?.schedule || {};
  const runs = ingestion?.runs || [];

  const handleAddSource = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);
    payload.enabled = true;
    try {
      await addKnowledgeSource(payload, adminToken);
      onRefresh();
      (e.target as HTMLFormElement).reset();
    } catch (err: any) {
      alert("Error agregando fuente: " + err.message);
    }
  };

  const handleSaveSchedule = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData);
    try {
      await saveIngestionSchedule(payload, adminToken);
      onRefresh();
    } catch (err: any) {
      alert("Error guardando crons: " + err.message);
    }
  };

  const handleTriggerRun = async (target: string) => {
    try {
      await triggerIngestionRun(target, adminToken);
      onRefresh();
    } catch (err: any) {
      alert("Error ejecutando run: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Crons de Ingestión</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveSchedule} className="space-y-4">
              <div className="space-y-2">
                <Label>Mercados Kalshi</Label>
                <Input name="market_ingestion_cron" defaultValue={schedule.market_ingestion_cron} placeholder="0 */2 * * *" />
              </div>
              <div className="space-y-2">
                <Label>Tendencias</Label>
                <Input name="trends_ingestion_cron" defaultValue={schedule.trends_ingestion_cron} placeholder="15 */4 * * *" />
              </div>
              <div className="space-y-2">
                <Label>Sync MentisDB</Label>
                <Input name="mentis_sync_cron" defaultValue={schedule.mentis_sync_cron} placeholder="30 */2 * * *" />
              </div>
              <div className="flex justify-end">
                <Button type="submit">Guardar Crons</Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Runs Manuales</CardTitle>
            <CardDescription>Ejecutar procesos de ingestión inmediatamente</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Button onClick={() => handleTriggerRun("markets")} variant="secondary">Mercados</Button>
              <Button onClick={() => handleTriggerRun("trends")} variant="secondary">Tendencias</Button>
              <Button onClick={() => handleTriggerRun("mentis")} variant="secondary">MentisDB</Button>
              <Button onClick={() => handleTriggerRun("all")}>Todo</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Agregar Fuente</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddSource} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2 lg:col-span-1">
              <Label>Nombre</Label>
              <Input name="name" required placeholder="Ej. Kalshi Fed markets" />
            </div>
            <div className="space-y-2 lg:col-span-1">
              <Label>Tipo</Label>
              <Select name="source_type" defaultValue="kalshi_market">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="kalshi_market">Kalshi market</SelectItem>
                  <SelectItem value="trend">Trend</SelectItem>
                  <SelectItem value="rss">RSS</SelectItem>
                  <SelectItem value="website">Website</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 lg:col-span-1">
              <Label>URL</Label>
              <Input name="url" placeholder="https://..." />
            </div>
            <div className="space-y-2 lg:col-span-1">
              <Label>Cron</Label>
              <Input name="schedule" placeholder="0 */2 * * *" />
            </div>
            <div className="lg:col-span-4 flex justify-end">
              <Button type="submit">Agregar Fuente</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div>
        <h3 className="text-lg font-medium mb-4">Fuentes Registradas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sourcesList.length > 0 ? sourcesList.map((source: any) => (
            <Card key={source.name}>
              <CardHeader className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <CardTitle className="text-base truncate" title={source.name}>{source.name}</CardTitle>
                  <StateBadge state={source.enabled ? "healthy" : "offline"} />
                </div>
                <CardDescription className="text-xs truncate">{source.source_type} · {source.schedule || "sin cron"}</CardDescription>
                <div className="text-xs text-muted-foreground truncate mt-2">{source.url || "Sin URL"}</div>
              </CardHeader>
            </Card>
          )) : (
            <div className="text-muted-foreground text-sm">No hay fuentes registradas.</div>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-4">Historial de Ejecuciones</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {runs.length > 0 ? runs.map((run: any, idx: number) => (
            <Card key={idx}>
              <CardHeader className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <CardTitle className="text-base truncate uppercase">{run.target}</CardTitle>
                  <StateBadge state={run.status === "queued" ? "unknown" : run.status} />
                </div>
                <CardDescription className="text-xs">{run.started_at}</CardDescription>
                <div className="text-xs text-muted-foreground mt-2 truncate">{run.detail}</div>
              </CardHeader>
            </Card>
          )) : (
            <div className="text-muted-foreground text-sm">Todavía no hay ejecuciones registradas.</div>
          )}
        </div>
      </div>
    </div>
  );
}
