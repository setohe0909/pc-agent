import type { FormEvent } from "react";
import { Code, Globe, Save, Cpu, Database, Layout, Terminal, Zap, Shield } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function CoderWebView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { runtime } = data;
  const currentRuntime = runtime?.runtime || {};
  const secrets = currentRuntime.secrets || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);
    
    // Cleanup empty strings
    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    console.log("[CODER-WEB] Saving payload:", payload);
    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="flex justify-between items-center bg-card p-4 rounded-lg border sticky top-0 z-20 shadow-sm">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-500" />
            Coder Web Agent (Pilot)
          </h2>
          <p className="text-xs text-muted-foreground">Configuración avanzada de despliegue y automatización.</p>
        </div>
        <Button type="submit" className="gap-2 shadow-lg bg-blue-600 hover:bg-blue-700">
          <Save className="w-4 h-4" /> Guardar Cambios
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Code className="w-5 h-5 text-slate-900 dark:text-white" />
              GitHub Repository Control
            </CardTitle>
            <CardDescription>Configuración para el despliegue de proyectos React/TS.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>GitHub Personal Token</Label>
              <Input 
                name="github_token" 
                type="password" 
                placeholder={secrets.github_token ? "••••••••••••••••" : "ghp_..."}
              />
              {secrets.github_token && <p className="text-[10px] text-green-500">✓ Token guardado exitosamente</p>}
            </div>
            <div className="space-y-2">
              <Label>GitHub Organization / User</Label>
              <Input 
                name="github_org" 
                placeholder="tu-org"
                defaultValue={currentRuntime.github_org || ""}
              />
              {currentRuntime.github_org && <p className="text-[10px] text-blue-500">User/Org: {currentRuntime.github_org}</p>}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 border-blue-500/30 bg-blue-500/5">
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              Pilot AI Engine
            </CardTitle>
            <CardDescription>Configuración del motor Pilot para generación de código y diseño.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-1">
              <p className="text-sm font-bold flex items-center gap-2">
                <Layout className="w-4 h-4" /> Layout Builder
              </p>
              <p className="text-[10px] text-muted-foreground">Generación automática de layouts responsivos con Tailwind CSS.</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold flex items-center gap-2">
                <Database className="w-4 h-4" /> Supabase Architect
              </p>
              <p className="text-[10px] text-muted-foreground">Modelado automático de bases de datos y políticas RLS.</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold flex items-center gap-2">
                <Shield className="w-4 h-4" /> Version Control
              </p>
              <p className="text-[10px] text-muted-foreground">Versionado automático de cambios en Git.</p>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Terminal className="w-5 h-5 text-amber-500" />
              Stack & Preferencias de Desarrollo
            </CardTitle>
            <CardDescription>Define el stack tecnológico por defecto para nuevos proyectos.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label>Stack Principal</Label>
              <Select name="coder_web_stack" defaultValue={currentRuntime.coder_web_stack || "react-ts"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="react-ts">React/TS + Tailwind + Supabase</SelectItem>
                  <SelectItem value="nextjs">Next.js + Tailwind + Prisma</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Nivel de Autonomía</Label>
              <Select name="coder_web_autonomy" defaultValue={currentRuntime.coder_web_autonomy || "human-in-loop"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="full">Total (Auto-deploy)</SelectItem>
                  <SelectItem value="human-in-loop">Revisión Requerida</SelectItem>
                  <SelectItem value="draft">Solo Borradores</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Prioridad de Performance</Label>
              <Select name="coder_web_perf" defaultValue={currentRuntime.coder_web_perf || "high"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">Máxima (SEO & Speed)</SelectItem>
                  <SelectItem value="balanced">Balanceada</SelectItem>
                  <SelectItem value="dev">Desarrollo Rápido</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 bg-muted/30 border-dashed">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-500" />
              Operaciones en Tiempo Real (Pilot Monitor)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="flex items-center gap-2 p-2 rounded bg-background border">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span>Pilot Engine: **Online**</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded bg-background border">
                  <Database className="w-3 h-3 text-muted-foreground" />
                  <span>Sync Supabase: **Conectado**</span>
                </div>
                <div className="flex items-center gap-2 p-2 rounded bg-background border">
                  <Globe className="w-3 h-3 text-muted-foreground" />
                  <span>CI/CD Pipelines: **Activos**</span>
                </div>
              </div>
              
              <div className="p-4 rounded-lg bg-black text-green-400 font-mono text-[10px] space-y-1">
                <p>{">"} [SYSTEM] Pilot initialized.</p>
                <p>{">"} [INFO] Monitoring repository ecommerce-3a2f...</p>
                <p>{">"} [STATUS] Awaiting next instruction...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
