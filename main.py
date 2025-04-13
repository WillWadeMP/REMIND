#!/usr/bin/env python
"""
Main entry point for the REMIND system.
This version uses a new concept–graph memory system.
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import config
from src.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="REMIND - Retrieval-Enhanced Memory for Interactive Natural Dialogue"
    )
    parser.add_argument("--web", action="store_true", help="Run in web interface mode")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument(
        "--model", type=str, default=None, 
        help=f"Claude model to use (default: {config.CLAUDE_MODEL})"
    )
    parser.add_argument(
        "--port", type=int, default=config.WEB_PORT,
        help=f"Port for web interface (default: {config.WEB_PORT})"
    )
    parser.add_argument(
        "--host", type=str, default=config.WEB_HOST,
        help=f"Host for web interface (default: {config.WEB_HOST})"
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    return parser.parse_args()

def run_cli_mode(memory_manager: MemoryManager, model=None):
    """
    Run the system in CLI mode using the concept–graph memory.
    Each user message is processed to update the concept nodes, and a response is generated.
    """
    print("\nWelcome to REMIND CLI Mode!")
    print("Type 'exit' to quit, 'help' for commands\n")
    
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        elif user_input.lower() in ["help", "h", "?"]:
            print("\nEnter any message to talk to the assistant.")
            print("  exit  - Quit the program")
            print("  help  - Show this help message\n")
            continue
        
        # Process the input into concept nodes
        updated_concepts = memory_manager.process_memory(user_input)
        # Generate response using current concept nodes as context
        response = memory_manager.generate_response(query=user_input)
        
        print(f"\nAssistant: {response}")
        print(f"(Concepts updated: {', '.join(updated_concepts)})\n")

def run_web_mode(memory_manager: MemoryManager, host: str, port: int, debug: bool, model: str):
    """
    Run the web interface (updated to include conversation manager).
    """
    try:
        from web.app import run_web_app
        from src.conversation_manager import ConversationManager

        conversation_manager = ConversationManager()

        run_web_app(
            memory_manager_instance=memory_manager,
            conv_manager_instance=conversation_manager,
            host=host,
            port=port,
            debug=debug,
            model=model
        )
    except ImportError:
        print("Error: Web interface not available. Please install flask.")
        print("Run 'pip install flask' to install.")
        sys.exit(1)


def main():
    """Main function."""
    args = parse_args()
    
    # Override model if specified, otherwise use default from config
    model = args.model if args.model else config.CLAUDE_MODEL
    
    # Create (or use a new) directory for concept nodes
    concepts_dir = config.MEMORY_DIR / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the new MemoryManager with the concepts directory
    memory_manager = MemoryManager(concepts_dir=concepts_dir)
    
    # Choose mode
    if args.web:
        run_web_mode(memory_manager, host=args.host, port=args.port, debug=args.debug, model=model)
    elif args.cli:
        run_cli_mode(memory_manager, model=model)
    else:
        print("Please specify a mode: --cli or --web")
        print("Example: python main.py --cli")
        print("Run with --help for more options.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format=config.LOG_FORMAT,
                        handlers=[logging.FileHandler(config.LOG_FILE),
                                  logging.StreamHandler()])
    main()
