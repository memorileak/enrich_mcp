import asyncio
import os
import sys
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def run_test():
    # 1. Define how to launch the MCP server
    # We pass the current environment variables so the server gets our API keys.
    env = os.environ.copy()

    # Print environment variables for debugging 
    print("Current Environment Variables:")
    for key in ["ENRICHER_PROVIDER", "ANTHROPIC_MODEL", "COPILOT_MODEL", "MAX_OUTPUT_TOKENS"]:
        print(f"{key}={env.get(key)}")
    print("\n")

    if "ENRICHER_PROVIDER" not in env:
        print("Warning: ENRICHER_PROVIDER not set. Defaulting to 'anthropic'.")
        env["ENRICHER_PROVIDER"] = "anthropic"
    
    server_params = StdioServerParameters(
        command=sys.executable, # Uses the current python environment
        args=["enrich_mcp.py"], # <-- Change this if your server script has a different name
        env=env
    )

    print(f"Starting MCP client and launching server with provider: {env['ENRICHER_PROVIDER']}...")
    
    # 2. Connect to the server over stdio
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Must initialize the connection before calling tools
            await session.initialize()
            print("Successfully connected and initialized!\n")

            # 3. Setup dummy payload for the test
            test_raw_data = ""
            test_focus = ""

            if os.path.exists("sample/mcp_input_sample.json"):
                with open("sample/mcp_input_sample.json", "r") as f:
                    sample_data = json.load(f)
                    test_raw_data = sample_data.get("raw_codegraph_data", test_raw_data)
                    test_focus = sample_data.get("target_focus", test_focus)

            print(f"Calling tool 'enrich_architectural_context' for focus: '{test_focus}'...")
            print("Waiting for response (check stderr above if testing Copilot for the first time)...\n")
            
            # 4. Execute the tool
            result = await session.call_tool(
                "enrich_architectural_context",
                arguments={
                    "raw_codegraph_data": test_raw_data,
                    "target_focus": test_focus
                }
            )

            # 5. Output the result
            print("=========================================")
            print("           ENRICHMENT RESULT             ")
            print("=========================================")
            for content in result.content:
                if content.type == "text":
                    print(content.text)
            print("=========================================")

if __name__ == "__main__":
    asyncio.run(run_test())
