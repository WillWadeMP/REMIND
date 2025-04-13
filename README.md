# REMIND - Retrieval-Enhanced Memory for Interactive Natural Dialogue

REMIND is a lightweight memory framework for Large Language Models (LLMs) that enhances AI dialogue systems with dynamic memory management for more coherent and contextual conversations.

## Features

- **Three-Tier Memory System**:
  - **Conversation Memory**: Stores entire conversations for seamless context
  - **Episodic Memory**: Captures specific interactions and events
  - **Non-Episodic Memory**: Retains facts, preferences, and general knowledge

- **Efficient Retrieval**: Quickly access relevant memories using vector similarity search
- **Browser Interface**: Explore and manage AI memories through an intuitive web UI
- **Claude-Powered**: Leverages Claude AI for natural language understanding and generation
- **Simple File Structure**: JSON-based storage for easy inspection and portability

## System Overview

REMIND consists of these core modules:

- **Memory Manager**: Central component that coordinates all memory operations
- **Memory Storage**: Handles saving, loading, and organizing memories
- **Retriever**: Finds relevant memories based on current context
- **Processor**: Transforms raw conversations into structured memories
- **Web Interface**: Visualizes memories and provides interactive access

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/remind.git
cd remind

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
# Linux/macOS:
export ANTHROPIC_API_KEY=your_api_key_here
# Windows:
set ANTHROPIC_API_KEY=your_api_key_here

# Run the application
python main.py
```

## Usage

### Web Interface

Start the web interface:

```bash
python main.py --web
```

Then open your browser and navigate to http://127.0.0.1:5000/

### Command Line Interface

Run the system in CLI mode:

```bash
python main.py --cli
```

## Memory Structure

### Conversation Memory

Stores entire conversations for consistent context across multiple interactions.

```json
{
  "id": "conv_20250413120000",
  "type": "conversation",
  "created_at": "2025-04-13T12:00:00.000Z",
  "updated_at": "2025-04-13T12:15:00.000Z",
  "title": "Discussion about Paris travel plans",
  "summary": "Conversation about planning a trip to Paris, including best times to visit and top attractions",
  "messages": [
    {"role": "user", "content": "What's the best time to visit Paris?", "timestamp": "2025-04-13T12:00:00.000Z"},
    {"role": "assistant", "content": "The best time to visit Paris is...", "timestamp": "2025-04-13T12:00:10.000Z"}
  ],
  "tags": ["paris", "travel", "vacation", "france"]
}
```

### Episodic Memory

Stores specific events, interactions, or experiences.

```json
{
  "id": "ep_20250413120500",
  "type": "episodic",
  "created_at": "2025-04-13T12:05:00.000Z",
  "conversation_id": "conv_20250413120000",
  "content": "User mentioned they prefer to travel in spring or fall, avoiding summer crowds",
  "tags": ["preferences", "travel", "seasons", "crowds"]
}
```

### Non-Episodic Memory

Stores facts, preferences, or other persistent information.

```json
{
  "id": "nep_20250413121000",
  "type": "non_episodic",
  "created_at": "2025-04-13T12:10:00.000Z",
  "content": "User's favorite season for travel is fall",
  "confidence": 0.85,
  "tags": ["preferences", "travel", "fall", "seasons"]
}
```

## Project Structure

```
REMIND/
├── README.md
├── requirements.txt
├── config.py                   # Configuration settings
├── main.py                     # Main entry point
├── memory/                     # Memory storage
│   ├── conversations/          # Conversation memories
│   ├── episodic/               # Episodic memories
│   └── non_episodic/           # Non-episodic memories
├── src/                        # Core modules
│   ├── memory_manager.py       # Central memory management
│   ├── memory_storage.py       # Memory persistence
│   ├── memory_retriever.py     # Memory retrieval logic
│   ├── memory_processor.py     # Process raw data into memories
│   ├── claude_client.py        # Claude API client
│   └── utils.py                # Utility functions
└── web/                        # Web interface
    ├── app.py                  # Flask web application
    ├── static/                 # CSS, JS files
    └── templates/              # HTML templates
```

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Acknowledgments

- This project uses the Anthropic Claude API for natural language processing