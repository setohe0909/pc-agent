import type { FormEvent } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuración Runtime</CardTitle>
          <CardDescription>URLs e integraciones que el panel usa para verificar servicios.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Assistant runtime URL</Label>
              <Input name="open_claw_base_url" defaultValue={integrations.open_claw} placeholder="http://localhost:8100" />
            </div>
            
            <div className="space-y-2">
              <Label>MentisDB URL</Label>
              <Input name="mentis_base_url" defaultValue={integrations.mentis} placeholder="http://localhost:9471" />
            </div>
            <div className="space-y-2">
              <Label>MentisDB Estado</Label>
              <Select name="mentis_enabled" defaultValue={String(integrations.mentis_enabled)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Opcional desactivado</SelectItem>
                  <SelectItem value="true">Verificar servicio</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Langfuse URL</Label>
              <Input name="langfuse_host" defaultValue={integrations.langfuse} placeholder="http://localhost:3000" />
            </div>
            <div className="space-y-2">
              <Label>Langfuse Estado</Label>
              <Select name="langfuse_enabled" defaultValue={String(integrations.langfuse_enabled)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="false">Opcional desactivado</SelectItem>
                  <SelectItem value="true">Verificar servicio</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Langfuse Public Key</Label>
              <Input name="langfuse_public_key" type="password" placeholder="pk-..." autoComplete="off" />
            </div>
            <div className="space-y-2">
              <Label>Langfuse Secret Key</Label>
              <Input name="langfuse_secret_key" type="password" placeholder="sk-..." autoComplete="off" />
            </div>

            <div className="space-y-2">
              <Label>Ollama URL</Label>
              <Input name="ollama_base_url" defaultValue={integrations.ollama} placeholder="http://localhost:11434" />
            </div>
            <div className="space-y-2">
              <Label>OpenAI API Key</Label>
              <Input name="openai_api_key" type="password" placeholder="sk-..." autoComplete="off" />
            </div>
            <div className="space-y-2">
              <Label>Gemini API Key</Label>
              <Input name="gemini_api_key" type="password" placeholder="AIza..." autoComplete="off" />
            </div>

            <div className="space-y-2 lg:col-span-3">
              <Label>Supabase URL</Label>
              <Input name="supabase_url" defaultValue={integrations.supabase?.url} placeholder="https://project.supabase.co" />
            </div>

            <div className="space-y-2">
              <Label>Supabase publishable key</Label>
              <Input name="supabase_publishable_key" type="password" autoComplete="off" />
            </div>
            <div className="space-y-2">
              <Label>Supabase service role key</Label>
              <Input name="supabase_service_role_key" type="password" autoComplete="off" />
            </div>

            <div className="space-y-2">
              <Label>Embedding model</Label>
              <Input name="embedding_model" defaultValue={integrations.supabase?.embedding_model} placeholder="mxbai-embed-large" />
            </div>
            <div className="space-y-2">
              <Label>Embedding dimensions</Label>
              <Input name="embedding_dimensions" type="number" defaultValue={integrations.supabase?.embedding_dimensions} min="1" max="8192" />
            </div>

            <div className="lg:col-span-3 flex justify-end mt-4">
              <Button type="submit">Guardar Configuración</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
