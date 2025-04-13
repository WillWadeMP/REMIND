# REMIND - Retrieval of Episodic & Metadata-Indexed Information for Natural Dialogue

REMIND is a lightweight, pseudo-memory framework for Large Language Models (LLMs), designed to simulate memory recall and retention using local file-based storage. It enhances AI dialogue systems by allowing dynamic referencing of past interactions and stored knowledge.

## Features

- **Structured Memory Organization**: Episodic and non-episodic memory formats
- **Efficient Retrieval**: Using summarization, keyword extraction, and contextual hooks
- **Browser-Based Interface**: Explore and visualize AI memories
- **Claude-Powered**: Leverages Claude for natural language understanding and generation
- **File-Based Storage**: Simple JSON-based storage for easy deployment and inspection

## System Overview

REMIND is composed of the following core modules:

- **User Prompt Handler**: Processes user inputs
- **Summariser**: Creates concise summaries of text
- **Memory Layer**: Manages episodic and non-episodic memories
- **Metadata Extractor**: Extracts keywords, dates, and themes
- **Relevancer**: Retrieves relevant memories based on context
- **Response Generator**: Creates responses incorporating relevant memories
- **Memory Updater**: Updates the memory system with new information
- **Hook Generator**: Creates hooks for efficient memory indexing

## Quick Setup

For a quick and easy setup, run:

```
python setup.py
```

This script will:
1. Install all required dependencies
2. Create the necessary directories
3. Help you set up your Claude API key
4. Provide instructions for running the system

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/remind.git
   cd remind
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Claude API key:
   ```
   export CLAUDE_API_KEY=your_api_key_here  # On Windows: set CLAUDE_API_KEY=your_api_key_here
   ```

## Usage

### Command Line Interface

Run the system in CLI mode:

```
python main.py --cli
```

### Web Interface

Start the web interface:

```
python main.py --web
```

Then open your browser and navigate to http://127.0.0.1:5000/

## Memory Structures

### Episodic Memory

Stores timestamped summaries of past conversations, indexed by date and topic-specific hooks.

Example:
```json
{
  "type": "episodic",
  "conversation_id": "20250413120000",
  "timestamp": "2025-04-13T12:00:00.000Z",
  "content": "User: What's the capital of France?\n\nAssistant: The capital of France is Paris.",
  "summary": "Conversation about the capital of France",
  "hooks": ["france", "capital", "paris", "geography", "europe"]
}
```

### Non-Episodic Memory

Stores general facts, opinions, or persistent truths in a topic-agnostic format.

Example:
```json
{
  "type": "non_episodic",
  "timestamp": "2025-04-13T12:00:00.000Z",
  "content": "User's favorite color is blue",
  "hooks": ["blue", "favorite color", "preference", "user info"]
}
```

## Web Interface

The web interface provides a way to interact with the REMIND system and explore its memories:

- **Chat Interface**: Talk to the AI assistant
- **Episodic Memory Viewer**: Browse past interactions
- **Non-Episodic Memory Viewer**: Explore stored facts and knowledge
- **Hook Browser**: View and filter by memory hooks

## Development

### Project Structure

```
REMIND/
├── README.md
├── requirements.txt
├── config.py                   # Configuration settings
├── main.py                     # Main entry point
├── memory/                     # Memory storage
│   ├── __init__.py
│   ├── episodic/               # Episodic memories (date-based)
│   └── non_episodic/           # Non-episodic memories (fact-based)
├── web_interface/              # Browser-based interface
│   ├── __init__.py
│   ├── static/                 # CSS, JS files
│   ├── templates/              # HTML templates
│   └── app.py                  # Flask web app
├── src/                        # Core modules
│   ├── __init__.py
│   ├── prompt_handler.py       # User prompt processing
│   ├── summarizer.py           # Create summaries using Claude
│   ├── metadata_extractor.py   # Extract keywords, dates, etc.
│   ├── memory_layer.py         # Memory management
│   ├── relevancer.py           # Retrieval engine
│   ├── response_generator.py   # Generate responses with Claude
│   ├── memory_updater.py       # Update memory with new information
│   ├── hook_generator.py       # Generate hooks for indexing
│   └── utils.py                # Utility functions
└── tests/                      # Test cases
    ├── __init__.py
    └── test_*.py               # Various test files
```

### Running Tests

Run the test suite:

```
pytest
```

## Future Enhancements

- **Hook Frequency Tracker**: Weight common vs. rare tags
- **Memory Pruner**: Trim low-relevance memories over time
- **Contextual Balancer**: Balance recency vs. relevance in memory retrieval
- **Database Integration**: Support for SQL or NoSQL databases
- **Multi-user Support**: Separate memory spaces for different users
- **Memory Visualization**: Advanced visualizations of memory connections

## Troubleshooting

### API Key Issues

If you encounter issues with the Claude API, make sure:

1. Your API key is correctly set in the environment variable `CLAUDE_API_KEY`.
2. You're using a compatible model version. Try an older, more stable model:
   ```
   python main.py --model claude-2.0 --cli
   ```

### Compatibility Issues

If you encounter compatibility issues with the Anthropic Python SDK:

1. Try installing an older version:
   ```
   pip install anthropic==0.4.0
   ```

2. Use a different model version:
   ```
   python main.py --model claude-2.0 --cli
   ```

### Other Issues

If you continue to experience problems:

1. Check the log file at `remind.log` for more detailed error messages.
2. Make sure all dependencies are installed correctly.
3. Ensure your API key has the necessary permissions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project was developed using the Anthropic Claude API for natural language processing
- Inspired by research on episodic memory in cognitive science