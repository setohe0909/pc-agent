import { Mail, ShieldCheck, Tags, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function EmailView({ data }: { data: any }) {
  const email = data.config?.integrations?.email || {};
  const templates = readTemplates(data.runtime?.runtime?.email_templates);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border bg-card p-4 shadow-sm">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold">
            <Mail className="h-5 w-5 text-sky-600" />
            Email Sub-Agent
          </h2>
          <p className="text-xs text-muted-foreground">
            Lectura, categorias y respuestas bulk controladas desde proveedores configurados en Runtime Settings.
          </p>
        </div>
        <Badge variant={email.provider && email.provider !== "not_configured" ? "default" : "outline"}>
          {email.provider || "not_configured"}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-md">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Proveedor
            </CardTitle>
            <CardDescription>Estado de conexion y permisos.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <StatusRow label="Cuenta" value={email.account_id || "Sin cuenta"} />
            <StatusRow label="Lectura" value={providerReady(email) ? "Lista" : "Pendiente"} />
            <StatusRow label="Envio" value={email.send_enabled ? "Con aprobacion" : "Bloqueado"} />
            <StatusRow label="Limite bulk" value={`${email.bulk_rate_limit || 30}/min`} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-md">
              <Tags className="h-4 w-4 text-sky-600" />
              Categorias
            </CardTitle>
            <CardDescription>Uso desde Discord.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Command text="!email categorize lead" />
            <Command text="!email categorize soporte" />
            <Command text="!email sent-today" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-md">
              <Send className="h-4 w-4 text-indigo-600" />
              Templates
            </CardTitle>
            <CardDescription>{templates.length} templates disponibles.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {templates.length === 0 ? (
              <p className="text-muted-foreground">Crea templates en Configuracion &gt; Email.</p>
            ) : (
              templates.slice(0, 6).map((template: any) => (
                <div key={template.name} className="rounded-md border p-3">
                  <p className="font-medium">{template.name}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{template.category || "sin categoria"}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b py-2 last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function Command({ text }: { text: string }) {
  return <code className="block rounded-md bg-muted px-3 py-2 text-xs">{text}</code>;
}

function providerReady(email: any) {
  return Boolean(email.has_google_oauth || email.has_outlook_oauth || email.has_imap_smtp || email.has_pc_client_bridge);
}

function readTemplates(value: any) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}
