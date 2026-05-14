import { useState, useEffect } from "react";
import { History, Sparkles, Calendar, ChevronRight, Brain } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getJson } from "@/lib/api";

export function ConsolidationView() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<any>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await getJson("/intelligence/memory/consolidation");
      setHistory(data.history || []);
      if (data.history?.length > 0 && !selectedItem) {
        setSelectedItem(data.history[0]);
      }
    } catch (err) {
      console.error("Error fetching consolidation history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
      {/* Sidebar Historial */}
      <Card className="md:col-span-1 flex flex-col overflow-hidden">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="w-5 h-5 text-blue-500" />
            Historial de Consolidación
          </CardTitle>
          <CardDescription>Eventos de memoria de largo plazo</CardDescription>
        </CardHeader>
        <CardContent className="p-0 flex-1">
          <ScrollArea className="h-full">
            {loading ? (
              <div className="p-8 text-center text-muted-foreground animate-pulse">Cargando historial...</div>
            ) : history.length > 0 ? (
              <div className="divide-y">
                {history.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedItem(item)}
                    className={`w-full text-left p-4 hover:bg-muted/50 transition-colors flex items-center justify-between group ${
                      selectedItem === item ? "bg-blue-500/10 border-r-2 border-blue-500" : ""
                    }`}
                  >
                    <div className="space-y-1 overflow-hidden">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {item.category.replace("consolidated_", "")}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm font-medium truncate">
                        {item.summary.split('\n')[0].replace(/#/g, '').trim() || "Consolidación de Memoria"}
                      </p>
                    </div>
                    <ChevronRight className={`w-4 h-4 text-muted-foreground group-hover:text-blue-500 transition-transform ${selectedItem === item ? "rotate-90 text-blue-500" : ""}`} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">No hay registros de consolidación aún.</div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Visor de Contenido */}
      <Card className="md:col-span-2 flex flex-col overflow-hidden">
        {selectedItem ? (
          <>
            <CardHeader className="border-b bg-blue-500/5">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Memoria Evolutiva</span>
                  </div>
                  <CardTitle className="text-2xl">
                    Consolidación: {selectedItem.category.replace("consolidated_", "").toUpperCase()}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2 mt-1">
                    <Calendar className="w-4 h-4" />
                    Generado el {new Date(selectedItem.created_at).toLocaleString()}
                  </CardDescription>
                </div>
                <Badge className="bg-blue-600">v{selectedItem.metadata?.batch || 1}.0</Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-hidden">
              <ScrollArea className="h-full p-6">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {selectedItem.summary.split('\n').map((line: string, i: number) => {
                    if (line.startsWith('###')) return <h3 key={i} className="text-lg font-bold mt-4 mb-2 text-blue-500">{line.replace('###', '')}</h3>;
                    if (line.startsWith('##')) return <h2 key={i} className="text-xl font-bold mt-6 mb-3 border-b pb-1">{line.replace('##', '')}</h2>;
                    if (line.startsWith('#')) return <h1 key={i} className="text-2xl font-bold mt-8 mb-4">{line.replace('#', '')}</h1>;
                    if (line.startsWith('-') || line.startsWith('*')) return <li key={i} className="ml-4 mb-1">{line.substring(1).trim()}</li>;
                    return <p key={i} className="mb-3 text-sm leading-relaxed text-muted-foreground">{line}</p>;
                  })}
                </div>
                
                <div className="mt-8 pt-6 border-t border-dashed">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
                    <Brain className="w-4 h-4" />
                    <span>Metadatos de Consolidación</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/30 p-3 rounded-lg border">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Algoritmo</p>
                      <p className="text-xs">Recursive Long-Term Synthesis</p>
                    </div>
                    <div className="bg-muted/30 p-3 rounded-lg border">
                      <p className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Batch ID</p>
                      <p className="text-xs">#{selectedItem.metadata?.batch || 1}</p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Brain className="w-8 h-8 opacity-20" />
            </div>
            <h3 className="text-lg font-medium">Selecciona un registro</h3>
            <p className="text-sm max-w-xs mt-2">
              Elige un evento del historial para ver los aprendizajes consolidados por la IA.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
