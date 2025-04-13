"""
Retrieval engine for finding relevant memories.
"""
import logging
import re
from datetime import datetime
import config
from src.hook_generator import HookGenerator
from src.claude_client import create_claude_client
from src.utils import extract_dates_from_text

logger = logging.getLogger(__name__)

class Relevancer:
    """Retrieves relevant memories based on user input."""
    
    def __init__(self, memory_layer):
        """
        Initialize the Relevancer.
        
        Args:
            memory_layer (MemoryLayer): The memory layer to retrieve memories from.
        """
        self.memory_layer = memory_layer
        self.hook_generator = HookGenerator()
        self.client = create_claude_client()
        # Use standard model for ranking, which requires reasoning
        self.model = config.CLAUDE_MODEL
        self.max_memories = config.MAX_MEMORIES_TO_RETRIEVE
        logger.info(f"Relevancer initialized with model: {self.model}")
    
    def retrieve(self, processed_prompt):
        """
        Retrieve relevant memories based on a processed prompt.
        
        Args:
            processed_prompt (dict): The processed prompt information.
            
        Returns:
            list: A list of relevant memories.
        """
        logger.debug(f"Retrieving memories for prompt: {processed_prompt}")
        
        # Extract information from the processed prompt
        prompt_text = processed_prompt.get("original_prompt", "")
        prompt_summary = processed_prompt.get("summary", "")
        prompt_metadata = processed_prompt.get("metadata", {})
        
        # FIXED: Extract date references to improve temporal retrieval
        date_references = prompt_metadata.get("dates", [])
        if not date_references:
            # If no dates in metadata, try extracting from the prompt directly
            date_references = extract_dates_from_text(prompt_text)
        
        # FIXED: Add special handling for date-based queries about past conversations
        time_related_phrases = [
            "yesterday", "last week", "last time", "previously", "before",
            "earlier", "last month", "remember", "recall", "mentioned",
            "talked about", "discussed", "said", "told", "asked"
        ]
        
        time_query = False
        date_query = False
        specific_date = None
        
        # Check if this is a temporal query
        lower_prompt = prompt_text.lower()
        
        # Check for date mentions with special focus on specific dates
        if date_references:
            date_query = True
            for date_ref in date_references:
                # Try to parse the date
                try:
                    # Handle relative date references like "yesterday" or "last week"
                    if date_ref.lower() in ["today", "yesterday", "tomorrow"]:
                        specific_date = date_ref.lower()
                    else:
                        # Try to parse explicit dates
                        # This is a simplified approach, you might need more robust date parsing
                        date_patterns = [
                            # Match patterns like "April 13, 2025" or "April 13 2025"
                            r'(\w+)\s+(\d{1,2})(?:,?\s+|\s*,\s*)(\d{4})',
                            # Match patterns like "13 April 2025"
                            r'(\d{1,2})(?:\s+|\s*\w{2}\s+)(\w+)(?:,?\s+|\s*,\s*)(\d{4})',
                            # Match ISO format YYYY-MM-DD
                            r'(\d{4})-(\d{2})-(\d{2})'
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, date_ref)
                            if match:
                                specific_date = date_ref
                                break
                except Exception as e:
                    logger.warning(f"Error parsing date {date_ref}: {e}")
                    continue
        
        # Check for time-related phrases
        for phrase in time_related_phrases:
            if phrase in lower_prompt:
                time_query = True
                break
        
        # Generate hooks from the prompt
        hooks = self.hook_generator.generate_hooks(prompt_text)
        
        # Add keywords from metadata to hooks
        if "keywords" in prompt_metadata:
            hooks.extend(prompt_metadata["keywords"])
        
        # Add themes from metadata to hooks
        if "themes" in prompt_metadata:
            hooks.extend(prompt_metadata["themes"])
        
        # FIXED: Add special hooks for temporal queries
        if time_query or date_query:
            hooks.extend(["conversation", "discussion", "memory", "recall"])
            
            # Add specific date as a hook if available
            if specific_date:
                hooks.append(specific_date)
        
        # Get unique hooks
        hooks = list(set(hooks))
        
        # FIXED: Directly search memory by date if this is a query about a specific date
        date_filtered_memories = []
        if specific_date:
            # Get all memories
            all_episodic = self.memory_layer.get_episodic_memories()
            all_non_episodic = self.memory_layer.get_non_episodic_memories()
            all_memories = all_episodic + all_non_episodic
            
            for memory in all_memories:
                # Check if memory timestamp contains the specific date
                memory_timestamp = memory.get("timestamp", "")
                if specific_date in memory_timestamp:
                    date_filtered_memories.append(memory)
            
            # If we found memories for the specific date, prioritize them
            if date_filtered_memories:
                logger.debug(f"Found {len(date_filtered_memories)} memories for specific date: {specific_date}")
                # If we have few memories, we can skip the relevance ranking
                if len(date_filtered_memories) <= self.max_memories:
                    return date_filtered_memories
                else:
                    # Rank date-filtered memories by relevance to the query
                    return self._rank_memories_by_relevance(prompt_text, date_filtered_memories)
        
        # Standard retrieval using hooks
        episodic_memories = self.memory_layer.get_episodic_memories(hooks=hooks)
        non_episodic_memories = self.memory_layer.get_non_episodic_memories(hooks=hooks)
        
        # Combine all potential memories
        all_potential_memories = episodic_memories + non_episodic_memories
        
        # FIXED: If no memories found but this was a date query, try a broader search
        if not all_potential_memories and (time_query or date_query):
            logger.debug("No memories found with hooks, trying broader date-based search")
            # Get a limited number of recent memories
            episodic_memories = self.memory_layer.get_episodic_memories(max_count=20)
            non_episodic_memories = self.memory_layer.get_non_episodic_memories(max_count=10)
            all_potential_memories = episodic_memories + non_episodic_memories
        
        # If we have no memories, return an empty list
        if not all_potential_memories:
            logger.debug("No potentially relevant memories found")
            return []
        
        # If we have few memories, we can skip the relevance ranking
        if len(all_potential_memories) <= self.max_memories:
            logger.debug(f"Retrieved {len(all_potential_memories)} memories (no ranking needed)")
            return all_potential_memories
        
        # Rank memories by relevance using Claude
        ranked_memories = self._rank_memories_by_relevance(prompt_text, all_potential_memories)
        
        # Return the top N most relevant memories
        top_memories = ranked_memories[:self.max_memories]
        logger.debug(f"Retrieved {len(top_memories)} memories (after ranking)")
        return top_memories
    
    def _rank_memories_by_relevance(self, prompt_text, memories):
        """
        Rank memories by relevance to the prompt.
        
        Args:
            prompt_text (str): The original prompt text.
            memories (list): The list of memories to rank.
            
        Returns:
            list: A list of memories sorted by relevance (most relevant first).
        """
        # FIXED: Improved memory preparation for ranking
        memory_summaries = []
        for i, memory in enumerate(memories):
            content = memory.get("content", "")
            summary = memory.get("summary", "")
            timestamp = memory.get("timestamp", "")
            
            # Format timestamp for better readability if possible
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                formatted_time = timestamp
                
            memory_text = summary if summary else content
            memory_summaries.append(f"Memory {i+1} (from {formatted_time}): {memory_text}")
        
        # Join memory summaries into a single text
        memories_text = "\n\n".join(memory_summaries)
        
        # FIXED: Enhanced ranking prompt for better relevance determination
        ranking_prompt = f"""
        I need to find memories that are most relevant to the following prompt:
        
        "{prompt_text}"
        
        Here are the available memories:
        
        {memories_text}
        
        Please rank these memories by their relevance to the prompt.
        Consider:
        1. Direct relevance to the subject matter or question
        2. Temporal relevance (if the prompt asks about a specific time)
        3. Semantic connections between the prompt and memory content
        
        Return ONLY a JSON array of memory indices in order of relevance (most relevant first).
        Example: [3, 1, 5, 2, 4]
        """
        
        try:
            # Use the client wrapper
            response = self.client.messages_create(
                model=self.model,
                max_tokens=1024,
                temperature=0.2,  # Lower temperature for more deterministic ranking
                messages=[
                    {"role": "user", "content": ranking_prompt}
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
                    indices_json = f"[{array_match.group(1)}]"
                    indices = json.loads(indices_json)
                    
                    # Convert 1-based indices to 0-based indices and filter out invalid indices
                    valid_indices = [idx - 1 for idx in indices if isinstance(idx, int) and 1 <= idx <= len(memories)]
                    
                    # Reorder memories based on the indices
                    ranked_memories = [memories[idx] for idx in valid_indices if idx < len(memories)]
                    
                    # Add any memories that weren't ranked (as a fallback)
                    ranked_indices_set = set(valid_indices)
                    for i in range(len(memories)):
                        if i not in ranked_indices_set:
                            ranked_memories.append(memories[i])
                    
                    return ranked_memories
                except json.JSONDecodeError as e:
                    # FIXED: Better error handling for JSON parsing
                    logger.warning(f"Failed to parse ranked indices: {e}")
                    logger.warning(f"Response text: {response_text[:200]}...")
                    
                    # Try a simpler approach - just extract numbers
                    try:
                        numbers = re.findall(r'\d+', array_match.group(1))
                        indices = [int(num) for num in numbers]
                        valid_indices = [idx - 1 for idx in indices if 1 <= idx <= len(memories)]
                        
                        # Reorder memories based on the indices
                        ranked_memories = [memories[idx] for idx in valid_indices if idx < len(memories)]
                        
                        # Add any memories that weren't ranked
                        ranked_indices_set = set(valid_indices)
                        for i in range(len(memories)):
                            if i not in ranked_indices_set:
                                ranked_memories.append(memories[i])
                        
                        return ranked_memories
                    except Exception:
                        logger.warning("Failed to extract numbers from response")
                        return memories
            
            # If no array was found, fall back to the original order
            logger.warning("No ranked indices found, using original order")
            return memories
            
        except Exception as e:
            logger.error(f"Error ranking memories: {e}")
            # Return memories in original order as a fallback
            return memories
            
    def _extract_date_from_prompt(self, prompt_text):
        """
        Extract date information from the prompt text.
        
        Args:
            prompt_text (str): The prompt text.
            
        Returns:
            tuple: (is_date_query, specific_date) where is_date_query is a boolean
                  indicating if this is a date-related query, and specific_date is
                  the extracted date string (if any).
        """
        # This is a simplified implementation, you might want to use a more robust
        # date extraction library in a production system
        
        # Check for common date query patterns
        date_query_patterns = [
            r'(?:what|when|how).{1,20}(?:on|at).{1,10}(\w+ \d{1,2},? \d{4})',
            r'(?:what|when|how).{1,20}(?:on|at).{1,10}(\d{1,2} \w+ \d{4})',
            r'(?:what|when|how).{1,20}(?:on|at).{1,10}(\d{4}-\d{2}-\d{2})',
            r'(?:on|at) (\w+ \d{1,2},? \d{4})',
            r'(?:on|at) (\d{1,2} \w+ \d{4})',
            r'(?:on|at) (\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_query_patterns:
            match = re.search(pattern, prompt_text, re.IGNORECASE)
            if match:
                return True, match.group(1)
        
        # Check for relative time expressions
        relative_time_patterns = [
            (r'yesterday', 'yesterday'),
            (r'last week', 'last week'),
            (r'last month', 'last month'),
            (r'today', 'today'),
            (r'this morning', 'today'),
            (r'this afternoon', 'today'),
            (r'this evening', 'today')
        ]
        
        for pattern, value in relative_time_patterns:
            if re.search(pattern, prompt_text, re.IGNORECASE):
                return True, value
                
        return False, None