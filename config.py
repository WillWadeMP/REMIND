"""
Configuration settings for the REMIND system.
"""
import os
import logging
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# API Configuration
# Hardcoded key for personal use
CLAUDE_API_KEY = "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"
# Model Configuration
# Main model for response generation and complex tasks
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Modern, capable model

# Model for simpler, faster tasks like summarization and metadata extraction
CLAUDE_FAST_MODEL = "claude-3-5-haiku-20241022"  # Faster, cheaper model

# Memory Configuration
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
EPISODIC_MEMORY_DIR = os.path.join(MEMORY_DIR, "episodic")
NON_EPISODIC_MEMORY_DIR = os.path.join(MEMORY_DIR, "non_episodic")

# Ensure memory directories exist
os.makedirs(EPISODIC_MEMORY_DIR, exist_ok=True)
os.makedirs(NON_EPISODIC_MEMORY_DIR, exist_ok=True)

MAX_EPISODIC_MEMORIES = 1000
MAX_NON_EPISODIC_MEMORIES = 500
MEMORY_RETENTION_DAYS = 30  # Number of days to keep episodic memories

# Hook Configuration
MAX_HOOKS_PER_MEMORY = 10
MIN_HOOK_LENGTH = 2
MAX_HOOK_LENGTH = 30

# Retrieval Configuration
MAX_MEMORIES_TO_RETRIEVE = 5

# Web Interface Configuration
WEB_HOST = "127.0.0.1"
WEB_PORT = 5000
WEB_DEBUG = False

# Logging Configuration
LOG_LEVEL = "INFO"  # String version for compatibility with getattr()
LOG_FILE = "remind.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Initialize logging
def setup_logging():
    """Set up logging configuration."""
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