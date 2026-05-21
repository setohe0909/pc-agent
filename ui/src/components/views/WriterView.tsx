import type { FormEvent, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  CheckCircle2,
  ExternalLink,
  Files,
  Folder,
  Image,
  Languages,
  PenTool,
  Save,
  Settings,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

const folderStructure = [
  {
    name: "Blog",
    path: "/Blog",
    description: "Artículos largos, SEO y análisis editorial.",
  },
  {
    name: "Story-telling",
    path: "/Story-telling",
    description: "Narrativas emocionales, marca y contenido de campaña.",
  },
  {
    name: "Assets",
    path: "/Assets",
    description: "Recursos visuales, referencias e imágenes asociadas.",
  },
];

const writerFlow = [
  "Prompt",
  "Memoria de voz",
  "Borrador",
  "Vault",
];

export function WriterView({ data, onSave }: { data: any, adminToken: string, onSave: (payload: any) => Promise<void> }) {
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

  const openObsidian = () => {
    window.open("http://localhost:3010", "_blank");
  };

  return (
    <form onSubmit={handleSave} className="space-y-5 pb-10">
      <section className="sticky top-0 z-20 rounded-[10px] border border-neutral-200 bg-white/95 px-5 py-4 shadow-sm backdrop-blur">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <PenTool className="size-5" />
            </span>
            <div className="min-w-0">
              <h2 className="text-xl font-semibold tracking-tight text-neutral-950">Writer Sub-Agent Portal</h2>
              <p className="mt-1 text-sm text-neutral-500">Producción editorial, memoria de voz y sincronización con Obsidian.</p>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button type="button" variant="outline" onClick={openObsidian} className="h-10 gap-2 rounded-[8px] border-neutral-200 bg-white px-4 shadow-sm">
              <ExternalLink className="size-4" />
              Abrir Obsidian
            </Button>
            <Button type="submit" className="h-10 gap-2 rounded-[8px] bg-neutral-950 px-4 text-white shadow-sm hover:bg-neutral-800">
              <Save className="size-4" />
              Guardar configuración
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <SettingsSection
            icon={Files}
            title="Obsidian Vault"
            description="Define la ruta donde el runtime escribe notas, blogs e historias."
            action={
              <Badge className="rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
                <CheckCircle2 className="mr-1 size-3" />
                Sincronizado
              </Badge>
            }
          >
            <Field label="Ruta del Vault (Docker)" hint="Ruta interna en el contenedor assistant-runtime.">
              <Input
                name="obsidian_vault_path"
                placeholder="/vault"
                defaultValue={currentRuntime.obsidian_vault_path || "/vault"}
                className="writer-input"
              />
            </Field>
            <div className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
              <p className="text-sm font-semibold text-neutral-950">Estado de sincronización</p>
              <p className="mt-1 text-sm leading-6 text-neutral-500">Conectado al volumen compartido `obsidian-vault`.</p>
              <code className="mt-3 block rounded-[6px] bg-neutral-950 px-3 py-2 text-xs text-neutral-100">localhost:3010 · /vault</code>
            </div>
          </SettingsSection>

          <SettingsSection
            icon={Sparkles}
            title="Preferencias de Redacción"
            description="Controla idioma, formato de archivo y convenciones editoriales."
          >
            <Field label="Idioma por defecto">
              <Select name="writer_default_lang" defaultValue={currentRuntime.writer_default_lang || "es"}>
                <SelectTrigger className="writer-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="es">Español</SelectItem>
                  <SelectItem value="en">Inglés (English)</SelectItem>
                </SelectContent>
              </Select>
            </Field>
            <Field label="Formato de título">
              <Select name="writer_title_format" defaultValue={currentRuntime.writer_title_format || "date-suffix"}>
                <SelectTrigger className="writer-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="date-suffix">Título-Fecha.md</SelectItem>
                  <SelectItem value="date-prefix">Fecha-Título.md</SelectItem>
                  <SelectItem value="clean">Solo Título.md</SelectItem>
                </SelectContent>
              </Select>
            </Field>
          </SettingsSection>

          <SettingsSection icon={BookOpen} title="Estructura de carpetas" description="Organización automática de salidas en el vault." columns={1}>
            <div className="grid gap-3 md:grid-cols-3">
              {folderStructure.map((folder) => (
                <div key={folder.name} className="rounded-[8px] border border-neutral-200 bg-neutral-50 p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Folder className="size-4 text-[#168a5b]" />
                      <p className="text-sm font-semibold text-neutral-950">{folder.name}</p>
                    </div>
                    <code className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-neutral-500 ring-1 ring-neutral-200">{folder.path}</code>
                  </div>
                  <p className="text-xs leading-5 text-neutral-500">{folder.description}</p>
                </div>
              ))}
            </div>
          </SettingsSection>
        </div>

        <aside className="space-y-4">
          <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="border-b border-neutral-200 px-5 py-4">
              <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
                <Languages className="size-4 text-[#3ecf8e]" />
                Flujo editorial
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Cómo el sub-agente convierte una solicitud en archivo persistido.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 p-5">
              {writerFlow.map((step, index) => (
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
                <Image className="size-4 text-[#3ecf8e]" />
                Unsplash
              </CardTitle>
              <CardDescription className="text-sm text-neutral-500">Enriquecimiento visual para piezas editoriales.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-5">
              {["Keyword analysis", "Dynamic embedding", "Creative Commons"].map((feature) => (
                <div key={feature} className="flex items-center gap-2 rounded-[8px] bg-neutral-50 px-3 py-2 text-sm font-medium text-neutral-700">
                  <Settings className="size-4 text-neutral-400" />
                  {feature}
                </div>
              ))}
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
