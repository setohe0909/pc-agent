import asyncio
import os
import json
from pathlib import Path
import httpx


async def _send_assistant_request(payload: dict) -> dict:
    base_url = _get_env("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{base_url}/assistant/request", json=payload)
    response.raise_for_status()
    return response.json()


def _get_env(key: str, default: str | None = None) -> str | None:
    # 1. Check environment
    val = os.getenv(key)
    if val:
        return val
    # 2. Check shared runtime config
    config_path = os.getenv("RUNTIME_CONFIG_PATH", "/config/runtime-config.json")
    try:
        if Path(config_path).exists():
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            return config.get(key.lower()) or default
    except Exception:
        pass
    return default


def _is_requests_channel(channel_id: int) -> bool:
    expected = _get_env("DISCORD_REQUESTS_CHANNEL_ID")
    return bool(expected) and str(channel_id) == expected


def _approvers() -> set[str]:
    return {value.strip() for value in _get_env("DISCORD_APPROVER_USER_IDS", "").split(",") if value.strip()}


async def main() -> None:
    token = None
    while not token:
        token = _get_env("DISCORD_BOT_TOKEN") or _get_env("DISCORD_TOKEN")
        if not token:
            print("Discord bot en espera: falta DISCORD_BOT_TOKEN o DISCORD_TOKEN en env o runtime config")
            await asyncio.sleep(10)

    import discord

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        print(f"Discord conectado como {client.user}")

    @client.event
    async def on_message(message) -> None:
        if message.author == client.user or not _is_requests_channel(message.channel.id):
            return

        content = message.content.strip()
        if not content.startswith(("!ask ", "!research ", "!approve_trade ", "!status")):
            return

        if content == "!status":
            try:
                base_url = _get_env("CONTROL_API_URL", "http://control-api:8000").rstrip("/")
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get(f"{base_url}/status")
                
                if resp.status_code == 200:
                    status_data = resp.json()
                    services = status_data.get("services", [])
                    report = "**PC Agent - System Status**\n"
                    for s in services:
                        emoji = "✅" if s["state"] == "healthy" else "❌" if s["state"] == "offline" else "⚠️"
                        report += f"{emoji} **{s['name']}**: {s['state']} ({s['detail']})\n"
                    await message.reply(report)
                else:
                    await message.reply(f"Error al obtener status: HTTP {resp.status_code}")
            except Exception as exc:
                await message.reply(f"No pude conectar con el Control API: {exc}")
            return

        action_type = "chat"
        prompt = content
        approval = None
        if content.startswith("!research "):
            action_type = "research"
            prompt = content.removeprefix("!research ").strip()
        elif content.startswith("!ask "):
            prompt = content.removeprefix("!ask ").strip()
        elif content.startswith("!approve_trade "):
            approvers = _approvers()
            if approvers and str(message.author.id) not in approvers:
                await message.reply("No estas autorizado para aprobar decisiones de trading.")
                return
            action_type = "trade_decision"
            prompt = content.removeprefix("!approve_trade ").strip()
            approval = {
                "status": "approved",
                "channel_id": str(message.channel.id),
                "approver_user_id": str(message.author.id),
                "message_id": str(message.id),
            }

        payload = {
            "action_type": action_type,
            "prompt": prompt,
            "source": {
                "platform": "discord",
                "channel_id": str(message.channel.id),
                "user_id": str(message.author.id),
            },
            "approval": approval,
        }
        try:
            result = await _send_assistant_request(payload)
            
            # Si es una decision de trade, enviamos un Embed profesional
            if action_type == "trade_decision" and result.get("status") == "executed":
                embed = discord.Embed(
                    title="🚀 Trade Ejecutado con Éxito",
                    description=result.get("message"),
                    color=discord.Color.green()
                )
                order = result.get("order", {})
                embed.add_field(name="Ticker", value=order.get("ticker", "N/A"), inline=True)
                embed.add_field(name="ID de Orden", value=order.get("order_id", "N/A"), inline=True)
                
                critic_note = result.get("critic_note", "Sin observaciones.")
                embed.add_field(name="🛡️ Nota del Crítico", value=critic_note, inline=False)
                
                embed.set_footer(text="Sistema Pro - Analista + Crítico + Motor de Riesgo")
                await message.reply(embed=embed)
            
            elif action_type == "trade_decision" and "rejected" in result.get("status", ""):
                # Embed para rechazos (Motor de riesgo o Critico)
                embed = discord.Embed(
                    title="⚠️ Trade Detenido por Seguridad",
                    description=result.get("message"),
                    color=discord.Color.orange()
                )
                await message.reply(embed=embed)
            else:
                # Respuesta normal para chat/research
                await message.reply(f"Estado: {result.get('status')}. {result.get('reason') or result.get('message')}")
        except Exception as exc:
            await message.reply(f"No pude contactar al runtime del asistente: {exc}")

    while True:
        try:
            await client.start(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                # Discord rate limit
                wait_time = 60
                print(f"RATE LIMIT: Discord nos ha bloqueado temporalmente (429). Durmiendo {wait_time}s antes de reintentar...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Error de conexion con Discord: {e}")
                await asyncio.sleep(10)
        except Exception as e:
            print(f"Error inesperado en el bot: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
