from app.domain.model_status import AgentModelStatus, ModelConnection
from app.domain.ports.llm import LLMPort


class ModelStatusService:
    def __init__(self, llm: LLMPort) -> None:
        self.llm = llm

    def get_status(self, agent: str) -> dict:
        normalized_agent = _normalize_agent(agent)
        inventory = self.llm.model_inventory()
        status = _build_agent_status(normalized_agent, inventory)
        return {
            "status": "success",
            "message": status.to_message(),
            "model_status": status.to_dict(),
        }


def _normalize_agent(agent: str) -> str:
    normalized = (agent or "").strip().lower().replace("_", "-")
    aliases = {
        "marketer": "marketer",
        "marketing": "marketer",
        "picture": "picture",
        "image": "picture",
        "claw": "claw",
        "open-claw": "claw",
        "writer": "writer",
        "email": "email",
        "mail": "email",
        "coder": "coder-web",
        "coder-web": "coder-web",
        "pilot": "coder-web",
    }
    return aliases.get(normalized, normalized or "claw")


def _build_agent_status(agent: str, inventory: dict) -> AgentModelStatus:
    text_cheap = _connection_from_inventory(inventory, "text_cheap", "Chat / redacción rápida")
    text_smart = _connection_from_inventory(inventory, "text_smart", "Razonamiento / tools")
    image_generation = _connection_from_inventory(inventory, "image_generation", "Generación de imagen")
    image_edit = _connection_from_inventory(inventory, "image_edit", "Edición de imagen")

    if agent == "marketer":
        return AgentModelStatus(
            agent="marketer",
            display_name="Marketer Agent",
            connections=[
                _with_purpose(text_smart, "Intención y herramientas"),
                _with_purpose(text_cheap, "Copys, análisis y respuestas"),
                _with_purpose(image_generation, "Visuales con --free-model"),
                _with_purpose(image_edit, "Edición visual con imagen adjunta"),
            ],
            warnings=_shared_warnings(inventory),
        )
    if agent == "picture":
        return AgentModelStatus(
            agent="picture",
            display_name="Picture Agent",
            connections=[
                _with_purpose(text_cheap, "Plan creativo y verificación"),
                image_generation,
                image_edit,
            ],
            warnings=_shared_warnings(inventory),
        )
    if agent == "writer":
        return AgentModelStatus(
            agent="writer",
            display_name="Writer Agent",
            connections=[
                _with_purpose(text_cheap, "Blogs, storytelling y chat"),
                _with_purpose(text_cheap, "Keywords para imagen sugerida"),
            ],
            warnings=[],
        )
    if agent == "coder-web":
        return AgentModelStatus(
            agent="coder-web",
            display_name="Coder Web Agent",
            connections=[
                _with_purpose(text_cheap, "Análisis de mockups y referencias"),
                _with_purpose(text_cheap, "Plan técnico y revisión"),
                ModelConnection(
                    purpose="Ejecución externa",
                    provider="pilot-web",
                    model="repository adapter",
                    status="configured",
                    detail="Usa el adapter Pilot Web para crear o ajustar repositorios.",
                ),
            ],
            warnings=[],
        )
    if agent == "email":
        return AgentModelStatus(
            agent="email",
            display_name="Email Agent",
            connections=[
                _with_purpose(text_smart, "Clasificacion, filtros y seleccion de template"),
                _with_purpose(text_cheap, "Resumenes de bandeja y borradores"),
                ModelConnection(
                    purpose="Proveedor de email",
                    provider="google/outlook/imap_smtp/pc_client",
                    model="adapter port",
                    status="configured",
                    detail="La UI administra proveedor, credenciales, permisos de envio, templates y rate limits.",
                ),
            ],
            warnings=[
                "Bulk replies requieren aprobacion humana, idempotencia, auditoria y limites por proveedor antes de enviar."
            ],
        )
    return AgentModelStatus(
        agent="claw",
        display_name="Open Claw",
        connections=[
            _with_purpose(text_cheap, "Chat general"),
            _with_purpose(text_cheap, "Research conversacional"),
        ],
        warnings=[],
    )


def _connection_from_inventory(inventory: dict, key: str, purpose: str) -> ModelConnection:
    data = inventory.get(key, {})
    return ModelConnection(
        purpose=purpose,
        provider=data.get("provider", "unknown"),
        model=data.get("model", "unknown"),
        status=data.get("status", "unknown"),
        detail=data.get("detail", "Sin detalle."),
    )


def _with_purpose(connection: ModelConnection, purpose: str) -> ModelConnection:
    return ModelConnection(
        purpose=purpose,
        provider=connection.provider,
        model=connection.model,
        status=connection.status,
        detail=connection.detail,
    )


def _shared_warnings(inventory: dict) -> list[str]:
    warnings = []
    if inventory.get("image_generation", {}).get("provider") == "together":
        warnings.append("`--free-model` requiere `TOGETHER_API_KEY`; si falta, la generación visual fallará.")
    if inventory.get("image_edit", {}).get("provider") == "local":
        warnings.append("La edición local requiere `PICTURE_LOCAL_IMAGE_EDIT_URL` disponible.")
    return warnings
