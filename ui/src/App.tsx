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

const navGroups: Record<(typeof navItems)[number]["group"], string> = {
  main: "Workspace",
  agents: "Agentes",
  ops: "Operación",
  docs: "Sistema",
};

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
  modelUsage?: {
    period?: { label?: string; start?: string; end?: string };
    providers?: Array<{
      provider: string;
      status: string;
      configured?: boolean;
      used?: number | null;
      limit?: number | null;
      unit?: string;
      source?: string;
      detail?: string;
    }>;
  } | null;
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
      getJson("/ingestion").catch(() => null),
      getJson("/models/usage").catch(() => null)
    ]).then(([status, config, runtime, sources, supabase, mentis, ingestion, modelUsage]) => {
      setData({ status, config, runtime, sources, supabase, mentis, ingestion, modelUsage });
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
    <div className="min-h-screen bg-[#101010] text-neutral-950">
      <div className="min-h-screen bg-[#f7f7f6]">
        <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical" className="min-h-screen w-full flex-row gap-0">
          <aside className="app-sidebar fixed inset-y-0 left-0 z-20 flex w-[72px] flex-col border-r border-white/10 bg-[#171717] px-2 py-3 text-neutral-300 shadow-[14px_0_32px_rgba(0,0,0,0.18)] md:w-[248px] md:px-3">
            <div className="app-sidebar-brand mb-3 flex h-11 items-center justify-center gap-3 rounded-[8px] px-0 md:justify-start md:px-2">
              <div className="flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-[6px] bg-black ring-1 ring-white/10">
                <img src="/pc-agent-logo.png" alt="PC Agent" className="size-7 object-contain" />
              </div>
              <div className="app-sidebar-brand-copy hidden min-w-0 md:block">
                <p className="truncate text-sm font-semibold leading-5 text-white">PC Agent</p>
                <p className="truncate text-xs leading-4 text-neutral-500">Control Plane</p>
              </div>
            </div>

            <TabsList className="h-auto w-full flex-1 flex-col items-stretch justify-start gap-0 overflow-y-auto bg-transparent p-0 text-neutral-400 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {navItems.map((item, index) => {
                const Icon = item.icon;
                const previous = navItems[index - 1];
                const startsGroup = !previous || previous.group !== item.group;

                return (
                  <div key={item.value} className="w-full">
                    {startsGroup ? (
                      <div className={index === 0 ? "app-sidebar-group-label hidden px-2 pb-1 pt-2 md:block" : "app-sidebar-group-label hidden px-2 pb-1 pt-5 md:block"}>
                        <p className="text-[11px] font-medium uppercase leading-4 tracking-[0.08em] text-neutral-600">
                          {navGroups[item.group]}
                        </p>
                      </div>
                    ) : null}
                    <TabsTrigger
                      value={item.value}
                      title={item.label}
                      aria-label={item.label}
                      className="app-sidebar-nav-trigger relative mb-0.5 !flex h-9 w-full !flex-none !grow-0 !basis-auto items-center justify-center gap-2.5 rounded-[6px] border border-transparent bg-transparent px-0 py-0 text-sm font-medium text-neutral-400 shadow-none transition-colors before:absolute before:left-0 before:top-1/2 before:h-4 before:w-[2px] before:-translate-y-1/2 before:rounded-full before:bg-transparent hover:bg-white/[0.06] hover:text-neutral-100 data-active:!border-white/10 data-active:!bg-white/[0.08] data-active:!text-white data-active:before:bg-[#3ecf8e] md:justify-start md:px-2.5 [&_svg]:!size-4 [&_svg]:shrink-0 [&_svg]:stroke-[2]"
                    >
                      <Icon className="size-4" />
                      <span className="app-sidebar-item-label hidden truncate md:inline">{item.label}</span>
                    </TabsTrigger>
                  </div>
                );
              })}
            </TabsList>

            <div className="mt-3 border-t border-white/10 pt-3">
              <Button variant="ghost" onClick={refresh} title="Refrescar" aria-label="Refrescar" className="app-sidebar-footer-row h-9 w-full justify-center gap-2 rounded-[6px] px-0 text-sm font-medium text-neutral-400 hover:bg-white/[0.06] hover:text-neutral-100 md:justify-start md:px-2.5">
                <RefreshCw className="size-4" />
                <span className="app-sidebar-footer-label hidden md:inline">Refrescar</span>
              </Button>
              <div className="app-sidebar-footer-row mt-2 flex h-10 items-center justify-center gap-2 rounded-[6px] px-0 text-neutral-300 md:justify-start md:px-2" title="Perfil">
                <div className="flex size-7 items-center justify-center rounded-full bg-neutral-800 ring-1 ring-white/10">
                  <UserCircle className="size-4" />
                </div>
                <div className="app-sidebar-footer-label hidden min-w-0 md:block">
                  <p className="truncate text-sm font-medium leading-4 text-neutral-200">Admin</p>
                  <p className="truncate text-xs leading-4 text-neutral-500">Local session</p>
                </div>
              </div>
            </div>
          </aside>

          <main className="app-shell-main min-h-screen min-w-0 flex-1 pl-[72px] md:pl-[248px]">
            <div className="min-h-screen bg-[#f7f7f6]">
              <header className="w-full border-b border-neutral-200 bg-white/90 px-5 py-5 backdrop-blur sm:px-8 lg:px-10">
                <div className="flex w-full flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-4xl">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className="inline-flex items-center gap-2 rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-600 ring-1 ring-neutral-200">
                        <ShieldCheck className="size-3.5 text-[#2eb67d]" />
                        Control Panel v0.6.0
                      </span>
                      <span className="inline-flex items-center gap-2 rounded-full bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-600 ring-1 ring-neutral-200">
                        <Activity className="size-3.5 text-[#2eb67d]" />
                        {healthy}/{services.length || 0} servicios healthy
                      </span>
                    </div>
                    <h1 className="text-2xl font-semibold tracking-normal text-neutral-950 sm:text-3xl">
                      {activeTitle.title}
                    </h1>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-600">
                      {activeTitle.subtitle}
                    </p>
                  </div>

                  <div className="w-full max-w-md rounded-[8px] border border-neutral-200 bg-white p-3 shadow-sm lg:w-[360px]">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <span className="text-xs font-medium text-neutral-500">Admin Token</span>
                      <Zap className="size-4 text-[#2eb67d]" />
                    </div>
                    <Input
                      type="password"
                      placeholder="Token secreto..."
                      value={adminToken}
                      onChange={e => setAdminToken(e.target.value)}
                      className="h-9 border-neutral-200 bg-white text-sm shadow-none"
                    />
                  </div>
                </div>
              </header>

              <div className="w-full px-5 py-6 sm:px-8 lg:px-10">
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
