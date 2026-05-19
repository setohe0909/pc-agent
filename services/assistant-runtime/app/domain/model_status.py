from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelConnection:
    purpose: str
    provider: str
    model: str
    status: str
    detail: str

    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AgentModelStatus:
    agent: str
    display_name: str
    connections: list[ModelConnection]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "display_name": self.display_name,
            "connections": [connection.to_dict() for connection in self.connections],
            "warnings": self.warnings,
        }

    def to_message(self) -> str:
        lines = [f"**{self.display_name} - Model Status**"]
        for connection in self.connections:
            icon = "✅" if connection.status == "configured" else "⚠️"
            lines.append(
                f"{icon} **{connection.purpose}**\n"
                f"Proveedor: `{connection.provider}`\n"
                f"Modelo: `{connection.model}`\n"
                f"Estado: `{connection.status}` - {connection.detail}"
            )
        if self.warnings:
            lines.append("**Notas**")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n\n".join(lines)
