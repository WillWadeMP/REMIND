import json
from pathlib import Path
from datetime import datetime


class ConceptNode:
    """
    Represents a single concept in the dynamic concept graph.

    Each concept is stored as a JSON file and contains:
      - name: The identifier for the concept (lowercase).
      - type: The category of the concept (e.g., person, hobby, food).
      - traits: A dictionary of attributes (keys map to lists of values).
      - related_concepts: A mapping of related concept names to the type of relationship.
      - tags: A list of additional tags (keywords).
      - linked_memories: A list of IDs that link this concept to episodic memories.
      - last_updated: ISO-formatted timestamp when the node was last modified.
    """

    def __init__(self, name: str, base_path: Path):
        """
        Initialize the concept node. Loads from file if it exists; otherwise, creates a new structure.

        Args:
            name (str): The name of the concept.
            base_path (Path): The directory where concept JSONs are stored.
        """
        self.name = name.lower()
        self.base_path = base_path
        self.file_path = base_path / f"{self.name}.json"
        self.data = self._load()

    def _load(self):
        """Load the concept data from its JSON file or create a default structure."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except json.JSONDecodeError:
                # If the file is corrupt, fall back to a fresh structure.
                pass

        # Default structure if the file doesn't exist
        return {
            "name": self.name,
            "type": "unknown",
            "traits": {},
            "related_concepts": {},
            "tags": [],
            "linked_memories": [],
            "last_updated": datetime.utcnow().isoformat()
        }

    def add_trait(self, key: str, value: str):
        """
        Add a trait key-value pair to the concept.
        
        Args:
            key (str): The trait name (e.g., 'likes_to_eat').
            value (str): The trait value (e.g., 'fish').
        """
        if key not in self.data["traits"]:
            self.data["traits"][key] = []
        if value not in self.data["traits"][key]:
            self.data["traits"][key].append(value)
        self._update_timestamp()

    def add_tag(self, tag: str):
        """
        Add a tag to the concept if it is not already present.
        
        Args:
            tag (str): A keyword tag.
        """
        tag = tag.lower().strip()
        if tag and tag not in self.data["tags"]:
            self.data["tags"].append(tag)
        self._update_timestamp()

    def relate_to(self, other_concept: str, relation_type: str):
        """
        Create or update a relationship to another concept.
        
        Args:
            other_concept (str): The name of the related concept.
            relation_type (str): A description of the relationship (e.g., "hobby" or "food_preference").
        """
        other_concept = other_concept.lower().strip()
        self.data["related_concepts"][other_concept] = relation_type.lower().strip()
        self._update_timestamp()

    def link_memory(self, memory_id: str):
        """
        Link a memory ID to this concept.
        
        Args:
            memory_id (str): The identifier for an episodic memory.
        """
        if memory_id not in self.data["linked_memories"]:
            self.data["linked_memories"].append(memory_id)
        self._update_timestamp()

    def set_type(self, concept_type: str):
        """
        Set the type or category of the concept (e.g., person, hobby, food).
        
        Args:
            concept_type (str): The category/type for the concept.
        """
        self.data["type"] = concept_type.lower().strip()
        self._update_timestamp()

    def _update_timestamp(self):
        """Update the last_updated timestamp to the current UTC time."""
        self.data["last_updated"] = datetime.utcnow().isoformat()

    def save(self):
        """
        Save the current state of the concept node back to disk.
        """
        self._update_timestamp()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def __repr__(self):
        return f"<ConceptNode: {self.name} ({self.data.get('type', 'unknown')})>"
