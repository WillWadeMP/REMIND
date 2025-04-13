import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, render_template, request, jsonify

import config
from src.claude_client import ClaudeClient
from src.memory_manager import MemoryManager  # New concept–graph memory system
from src.conversation_manager import ConversationManager  # New persistent conversation system

logger = logging.getLogger(__name__)

# Initialize Flask app with template and static directories
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# Global instances set in run_web_app below
memory_manager = None        # Concept-based MemoryManager
conv_manager = None          # ConversationManager for chat logs
default_model = None         # Default model from config

@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle chat requests.
    - Persist the user message (and later the assistant response) via ConversationManager.
    - Process the user message through MemoryManager (to update concept nodes).
    - Generate a response via MemoryManager.
    """
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    message = data.get("message")
    conversation_id = data.get("conversation_id")  # Optional: update existing convo.
    model = data.get("model", default_model)

    if not message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # If conversation exists, update it; otherwise create new conversation.
        if conversation_id:
            conv = conv_manager.add_message(conversation_id, {"role": "user", "content": message})
            if conv is None:
                # Conversation not found—create a new one.
                conv = conv_manager.create_conversation({"role": "user", "content": message})
                conversation_id = conv["id"]
        else:
            conv = conv_manager.create_conversation({"role": "user", "content": message})
            conversation_id = conv["id"]

        # Process the message into concept nodes.
        updated_concepts = memory_manager.process_memory(message)
        # Generate assistant's response using concept–graph context.
        response = memory_manager.generate_response(query=message)
        # Record the assistant's reply into the conversation log.
        conv_manager.add_message(conversation_id, {"role": "assistant", "content": response})

        return jsonify({
            "response": response,
            "conversation_id": conversation_id,
            "concepts_updated": updated_concepts,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    """
    Retrieve a list of recent conversations (persisted via ConversationManager).
    """
    try:
        convs = conv_manager.list_conversations(limit=20)
        return jsonify({
            "conversations": convs,
            "count": len(convs)
        })
    except Exception as e:
        logger.error(f"Error retrieving conversations: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """
    Retrieve a specific conversation by its ID.
    """
    try:
        conv = conv_manager.get_conversation(conversation_id)
        if conv is None:
            return jsonify({"error": "Conversation not found"}), 404
        return jsonify(conv)
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/concepts", methods=["GET"])
def get_concepts():
    """
    Retrieve all concept nodes stored in the MemoryManager.
    """
    try:
        concept_nodes = memory_manager.concept_manager.list_all_concepts()
        concepts_data = [node.data for node in concept_nodes]
        return jsonify({
            "concepts": concepts_data,
            "count": len(concepts_data)
        })
    except Exception as e:
        logger.error(f"Error retrieving concepts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/concepts/graph", methods=["GET"])
def get_concepts_graph():
    """
    Retrieve a graph view of the concept nodes.
    Each node’s 'related_concepts' field defines edges.
    """
    try:
        concept_nodes = memory_manager.concept_manager.list_all_concepts()
        nodes = []
        edges = []
        for node in concept_nodes:
            data = node.data
            nodes.append({
                "id": data["name"],
                "label": data["name"],
                "type": data.get("type", "unknown"),
                "tags": data.get("tags", []),
                "traits": data.get("traits", {}),
            })
            for related, rel_type in data.get("related_concepts", {}).items():
                edges.append({
                    "source": data["name"],
                    "target": related,
                    "relationship": rel_type,
                })
        return jsonify({"nodes": nodes, "edges": edges})
    except Exception as e:
        logger.error(f"Error retrieving concepts graph: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/memories", methods=["GET"])
def get_memories():
    """
    Legacy endpoint for memories.
    Since we no longer have episodic/non-episodic memories, if a type parameter is provided
    and it's "episodic" or "non_episodic", we return an empty array.
    Otherwise, return aggregated info (conversation logs and concept nodes).
    """
    mem_type = request.args.get("type")
    if mem_type in ["episodic", "non_episodic"]:
        return jsonify([])
    # Return aggregated info for debugging.
    convs = conv_manager.list_conversations(limit=100)
    concepts = [node.data for node in memory_manager.concept_manager.list_all_concepts()]
    return jsonify({
        "counts": {
            "conversations": len(convs),
            "concepts": len(concepts)
        },
        "conversations": convs,
        "concepts": concepts
    })

@app.route("/api/tags", methods=["GET"])
def get_tags():
    """
    Return aggregated tags computed from all concept nodes.
    """
    tags_counter = {}
    concept_nodes = memory_manager.concept_manager.list_all_concepts()
    for node in concept_nodes:
        for tag in node.data.get("tags", []):
            tags_counter[tag] = tags_counter.get(tag, 0) + 1
    tags_list = [{"tag": tag, "count": count} for tag, count in tags_counter.items()]
    tags_list.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(tags_list)

@app.route("/api/search", methods=["GET"])
def search_memories():
    """
    Search both conversation logs and concept nodes.
    If a 'type' parameter is provided:
      - For "conversations", search conversation titles and summaries.
      - For "concepts", search in concept names and tags.
      - For "episodic" or "non_episodic", return an empty array.
    If no type is specified, return search results from both.
    """
    query = request.args.get("q", "").strip()
    mem_type = request.args.get("type")
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    results = {}
    if mem_type:
        if mem_type in ["episodic", "non_episodic"]:
            results[mem_type] = []
        elif mem_type == "conversations":
            all_convs = conv_manager.list_conversations(limit=100)
            filtered_convs = [conv for conv in all_convs
                              if query.lower() in (conv.get("title", "").lower() + conv.get("summary", "").lower())]
            results["conversations"] = filtered_convs
        elif mem_type == "concepts":
            all_concepts = memory_manager.concept_manager.list_all_concepts()
            filtered_concepts = [
                node.data for node in all_concepts
                if query.lower() in node.data.get("name", "").lower() or
                   query.lower() in " ".join(node.data.get("tags", [])).lower()
            ]
            results["concepts"] = filtered_concepts
    else:
        all_convs = conv_manager.list_conversations(limit=100)
        filtered_convs = [conv for conv in all_convs
                          if query.lower() in (conv.get("title", "").lower() + conv.get("summary", "").lower())]
        all_concepts = memory_manager.concept_manager.list_all_concepts()
        filtered_concepts = [
            node.data for node in all_concepts
            if query.lower() in node.data.get("name", "").lower() or
               query.lower() in " ".join(node.data.get("tags", [])).lower()
        ]
        results = {
            "conversations": filtered_convs,
            "concepts": filtered_concepts
        }
    return jsonify(results)

def run_web_app(memory_manager_instance: MemoryManager, conv_manager_instance: ConversationManager,
                host: str = "127.0.0.1", port: int = 5000, debug: bool = False, model: Any = None):
    """
    Run the web application.
    
    Args:
        memory_manager_instance (MemoryManager): Instance of the concept-based memory manager.
        conv_manager_instance (ConversationManager): Instance of the conversation manager.
        host (str): Host to bind.
        port (int): Port number.
        debug (bool): Whether to run in debug mode.
        model: Optional model specifier.
    """
    global memory_manager, conv_manager, default_model
    memory_manager = memory_manager_instance
    conv_manager = conv_manager_instance
    default_model = model if model else config.CLAUDE_MODEL

    logger.info(f"Starting web app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    from pathlib import Path
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler()],
    )

    # Initialize MemoryManager with the concepts directory.
    concepts_dir = config.MEMORY_DIR / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    mem_manager = MemoryManager(concepts_dir=concepts_dir)

    # Initialize ConversationManager with the conversations directory.
    conv_dir = config.CONVERSATIONS_DIR
    conv_dir.mkdir(parents=True, exist_ok=True)
    conv_manager_instance = ConversationManager()

    # Run the web app.
    run_web_app(
        memory_manager_instance=mem_manager,
        conv_manager_instance=conv_manager_instance,
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=config.WEB_DEBUG,
    )
