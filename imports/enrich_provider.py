import asyncio
import sys
import os
import json
import time
import httpx

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from imports.enrich_logging import logging

logger = logging.getLogger("EnrichProvider")

class CopilotAuthManager:
    """Handles GitHub Device Auth, OAuth tokens, and Copilot Token refreshing."""
    CLIENT_ID = "01ab8ac9400c4e429b23" # Hardcoded client ID for GitHub Copilot extension (publicly known)
    TOKEN_FILE = os.path.expanduser("~/.config/enrich_mcp/oauth_token.json")

    COMMON_HEADERS = {
        "User-Agent": "GithubCopilot/1.388.0",
        "Editor-Plugin-Version": "copilot/1.388.0",
        "Editor-Version": "vscode/1.112.0",
        "Copilot-Integration-Id": "vscode-chat"
    }

    def __init__(self):
        self.oauth_token = None
        self.copilot_token = None
        self.token_expires_at = 0
        self._load_oauth_token()

    def _load_oauth_token(self):
        std_path = os.path.expanduser("~/.config/github-copilot/hosts.json")
        if os.path.exists(std_path):
            try:
                with open(std_path, 'r') as f:
                    data = json.load(f)
                    self.oauth_token = data.get("github.com", {}).get("oauth_token")
                    if self.oauth_token:
                        logger.info("Found existing Copilot OAuth token in standard VSCode config.")
                        return
            except Exception:
                pass

        if os.path.exists(CopilotAuthManager.TOKEN_FILE):
            try:
                with open(CopilotAuthManager.TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.oauth_token = data.get("oauth_token")
            except Exception:
                pass

    def _save_oauth_token(self):
        os.makedirs(os.path.dirname(CopilotAuthManager.TOKEN_FILE), exist_ok=True)
        with open(CopilotAuthManager.TOKEN_FILE, 'w') as f:
            json.dump({"oauth_token": self.oauth_token}, f)

    async def _authenticate_device(self):
        if self.oauth_token:
            return

        logger.info("Starting GitHub Device Flow authentication...")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://github.com/login/device/code",
                json={"client_id": CopilotAuthManager.CLIENT_ID, "scope": "read:user"},
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()

            print(f"\n=======================================================", file=sys.stderr)
            print(f"ACTION REQUIRED: Please authenticate with GitHub Copilot", file=sys.stderr)
            print(f"1. Go to: {data['verification_uri']}", file=sys.stderr)
            print(f"2. Enter the code: {data['user_code']}", file=sys.stderr)
            print(f"=======================================================\n", file=sys.stderr)

            interval = data["interval"]
            while True:
                await asyncio.sleep(interval)
                poll_resp = await client.post(
                    "https://github.com/login/oauth/access_token",
                    json={
                        "client_id": CopilotAuthManager.CLIENT_ID,
                        "device_code": data["device_code"],
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    },
                    headers={"Accept": "application/json"}
                )
                poll_data = poll_resp.json()

                if "access_token" in poll_data:
                    self.oauth_token = poll_data["access_token"]
                    self._save_oauth_token()
                    logger.info("Successfully authenticated with GitHub!")
                    break
                elif poll_data.get("error") == "authorization_pending":
                    continue
                elif poll_data.get("error") == "slow_down":
                    interval += 5
                else:
                    raise Exception(f"Auth failed: {poll_data}")

    async def get_valid_copilot_token(self) -> str:
        await self._authenticate_device()

        if self.copilot_token and time.time() < (self.token_expires_at - 300):
            return self.copilot_token

        logger.info("Requesting/refreshing Copilot access token...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/copilot_internal/v2/token",
                headers=CopilotAuthManager.COMMON_HEADERS | {
                    "Authorization": f"token {self.oauth_token}",
                    "Accept": "application/json"
                }
            )
            if resp.status_code != 200:
                self.oauth_token = None
                if os.path.exists(CopilotAuthManager.TOKEN_FILE):
                    os.remove(CopilotAuthManager.TOKEN_FILE)
                raise Exception("Failed to get Copilot token. Credentials cleared. Please restart.")

            data = resp.json()
            self.copilot_token = data["token"]
            self.token_expires_at = data["expires_at"]
            return self.copilot_token
