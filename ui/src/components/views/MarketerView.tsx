import type { FormEvent } from "react";
import { Instagram, Music2, Megaphone, Save, Sparkles, TrendingUp, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function MarketerView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { config, runtime } = data;
  const integrations = config?.integrations || {};
  const currentRuntime = runtime?.runtime || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);
    
    // Cleanup empty strings
    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="flex justify-between items-center bg-card p-4 rounded-lg border sticky top-0 z-20 shadow-sm">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Megaphone className="w-5 h-5 text-pink-500" />
            Marketer Sub-Agent Portal
          </h2>
          <p className="text-xs text-muted-foreground">Configura el comportamiento y conexiones de tu agente de marketing.</p>
        </div>
        <Button type="submit" className="gap-2 shadow-lg bg-pink-600 hover:bg-pink-700">
          <Save className="w-4 h-4" /> Guardar Configuración
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Instagram className="w-5 h-5 text-pink-500" />
              Instagram Business
            </CardTitle>
            <CardDescription>Conecta tu cuenta para responder comentarios y planificar.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Instagram Access Token</Label>
              <Input 
                name="instagram_access_token" 
                type="password" 
                placeholder="EAAB..." 
                defaultValue={currentRuntime.instagram_access_token}
              />
            </div>
            <div className="space-y-2">
              <Label>Instagram Account ID</Label>
              <Input 
                name="instagram_account_id" 
                placeholder="1784..." 
                defaultValue={currentRuntime.instagram_account_id}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Music2 className="w-5 h-5 text-black" />
              TikTok For Business
            </CardTitle>
            <CardDescription>Gestión de contenido y tendencias en TikTok.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>TikTok API Key</Label>
              <Input 
                name="tiktok_api_key" 
                type="password" 
                placeholder="tk_..." 
                defaultValue={currentRuntime.tiktok_api_key}
              />
            </div>
            <div className="space-y-2">
              <Label>TikTok User ID</Label>
              <Input 
                name="tiktok_user_id" 
                placeholder="@username" 
                defaultValue={currentRuntime.tiktok_user_id}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Identidad de Marca & Tono
            </CardTitle>
            <CardDescription>Define cómo debe actuar el agente al interactuar.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label>Tipo de Marca</Label>
              <Select name="marketing_brand_type" defaultValue={currentRuntime.marketing_brand_type || "fashion"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="fashion">Moda / Diseño</SelectItem>
                  <SelectItem value="tech">Tecnología</SelectItem>
                  <SelectItem value="food">Gastronomía</SelectItem>
                  <SelectItem value="service">Servicios</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tono de Respuesta</Label>
              <Select name="marketing_tone" defaultValue={currentRuntime.marketing_tone || "empathetic"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="empathetic">Empático & Positivo</SelectItem>
                  <SelectItem value="professional">Profesional & Serio</SelectItem>
                  <SelectItem value="funny">Divertido & Casual</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Frecuencia de Sondeo</Label>
              <Select name="marketing_poll_frequency" defaultValue={currentRuntime.marketing_poll_frequency || "daily"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Cada hora</SelectItem>
                  <SelectItem value="daily">Diario</SelectItem>
                  <SelectItem value="weekly">Semanal</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 bg-muted/30 border-dashed">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Estado de Operaciones
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="flex items-center gap-2 p-2 rounded bg-background border">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span>Escucha de comentarios: **Activa**</span>
              </div>
              <div className="flex items-center gap-2 p-2 rounded bg-background border">
                <Search className="w-3 h-3 text-muted-foreground" />
                <span>Sondeo de competencia: **En espera**</span>
              </div>
              <div className="flex items-center gap-2 p-2 rounded bg-background border">
                <Megaphone className="w-3 h-3 text-muted-foreground" />
                <span>Última campaña: **Primavera 2026**</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
