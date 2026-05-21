import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Bell,
  Bot,
  CheckCircle2,
  Hash,
  KeyRound,
  MessageSquare,
  Save,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function StateBadge({ state }: { state: string }) {
  const tone = state === "healthy"
    ? "bg-emerald-50 text-emerald-700 ring-emerald-100"
    : "bg-red-50 text-red-700 ring-red-100";

  return <Badge className={`rounded-full px-2.5 py-1 text-[10px] uppercase ring-1 hover:bg-inherit ${tone}`}>{state}</Badge>;
}

function DiscordStatusCard({ title, value, state, icon: Icon }: { title: string; value: string; state: string; icon: LucideIcon }) {
  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="p-4">
        <div className="mb-4 flex items-center justify-between gap-3">
          <span className="flex size-8 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
            <Icon className="size-4" />
          </span>
          <StateBadge state={state} />
        </div>
        <CardTitle className="text-base font-semibold text-neutral-950">{title}</CardTitle>
        <CardDescription className="mt-2 break-words text-sm text-neutral-500">{value}</CardDescription>
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

    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);

    const tokenInput = e.currentTarget.elements.namedItem("discord_bot_token") as HTMLInputElement;
    if (tokenInput) tokenInput.value = "";
  };

  const statusCards = [
    { title: "Solicitudes", value: discord.requests_channel_id || "Sin configurar", state: discord.requests_channel_id ? "healthy" : "offline", icon: MessageSquare },
    { title: "Notificaciones", value: discord.notifications_channel_id || "Sin configurar", state: discord.notifications_channel_id ? "healthy" : "offline", icon: Bell },
    { title: "Estado", value: discord.status_channel_id || "Sin configurar", state: discord.status_channel_id ? "healthy" : "offline", icon: Hash },
    { title: "Bot", value: control.has_bot_token ? "Token configurado" : "Sin token", state: control.has_bot_token ? "healthy" : "offline", icon: Bot },
    { title: "Aprobadores", value: control.approver_user_ids || "Sin configurar", state: control.approver_user_ids ? "healthy" : "offline", icon: Users },
  ];

  return (
    <div className="w-full space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Bot className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Discord Control Plane</h2>
                <Badge className="rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-50">Bot Ops</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">Canales, aprobaciones y configuración operacional del bot.</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-[8px] bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100">
            <CheckCircle2 className="size-4" />
            Control plane activo
          </div>
        </div>
      </section>

      <div className="grid w-full grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {statusCards.map((card) => (
          <DiscordStatusCard key={card.title} {...card} />
        ))}
      </div>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
          <CardHeader className="border-b border-neutral-200 px-5 py-4">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
              <ShieldCheck className="size-4 text-neutral-700" />
              Configurar Discord
            </CardTitle>
            <CardDescription className="text-sm text-neutral-500">Canales y autorizaciones para solicitudes, notificaciones y aprobaciones.</CardDescription>
          </CardHeader>
          <CardContent className="p-5">
            <form onSubmit={handleSave} className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Field label="Discord Bot Token">
                <Input name="discord_bot_token" type="password" placeholder="Token del bot" autoComplete="off" className="discord-input" />
              </Field>
              <Field label="Canal solicitudes">
                <Input name="discord_requests_channel_id" defaultValue={discord.requests_channel_id} placeholder="ID del canal" className="discord-input" />
              </Field>
              <Field label="Canal notificaciones">
                <Input name="discord_notifications_channel_id" defaultValue={discord.notifications_channel_id} placeholder="ID del canal" className="discord-input" />
              </Field>
              <Field label="Canal estado">
                <Input name="discord_status_channel_id" defaultValue={discord.status_channel_id} placeholder="ID del canal" className="discord-input" />
              </Field>
              <div className="lg:col-span-2">
                <Field label="Usuarios aprobadores">
                  <Input name="discord_approver_user_ids" defaultValue={control.approver_user_ids} placeholder="IDs separados por coma" className="discord-input" />
                </Field>
              </div>
              <div className="flex justify-end lg:col-span-2">
                <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
                  <Save className="size-4" />
                  Guardar Discord
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <KeyRound className="size-4 text-[#3ecf8e]" />
                Seguridad
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Resumen de permisos sensibles del bot.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              <InfoRow label="Token bot" value={control.has_bot_token ? "Configurado" : "Pendiente"} />
              <InfoRow label="Aprobadores" value={control.approver_user_ids ? "Definidos" : "Pendientes"} />
              <InfoRow label="Solicitudes" value={discord.requests_channel_id ? "Enrutadas" : "Sin canal"} />
            </CardContent>
          </Card>
        </aside>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold text-neutral-900">{label}</Label>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      <span className="text-xs font-semibold text-neutral-950">{value}</span>
    </div>
  );
}
