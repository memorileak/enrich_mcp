import asyncio
import sys
import logging
import os
from mcp.server.fastmcp import FastMCP
from anthropic import AsyncAnthropic

# Route logging to stderr to prevent breaking the MCP stdio stream
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr 
)
logger = logging.getLogger("ClaudeEnricher")

# Initialize FastMCP
mcp = FastMCP("ClaudeContextEnricher")

# Anthropic client (automatically uses ANTHROPIC_API_KEY from environment)
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
    logger.info(f"Received enrichment request for focus: {target_focus}")
    
    prompt = f"""
    You are an expert Principal Software Engineer. I am providing you with raw codebase data 
    retrieved from a code graph tool. The user's current focus is: `{target_focus}`.
    
    Your job is to process this raw data into a clean, token-efficient payload 
    for an AI coding assistant (GitHub Copilot) so it can write code accurately without hallucinating.

    Format your response exactly using these two XML tags:

    <pre_thinking>
    Perform an architectural breakdown. Explain how this code works, how data flows in and out, 
    what state mutations occur, and highlight the most critical dependencies or callers. 
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

    logger.info("Sending raw data to Anthropic for architectural enrichment...")
    
    try:
        response = await anthropic.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        enriched_result = response.content[0].text
        logger.info("Successfully enriched context.")
        return enriched_result
        
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return f"Error during Anthropic enrichment: {e}"

if __name__ == "__main__":
    mcp.run()
