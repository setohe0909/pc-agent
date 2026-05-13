import httpx
import json

api_key = "IST.eyJraWQiOiJQb3pIX2FDMiIsImFsZyI6IlJTMjU2In0.eyJkYXRhIjoie1wiaWRcIjpcImQ1NzE4NWM5LWI2NDItNDYyZS1iMGNjLTczNjQ1MGU0NjAzMVwiLFwiaWRlbnRpdHlcIjp7XCJ0eXBlXCI6XCJhcHBsaWNhdGlvblwiLFwiaWRcIjpcIjE0OTlkZTM0LWNiMDYtNDA0Ni1iZWRhLTg3MGY1MWYwYTRmMVwifSxcInRlbmFudFwiOntcInR5cGVcIjpcImFjY291bnRcIixcImlkXCI6XCI5ZDFkNzc3OC0wNTEzLTRiOGYtOTJhZi0wMWVjZjI5YTNiYzhcIn19IiwiaWF0IjoxNzc4Njk1MzI2fQ.G4xVJ_DiZhGGQf_rKyRNCwy7tdjMUezgzEMpY_WZyyU49TgUhxuw-Xa57fN0xYH26-qD7m6w6kjf-qH2vQ69nJs5RODT0eIvJmEVqZarMCL7Br0tYCEekZliOe_i2bysjWZovo1VEmlSXPevqw0_Dfi9-H0p1PWvm9XGEFm9pmpVGTxuxyH0Ba5kEAEbctfXAs002QNaLmpUKVtobE0bcDb9SRVeSfYw03Q8wHhaSM2F1GVAqQAHedU8DBSqsg5URi1tHjia8OLPTmIcrvUNjwtHxrN8wqZZTS1c9epxTLfObNpBXULJP2T4ZEYTQBEnVNYxQwv-SMlfN7Flxhh92w"
site_id = "289e82d6-3474-4141-b6ea-aba3112ff2db"
account_id = "9d1d7778-0513-4b8f-92af-01ecf29a3bc8"

headers = {
    "Authorization": api_key,
    "wix-site-id": site_id,
    "wix-account-id": account_id,
    "Content-Type": "application/json"
}

async def test_wix():
    urls = [
        # 1. Wix Stores - Query Products
        "https://www.wixapis.com/stores/v1/products/query"
    ]
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            print(f"\n--- Testing URL: {url} ---")
            try:
                resp = await client.post(url, headers=headers, json={"query": {}})
                print(f"Status: {resp.status_code}")
                print(f"Response: {resp.text[:500]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_wix())
