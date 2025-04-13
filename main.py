#!/usr/bin/env python
"""
Main entry point for the REMIND system.
"""
import os
import sys
import logging
import argparse
import config
from src.memory_layer import MemoryLayer
from src.prompt_handler import PromptHandler
from src.relevancer import Relevancer
from src.response_generator import ResponseGenerator
from src.memory_updater import MemoryUpdater

# Check if we want to run in web mode
if "--web" in sys.argv:
    from web_interface.app import start_web_app

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="REMIND - Retrieval of Episodic & Metadata-Indexed Information for Natural Dialogue")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--web", action="store_true", help="Run in web interface mode")
    parser.add_argument("--model", type=str, default=None, help=f"Claude model to use (default: {config.CLAUDE_MODEL})")
    parser.add_argument("--port", type=int, default=5000, help="Port for web interface (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for web interface (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    return parser.parse_args()

def run_cli_mode(args):
    """Run the system in CLI mode."""
    print("Starting REMIND in CLI mode...")
    
    # Set up logging with correct level
    log_level_int = getattr(logging, config.LOG_LEVEL, logging.INFO)
    if args.debug:
        log_level_int = logging.DEBUG
    
    # Initialize components
    memory_layer = MemoryLayer()
    prompt_handler = PromptHandler()
    relevancer = Relevancer(memory_layer)
    response_generator = ResponseGenerator()
    memory_updater = MemoryUpdater(memory_layer)
    
    # Update model if specified
    if args.model:
        config.CLAUDE_MODEL = args.model
        print(f"Using model: {config.CLAUDE_MODEL}")
    
    print("Type 'exit' to quit.")
    
    # CLI loop
    while True:
        user_input = input("\nYou: ").strip()
        
        # Check if the user wants to exit
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        try:
            # Process the prompt
            processed_prompt = prompt_handler.process(user_input)
            
            # Retrieve relevant memories
            relevant_memories = relevancer.retrieve(processed_prompt)
            
            # Generate a response
            response = response_generator.generate(user_input, relevant_memories)
            
            # Update memories
            memory_updater.update(user_input, response)
            
            # Print the response
            print(f"\nAssistant: {response}")
            
        except Exception as e:
            print(f"\nAn error occurred: {e}")

def main():
    """Main function."""
    args = parse_args()
    
    # Override log level if in debug mode
    if args.debug:
        log_level_str = "DEBUG"
        log_level_int = logging.DEBUG
    else:
        log_level_str = config.LOG_LEVEL
        log_level_int = getattr(logging, config.LOG_LEVEL, logging.INFO)
    
    # Set up logging
    logging.basicConfig(
        level=log_level_int,
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Update model if specified
    if args.model:
        config.CLAUDE_MODEL = args.model
    
    # Run in the specified mode
    if args.web:
        if "web_interface" in sys.modules:
            start_web_app(host=args.host, port=args.port, debug=args.debug)
        else:
            print("Error: Web interface mode requires Flask. Please install it with 'pip install flask'.")
    elif args.cli:
        run_cli_mode(args)
    else:
        print("Please specify a mode: --cli or --web")
        print("Example: python main.py --cli")
        print("Run 'python main.py --help' for more information.")

if __name__ == "__main__":
    main()