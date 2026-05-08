import { Activity, Database, Globe, Key, LayoutGrid, Save, Server } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function ConfigView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { config } = data;
  const integrations = config?.integrations || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);
    
    // Type coercions
    if (payload.embedding_dimensions) payload.embedding_dimensions = Number(payload.embedding_dimensions);
    if (payload.mentis_enabled === "true") payload.mentis_enabled = true;
    if (payload.mentis_enabled === "false") payload.mentis_enabled = false;
    if (payload.langfuse_enabled === "true") payload.langfuse_enabled = true;
    if (payload.langfuse_enabled === "false") payload.langfuse_enabled = false;
    
    // API Keys mapping
    if (payload.openai_api_key) payload.openai_api_key = payload.openai_api_key;
    if (payload.gemini_api_key) payload.gemini_api_key = payload.gemini_api_key;
    // Remove empty strings so we don't override with empties if backend expects omission
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
            <LayoutGrid className="w-5 h-5 text-primary" />
            Centro de Configuración
          </h2>
          <p className="text-xs text-muted-foreground">Gestiona la infraestructura y llaves de tu agente.</p>
        </div>
        <Button type="submit" className="gap-2 shadow-lg">
          <Save className="w-4 h-4" /> Guardar Cambios
        </Button>
      </div>

      <Tabs defaultValue="core" className="w-full">
        <TabsList className="grid grid-cols-4 w-full h-12 bg-muted/50 p-1">
          <TabsTrigger value="core" className="gap-2">
            <Server className="w-4 h-4" /> Infraestructura
          </TabsTrigger>
          <TabsTrigger value="ai" className="gap-2">
            <Brain className="w-4 h-4" /> Modelos e IA
          </TabsTrigger>
          <TabsTrigger value="data" className="gap-2">
            <Database className="w-4 h-4" /> Datos y RAG
          </TabsTrigger>
          <TabsTrigger value="trading" className="gap-2">
            <Activity className="w-4 h-4" /> Trading
          </TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <TabsContent value="core" className="space-y-4 outline-none">
            <Card>
              <CardHeader>
                <CardTitle className="text-md">Servicios Core</CardTitle>
                <CardDescription>URLs de conexión para los microservicios de Docker.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Assistant Runtime URL</Label>
                  <Input name="open_claw_base_url" defaultValue={integrations.open_claw} placeholder="http://assistant-runtime:8100" />
                  <p className="text-[10px] text-muted-foreground italic">Por defecto: http://assistant-runtime:8100</p>
                </div>
                <div className="space-y-2">
                  <Label>Ollama URL</Label>
                  <Input name="ollama_base_url" defaultValue={integrations.ollama} placeholder="http://ollama:11434" />
                  <p className="text-[10px] text-muted-foreground italic">Usa host.docker.internal:11434 para usar Ollama Desktop.</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-md">Observabilidad (Langfuse)</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Estado del Servicio</Label>
                  <Select name="langfuse_enabled" defaultValue={String(integrations.langfuse_enabled)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="false">Desactivado</SelectItem>
                      <SelectItem value="true">Activo (Trazas habilitadas)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Langfuse Host</Label>
                  <Input name="langfuse_host" defaultValue={integrations.langfuse} placeholder="http://langfuse-web:3000" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai" className="space-y-4 outline-none">
            <Card>
              <CardHeader>
                <CardTitle className="text-md">Proveedores de LLM</CardTitle>
                <CardDescription>Configura tus llaves de API. El sistema prioriza Gemini si está configurado.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Label>Gemini API Key</Label>
                      <StatusBadge active={integrations.gemini_api_key_configured} />
                    </div>
                    <Input name="gemini_api_key" type="password" placeholder="AIza..." />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Label>OpenAI API Key</Label>
                      <StatusBadge active={integrations.openai_api_key_configured} />
                    </div>
                    <Input name="openai_api_key" type="password" placeholder="sk-..." />
                  </div>
                </div>

                <div className="pt-4 border-t grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Label>Langfuse Public Key</Label>
                      <StatusBadge active={integrations.langfuse_public_key_configured} />
                    </div>
                    <Input name="langfuse_public_key" type="password" placeholder="pk-lf-..." />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <Label>Langfuse Secret Key</Label>
                      <StatusBadge active={integrations.langfuse_secret_key_configured} />
                    </div>
                    <Input name="langfuse_secret_key" type="password" placeholder="sk-lf-..." />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="data" className="space-y-4 outline-none">
            <Card>
              <CardHeader>
                <CardTitle className="text-md">Supabase & Vector Store</CardTitle>
                <CardDescription>Almacenamiento de largo plazo para el conocimiento del agente.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 gap-4">
                  <div className="space-y-2">
                    <Label>Supabase Project URL</Label>
                    <Input name="supabase_url" defaultValue={integrations.supabase?.url} placeholder="https://xyz.supabase.co" />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label>Publishable Key</Label>
                    <Input name="supabase_publishable_key" type="password" placeholder="Anon Key" />
                  </div>
                  <div className="space-y-2">
                    <Label>Service Role Key</Label>
                    <Input name="supabase_service_role_key" type="password" placeholder="Service Key" />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border-t pt-4">
                  <div className="space-y-2">
                    <Label>Embedding Model</Label>
                    <Input name="embedding_model" defaultValue={integrations.supabase?.embedding_model} placeholder="mxbai-embed-large" />
                  </div>
                  <div className="space-y-2">
                    <Label>Dimensions</Label>
                    <Input name="embedding_dimensions" type="number" defaultValue={integrations.supabase?.embedding_dimensions} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-md">MentisDB (Short-term Memory)</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <Select name="mentis_enabled" defaultValue={String(integrations.mentis_enabled)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="false">Desactivado</SelectItem>
                      <SelectItem value="true">Activo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Mentis URL</Label>
                  <Input name="mentis_base_url" defaultValue={integrations.mentis} placeholder="http://mentisdb:80" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trading" className="space-y-4 outline-none">
            <Card className="border-blue-500/20 bg-blue-500/5">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-md flex items-center gap-2">
                    <Globe className="w-5 h-5 text-blue-500" />
                    Cuenta de Kalshi
                  </CardTitle>
                  <span className={`px-2 py-1 text-[10px] font-bold rounded border ${integrations.kalshi_configured ? "bg-green-500/10 text-green-500 border-green-500/20" : "bg-amber-500/10 text-amber-500 border-amber-500/20"}`}>
                    {integrations.kalshi_configured ? "VINCULADA" : "PENDIENTE"}
                  </span>
                </div>
                <CardDescription>Credenciales para ejecución real de mercados de predicción.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>Username / Email</Label>
                  <Input name="kalshi_username" defaultValue={config.kalshi_username} placeholder="user@mail.com" />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input name="kalshi_password" type="password" placeholder="••••••••" />
                </div>
                <div className="space-y-2">
                  <Label>Key ID (Opcional)</Label>
                  <Input name="kalshi_key_id" defaultValue={config.kalshi_key_id} placeholder="UUID" />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </div>
      </Tabs>
    </form>
  );
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${active ? "bg-green-500/10 text-green-500" : "bg-amber-500/10 text-amber-500"}`}>
      {active ? "✓ CONFIGURADO" : "⚠ PENDIENTE"}
    </span>
  );
}
