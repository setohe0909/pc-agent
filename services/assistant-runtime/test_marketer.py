import asyncio
from app.main import assistant_request, AssistantRequest, ActionType, Source

async def main():
    req = AssistantRequest(
        action_type=ActionType.marketing,
        prompt="Genera un dashboard de mis métricas actuales",
        source=Source(platform="discord", user_id="123")
    )
    res = await assistant_request(req)
    print(res)

asyncio.run(main())
