"""
Web interface for the REMIND system.
"""
import logging
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import config
from src.prompt_handler import PromptHandler
from src.memory_layer import MemoryLayer
from src.relevancer import Relevancer
from src.response_generator import ResponseGenerator
from src.memory_updater import MemoryUpdater

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize components
memory_layer = MemoryLayer()
prompt_handler = PromptHandler()
relevancer = Relevancer(memory_layer)
response_generator = ResponseGenerator()
memory_updater = MemoryUpdater(memory_layer)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    data = request.json
    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id', datetime.now().strftime("%Y%m%d%H%M%S"))
    
    # Process user prompt
    processed_prompt = prompt_handler.process(user_input)
    
    # Retrieve relevant memories
    relevant_memories = relevancer.retrieve(processed_prompt)
    
    # Generate response
    response = response_generator.generate(user_input, relevant_memories)
    
    # Update memory with new interaction
    episodic_path, non_episodic_paths = memory_updater.update(user_input, response, conversation_id)
    
    # Return response and metadata
    return jsonify({
        'response': response,
        'conversation_id': conversation_id,
        'relevant_memories': [memory_to_dict(memory) for memory in relevant_memories],
        'episodic_path': episodic_path,
        'non_episodic_paths': non_episodic_paths
    })

@app.route('/api/memories')
def get_memories():
    """Get all memories."""
    episodic_memories = memory_layer.get_episodic_memories()
    non_episodic_memories = memory_layer.get_non_episodic_memories()
    
    return jsonify({
        'episodic_memories': [memory_to_dict(memory) for memory in episodic_memories],
        'non_episodic_memories': [memory_to_dict(memory) for memory in non_episodic_memories]
    })

@app.route('/api/memories/episodic')
def get_episodic_memories():
    """Get episodic memories, optionally filtered by hooks."""
    hooks = request.args.get('hooks', '').split(',') if request.args.get('hooks') else None
    max_count = int(request.args.get('max_count', 100))
    
    memories = memory_layer.get_episodic_memories(hooks=hooks, max_count=max_count)
    
    return jsonify({
        'memories': [memory_to_dict(memory) for memory in memories]
    })

@app.route('/api/memories/non_episodic')
def get_non_episodic_memories():
    """Get non-episodic memories, optionally filtered by hooks."""
    hooks = request.args.get('hooks', '').split(',') if request.args.get('hooks') else None
    max_count = int(request.args.get('max_count', 100))
    
    memories = memory_layer.get_non_episodic_memories(hooks=hooks, max_count=max_count)
    
    return jsonify({
        'memories': [memory_to_dict(memory) for memory in memories]
    })

@app.route('/api/memories/hooks')
def get_all_hooks():
    """Get all unique hooks from all memories."""
    hooks = memory_layer.get_all_hooks()
    
    return jsonify({
        'hooks': hooks
    })

@app.route('/api/memories/<memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """Delete a memory by ID."""
    # In this implementation, memory_id is the file path
    success = memory_layer.delete_memory(memory_id)
    
    return jsonify({
        'success': success
    })

def memory_to_dict(memory):
    """Convert a memory dictionary to a safe dictionary for JSON serialization."""
    # Create a deep copy of the memory
    memory_dict = dict(memory)
    
    # Remove file path if present (and replace with just the filename)
    if 'file_path' in memory_dict:
        memory_dict['id'] = os.path.basename(memory_dict['file_path'])
        memory_dict['file_path'] = os.path.basename(memory_dict['file_path'])
    
    return memory_dict

def start_web_app(host="127.0.0.1", port=5000, debug=False):
    """
    Start the web app.
    
    Args:
        host (str): The host to run the web app on.
        port (int): The port to run the web app on.
        debug (bool): Whether to run in debug mode.
    """
    logger.info(f"Starting web app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)