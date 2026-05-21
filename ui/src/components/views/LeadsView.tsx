import { useEffect, useMemo, useState } from "react";
import { getLeads } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, RefreshCw, Search, Target, TrendingUp, Users } from "lucide-react";

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

  const stats = useMemo(() => {
    const hot = leads.filter((lead) => lead.category === "hot").length;
    const avgScore = leads.length
      ? (leads.reduce((sum, lead) => sum + Number(lead.intent_score || 0), 0) / leads.length).toFixed(1)
      : "0.0";
    const platforms = new Set(leads.map((lead) => lead.platform).filter(Boolean)).size;

    return [
      { label: "Leads capturados", value: leads.length.toString(), icon: Users },
      { label: "Alta intención", value: hot.toString(), icon: Target },
      { label: "Score promedio", value: avgScore, icon: TrendingUp },
      { label: "Plataformas", value: platforms.toString(), icon: Search },
    ];
  }, [leads]);

  return (
    <div className="space-y-5 pb-10">
      <section className="rounded-[10px] border border-neutral-200 bg-white px-5 py-4 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-neutral-950 text-white">
              <Users className="size-5" />
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-semibold tracking-tight text-neutral-950">CRM: Marketing Leads</h2>
                <Badge className="rounded-full bg-indigo-50 text-indigo-700 hover:bg-indigo-50">Pipeline</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">Prospectos calificados automáticamente por el agente PC Agent.</p>
            </div>
          </div>
          <Button variant="outline" onClick={fetchLeads} disabled={loading} className="h-10 gap-2 rounded-[8px] border-neutral-200 bg-white px-4 shadow-sm">
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
            Refrescar
          </Button>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
            <CardHeader className="p-4">
              <div className="mb-4 flex size-9 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-700">
                <stat.icon className="size-4" />
              </div>
              <CardDescription className="text-sm text-neutral-500">{stat.label}</CardDescription>
              <CardTitle className="text-3xl font-semibold tracking-tight text-neutral-950">{stat.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card className="rounded-[10px] border-neutral-200 bg-white shadow-sm">
        <CardHeader className="border-b border-neutral-200 px-5 py-4">
          <CardTitle className="text-base font-semibold text-neutral-950">Prospectos capturados</CardTitle>
          <CardDescription className="text-sm text-neutral-500">Usuarios con señales de intención detectadas en redes sociales.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-neutral-200 bg-neutral-50 text-xs uppercase text-neutral-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Fecha</th>
                  <th className="px-5 py-3 font-semibold">Plataforma</th>
                  <th className="px-5 py-3 font-semibold">Usuario</th>
                  <th className="px-5 py-3 font-semibold">Categoría</th>
                  <th className="px-5 py-3 font-semibold">Score</th>
                  <th className="px-5 py-3 font-semibold">Razón</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                {leads.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="px-5 py-16">
                      <div className="mx-auto flex max-w-md flex-col items-center text-center">
                        <span className="mb-3 flex size-10 items-center justify-center rounded-[8px] bg-neutral-100 text-neutral-500">
                          <Search className="size-5" />
                        </span>
                        <p className="text-sm font-semibold text-neutral-950">Todavía no hay leads calificados</p>
                        <p className="mt-1 text-sm leading-6 text-neutral-500">
                          Cuando el agente detecte intención de compra, los prospectos aparecerán aquí con score, plataforma y razón.
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
                {leads.map((lead, idx) => (
                  <tr key={idx} className="transition-colors hover:bg-neutral-50">
                    <td className="px-5 py-4 font-mono text-xs text-neutral-500">
                      {new Date(lead.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-5 py-4">
                      <Badge variant="outline" className="rounded-full capitalize">{lead.platform}</Badge>
                    </td>
                    <td className="px-5 py-4 font-medium text-neutral-950">
                      <div className="flex items-center gap-2">
                        {lead.external_user}
                        <ExternalLink className="size-3 text-neutral-400" />
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <Badge className={lead.category === "hot" ? "rounded-full bg-red-50 text-red-700 hover:bg-red-50" : "rounded-full bg-amber-50 text-amber-700 hover:bg-amber-50"}>
                        {lead.category}
                      </Badge>
                    </td>
                    <td className="px-5 py-4 font-semibold text-neutral-950">{lead.intent_score}/10</td>
                    <td className="max-w-xs truncate px-5 py-4 text-xs text-neutral-500">{lead.reason}</td>
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
