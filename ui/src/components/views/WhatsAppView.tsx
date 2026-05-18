import { useEffect, useState } from "react";
import { MessageCircle, Plus, RefreshCw, Send } from "lucide-react";
import { addWhatsAppContact, createWhatsAppCampaign, getWhatsAppOutreach } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function WhatsAppView({ adminToken }: { adminToken: string }) {
  const [contacts, setContacts] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await getWhatsAppOutreach();
      setContacts(data.contacts || []);
      setCampaigns(data.campaigns || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleContact = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const tags = String(form.get("tags") || "")
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
    await addWhatsAppContact(
      {
        phone_number: form.get("phone_number"),
        display_name: form.get("display_name"),
        source: "ui",
        consent_status: "opted_in",
        tags,
      },
      adminToken,
    );
    event.currentTarget.reset();
    refresh();
  };

  const handleCampaign = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await createWhatsAppCampaign(
      {
        name: form.get("name"),
        message_template: form.get("message_template"),
        target_tag: form.get("target_tag") || null,
      },
      adminToken,
    );
    event.currentTarget.reset();
    refresh();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border bg-card p-4 shadow-sm">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold">
            <MessageCircle className="h-5 w-5 text-emerald-500" />
            WhatsApp Outreach
          </h2>
          <p className="text-xs text-muted-foreground">
            Contactos opt-in y campañas draft para que !marketer pueda operar con OpenWA sin enviar mensajes sin aprobación.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh} disabled={loading} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refrescar
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-md">Nuevo Contacto Opt-in</CardTitle>
            <CardDescription>Solo agrega números con permiso explícito para recibir campañas.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleContact} className="space-y-4">
              <div className="space-y-2">
                <Label>Número</Label>
                <Input name="phone_number" placeholder="+573001112233" required />
              </div>
              <div className="space-y-2">
                <Label>Nombre</Label>
                <Input name="display_name" placeholder="Cliente potencial" />
              </div>
              <div className="space-y-2">
                <Label>Tags</Label>
                <Input name="tags" placeholder="hot, launch, crm" />
              </div>
              <Button type="submit" className="gap-2">
                <Plus className="h-4 w-4" />
                Guardar contacto
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-md">Campaña Draft</CardTitle>
            <CardDescription>La campaña queda guardada para aprobación; no se envía automáticamente.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCampaign} className="space-y-4">
              <div className="space-y-2">
                <Label>Nombre</Label>
                <Input name="name" placeholder="Lanzamiento mayo" required />
              </div>
              <div className="space-y-2">
                <Label>Tag objetivo</Label>
                <Input name="target_tag" placeholder="hot" />
              </div>
              <div className="space-y-2">
                <Label>Mensaje</Label>
                <Input name="message_template" placeholder="Hola {{name}}, tenemos una novedad..." required />
              </div>
              <Button type="submit" className="gap-2">
                <Send className="h-4 w-4" />
                Crear draft
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-md">Contactos</CardTitle>
            <CardDescription>{contacts.length} contactos cargados desde Supabase.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {contacts.length === 0 && <p className="text-sm text-muted-foreground">No hay contactos opt-in todavía.</p>}
            {contacts.map((contact) => (
              <div key={contact.id || contact.phone_number} className="flex items-center justify-between border-b py-3">
                <div>
                  <p className="font-medium">{contact.display_name || contact.phone_number}</p>
                  <p className="text-xs text-muted-foreground">{contact.phone_number}</p>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline">{contact.consent_status}</Badge>
                  {(contact.tags || []).slice(0, 2).map((tag: string) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-md">Campañas</CardTitle>
            <CardDescription>Borradores listos para revisión de !marketer.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {campaigns.length === 0 && <p className="text-sm text-muted-foreground">No hay campañas WhatsApp creadas.</p>}
            {campaigns.map((campaign) => (
              <div key={campaign.id || campaign.name} className="border-b py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium">{campaign.name}</p>
                  <Badge>{campaign.status}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {campaign.recipient_count} destinatarios · tag {campaign.target_tag || "todos"}
                </p>
                <p className="mt-2 line-clamp-2 text-sm">{campaign.message_template}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
