import { useState, useEffect } from "react";
import { History, Sparkles, Calendar, ChevronRight, Brain, CheckCircle2, Clock3, Layers3, Search, Database, UserRound } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { getJson } from "@/lib/api";

type ConsolidationRecord = {
  id: string;
  category: string;
  title: string;
  summary: string;
  status: string;
  memory_count: number;
  metadata: Record<string, any>;
  created_at: string;
};

type MemoryFragment = {
  id?: string;
  category: string;
  summary: string;
  metadata?: Record<string, any>;
  created_at?: string;
};

type ViewMode = "consolidations" | "memory";
type AgentFilter = "all" | "general" | "marketer" | "writer" | "picture" | "coder-web";

const agentFilters: Array<{ value: AgentFilter; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "general", label: "General" },
  { value: "marketer", label: "Marketing" },
  { value: "writer", label: "Writer" },
  { value: "picture", label: "Picture" },
  { value: "coder-web", label: "Coder Web" },
];

const cleanCategory = (category: string) =>
  category.replace("consolidated_", "").replace(/_/g, " ").trim();

const agentFromCategory = (category: string): AgentFilter => {
  if (category.startsWith("marketing")) return "marketer";
  if (category.startsWith("writer")) return "writer";
  if (category.startsWith("picture")) return "picture";
  if (category.startsWith("coder-web")) return "coder-web";
  return "general";
};

const agentLabel = (agent: AgentFilter) =>
  agentFilters.find((filter) => filter.value === agent)?.label || "General";

const formatDate = (date: string) =>
  new Intl.DateTimeFormat("es-CO", { month: "short", day: "numeric", year: "numeric" }).format(new Date(date));

const formatDateTime = (date: string) =>
  new Intl.DateTimeFormat("es-CO", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(date));

const getStatusLabel = (status: string) => {
  if (status === "succeeded") return "Completado";
  if (status === "failed") return "Fallido";
  return status || "Pendiente";
};

const renderSummaryLine = (line: string, index: number) => {
  const trimmed = line.trim();
  if (!trimmed) return null;

  const content = trimmed
    .replace(/^[-*]\s*/, "")
    .replace(/\*\*/g, "")
    .replace(/^#+\s*/, "");

  if (trimmed.startsWith("###")) {
    return <h3 key={index} className="mt-6 text-base font-semibold text-neutral-950">{content}</h3>;
  }

  if (trimmed.startsWith("##")) {
    return <h2 key={index} className="mt-8 border-t border-neutral-200 pt-6 text-xl font-semibold tracking-tight text-neutral-950">{content}</h2>;
  }

  if (trimmed.startsWith("#")) {
    return <h1 key={index} className="mt-6 text-2xl font-semibold tracking-tight text-neutral-950">{content}</h1>;
  }

  if (trimmed.startsWith("-") || trimmed.startsWith("*")) {
    return (
      <div key={index} className="flex gap-3 rounded-[8px] px-2 py-1.5 text-sm leading-6 text-neutral-700">
        <span className="mt-2 size-1.5 shrink-0 rounded-full bg-[#3ecf8e]" />
        <p>{content}</p>
      </div>
    );
  }

  return <p key={index} className="text-sm leading-7 text-neutral-600">{content}</p>;
};

export function ConsolidationView() {
  const [history, setHistory] = useState<ConsolidationRecord[]>([]);
  const [memory, setMemory] = useState<MemoryFragment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<ConsolidationRecord | null>(null);
  const [selectedMemory, setSelectedMemory] = useState<MemoryFragment | null>(null);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<ViewMode>("consolidations");
  const [agentFilter, setAgentFilter] = useState<AgentFilter>("all");

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const [historyData, memoryData] = await Promise.all([
        getJson("/intelligence/memory/consolidation"),
        getJson("/intelligence/memory/today?context=all&limit=200"),
      ]);
      const nextHistory = historyData.history || [];
      const nextMemory = memoryData.memory || [];
      setHistory(nextHistory);
      setMemory(nextMemory);
      if (nextHistory.length > 0 && !selectedItem) {
        setSelectedItem(nextHistory[0]);
      }
      if (nextMemory.length > 0 && !selectedMemory) {
        setSelectedMemory(nextMemory[0]);
      }
    } catch (err) {
      console.error("Error fetching memory history", err);
      setError("No pude cargar la memoria.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredHistory = history.filter((item) => {
    const needle = query.toLowerCase().trim();
    if (!needle) return true;
    return `${item.category} ${item.title} ${item.summary}`.toLowerCase().includes(needle);
  });

  const filteredMemory = memory.filter((item) => {
    const itemAgent = agentFromCategory(item.category);
    const matchesAgent = agentFilter === "all" || itemAgent === agentFilter;
    const needle = query.toLowerCase().trim();
    const matchesQuery = !needle || `${item.category} ${item.summary}`.toLowerCase().includes(needle);
    return matchesAgent && matchesQuery;
  });

  const memoryCounts = memory.reduce<Record<AgentFilter, number>>(
    (acc, item) => {
      const agent = agentFromCategory(item.category);
      acc.all += 1;
      acc[agent] += 1;
      return acc;
    },
    { all: 0, general: 0, marketer: 0, writer: 0, picture: 0, "coder-web": 0 }
  );

  const activeListCount = mode === "consolidations" ? filteredHistory.length : filteredMemory.length;

  return (
    <div className="grid h-[calc(100vh-12rem)] grid-cols-1 gap-5 xl:grid-cols-[380px_minmax(0,1fr)]">
      <Card className="flex min-h-0 flex-col overflow-hidden rounded-[10px] border-neutral-200 bg-white shadow-sm">
        <CardHeader className="border-b border-neutral-200 bg-white px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-neutral-950">
              {mode === "consolidations" ? <History className="size-4 text-[#3ecf8e]" /> : <Database className="size-4 text-[#3ecf8e]" />}
              {mode === "consolidations" ? "Consolidaciones" : "Memoria viva"}
            </CardTitle>
            <Badge variant="outline" className="rounded-full border-neutral-200 bg-neutral-50 text-xs text-neutral-600">
              {activeListCount}
            </Badge>
          </div>
          <CardDescription className="text-sm text-neutral-500">
            {history.length} consolidaciones · {memory.length} fragmentos totales
          </CardDescription>
          <div className="grid grid-cols-2 gap-2 pt-2">
            <button
              type="button"
              onClick={() => setMode("consolidations")}
              className={`rounded-[8px] border px-3 py-2 text-sm font-medium transition-colors ${
                mode === "consolidations" ? "border-[#3ecf8e]/60 bg-[#f1fcf7] text-[#168a5b]" : "border-neutral-200 bg-white text-neutral-600 hover:bg-neutral-50"
              }`}
            >
              Consolidado
            </button>
            <button
              type="button"
              onClick={() => setMode("memory")}
              className={`rounded-[8px] border px-3 py-2 text-sm font-medium transition-colors ${
                mode === "memory" ? "border-[#3ecf8e]/60 bg-[#f1fcf7] text-[#168a5b]" : "border-neutral-200 bg-white text-neutral-600 hover:bg-neutral-50"
              }`}
            >
              Por agente
            </button>
          </div>
          <div className="relative pt-2">
            <Search className="absolute left-3 top-1/2 size-4 translate-y-[-20%] text-neutral-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={mode === "consolidations" ? "Buscar consolidación..." : "Buscar memoria..."}
              className="h-9 rounded-[8px] border-neutral-200 bg-neutral-50 pl-9 text-sm shadow-none"
            />
          </div>
          {mode === "memory" ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {agentFilters.map((filter) => (
                <button
                  key={filter.value}
                  type="button"
                  onClick={() => setAgentFilter(filter.value)}
                  className={`rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
                    agentFilter === filter.value
                      ? "border-[#3ecf8e]/70 bg-[#e9fbf2] text-[#168a5b]"
                      : "border-neutral-200 bg-white text-neutral-500 hover:bg-neutral-50"
                  }`}
                >
                  {filter.label} <span className="text-neutral-400">{memoryCounts[filter.value]}</span>
                </button>
              ))}
            </div>
          ) : null}
        </CardHeader>
        <CardContent className="min-h-0 flex-1 p-0">
          <ScrollArea className="h-full">
            {loading ? (
              <div className="p-8 text-center text-sm text-neutral-500 animate-pulse">Cargando memoria...</div>
            ) : error ? (
              <div className="p-8 text-center text-sm text-red-500">{error}</div>
            ) : mode === "consolidations" && filteredHistory.length > 0 ? (
              <div className="space-y-2 p-3">
                {filteredHistory.map((item) => {
                  const selected = selectedItem?.id === item.id;
                  const category = cleanCategory(item.category);

                  return (
                  <button
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className={`group w-full rounded-[8px] border p-3 text-left transition-colors ${
                      selected
                        ? "border-[#3ecf8e]/60 bg-[#f1fcf7] shadow-sm"
                        : "border-transparent hover:border-neutral-200 hover:bg-neutral-50"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-2">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="truncate rounded-full border border-neutral-200 bg-white px-2 py-0.5 text-[11px] font-medium capitalize text-neutral-700">
                            {category}
                          </span>
                          <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
                            <CheckCircle2 className="size-3" />
                            {getStatusLabel(item.status)}
                          </span>
                        </div>
                        <p className="line-clamp-2 text-sm font-semibold leading-5 text-neutral-950">
                          {item.title || "Consolidación de memoria"}
                        </p>
                        <span className="inline-flex items-center gap-1 text-xs text-neutral-500">
                          <Calendar className="size-3.5" />
                          {formatDate(item.created_at)}
                        </span>
                      </div>
                      <ChevronRight className={`mt-8 size-4 shrink-0 text-neutral-400 transition-transform group-hover:text-neutral-700 ${selected ? "translate-x-0.5 text-[#168a5b]" : ""}`} />
                    </div>
                  </button>
                  );
                })}
              </div>
            ) : mode === "memory" && filteredMemory.length > 0 ? (
              <div className="space-y-2 p-3">
                {filteredMemory.map((item) => {
                  const selected = selectedMemory?.id === item.id;
                  const agent = agentFromCategory(item.category);

                  return (
                    <button
                      key={item.id || `${item.category}-${item.created_at}`}
                      onClick={() => setSelectedMemory(item)}
                      className={`group w-full rounded-[8px] border p-3 text-left transition-colors ${
                        selected
                          ? "border-[#3ecf8e]/60 bg-[#f1fcf7] shadow-sm"
                          : "border-transparent hover:border-neutral-200 hover:bg-neutral-50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1 space-y-2">
                          <div className="flex min-w-0 items-center gap-2">
                            <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-neutral-200 bg-white px-2 py-0.5 text-[11px] font-medium text-neutral-700">
                              <UserRound className="size-3" />
                              {agentLabel(agent)}
                            </span>
                            <span className="truncate rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] font-medium text-neutral-500">
                              {cleanCategory(item.category)}
                            </span>
                          </div>
                          <p className="line-clamp-3 text-sm font-medium leading-5 text-neutral-900">
                            {item.summary || "Fragmento sin resumen"}
                          </p>
                          <span className="inline-flex items-center gap-1 text-xs text-neutral-500">
                            <Calendar className="size-3.5" />
                            {item.created_at ? formatDate(item.created_at) : "Sin fecha"}
                          </span>
                        </div>
                        <ChevronRight className={`mt-8 size-4 shrink-0 text-neutral-400 transition-transform group-hover:text-neutral-700 ${selected ? "translate-x-0.5 text-[#168a5b]" : ""}`} />
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center text-sm text-neutral-500">
                {mode === "consolidations" ? "No hay consolidaciones que coincidan." : "No hay memoria para este agente/filtro."}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <Card className="flex min-h-0 flex-col overflow-hidden rounded-[10px] border-neutral-200 bg-white shadow-sm">
        {mode === "consolidations" && selectedItem ? (
          <>
            <CardHeader className="border-b border-neutral-200 bg-gradient-to-b from-white to-neutral-50 px-6 py-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e9fbf2] px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-[#168a5b]">
                      <Sparkles className="size-3.5" />
                      Memoria evolutiva
                    </span>
                    <Badge variant="outline" className="rounded-full border-neutral-200 bg-white px-2.5 text-xs text-neutral-600">
                      v{selectedItem.metadata?.batch || 1}.0
                    </Badge>
                  </div>
                  <CardTitle className="max-w-4xl text-2xl font-semibold tracking-tight text-neutral-950">
                    {cleanCategory(selectedItem.category)}
                  </CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-2 text-sm text-neutral-500">
                    <Clock3 className="size-4" />
                    Generado {formatDateTime(selectedItem.created_at)}
                  </CardDescription>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:min-w-[260px]">
                  <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                    <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Estado</p>
                    <p className="mt-1 text-sm font-semibold text-neutral-900">{getStatusLabel(selectedItem.status)}</p>
                  </div>
                  <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                    <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Fuentes</p>
                    <p className="mt-1 text-sm font-semibold text-neutral-900">{selectedItem.memory_count || "N/D"}</p>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="min-h-0 flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full">
                <div className="mx-auto max-w-5xl px-6 py-7">
                  <div className="rounded-[10px] border border-neutral-200 bg-white p-5 shadow-sm">
                    <div className="flex items-center gap-2 border-b border-neutral-100 pb-4">
                      <Layers3 className="size-4 text-neutral-500" />
                      <p className="text-sm font-semibold text-neutral-900">Síntesis consolidada</p>
                    </div>
                    <div className="space-y-3 pt-4">
                      {selectedItem.summary.split("\n").map(renderSummaryLine)}
                    </div>
                  </div>
                </div>
                <div className="border-t border-neutral-200 bg-neutral-50 px-6 py-4">
                  <div className="mx-auto grid max-w-5xl gap-3 sm:grid-cols-3">
                    <div className="flex items-center gap-3 rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <Brain className="size-4 text-[#168a5b]" />
                      <div>
                        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Algoritmo</p>
                        <p className="text-sm font-medium text-neutral-800">Recursive Synthesis</p>
                      </div>
                    </div>
                    <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Batch</p>
                      <p className="text-sm font-medium text-neutral-800">#{selectedItem.metadata?.batch || 1}</p>
                    </div>
                    <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Registro</p>
                      <p className="truncate text-sm font-medium text-neutral-800">{selectedItem.id}</p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </>
        ) : mode === "memory" && selectedMemory ? (
          <>
            <CardHeader className="border-b border-neutral-200 bg-gradient-to-b from-white to-neutral-50 px-6 py-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e9fbf2] px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-[#168a5b]">
                      <Database className="size-3.5" />
                      Memoria por agente
                    </span>
                    <Badge variant="outline" className="rounded-full border-neutral-200 bg-white px-2.5 text-xs text-neutral-600">
                      {agentLabel(agentFromCategory(selectedMemory.category))}
                    </Badge>
                  </div>
                  <CardTitle className="max-w-4xl text-2xl font-semibold tracking-tight text-neutral-950">
                    {cleanCategory(selectedMemory.category)}
                  </CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-2 text-sm text-neutral-500">
                    <Clock3 className="size-4" />
                    {selectedMemory.created_at ? `Registrado ${formatDateTime(selectedMemory.created_at)}` : "Sin fecha registrada"}
                  </CardDescription>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:min-w-[260px]">
                  <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                    <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Agente</p>
                    <p className="mt-1 text-sm font-semibold text-neutral-900">{agentLabel(agentFromCategory(selectedMemory.category))}</p>
                  </div>
                  <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                    <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Tipo</p>
                    <p className="mt-1 truncate text-sm font-semibold text-neutral-900">{selectedMemory.metadata?.type || "fragmento"}</p>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="min-h-0 flex-1 overflow-hidden p-0">
              <ScrollArea className="h-full">
                <div className="mx-auto max-w-5xl px-6 py-7">
                  <div className="rounded-[10px] border border-neutral-200 bg-white p-5 shadow-sm">
                    <div className="flex items-center gap-2 border-b border-neutral-100 pb-4">
                      <Brain className="size-4 text-neutral-500" />
                      <p className="text-sm font-semibold text-neutral-900">Fragmento de memoria</p>
                    </div>
                    <div className="space-y-3 pt-4">
                      {selectedMemory.summary.split("\n").map(renderSummaryLine)}
                    </div>
                  </div>
                </div>
                <div className="border-t border-neutral-200 bg-neutral-50 px-6 py-4">
                  <div className="mx-auto grid max-w-5xl gap-3 sm:grid-cols-3">
                    <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Categoría</p>
                      <p className="truncate text-sm font-medium text-neutral-800">{selectedMemory.category}</p>
                    </div>
                    <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Registro</p>
                      <p className="truncate text-sm font-medium text-neutral-800">{selectedMemory.id || "N/D"}</p>
                    </div>
                    <div className="rounded-[8px] border border-neutral-200 bg-white px-3 py-2">
                      <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-neutral-400">Metadata</p>
                      <p className="truncate text-sm font-medium text-neutral-800">
                        {selectedMemory.metadata && Object.keys(selectedMemory.metadata).length > 0
                          ? `${Object.keys(selectedMemory.metadata).length} campos`
                          : "Sin metadata"}
                      </p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center p-12 text-center text-neutral-500">
            <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-neutral-100">
              <Brain className="size-8 text-neutral-300" />
            </div>
            <h3 className="text-lg font-semibold text-neutral-950">Selecciona un registro</h3>
            <p className="mt-2 max-w-xs text-sm">
              Elige una consolidación o un fragmento de memoria para ver el detalle.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
