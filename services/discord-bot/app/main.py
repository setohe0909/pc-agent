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
    from discord.ui import Button, View

    class TradeView(View):
        def __init__(self, payload, message_author):
            super().__init__(timeout=120)
            self.payload = payload
            self.message_author = message_author

        @discord.ui.button(label="✅ Confirmar Orden", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != str(self.message_author.id):
                await interaction.response.send_message("No eres el autor de esta solicitud.", ephemeral=True)
                return
            
            await interaction.response.edit_message(content="⏳ Procesando ejecución con análisis dual...", view=None)
            try:
                result = await _send_assistant_request(self.payload)
                
                if result.get("status") == "executed":
                    embed = discord.Embed(
                        title="🚀 TRADE EJECUTADO",
                        description=result.get("message"),
                        color=discord.Color.green()
                    )
                    order = result.get("order", {})
                    embed.add_field(name="Ticker", value=order.get("ticker", "N/A"), inline=True)
                    embed.add_field(name="ID Orden", value=order.get("order_id", "N/A"), inline=True)
                    embed.add_field(name="🛡️ Nota Crítica", value=result.get("critic_note", "N/A"), inline=False)
                    embed.set_footer(text="Confirmado vía botón - PC Agent Pro")
                    await interaction.message.edit(content=None, embed=embed)
                else:
                    embed = discord.Embed(
                        title="⚠️ Operación Detenida",
                        description=result.get("message"),
                        color=discord.Color.orange()
                    )
                    await interaction.message.edit(content=None, embed=embed)
            except Exception as e:
                await interaction.message.edit(content=f"❌ Error técnico: {e}", embed=None)

        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="🚫 Orden cancelada y descartada.", embed=None, view=None)

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
                async with httpx.AsyncClient(timeout=5) as client_http:
                    resp = await client_http.get(f"{base_url}/status")
                
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
            
            payload = {
                "action_type": action_type,
                "prompt": prompt,
                "source": {"platform": "discord", "channel_id": str(message.channel.id), "user_id": str(message.author.id)},
                "approval": {"status": "approved"}
            }

            embed = discord.Embed(
                title="⚖️ Confirmación de Operación",
                description=f"Instrucción: **{prompt}**\n\n¿Deseas que el Analista y el Crítico procesen esta orden?",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Haz clic en un botón para proceder.")
            
            await message.reply(embed=embed, view=TradeView(payload, message.author))
            return

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
            await message.reply(f"Respuesta: {result.get('message')}")
        except Exception as exc:
            await message.reply(f"No pude contactar al runtime: {exc}")

    while True:
        try:
            await client.start(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
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
