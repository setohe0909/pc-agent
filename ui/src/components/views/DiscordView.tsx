import type { FormEvent } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function StateBadge({ state }: { state: string }) {
  const variant = state === "healthy" ? "default" : state === "offline" ? "destructive" : "secondary";
  return <Badge variant={variant} className="uppercase text-[10px]">{state}</Badge>;
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
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-base">Solicitudes</CardTitle>
              <StateBadge state={discord.requests_channel_id ? "healthy" : "offline"} />
            </div>
            <CardDescription className="text-xs break-words">{discord.requests_channel_id || "Sin configurar"}</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-base">Notificaciones</CardTitle>
              <StateBadge state={discord.notifications_channel_id ? "healthy" : "offline"} />
            </div>
            <CardDescription className="text-xs break-words">{discord.notifications_channel_id || "Sin configurar"}</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-base">Estado</CardTitle>
              <StateBadge state={discord.status_channel_id ? "healthy" : "offline"} />
            </div>
            <CardDescription className="text-xs break-words">{discord.status_channel_id || "Sin configurar"}</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-base">Bot</CardTitle>
              <StateBadge state={control.has_bot_token ? "healthy" : "offline"} />
            </div>
            <CardDescription className="text-xs break-words">{control.has_bot_token ? "Token configurado" : "Sin token"}</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CardTitle className="text-base">Aprobadores</CardTitle>
              <StateBadge state={control.approver_user_ids ? "healthy" : "offline"} />
            </div>
            <CardDescription className="text-xs break-words">{control.approver_user_ids || "Sin configurar"}</CardDescription>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configurar Discord</CardTitle>
          <CardDescription>Canales y autorizaciones para solicitudes y notificaciones.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            <div className="space-y-2 md:col-span-2">
              <Label>Usuarios Aprobadores</Label>
              <Input name="discord_approver_user_ids" defaultValue={control.approver_user_ids} placeholder="IDs separados por coma" />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button type="submit">Guardar Discord</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
