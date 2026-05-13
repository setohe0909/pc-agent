import { useEffect, useState } from "react";
import { getLeads } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, RefreshCw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LeadsView() {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const data = await getLeads();
      setLeads(data.leads || []);
    } catch (err) {
      console.error("Error cargando leads", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-card p-4 rounded-lg border shadow-sm">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-500" />
            CRM: Marketing Leads
          </h2>
          <p className="text-xs text-muted-foreground">Prospectos calificados automáticamente por el agente PC Agent v0.5.0</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchLeads} disabled={loading} className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refrescar
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-md">Prospectos Capturados</CardTitle>
          <CardDescription>Lista de usuarios con alta intención de compra detectados en redes sociales.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                <tr>
                  <th className="px-4 py-3 font-medium">Fecha</th>
                  <th className="px-4 py-3 font-medium">Plataforma</th>
                  <th className="px-4 py-3 font-medium">Usuario</th>
                  <th className="px-4 py-3 font-medium">Categoría</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Razón</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {leads.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-muted-foreground">
                      No se han encontrado leads calificados todavía.
                    </td>
                  </tr>
                )}
                {leads.map((lead, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-4 text-xs font-mono">
                      {new Date(lead.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant="outline" className="capitalize">{lead.platform}</Badge>
                    </td>
                    <td className="px-4 py-4 font-medium">
                      <div className="flex items-center gap-2">
                        {lead.external_user}
                        <ExternalLink className="w-3 h-3 text-muted-foreground cursor-pointer" />
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <Badge className={lead.category === 'hot' ? 'bg-red-500 hover:bg-red-600' : 'bg-orange-500 hover:bg-orange-600'}>
                        {lead.category}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 font-bold text-indigo-600">
                      {lead.intent_score}/10
                    </td>
                    <td className="px-4 py-4 text-xs text-muted-foreground italic max-w-xs truncate">
                      "{lead.reason}"
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
