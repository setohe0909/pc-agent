import { useState, useEffect } from "react";
import {
  Activity,
  BookOpen,
  Brain,
  Camera,
  Code,
  FolderKanban,
  History,
  Home,
  Megaphone,
  MessageCircle,
  PenTool,
  RefreshCw,
  Settings,
  ShieldCheck,
  TerminalSquare,
  UserCircle,
  Users,
  Zap,
} from "lucide-react";
import { getJson, saveRuntimeConfig } from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OverviewView } from "@/components/views/OverviewView";
import { DiscordView } from "@/components/views/DiscordView";
import { KnowledgeView } from "@/components/views/KnowledgeView";
import { ConfigView } from "@/components/views/ConfigView";
import { ArchitectureView } from "@/components/views/ArchitectureView";
import { WikiView } from "@/components/views/WikiView";
import { MarketerView } from "@/components/views/MarketerView";
import { WriterView } from "@/components/views/WriterView";
import { PictureView } from "@/components/views/PictureView";
import { LeadsView } from "@/components/views/LeadsView";
import { CoderWebView } from "@/components/views/CoderWebView";
import { ConsolidationView } from "@/components/views/ConsolidationView";
import { WhatsAppView } from "@/components/views/WhatsAppView";

const navItems = [
  { value: "overview", label: "Resumen", icon: Home, group: "main" },
  { value: "knowledge", label: "Conocimiento", icon: FolderKanban, group: "main" },
  { value: "discord", label: "Discord", icon: Brain, group: "main" },
  { value: "marketing", label: "Marketing", icon: Megaphone, group: "main" },
  { value: "leads", label: "Leads", icon: Users, group: "main" },
  { value: "whatsapp", label: "WhatsApp", icon: MessageCircle, group: "main" },
  { value: "writer", label: "Redactor", icon: PenTool, group: "agents" },
  { value: "picture", label: "Imágenes", icon: Camera, group: "agents" },
  { value: "coder", label: "Coder Web", icon: Code, group: "agents" },
  { value: "consolidation", label: "Memoria LTM", icon: History, group: "ops" },
  { value: "config", label: "Configuración", icon: Settings, group: "ops" },
  { value: "architecture", label: "Arquitectura", icon: TerminalSquare, group: "docs" },
  { value: "wiki", label: "Wiki / Ayuda", icon: BookOpen, group: "docs" },
] as const;

const tabTitles: Record<string, { title: string; subtitle: string }> = {
  overview: {
    title: "PC Agent Operations Dashboard",
    subtitle: "Métricas, salud de servicios y señales de memoria para administrar la plataforma multiagente.",
  },
  discord: {
    title: "Discord Control Plane",
    subtitle: "Canales, aprobaciones y configuración operacional del bot.",
  },
  knowledge: {
    title: "Knowledge Projects",
    subtitle: "Fuentes, ingesta y disponibilidad del conocimiento vectorial.",
  },
  config: {
    title: "Runtime Settings",
    subtitle: "Parámetros de ejecución para modelos, integraciones y comportamiento de agentes.",
  },
  marketing: {
    title: "Marketing Agents",
    subtitle: "Automatización, investigación y workflows comerciales asistidos por IA.",
  },
  leads: {
    title: "Leads CRM",
    subtitle: "Oportunidades, campañas y señales accionables del pipeline.",
  },
  whatsapp: {
    title: "WhatsApp Outreach",
    subtitle: "Mensajería, plantillas y seguimiento de contactos.",
  },
  writer: {
    title: "Writer Workspace",
    subtitle: "Producción editorial, memoria de voz y salida a Obsidian.",
  },
  picture: {
    title: "Image Studio",
    subtitle: "Generación visual, memoria de estilo y flujos de imagen.",
  },
  coder: {
    title: "Coder Web",
    subtitle: "Experiencias web, e-commerce y cambios asistidos por subagentes.",
  },
  consolidation: {
    title: "Long-Term Memory",
    subtitle: "Consolidación diaria y trazabilidad de memoria operacional.",
  },
  architecture: {
    title: "Architecture",
    subtitle: "Mapa Clean/Hexagonal de servicios, casos de uso, puertos y adaptadores.",
  },
  wiki: {
    title: "Wiki / Help",
    subtitle: "Documentación viva para operar y extender PC Agent.",
  },
};

type ServiceStatus = {
  name: string;
  state: string;
  detail?: string;
};

type DashboardData = {
  status?: {
    services?: ServiceStatus[];
  } | null;
  config?: {
    discord?: {
      requests_channel_id?: string | null;
      notifications_channel_id?: string | null;
      status_channel_id?: string | null;
    };
    integrations?: {
      langfuse_enabled?: boolean;
      langfuse?: string;
      mentis_enabled?: boolean;
    };
  } | null;
  runtime?: unknown;
  sources?: {
    sources?: Array<{ enabled?: boolean }>;
  } | null;
  supabase?: {
    supabase: {
      knowledge_schema_ready?: boolean;
      reachable?: boolean;
      rest_available?: boolean;
      detail?: string;
    };
  } | null;
  mentis?: {
    mentis: {
      reachable?: boolean;
      can_read?: boolean;
      can_write?: boolean;
    };
  } | null;
  ingestion?: unknown;
};

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [adminToken, setAdminToken] = useState(localStorage.getItem("pc_agent_admin_token") || "");

  const refresh = () => {
    Promise.all([
      getJson("/status").catch(() => null),
      getJson("/config").catch(() => null),
      getJson("/config/runtime").catch(() => null),
      getJson("/knowledge-sources").catch(() => null),
      getJson("/supabase/verify").catch(() => null),
      getJson("/mentis/verify").catch(() => null),
      getJson("/ingestion").catch(() => null)
    ]).then(([status, config, runtime, sources, supabase, mentis, ingestion]) => {
      setData({ status, config, runtime, sources, supabase, mentis, ingestion });
    }).catch(err => console.error("Error cargando status", err));
  };

  useEffect(() => {
    localStorage.setItem("pc_agent_admin_token", adminToken);
  }, [adminToken]);

  useEffect(() => {
    document.documentElement.classList.remove("dark");
  }, []);

  useEffect(() => {
    refresh();
    const iv = setInterval(refresh, 5000);
    return () => clearInterval(iv);
  }, []);

  const handleSaveConfig = async (payload: unknown) => {
    console.log("[CONFIG] Intentando guardar payload:", payload);
    try {
      const result = await saveRuntimeConfig(payload, adminToken);
      console.log("[CONFIG] Resultado del servidor:", result);
      refresh();
      alert("Configuración guardada exitosamente");
    } catch (err: unknown) {
      console.error("[CONFIG] Error al guardar:", err);
      const message = err instanceof Error ? err.message : "error desconocido";
      alert("Error guardando configuración: " + message);
    }
  };

  if (!data) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#d8edf9] text-slate-700">
        <RefreshCw className="animate-spin" />
      </div>
    );
  }

  const renderContent = () => {
    switch (activeTab) {
      case "overview": return <OverviewView data={data} />;
      case "discord": return <DiscordView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "knowledge": return <KnowledgeView data={data} adminToken={adminToken} onRefresh={refresh} />;
      case "config": return <ConfigView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "architecture": return <ArchitectureView />;
      case "marketing": return <MarketerView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "leads": return <LeadsView />;
      case "whatsapp": return <WhatsAppView adminToken={adminToken} />;
      case "writer": return <WriterView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "picture": return <PictureView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "coder": return <CoderWebView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "consolidation": return <ConsolidationView />;
      case "wiki": return <WikiView />;
      default: return null;
    }
  };

  const activeTitle = tabTitles[activeTab] ?? tabTitles.overview;
  const services = data.status?.services || [];
  const healthy = services.filter((service) => service.state === "healthy").length;

  return (
    <div className="min-h-screen bg-[#dff2fb] text-slate-950">
      <div className="min-h-screen bg-[#eaf6fc]">
        <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical" className="min-h-screen w-full flex-row gap-0">
          <aside className="fixed inset-y-0 left-0 z-20 flex w-[76px] flex-col items-center border-r border-[#d3e3ee] bg-[#f9fdff] px-2.5 py-4 shadow-[8px_0_24px_rgba(68,112,143,0.07)]">
            <div className="mb-5 flex size-11 shrink-0 items-center justify-center rounded-[8px] bg-white shadow-sm ring-1 ring-[#d3e3ee]">
              <img src="/pc-agent-logo.png" alt="PC Agent" className="size-7 object-contain" />
            </div>

            <TabsList className="h-auto w-full flex-1 items-center justify-start gap-1.5 overflow-y-auto bg-transparent p-0 text-[#748394]">
              {navItems.map((item, index) => {
                const Icon = item.icon;
                const previous = navItems[index - 1];
                const startsGroup = previous && previous.group !== item.group;

                return (
                  <div key={item.value} className="w-full">
                    {startsGroup ? <div className="mx-auto my-2.5 h-px w-7 bg-[#d3e3ee]" /> : null}
                    <TabsTrigger
                      value={item.value}
                      title={item.label}
                      aria-label={item.label}
                      className="relative mx-auto !flex !size-9 !flex-none !grow-0 !basis-auto items-center justify-center rounded-[8px] border border-transparent bg-transparent p-0 text-[#8293a3] shadow-none transition-colors before:absolute before:-left-2 before:top-1/2 before:h-5 before:w-1 before:-translate-y-1/2 before:rounded-full before:bg-transparent hover:border-[#d3e3ee] hover:bg-white hover:text-[#27384d] data-active:!border-[#cfe8f8] data-active:!bg-[#e8f5fd] data-active:!text-[#1688d8] data-active:shadow-none data-active:before:bg-[#1688d8] [&_svg]:!size-5"
                    >
                      <Icon className="size-5" />
                    </TabsTrigger>
                  </div>
                );
              })}
            </TabsList>

            <div className="mt-3 flex flex-col items-center gap-2.5">
              <div className="h-px w-7 bg-[#d3e3ee]" />
              <Button variant="ghost" size="icon" onClick={refresh} title="Refrescar" aria-label="Refrescar" className="size-9 rounded-[8px] text-[#65778d] hover:bg-white hover:text-[#26394d]">
                <RefreshCw className="size-5" />
              </Button>
              <div className="flex size-9 items-center justify-center rounded-[8px] bg-white text-[#65778d] ring-1 ring-[#d3e3ee]" title="Perfil">
                <UserCircle className="size-5" />
              </div>
            </div>
          </aside>

          <main className="min-h-screen min-w-0 flex-1 pl-[76px]">
            <div className="min-h-screen bg-[#eaf6fc]">
              <header className="w-full border-b border-white/70 bg-[#dceffb]/80 px-5 py-6 backdrop-blur sm:px-8 lg:px-12">
                <div className="flex w-full flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-4xl">
                    <div className="mb-3 flex items-center gap-3">
                      <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200/80">
                        <ShieldCheck className="size-3.5 text-[#159947]" />
                        Control Panel v0.6.0
                      </span>
                      <span className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-200/80">
                        <Activity className="size-3.5 text-[#58aee9]" />
                        {healthy}/{services.length || 0} servicios healthy
                      </span>
                    </div>
                    <h1 className="text-3xl font-semibold tracking-normal text-slate-950 sm:text-4xl">
                      {activeTitle.title}
                    </h1>
                    <p className="mt-3 max-w-3xl text-base text-slate-600">
                      {activeTitle.subtitle}
                    </p>
                  </div>

                  <div className="w-full max-w-md rounded-2xl border border-white/80 bg-white/70 p-3 shadow-sm lg:w-[360px]">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <span className="text-xs font-medium text-slate-500">Admin Token</span>
                      <Zap className="size-4 text-[#58aee9]" />
                    </div>
                    <Input
                      type="password"
                      placeholder="Token secreto..."
                      value={adminToken}
                      onChange={e => setAdminToken(e.target.value)}
                      className="h-10 border-slate-200 bg-white text-sm shadow-none"
                    />
                  </div>
                </div>
              </header>

              <div className="w-full px-5 py-7 sm:px-8 lg:px-12">
                <div className="w-full">
                  {renderContent()}
                </div>
              </div>
            </div>
          </main>
        </Tabs>
      </div>
    </div>
  );
}
