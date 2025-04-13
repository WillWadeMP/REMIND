#!/usr/bin/env python
"""
Setup script for the REMIND system.
"""
import os
import sys
import subprocess
import platform

def print_header(text):
    """Print a header with decoration."""
    print("\n" + "=" * 60)
    print(f" {text} ".center(60, "="))
    print("=" * 60 + "\n")

def print_success(text):
    """Print a success message."""
    print(f"\n✅ {text}\n")

def print_error(text):
    """Print an error message."""
    print(f"\n❌ {text}\n")

def create_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    directories = [
        "memory",
        "memory/episodic",
        "memory/non_episodic",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  - Created {directory}/")
    
    print_success("Directories created successfully!")

def install_dependencies():
    """Install dependencies using pip."""
    print("Installing dependencies...")
    
    # List of dependencies
    dependencies = [
        "anthropic>=0.6.0",
        "flask>=2.0.0",
        "python-dotenv>=0.19.0",
        "requests>=2.25.0"
    ]
    
    # Install dependencies
    for dependency in dependencies:
        print(f"  - Installing {dependency}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
        except subprocess.CalledProcessError:
            print_error(f"Failed to install {dependency}")
            return False
    
    print_success("Dependencies installed successfully!")
    return True

def configure_api_key():
    """Configure the Claude API key."""
    print("Configuring Claude API key...")
    
    # Check if API key is already set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("Claude API key is already set in the environment.")
        return True
    
    # Ask for API key
    api_key = input("Please enter your Claude API key: ").strip()
    if not api_key:
        print_error("API key cannot be empty")
        return False
    
    # Create .env file for development
    with open(".env", "w") as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")
    
    print("API key saved to .env file.")
    
    # Set environment variable for current session
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    # Instructions for setting environment variable permanently
    system = platform.system()
    print("\nTo set the API key permanently, run the following command in your terminal:")
    
    if system == "Windows":
        print(f'  setx ANTHROPIC_API_KEY "{api_key}"')
    else:  # Linux or macOS
        print(f'  echo \'export ANTHROPIC_API_KEY="{api_key}"\' >> ~/.bashrc')
        print(f'  # Or if you use zsh:')
        print(f'  echo \'export ANTHROPIC_API_KEY="{api_key}"\' >> ~/.zshrc')
    
    print_success("API key configured successfully!")
    return True

def create_sample_config():
    """Create a sample config.py file."""
    print("Creating sample config file...")
    
    config_content = """\"\"\"
Configuration settings for the REMIND system.
\"\"\"
import os
import logging

# API Configuration
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Model Configuration
# Main model for response generation and complex tasks
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Modern, capable model

# Model for simpler, faster tasks like summarization and metadata extraction
CLAUDE_FAST_MODEL = "claude-3-5-haiku-20241022"  # Faster, cheaper model

# Memory Configuration
EPISODIC_MEMORY_DIR = os.path.join("memory", "episodic")
NON_EPISODIC_MEMORY_DIR = os.path.join("memory", "non_episodic")
MAX_EPISODIC_MEMORIES = 1000
MAX_NON_EPISODIC_MEMORIES = 500
MEMORY_RETENTION_DAYS = 30  # Number of days to keep episodic memories

# Hook Configuration
MAX_HOOKS_PER_MEMORY = 10
MIN_HOOK_LENGTH = 2
MAX_HOOK_LENGTH = 30

# Retrieval Configuration
MAX_MEMORIES_TO_RETRIEVE = 5

# Logging Configuration
LOG_LEVEL = "INFO"  # String version for compatibility with getattr()
LOG_FILE = "remind.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Initialize logging
def setup_logging():
    \"\"\"Set up logging configuration.\"\"\"
    log_level_int = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level_int,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

# Call setup_logging() when this module is imported
setup_logging()
"""
    
    # Check if config.py already exists
    if os.path.exists("config.py"):
        overwrite = input("config.py already exists. Overwrite? (y/n): ").lower() == "y"
        if not overwrite:
            print("Skipping config.py creation...")
            return
    
    # Write config.py
    with open("config.py", "w") as f:
        f.write(config_content)
    
    print_success("Sample config.py created successfully!")

def print_instructions():
    """Print instructions for running the REMIND system."""
    print_header("REMIND System Setup Complete!")
    print("You can now run the REMIND system using the following commands:")
    print("\n1. Run in command line mode:")
    print("   python main.py --cli")
    print("\n2. Run in web interface mode:")
    print("   python main.py --web")
    print("\n3. If you want to use a different Claude model:")
    print("   python main.py --model claude-3-5-sonnet-20241022 --web")
    print("\nFor more options, run:")
    print("   python main.py --help")

def main():
    """Main setup function."""
    print_header("REMIND System Setup")
    
    try:
        # Create directories
        create_directories()
        
        # Install dependencies
        if not install_dependencies():
            print_error("Failed to install dependencies")
            return
        
        # Configure API key
        if not configure_api_key():
            print_error("Failed to configure API key")
            return
        
        # Create sample config
        create_sample_config()
        
        # Print instructions
        print_instructions()
        
    except Exception as e:
        print_error(f"Setup failed: {e}")

if __name__ == "__main__":
    main()