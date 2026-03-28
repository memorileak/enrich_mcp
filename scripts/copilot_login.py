import asyncio

from imports.enrich_provider import CopilotAuthManager

async def login_and_print():
    auth_manager = CopilotAuthManager()
    token = await auth_manager.get_valid_copilot_token()
    return token

if __name__ == "__main__":
    token = asyncio.run(login_and_print())
    print(f"Obtained and saved Copilot Token: {token}")
