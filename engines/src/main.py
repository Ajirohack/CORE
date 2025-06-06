"""
Command-line interface for running the System Engine Control.
"""
import os
import sys
import logging
import argparse
from dotenv import load_dotenv

from .api import create_api_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("engine_control.main")


def main():
    """Run the System Engine Control API service."""
    parser = argparse.ArgumentParser(description="Run the System Engine Control API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger("engine_control").setLevel(logging.DEBUG)
    
    logger.info("Starting System Engine Control API")
    
    # In a real implementation, you would load the required components
    # ai_council = import_module("core.ai_council.src").AICouncil()
    # rag_system = import_module("core.rag_system.src").RAGSystem()
    # tools_system = import_module("core.tools_packages.src").ToolsSystem()
    
    # For now, we're using mock placeholders
    ai_council = None
    rag_system = None
    tools_system = None
    
    # Create the config
    config = {
        "debug": args.debug,
        "api_key": os.getenv("OPENAI_API_KEY"),
        "environment": os.getenv("ENV", "development")
    }
    
    # Create and run the API service
    api_service = create_api_service(
        ai_council=ai_council,
        rag_system=rag_system,
        tools_system=tools_system,
        config=config
    )
    
    logger.info(f"API service running at http://{args.host}:{args.port}")
    api_service.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()