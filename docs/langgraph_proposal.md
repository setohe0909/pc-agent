# Propuesta de Integración: LangGraph

Para transformar el `MarketingWorkflow` actual de un despachador `if/elif` a un agente autónomo y resiliente, podemos usar **LangGraph**.

## 1. Definición del Estado (State)

El grafo necesita un objeto que guarde el progreso:

```python
from typing import TypedDict, List, Optional

class MarketingState(TypedDict):
    prompt: str
    target_platform: str
    context_retrieved: bool
    competitor_data: Optional[dict]
    strategy_draft: Optional[str]
    human_approval: bool
    execution_result: Optional[str]
    errors: List[str]
```

## 2. Nodos del Grafo

Cada nodo es una función que procesa el estado:

1.  **RetrieveContext**: Busca en la memoria (Mentis/Supabase) sobre la marca.
2.  **ResearchCompetitors**: Si el prompt lo requiere, usa el adapter de marketing.
3.  **GenerateStrategy**: El LLM crea el plan basado en contexto + research.
4.  **HumanApprovalNode**: Un nodo que pausa la ejecución hasta que alguien haga clic en "Aprobar" en Discord.
5.  **ExecuteAction**: Publica o responde según la estrategia.

## 3. Estructura del Grafo

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(MarketingState)

# Agregar nodos
workflow.add_node("retrieve", retrieve_context_node)
workflow.add_node("research", research_node)
workflow.add_node("generate", generate_node)
workflow.add_node("approval", human_approval_node)
workflow.add_node("execute", execute_node)

# Definir flujo
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "research")
workflow.add_edge("research", "generate")
workflow.add_edge("generate", "approval")

# Condicional: Si es aprobado, ejecutar; si no, volver a generar
workflow.add_conditional_edges(
    "approval",
    lambda x: "execute" if x["human_approval"] else "generate"
)
workflow.add_edge("execute", END)

app = workflow.compile()
```

## 4. Por qué usar LangGraph aquí

1.  **Resiliencia**: Si el nodo `research` falla por API Rate Limit, LangGraph puede reintentar solo ese paso.
2.  **Control Humano**: La pausa en `approval` es nativa. El estado se guarda en un `Checkpointer` (puede ser Supabase).
3.  **Transparencia (Observabilidad)**: Podemos ver exactamente en qué nodo se encuentra el agente desde la UI de control o Langfuse.

## 5. Pasos para Implementar

1.  Agregar `langgraph` a `requirements.txt`.
2.  Refactorizar `MarketingWorkflow` para extraer sus métodos privados (`_respond_to_comments`, etc.) como nodos del grafo.
3.  Implementar un `Checkpointer` que use Supabase para que los grafos sobrevivan a reinicios del contenedor.
