import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.concept_node import ConceptNode


class ConceptManager:
    """
    Manages the dynamic concept graph.

    Responsibilities include:
      - Loading existing concept nodes from the file system.
      - Creating or retrieving a concept node by name.
      - Searching for concepts that match given query strings.
      - Merging similar concepts and pruning out-of-date nodes.
    """

    def __init__(self, concepts_dir: Path):
        """
        Initialize the ConceptManager with a directory for concept JSON files.

        Args:
            concepts_dir (Path): The base directory for storing concept JSON nodes.
        """
        self.concepts_dir = concepts_dir
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self._concepts_cache = {}  # Cache for loaded nodes

    def get_concept(self, name: str) -> ConceptNode:
        """
        Retrieve an existing concept node or create a new one if it doesn't exist.

        Args:
            name (str): The name of the concept.

        Returns:
            ConceptNode: The corresponding concept node.
        """
        name = name.lower().strip()
        if name in self._concepts_cache:
            return self._concepts_cache[name]

        node = ConceptNode(name=name, base_path=self.concepts_dir)
        self._concepts_cache[name] = node
        return node

    def save_concept(self, node: ConceptNode):
        """
        Save the provided concept node and update the cache.
        
        Args:
            node (ConceptNode): The concept node to save.
        """
        node.save()
        self._concepts_cache[node.name] = node

    def search_concepts(self, query: str) -> List[ConceptNode]:
        """
        Search for concept nodes matching the query string.

        This implementation uses a basic substring match on:
            - The concept name.
            - The tags.
            - Traits' keys and values.

        Args:
            query (str): The search query.

        Returns:
            List[ConceptNode]: A list of matching concept nodes.
        """
        query = query.lower().strip()
        results = []

        # Load all concepts from the directory if not cached yet
        for file_path in self.concepts_dir.glob("*.json"):
            concept_name = file_path.stem
            if concept_name not in self._concepts_cache:
                node = ConceptNode(name=concept_name, base_path=self.concepts_dir)
                self._concepts_cache[concept_name] = node
            else:
                node = self._concepts_cache[concept_name]

            data = node.data
            # Check in name, tags, and traits
            name_match = query in data.get("name", "")
            tag_match = any(query in tag for tag in data.get("tags", []))
            trait_match = any(
                query in key or any(query in str(val) for val in values)
                for key, values in data.get("traits", {}).items()
            )

            if name_match or tag_match or trait_match:
                results.append(node)

        return results

    def merge_concepts(self, primary: ConceptNode, secondary: ConceptNode) -> ConceptNode:
        """
        Merge two concept nodes into one.

        The secondary node's data (traits, tags, linked memories, and relationships)
        are merged into the primary node. After merging, the secondary node is removed.

        Args:
            primary (ConceptNode): The node to merge data into.
            secondary (ConceptNode): The node whose data will be merged, then deleted.

        Returns:
            ConceptNode: The updated primary node.
        """
        # Merge traits
        for key, values in secondary.data.get("traits", {}).items():
            for value in values:
                primary.add_trait(key, value)
        # Merge tags
        for tag in secondary.data.get("tags", []):
            primary.add_tag(tag)
        # Merge related concepts; if there's a conflict, primary's relation is kept
        for rel, rel_type in secondary.data.get("related_concepts", {}).items():
            if rel not in primary.data["related_concepts"]:
                primary.relate_to(rel, rel_type)
        # Merge linked memories
        for mem_id in secondary.data.get("linked_memories", []):
            primary.link_memory(mem_id)
        # Optionally update type if primary still unknown
        if primary.data.get("type", "unknown") == "unknown" and secondary.data.get("type", "unknown") != "unknown":
            primary.set_type(secondary.data.get("type"))

        # Update timestamp
        primary.data["last_updated"] = datetime.utcnow().isoformat()
        self.save_concept(primary)

        # Delete the secondary node
        self.delete_concept(secondary.name)

        return primary

    def delete_concept(self, name: str) -> bool:
        """
        Delete a concept node by name, removing it from the file system and cache.

        Args:
            name (str): The name of the concept node to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        name = name.lower().strip()
        node = self._concepts_cache.get(name)
        file_path = self.concepts_dir / f"{name}.json"
        try:
            if file_path.exists():
                file_path.unlink()
            if name in self._concepts_cache:
                del self._concepts_cache[name]
            return True
        except Exception as e:
            print(f"Error deleting concept node '{name}': {e}")
            return False

    def list_all_concepts(self) -> List[ConceptNode]:
        """
        List all concept nodes from the concepts directory.

        Returns:
            List[ConceptNode]: All loaded concept nodes.
        """
        nodes = []
        for file_path in self.concepts_dir.glob("*.json"):
            concept_name = file_path.stem
            node = self.get_concept(concept_name)
            nodes.append(node)
        return nodes
