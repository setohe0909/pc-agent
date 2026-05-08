import asyncio
import os

import httpx


def _approvers() -> set[str]:
    return {value.strip() for value in os.getenv("DISCORD_APPROVER_USER_IDS", "").split(",") if value.strip()}


def _is_requests_channel(channel_id: int) -> bool:
    expected = os.getenv("DISCORD_REQUESTS_CHANNEL_ID")
    return bool(expected) and str(channel_id) == expected


async def _send_assistant_request(payload: dict) -> dict:
    base_url = os.getenv("OPEN_CLAW_BASE_URL", "http://assistant-runtime:8100").rstrip("/")
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(f"{base_url}/assistant/request", json=payload)
    response.raise_for_status()
    return response.json()


async def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Discord bot en espera: falta DISCORD_BOT_TOKEN")
        while True:
            await asyncio.sleep(3600)

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
        if not content.startswith(("!ask ", "!research ", "!approve_trade ")):
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
            await message.reply(f"Estado: {result.get('status')}. {result.get('reason') or result.get('message')}")
        except Exception as exc:
            await message.reply(f"No pude contactar al runtime del asistente: {exc}")

    await client.start(token)


if __name__ == "__main__":
    asyncio.run(main())
