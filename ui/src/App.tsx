import { useState, useEffect } from "react";
import { Activity, BookOpen, Brain, Database, RefreshCw, Settings, TerminalSquare, Megaphone, PenTool, Camera } from "lucide-react";
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
import { CoderWebView } from "@/components/views/CoderWebView";
import { Users, Code } from "lucide-react";

export default function App() {
  const [data, setData] = useState<any>(null);
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
    refresh();
    const iv = setInterval(refresh, 5000);
    return () => clearInterval(iv);
  }, []);

  const handleSaveConfig = async (payload: any) => {
    try {
      await saveRuntimeConfig(payload, adminToken);
      refresh();
      alert("Configuración guardada exitosamente");
    } catch (err: any) {
      alert("Error guardando configuración: " + err.message);
    }
  };

  if (!data) {
    return <div className="flex h-screen items-center justify-center"><RefreshCw className="animate-spin text-muted-foreground" /></div>;
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
      case "writer": return <WriterView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "picture": return <PictureView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "coder": return <CoderWebView data={data} adminToken={adminToken} onSave={handleSaveConfig} />;
      case "wiki": return <WikiView />;
      default: return null;
    }
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="w-64 border-r bg-card flex flex-col fixed h-full z-10">
        <div className="p-6 border-b">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <TerminalSquare className="w-6 h-6" />
            PC Agent
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Control Panel v2.3.0</p>
        </div>

        <div className="p-4 flex-1 overflow-y-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical" className="w-full">
            <TabsList className="flex flex-col h-auto bg-transparent items-stretch space-y-1">
              <TabsTrigger value="overview" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Activity className="w-4 h-4 mr-2" /> Resumen
              </TabsTrigger>
              <TabsTrigger value="discord" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Brain className="w-4 h-4 mr-2" /> Discord
              </TabsTrigger>
              <TabsTrigger value="knowledge" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Database className="w-4 h-4 mr-2" /> Conocimiento
              </TabsTrigger>
              <TabsTrigger value="config" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Settings className="w-4 h-4 mr-2" /> Configuración
              </TabsTrigger>
              <TabsTrigger value="marketing" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Megaphone className="w-4 h-4 mr-2" /> Marketing
              </TabsTrigger>
              <TabsTrigger value="leads" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Users className="w-4 h-4 mr-2" /> Leads (CRM)
              </TabsTrigger>
              <TabsTrigger value="writer" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <PenTool className="w-4 h-4 mr-2" /> Redactor
              </TabsTrigger>
              <TabsTrigger value="picture" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Camera className="w-4 h-4 mr-2" /> Imágenes
              </TabsTrigger>
              <TabsTrigger value="coder" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <Code className="w-4 h-4 mr-2" /> Coder Web
              </TabsTrigger>
              <div className="my-2 border-t border-border"></div>
              <TabsTrigger value="architecture" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <TerminalSquare className="w-4 h-4 mr-2" /> Arquitectura
              </TabsTrigger>
              <TabsTrigger value="wiki" className="justify-start px-4 py-2 data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
                <BookOpen className="w-4 h-4 mr-2" /> Wiki / Ayuda
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="p-4 border-t bg-muted/30">
          <div className="text-xs text-muted-foreground mb-2">Admin Token (para cambios)</div>
          <Input 
            type="password" 
            placeholder="Token secreto..." 
            value={adminToken}
            onChange={e => setAdminToken(e.target.value)}
            className="text-xs h-8" 
          />
        </div>
      </aside>

      <main className="flex-1 ml-64 p-8 overflow-y-auto h-screen bg-background">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold capitalize flex items-center gap-2">
            {activeTab}
          </h2>
          <Button variant="outline" size="sm" onClick={refresh} className="gap-2">
            <RefreshCw className="w-4 h-4" /> Refrescar
          </Button>
        </div>
        
        {renderContent()}

      </main>
    </div>
  );
}
