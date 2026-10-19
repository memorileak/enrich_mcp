# GitHub Copilot Login Script

```bash
cd /path/to/cplogin
python -m scripts.copilot_login
```

Follow the printed instructions — visit the URL and enter the device code in your browser. The token is saved to `~/.config/cplogin/oauth_token.json` and reused on subsequent runs.

> **Note:** If you already have GitHub Copilot authenticated in VS Code, the token at `~/.config/github-copilot/hosts.json` is picked up automatically — no login step needed.
