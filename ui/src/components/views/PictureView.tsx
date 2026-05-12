import type { FormEvent } from "react";
import { Camera, Save, Sparkles, Image as ImageIcon, History } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function PictureView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
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

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="flex justify-between items-center bg-card p-4 rounded-lg border sticky top-0 z-20 shadow-sm">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Camera className="w-5 h-5 text-amber-500" />
            Picture Sub-Agent Portal
          </h2>
          <p className="text-xs text-muted-foreground">Gestiona la generación de imágenes y la memoria estética.</p>
        </div>
        <Button type="submit" className="gap-2 shadow-lg bg-amber-600 hover:bg-amber-700">
          <Save className="w-4 h-4" /> Guardar Configuración
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              Motor de Generación (DALL-E 3)
            </CardTitle>
            <CardDescription>Parámetros de calidad y estilo por defecto.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Calidad de Imagen</Label>
              <Select name="picture_quality" defaultValue={currentRuntime.picture_quality || "hd"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="standard">Standard (Rápido)</SelectItem>
                  <SelectItem value="hd">HD (Alta Definición)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tamaño por Defecto</Label>
              <Select name="picture_size" defaultValue={currentRuntime.picture_size || "1024x1024"}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1024x1024">Cuadrado (1024x1024)</SelectItem>
                  <SelectItem value="1024x1792">Vertical (Story)</SelectItem>
                  <SelectItem value="1792x1024">Horizontal (Web)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-md flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-amber-500" />
              Identidad Visual
            </CardTitle>
            <CardDescription>Define la estética recurrente de tu marca.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Estilo Artístico Base</Label>
              <Input 
                name="picture_default_style" 
                placeholder="Ej: Fotorealista, Minimalista, Cyberpunk..." 
                defaultValue={currentRuntime.picture_default_style}
              />
            </div>
            <div className="space-y-2">
              <Label>Paleta de Colores (Keywords)</Label>
              <Input 
                name="picture_color_palette" 
                placeholder="Ej: Pasteles, Neon, Monocromático..." 
                defaultValue={currentRuntime.picture_color_palette}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 bg-muted/30 border-dashed">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <History className="w-4 h-4" />
              Estado de Memoria Proactiva
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="flex items-center gap-2 p-3 rounded bg-background border">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <div className="space-y-1">
                  <p className="font-bold">Memoria de Estilo: Activa</p>
                  <p className="text-muted-foreground">El agente está inyectando aprendizajes de hoy en cada prompt.</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-3 rounded bg-background border">
                <ImageIcon className="w-4 h-4 text-muted-foreground" />
                <div className="space-y-1">
                  <p className="font-bold">Última Refinación</p>
                  <p className="text-muted-foreground">"Estética minimalista con tonos crema" - Hace 2 horas.</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </form>
  );
}
