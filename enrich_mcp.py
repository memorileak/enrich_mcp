import asyncio
import sys
import os

from mcp.server.fastmcp import FastMCP
from imports.enrich_provider import CopilotAuthManager, AsyncAnthropic, AsyncOpenAI
from imports.enrich_logging import logging

# Environment variables
ENRICHER_PROVIDER = os.environ.get("ENRICHER_PROVIDER", "anthropic").lower()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
COPILOT_MODEL = os.getenv("COPILOT_MODEL", "claude-sonnet-4.5")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "4096"))

logger = logging.getLogger("EnrichMCP")

# Initialize FastMCP
mcp = FastMCP("Enricher")

# Selecting and initializing the appropriate provider
if ENRICHER_PROVIDER == "copilot":
    copilot_auth = CopilotAuthManager()
elif ENRICHER_PROVIDER == "anthropic":
    anthropic = AsyncAnthropic()
else:
    logger.warning(f"Unknown provider '{ENRICHER_PROVIDER}'. Defaulting to Anthropic.")
    ENRICHER_PROVIDER = "anthropic"
    anthropic = AsyncAnthropic()

@mcp.tool()
async def enrich_architectural_context(raw_codegraph_data: str, target_focus: str) -> str:
    """
    Pass raw code snippets or graph data into this tool to have an AI Architect 
    analyze it, explain the data flow, and distill the context.
    
    Args:
        raw_codegraph_data: The raw output string previously retrieved from codegraph.
        target_focus: The name of the function, file, or feature you are trying to understand/modify.
    """
    logger.info(f"Received enrichment request for focus: {target_focus} using {ENRICHER_PROVIDER}")
    
    prompt = f"""
    You are an expert Principal Software Engineer. I am providing you with raw codebase data 
    retrieved from a code graph tool. The user's current focus is: `{target_focus}`.
    
    Your job is to process this raw data into a clean, token-efficient payload 
    for an AI coding assistant so it can write code accurately without hallucinating.

    Format your response exactly using these two XML tags:

    <pre_thinking>
    Perform an architectural breakdown. Explain: 
      - How this code works.
      - How data flows in and out.
      - What state mutations occur.
      - Highlight the most critical dependencies or callers. 
    Act as a mentor explaining the "gotchas" of this specific code execution path.
    </pre_thinking>

    <distilled_context>
    A concise, markdown-formatted summary containing ONLY what the coding assistant needs to know:
      - Exact function signatures and return types.
      - Required data structures / DTOs.
      - Immediate caller contexts.
    Drop all irrelevant noise, deep internal variables, or standard library imports.
    </distilled_context>

    Raw Code Graph Data:
    {raw_codegraph_data}
    """

    logger.info(f"Sending raw data to {ENRICHER_PROVIDER} for architectural enrichment...")
    
    if ENRICHER_PROVIDER == "copilot":
        try:
            copilot_token = await copilot_auth.get_valid_copilot_token()
            client = AsyncOpenAI(
                base_url="https://api.githubcopilot.com",
                api_key=copilot_token,
                default_headers=CopilotAuthManager.COMMON_HEADERS,
            )
            response = await client.chat.completions.create(
                model=COPILOT_MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )
            enriched_result = response.choices[0].message.content
            return enriched_result
        except Exception as e:
            logger.error(f"Copilot API error: {e}")
            return f"Error during Copilot enrichment: {e}"

    else:
        try:
            response = await anthropic.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )
            enriched_result = response.content[0].text
            return enriched_result
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error during Anthropic enrichment: {e}"

if __name__ == "__main__":
    mcp.run()
