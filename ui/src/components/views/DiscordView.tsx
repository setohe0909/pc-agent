import type { FormEvent } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function StateBadge({ state }: { state: string }) {
  const variant = state === "healthy" ? "default" : state === "offline" ? "destructive" : "secondary";
  const tone = state === "healthy"
    ? "bg-[#159947] text-white"
    : state === "offline"
      ? "bg-red-100 text-red-700"
      : "bg-amber-100 text-amber-700";

  return <Badge variant={variant} className={`rounded-[4px] px-2 uppercase text-[10px] ${tone}`}>{state}</Badge>;
}

function DiscordStatusCard({ title, value, state }: { title: string; value: string; state: string }) {
  return (
    <Card className="rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
      <CardHeader className="p-5">
        <div className="mb-6 flex items-center justify-between gap-3">
          <CardTitle className="text-base text-slate-950">{title}</CardTitle>
          <StateBadge state={state} />
        </div>
        <CardDescription className="break-words text-sm text-slate-500">{value}</CardDescription>
      </CardHeader>
    </Card>
  );
}

export function DiscordView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { config } = data;
  const discord = config?.discord || {};
  const control = config?.discord_control || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);
    // Remove empty fields
    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });
    await onSave(payload);
    // Reset token field
    const tokenInput = e.currentTarget.elements.namedItem("discord_bot_token") as HTMLInputElement;
    if (tokenInput) tokenInput.value = "";
  };

  return (
    <div className="w-full space-y-7">
      <div className="grid w-full grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-5">
        <DiscordStatusCard title="Solicitudes" value={discord.requests_channel_id || "Sin configurar"} state={discord.requests_channel_id ? "healthy" : "offline"} />
        <DiscordStatusCard title="Notificaciones" value={discord.notifications_channel_id || "Sin configurar"} state={discord.notifications_channel_id ? "healthy" : "offline"} />
        <DiscordStatusCard title="Estado" value={discord.status_channel_id || "Sin configurar"} state={discord.status_channel_id ? "healthy" : "offline"} />
        <DiscordStatusCard title="Bot" value={control.has_bot_token ? "Token configurado" : "Sin token"} state={control.has_bot_token ? "healthy" : "offline"} />
        <DiscordStatusCard title="Aprobadores" value={control.approver_user_ids || "Sin configurar"} state={control.approver_user_ids ? "healthy" : "offline"} />
      </div>

      <Card className="w-full rounded-[8px] border-white/80 bg-white py-0 shadow-sm ring-1 ring-slate-200/70">
        <CardHeader>
          <CardTitle className="text-slate-950">Configurar Discord</CardTitle>
          <CardDescription className="text-slate-500">Canales y autorizaciones para solicitudes y notificaciones.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="grid grid-cols-1 gap-5 xl:grid-cols-4">
            <div className="space-y-2">
              <Label>Discord Bot Token</Label>
              <Input name="discord_bot_token" type="password" placeholder="Token del bot" autoComplete="off" />
            </div>
            <div className="space-y-2">
              <Label>Canal Solicitudes</Label>
              <Input name="discord_requests_channel_id" defaultValue={discord.requests_channel_id} placeholder="ID del canal" />
            </div>
            <div className="space-y-2">
              <Label>Canal Notificaciones</Label>
              <Input name="discord_notifications_channel_id" defaultValue={discord.notifications_channel_id} placeholder="ID del canal" />
            </div>
            <div className="space-y-2">
              <Label>Canal Estado</Label>
              <Input name="discord_status_channel_id" defaultValue={discord.status_channel_id} placeholder="ID del canal" />
            </div>
            <div className="space-y-2 xl:col-span-3">
              <Label>Usuarios Aprobadores</Label>
              <Input name="discord_approver_user_ids" defaultValue={control.approver_user_ids} placeholder="IDs separados por coma" />
            </div>
            <div className="flex items-end justify-end">
              <Button type="submit">Guardar Discord</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
