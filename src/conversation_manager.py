import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages persistent storage for conversations.
    
    Each conversation is stored as a JSON file in config.CONVERSATIONS_DIR.
    A conversation includes an ID, a list of messages (each with role and content), and timestamps.
    """
    def __init__(self):
        self.conversations_dir = config.CONVERSATIONS_DIR
        self.conversations_dir.mkdir(exist_ok=True, parents=True)
    
    def create_conversation(self, initial_message: dict) -> dict:
        """
        Create a new conversation with the given initial message.
        initial_message: A dict with keys "role" and "content".
        """
        conv_id = str(uuid.uuid4())
        conversation = {
            "id": conv_id,
            "messages": [initial_message],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "title": initial_message["content"][:50]  # Naive title based on the first message
        }
        self._save_conversation(conversation)
        logger.info(f"Created conversation: {conv_id}")
        return conversation
    
    def add_message(self, conversation_id: str, message: dict) -> dict:
        """
        Append a message to an existing conversation.
        message: Dict with keys "role" and "content".
        """
        conversation = self.get_conversation(conversation_id)
        if conversation is None:
            logger.error(f"Conversation {conversation_id} not found.")
            return None
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.utcnow().isoformat()
        self._save_conversation(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: str) -> dict:
        """
        Retrieve a conversation by its ID.
        """
        file_path = self.conversations_dir / f"{conversation_id}.json"
        if not file_path.exists():
            logger.warning(f"Conversation file {file_path} does not exist.")
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                conversation = json.load(f)
            return conversation
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {e}")
            return None
    
    def list_conversations(self, limit: int = 10) -> list:
        """
        List recent conversations.
        """
        files = list(self.conversations_dir.glob("*.json"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        conversations = []
        for file in files[:limit]:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    conv = json.load(f)
                conversations.append(conv)
            except Exception as e:
                logger.error(f"Error reading conversation file {file}: {e}")
        return conversations
    
    def _save_conversation(self, conversation: dict):
        """
        Save a conversation to disk.
        """
        file_path = self.conversations_dir / f"{conversation['id']}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)
