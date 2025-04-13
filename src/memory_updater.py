"""
Updates memories based on new interactions.
"""
import logging
import re
from datetime import datetime
import config
from src.hook_generator import HookGenerator
from src.summarizer import Summarizer
from src.claude_client import create_claude_client

logger = logging.getLogger(__name__)

class MemoryUpdater:
    """Updates memories based on new interactions."""
    
    def __init__(self, memory_layer):
        """
        Initialize the MemoryUpdater.
        
        Args:
            memory_layer (MemoryLayer): The memory layer to update.
        """
        self.memory_layer = memory_layer
        self.hook_generator = HookGenerator()
        self.summarizer = Summarizer()
        self.client = create_claude_client()
        self.model = config.CLAUDE_MODEL
        logger.info(f"MemoryUpdater initialized with model: {self.model}")
    
    def update(self, user_input, response, conversation_id=None):
        """
        Update memories based on a new interaction.
        
        Args:
            user_input (str): The user's input.
            response (str): The assistant's response.
            conversation_id (str, optional): A unique identifier for the conversation. Defaults to None.
            
        Returns:
            tuple: (episodic_memory_path, non_episodic_memory_paths) - Paths to the stored memories.
        """
        logger.debug(f"Updating memories for: {user_input}")
        
        # FIXED: Check for empty or invalid inputs
        if not user_input or not response:
            logger.warning("Empty or invalid user input or response, skipping memory update")
            return (None, [])
        
        # Generate a unique conversation ID if not provided
        if conversation_id is None:
            conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # FIXED: Clean up responses that might contain internal reasoning
        # Look for patterns that indicate internal reasoning in AI responses
        cleaned_response = self._clean_response(response)
        
        # Create the full interaction text
        interaction_text = f"User: {user_input}\n\nAssistant: {cleaned_response}"
        
        # Store episodic memory
        episodic_memory = self._create_episodic_memory(interaction_text, conversation_id)
        episodic_memory_path = self.memory_layer.store_episodic_memory(episodic_memory)
        
        # Extract potential non-episodic memories
        non_episodic_memories = self._extract_non_episodic_memories(interaction_text)
        
        # Store non-episodic memories
        non_episodic_memory_paths = []
        for memory in non_episodic_memories:
            path = self.memory_layer.store_non_episodic_memory(memory)
            if path:
                non_episodic_memory_paths.append(path)
        
        logger.info(f"Updated memories: episodic={episodic_memory_path}, non_episodic={len(non_episodic_memory_paths)}")
        return (episodic_memory_path, non_episodic_memory_paths)
    
    def _clean_response(self, response):
        """
        Clean the assistant response to remove any internal reasoning.
        
        Args:
            response (str): The raw assistant response.
            
        Returns:
            str: The cleaned response.
        """
        # Check for patterns that might indicate internal reasoning
        patterns_to_check = [
            "I'll acknowledge", "Let me acknowledge", "I'll respond", 
            "I should", "I'm going to", "I will now", "Let me provide",
            "I'll give", "I need to", "I notice that", "I should respond",
            "My response should"
        ]
        
        cleaned_response = response
        
        # Check if response starts with any of these patterns
        for pattern in patterns_to_check:
            if response.startswith(pattern):
                # Try to find where the actual response begins (often in quotes)
                quote_start = response.find('"')
                quote_end = response.rfind('"')
                
                if quote_start != -1 and quote_end != -1 and quote_end > quote_start:
                    # Extract the content within quotes
                    direct_response = response[quote_start+1:quote_end].strip()
                    cleaned_response = direct_response
                    logger.debug(f"Cleaned internal reasoning from response")
                    break
                
                # Alternative: look for a clear sentence break
                sentence_breaks = ['. ', '! ', '? ']
                for break_char in sentence_breaks:
                    first_break = response.find(break_char)
                    if first_break != -1:
                        # Skip the first sentence which might be internal reasoning
                        potential_direct = response[first_break+2:].strip()
                        if len(potential_direct) > 20:  # Ensure we're not cutting too much
                            cleaned_response = potential_direct
                            logger.debug(f"Cleaned internal reasoning from response using sentence break")
                            break
        
        return cleaned_response
    
    def _create_episodic_memory(self, interaction_text, conversation_id):
        """
        Create an episodic memory from an interaction.
        
        Args:
            interaction_text (str): The interaction text.
            conversation_id (str): A unique identifier for the conversation.
            
        Returns:
            dict: An episodic memory.
        """
        # Generate a summary of the interaction
        summary = self.summarizer.summarize(interaction_text)
        
        # Generate hooks for retrieval
        hooks = self.hook_generator.generate_hooks(interaction_text)
        
        # FIXED: Extract potential entities (names, places, etc.) for better retrieval
        entities = self._extract_entities(interaction_text)
        if entities:
            hooks.extend(entities)
        
        # FIXED: Add basic categorical hooks
        interaction_lower = interaction_text.lower()
        categories = [
            ("personal", ["my", "i am", "i'm", "my name", "myself", "i have", "i've"]),
            ("question", ["what", "how", "why", "when", "where", "who", "can you", "could you"]),
            ("preference", ["like", "prefer", "favorite", "enjoy", "love", "hate", "dislike"]),
            ("food", ["eat", "food", "dish", "meal", "recipe", "cook", "bake", "restaurant"]),
            ("technology", ["computer", "software", "hardware", "app", "device", "phone", "laptop", "code"]),
            ("opinion", ["think", "believe", "opinion", "perspective", "view", "consider"]),
            ("place", ["city", "country", "location", "visit", "travel", "place", "region", "area"])
        ]
        
        for category, keywords in categories:
            if any(keyword in interaction_lower for keyword in keywords):
                hooks.append(category)
        
        # Get unique hooks
        hooks = list(set(hooks))
        
        # Create the episodic memory
        episodic_memory = {
            "type": "episodic",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "content": interaction_text,
            "summary": summary,
            "hooks": hooks
        }
        
        return episodic_memory
    
    def _extract_entities(self, text):
        """
        Extract potential entities from text.
        
        Args:
            text (str): The text to extract entities from.
            
        Returns:
            list: A list of potential entities.
        """
        # Simple regex-based entity extraction
        # This is a very simplified approach; you might want to use an NLP library
        
        # Find potential proper nouns (capitalized words not at the start of sentences)
        proper_nouns = re.findall(r'(?<=[.!?]\s|\n|\r)[^.!?]*?\b([A-Z][a-z]+)\b', text)
        
        # Find words that appear to be names (two consecutive capitalized words)
        names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        
        # Find any capitalized words (potential names, places, etc.)
        capitalized = re.findall(r'\b([A-Z][a-z]{2,})\b', text)
        
        # Combine and filter duplicates
        all_entities = proper_nouns + names + capitalized
        unique_entities = list(set([entity.lower() for entity in all_entities]))
        
        return unique_entities
    
    def _extract_non_episodic_memories(self, interaction_text):
        """
        Extract non-episodic memories from an interaction.
        
        Args:
            interaction_text (str): The interaction text.
            
        Returns:
            list: A list of non-episodic memories.
        """
        # FIXED: First try to extract simple facts directly with pattern matching
        simple_facts = self._extract_simple_facts(interaction_text)
        simple_memories = []
        
        for fact in simple_facts:
            # Generate hooks for retrieval
            hooks = self.hook_generator.generate_hooks(fact)
            
            # Create the non-episodic memory
            non_episodic_memory = {
                "type": "non_episodic",
                "timestamp": datetime.now().isoformat(),
                "content": fact,
                "hooks": hooks
            }
            
            simple_memories.append(non_episodic_memory)
        
        # If we found simple facts, we can skip the API call to save costs
        if len(simple_memories) >= 3:
            logger.debug(f"Extracted {len(simple_memories)} non-episodic memories using pattern matching")
            return simple_memories[:3]  # Limit to 3 memories
        
        # Use Claude to extract potential non-episodic memories (facts, observations, etc.)
        extraction_prompt = f"""
        Please analyze the following interaction and extract any potential non-episodic memories.
        Non-episodic memories are facts, observations, or general knowledge that might be useful to remember for future interactions.
        
        For example, from "User: My favorite color is blue. Assistant: That's great! Blue is a calming color.", 
        you might extract "User's favorite color is blue" as a non-episodic memory.
        
        Interaction:
        {interaction_text}
        
        Please extract 0-3 non-episodic memories from this interaction. Only extract memories if they represent concrete, useful facts.
        Return your response as a JSON array of strings, with each string being a potential memory.
        Example: ["User's name is John", "User is allergic to peanuts", "User works as a software developer"]
        
        If there are no clear non-episodic memories to extract, return an empty array: []
        """
        
        try:
            # Use the client wrapper
            response = self.client.messages_create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ]
            )
            
            # Extract the text from the response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                if isinstance(response.content[0], dict) and 'text' in response.content[0]:
                    response_text = response.content[0]['text'].strip()
                elif hasattr(response.content[0], 'text'):
                    response_text = response.content[0].text.strip()
                else:
                    response_text = str(response.content[0]).strip()
            else:
                response_text = str(response).strip()
            
            # Extract the JSON array from the response
            import json
            import re
            
            # Find JSON array in the response
            array_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
            if array_match:
                try:
                    # Try to parse the matched array
                    memories_json = f"[{array_match.group(1)}]"
                    memory_texts = json.loads(memories_json)
                    
                    # Create non-episodic memory objects
                    non_episodic_memories = []
                    for memory_text in memory_texts:
                        if isinstance(memory_text, str) and memory_text.strip():
                            # Generate hooks for retrieval
                            hooks = self.hook_generator.generate_hooks(memory_text)
                            
                            # Create the non-episodic memory
                            non_episodic_memory = {
                                "type": "non_episodic",
                                "timestamp": datetime.now().isoformat(),
                                "content": memory_text,
                                "hooks": hooks
                            }
                            
                            non_episodic_memories.append(non_episodic_memory)
                    
                    # Combine with simple memories found through pattern matching
                    combined_memories = non_episodic_memories + simple_memories
                    
                    # Limit to a reasonable number
                    result_memories = combined_memories[:3]
                    
                    logger.debug(f"Extracted {len(result_memories)} non-episodic memories")
                    return result_memories
                except json.JSONDecodeError:
                    # If JSON parsing fails, return simple memories as fallback
                    logger.warning("Failed to parse non-episodic memories, using pattern-matched facts")
                    return simple_memories
            
            # If no array was found, return simple memories as fallback
            logger.warning("No non-episodic memories found in API response, using pattern-matched facts")
            return simple_memories
            
        except Exception as e:
            logger.error(f"Error extracting non-episodic memories: {e}")
            # Return simple memories as a fallback
            return simple_memories
    
    def _extract_simple_facts(self, text):
        """
        Extract simple facts from text using pattern matching.
        
        Args:
            text (str): The text to extract facts from.
            
        Returns:
            list: A list of simple facts.
        """
        facts = []
        
        # Pattern for "User/I prefer/like/love/hate/enjoy X"
        preference_patterns = [
            r'User(?:\'s|\s+)(?:preferred|favorite|likes|loves|hates|enjoys|dislikes)\s+([^.!?]+)',
            r'I\s+(?:prefer|like|love|hate|enjoy|dislike)\s+([^.!?]+)'
        ]
        
        # Pattern for "User/I am/is X" (attributes/properties)
        attribute_patterns = [
            r'User\s+(?:is|was|has been|has|had|will be)\s+([^.!?]+)',
            r'I\s+(?:am|was|have been|have|had|will be)\s+([^.!?]+)'
        ]
        
        # Pattern for "User/My name is X"
        name_patterns = [
            r'(?:User|My)\s+name\s+is\s+([^.!?]+)',
            r'I\s+am\s+([^.!?]{2,30})'  # Short phrases that might be names
        ]
        
        # Pattern for locations
        location_patterns = [
            r'(?:User|I)\s+(?:live|lives|work|works|study|studies)\s+in\s+([^.!?]+)',
            r'(?:User|I)\s+(?:am|is)\s+from\s+([^.!?]+)',
            r'(?:User|I)\s+(?:visited|traveled|went|traveled)\s+to\s+([^.!?]+)'
        ]
        
        # Extract facts using the patterns
        for pattern_list in [preference_patterns, attribute_patterns, name_patterns, location_patterns]:
            for pattern in pattern_list:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Clean and format the fact
                    fact = match.strip()
                    if len(fact) > 5:  # Ignore very short matches
                        # Convert to third person if it starts with "I"
                        if pattern.startswith(r'I\s+'):
                            fact = "User " + fact[2:]
                        facts.append(fact)
        
        return facts