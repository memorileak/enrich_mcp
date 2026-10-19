import sys
import logging

# Route logging to stderr to prevent breaking the MCP stdio stream
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s]::%(levelname)s::%(name)s %(message)s',
    stream=sys.stderr 
)
