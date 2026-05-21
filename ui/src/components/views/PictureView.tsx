import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Aperture,
  Brush,
  Camera,
  CheckCircle2,
  Clock3,
  Image as ImageIcon,
  Layers3,
  Palette,
  Save,
  WandSparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const outputFormats = [
  {
    title: "Square",
    size: "1024x1024",
    description: "Posts, previews y assets reutilizables.",
  },
  {
    title: "Story",
    size: "1024x1792",
    description: "Vertical para redes, campañas y anuncios.",
  },
  {
    title: "Web Hero",
    size: "1792x1024",
    description: "Headers, landing pages y banners amplios.",
  },
];

const studioFlow = ["Prompt", "Estilo", "Generación", "Memoria"];

const memorySignals = [
  {
    icon: CheckCircle2,
    title: "Memoria de estilo",
    value: "Activa",
    description: "El agente inyecta aprendizajes recientes en cada prompt.",
  },
  {
    icon: Clock3,
    title: "Última refinación",
    value: "Hace 2 horas",
    description: "Estética minimalista con tonos crema.",
  },
];

export function PictureView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
  const { runtime } = data;
  const currentRuntime = runtime?.runtime || {};

  const handleSave = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload: any = Object.fromEntries(formData);

    Object.keys(payload).forEach(key => {
      if (payload[key] === "") delete payload[key];
    });

    await onSave(payload);
  };

  return (
    <form onSubmit={handleSave} className="space-y-5 pb-10">
      <section className="sticky top-0 z-20 rounded-[10px] border border-neutral-200 bg-white/95 px-5 py-4 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Camera className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Picture Sub-Agent Portal</h2>
                <Badge className="rounded-full bg-orange-50 text-orange-700 hover:bg-orange-50">Image Studio</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">Generación visual, memoria estética y consistencia de marca.</p>
            </div>
          </div>
          <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
            <Save className="size-4" />
            Guardar configuración
          </Button>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <SettingsSection
            icon={WandSparkles}
            title="Motor de generación"
            description="Parámetros base para calidad, tamaño y comportamiento visual."
            action={
              <Badge className="rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
                <CheckCircle2 className="mr-1 size-3" />
                DALL-E 3
              </Badge>
            }
          >
            <Field label="Calidad de imagen" hint="HD prioriza detalle y consistencia visual.">
              <Select name="picture_quality" defaultValue={currentRuntime.picture_quality || "hd"}>
                <SelectTrigger className="picture-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="standard">Standard (rápido)</SelectItem>
                  <SelectItem value="hd">HD (alta definición)</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Tamaño por defecto" hint="El formato se puede ajustar por cada solicitud.">
              <Select name="picture_size" defaultValue={currentRuntime.picture_size || "1024x1024"}>
                <SelectTrigger className="picture-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1024x1024">Cuadrado (1024x1024)</SelectItem>
                  <SelectItem value="1024x1792">Vertical (story)</SelectItem>
                  <SelectItem value="1792x1024">Horizontal (web)</SelectItem>
                </SelectContent>
              </Select>
            </Field>
          </SettingsSection>

          <SettingsSection
            icon={Palette}
            title="Identidad visual"
            description="Define los rasgos recurrentes para que el agente mantenga coherencia estética."
          >
            <Field label="Estilo artístico base" hint="Ejemplo: fotorealista editorial, minimalista, cinematic product shot.">
              <Input
                name="picture_default_style"
                placeholder="Fotorealista editorial, minimalista, cinematic..."
                defaultValue={currentRuntime.picture_default_style}
                className="picture-input"
              />
            </Field>
            <Field label="Paleta de colores" hint="Keywords separadas por coma para guiar la composición.">
              <Input
                name="picture_color_palette"
                placeholder="Verde profundo, crema, grafito, acentos neón..."
                defaultValue={currentRuntime.picture_color_palette}
                className="picture-input"
              />
            </Field>
          </SettingsSection>

          <SettingsSection icon={Layers3} title="Formatos de salida" description="Presets rápidos para los usos más comunes del estudio." columns={1}>
            <div className="grid gap-3 md:grid-cols-3">
              {outputFormats.map((format) => (
                <div key={format.title} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-neutral-950">{format.title}</p>
                    <code className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-neutral-500 ring-1 ring-neutral-200">
                      {format.size}
                    </code>
                  </div>
                  <p className="text-xs leading-5 text-neutral-500">{format.description}</p>
                </div>
              ))}
            </div>
          </SettingsSection>
        </div>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <Aperture className="size-4 text-[#3ecf8e]" />
                Flujo creativo
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Cómo una idea termina como imagen persistida.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 p-5">
              {studioFlow.map((step, index) => (
                <div key={step} className="flex items-center gap-3 rounded-[8px] bg-neutral-50 px-3 py-2">
                  <span className="flex size-6 items-center justify-center rounded-full bg-neutral-950 text-xs text-white">{index + 1}</span>
                  <span className="text-sm font-medium text-neutral-800">{step}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <Brush className="size-4 text-[#3ecf8e]" />
                Memoria proactiva
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Señales que el agente usa para refinar prompts visuales.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              {memorySignals.map((signal) => (
                <div key={signal.title} className="rounded-[8px] bg-neutral-50 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="flex size-7 items-center justify-center rounded-[7px] bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100">
                        <signal.icon className="size-3.5" />
                      </span>
                      <p className="text-sm font-semibold text-neutral-950">{signal.title}</p>
                    </div>
                    <span className="text-xs font-semibold text-neutral-500">{signal.value}</span>
                  </div>
                  <p className="text-xs leading-5 text-neutral-500">{signal.description}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-[10px] border-neutral-200 bg-neutral-950 text-white shadow-sm">
            <CardHeader className="border-b border-white/10 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold">
                <ImageIcon className="size-4 text-[#3ecf8e]" />
                Prompt Context
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 p-5 text-xs leading-5 text-neutral-300">
              <p>style.memory: active</p>
              <p>quality.default: {currentRuntime.picture_quality || "hd"}</p>
              <p>palette.inject: enabled</p>
            </CardContent>
          </Card>
        </aside>
      </section>
    </form>
  );
}

function SettingsSection({
  icon: Icon,
  title,
  description,
  children,
  action,
  columns = 2,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children: ReactNode;
  action?: ReactNode;
  columns?: 1 | 2;
}) {
  return (
    <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
      <CardHeader className="border-b border-neutral-200 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 gap-3">
            <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
              <Icon className="size-4" />
            </span>
            <div className="min-w-0">
              <CardTitle className="text-base font-semibold text-neutral-950">{title}</CardTitle>
              <CardDescription className="mt-1 text-sm text-neutral-500">{description}</CardDescription>
            </div>
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent className={`grid gap-4 p-5 ${columns === 2 ? "md:grid-cols-2" : "grid-cols-1"}`}>
        {children}
      </CardContent>
    </Card>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold text-neutral-900">{label}</Label>
      {children}
      {hint ? <p className="text-xs leading-5 text-neutral-500">{hint}</p> : null}
    </div>
  );
}
