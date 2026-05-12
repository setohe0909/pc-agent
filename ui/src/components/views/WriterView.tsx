import type { FormEvent } from "react";
import { PenTool, BookOpen, Save, Sparkles, Files, ExternalLink, Settings } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

export function WriterView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { runtime } = data;
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

  const openObsidian = () => {
    window.open("http://localhost:3010", "_blank");
  };

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="flex justify-between items-center bg-card p-4 rounded-lg border sticky top-0 z-20 shadow-sm">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <PenTool className="w-5 h-5 text-indigo-500" />
            Writer Sub-Agent Portal
          </h2>
          <p className="text-xs text-muted-foreground">Configura la creación de contenidos y la sincronización con Obsidian.</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={openObsidian} className="gap-2">
            <ExternalLink className="w-4 h-4" /> Abrir Obsidian
          </Button>
          <Button type="submit" className="gap-2 shadow-lg bg-indigo-600 hover:bg-indigo-700">
            <Save className="w-4 h-4" /> Guardar Configuración
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Files className="w-5 h-5 text-indigo-500" />
              Configuración de Obsidian
            </CardTitle>
            <CardDescription>Define dónde se almacenan tus notas y artículos.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Ruta del Vault (Docker)</Label>
              <Input 
                name="obsidian_vault_path" 
                placeholder="/vault" 
                defaultValue={currentRuntime.obsidian_vault_path || "/vault"}
              />
              <p className="text-[10px] text-muted-foreground">Esta es la ruta interna en el contenedor assistant-runtime.</p>
            </div>
            <div className="flex items-center gap-4 p-3 rounded-md bg-muted/50 border">
              <div className="flex-1">
                <p className="text-xs font-semibold">Estado de Sincronización</p>
                <p className="text-[10px] text-muted-foreground">Conectado al volumen compartido `obsidian-vault`</p>
              </div>
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-200">
                ACTIVO
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Preferencias de Redacción
            </CardTitle>
            <CardDescription>Personaliza el estilo de los blogs y historias.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Idioma por Defecto</Label>
              <Select name="writer_default_lang" defaultValue={currentRuntime.writer_default_lang || "es"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="es">Español</SelectItem>
                  <SelectItem value="en">Inglés (English)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Formato de Título</Label>
              <Select name="writer_title_format" defaultValue={currentRuntime.writer_title_format || "date-suffix"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="date-suffix">Título-Fecha.md</SelectItem>
                  <SelectItem value="date-prefix">Fecha-Título.md</SelectItem>
                  <SelectItem value="clean">Solo Título.md</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-500" />
              Estructura de Carpetas
            </CardTitle>
            <CardDescription>Organización automática de archivos en Obsidian.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 border rounded-lg bg-background">
                <p className="text-xs font-bold mb-1">📁 Blog</p>
                <p className="text-[10px] text-muted-foreground">Artículos largos optimizados para SEO.</p>
              </div>
              <div className="p-3 border rounded-lg bg-background">
                <p className="text-xs font-bold mb-1">📁 Story-telling</p>
                <p className="text-[10px] text-muted-foreground">Narrativas emocionales y de marca.</p>
              </div>
              <div className="p-3 border rounded-lg bg-background">
                <p className="text-xs font-bold mb-1">📁 Assets</p>
                <p className="text-[10px] text-muted-foreground">Imágenes y recursos externos (Próximamente).</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 bg-muted/30 border-dashed">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Integración con Unsplash
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground mb-3">
              El sub-agente utiliza la búsqueda por palabras clave de Unsplash para enriquecer tus artículos visualmente.
            </p>
            <div className="flex gap-2">
              <Badge variant="secondary" className="text-[10px]">Keyword Analysis</Badge>
              <Badge variant="secondary" className="text-[10px]">Dynamic Embedding</Badge>
              <Badge variant="secondary" className="text-[10px]">Creative Commons</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
