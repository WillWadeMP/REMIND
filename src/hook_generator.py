"""
Generates hooks for indexing memories using Claude.
"""
import logging
import re
import config
from src.claude_client import create_claude_client

logger = logging.getLogger(__name__)

class HookGenerator:
    """Generates hooks for indexing memories."""
    
    def __init__(self):
        """Initialize the HookGenerator with Claude API client."""
        self.client = create_claude_client()
        # Use the faster model for hook generation to reduce costs and improve speed
        self.model = config.CLAUDE_FAST_MODEL
        self.max_hooks = config.MAX_HOOKS_PER_MEMORY
        logger.info(f"HookGenerator initialized with model: {self.model}")
    
    def generate_hooks(self, text, existing_hooks=None):
        """
        Generate hooks for a piece of text.
        
        Args:
            text (str): The text to generate hooks for.
            existing_hooks (list, optional): Existing hooks to consider. Defaults to None.
            
        Returns:
            list: A list of hooks.
        """
        if not text:
            logger.warning("Empty text provided for hook generation")
            return []
        
        logger.debug(f"Generating hooks for text (length: {len(text)})")
        
        # FIXED: Add fallback method for faster hook generation without API if needed
        # Extract basic hooks from the text directly before using the API
        basic_hooks = self._extract_basic_hooks(text)
        
        # If we already have enough good hooks, skip the API call
        if len(basic_hooks) >= self.max_hooks:
            logger.debug(f"Using {len(basic_hooks)} basic hooks without API call")
            return basic_hooks[:self.max_hooks]
        
        # Continue with API-based hook generation for better quality
        existing_hooks_str = ""
        if existing_hooks:
            existing_hooks_str = "Consider the following existing hooks when generating new ones: " + ", ".join(existing_hooks)
        
        # FIXED: Improved prompting for better hook generation
        prompt = f"""
        Please analyze the following text and generate up to {self.max_hooks} hooks for indexing and retrieval.
        
        Hooks should be one to three word phrases that capture key entities, concepts, sentiments, or themes in the text.
        Good hooks are specific, diverse, and cover different aspects of the text.
        Include both general topics and specific details as hooks.
        
        Examples of good hooks:
        - For a text about a person's vacation: "beach trip", "summer vacation", "family bonding", "ocean swimming"
        - For a technical article: "machine learning", "neural networks", "data science", "algorithm optimization"
        - For a conversation about food: "favorite foods", "cooking recipes", "dietary preferences", "restaurant recommendations"
        
        {existing_hooks_str}
        
        Text: {text}
        
        Return ONLY a JSON array of strings, with each string being a hook.
        Example: ["hook1", "hook2", "hook3"]
        """
        
        try:
            # Use the client wrapper
            response = self.client.messages_create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
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
                    hooks_json = f"[{array_match.group(1)}]"
                    hooks = json.loads(hooks_json)
                    
                    # Filter out invalid hooks
                    hooks = [hook.strip() for hook in hooks if isinstance(hook, str) and hook.strip()]
                    
                    # Limit the number of hooks
                    hooks = hooks[:self.max_hooks]
                    
                    # FIXED: Combine with the basic hooks for more coverage
                    combined_hooks = list(set(hooks + basic_hooks))
                    
                    logger.debug(f"Generated hooks: {combined_hooks}")
                    return combined_hooks[:self.max_hooks]
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract hooks directly from the text
                    logger.warning("Failed to parse hook JSON, using fallback extraction")
                    pass
            
            # Fallback: extract hooks directly from the response
            # Look for quotes which likely contain hooks
            hooks = re.findall(r'"([^"]+)"', response_text)
            
            # If no quoted strings found, try comma-separated values
            if not hooks:
                # Remove brackets and split by commas
                clean_text = response_text.replace('[', '').replace(']', '')
                hooks = [h.strip().strip('"\'') for h in clean_text.split(',')]
            
            # Filter out invalid hooks and limit the number
            hooks = [hook.strip() for hook in hooks if hook.strip()]
            
            # Combine with basic hooks
            combined_hooks = list(set(hooks + basic_hooks))
            combined_hooks = combined_hooks[:self.max_hooks]
            
            logger.debug(f"Generated hooks (fallback method): {combined_hooks}")
            return combined_hooks
            
        except Exception as e:
            logger.error(f"Error generating hooks: {e}")
            # Return basic hooks as a fallback
            logger.info(f"Using basic hooks as fallback due to API error")
            return basic_hooks[:self.max_hooks]
    
    def _extract_basic_hooks(self, text):
        """
        Extract basic hooks directly from the text without using an API call.
        
        Args:
            text (str): The text to extract hooks from.
            
        Returns:
            list: A list of basic hooks.
        """
        # Extract single words and compound terms
        
        # Normalize text: lowercase and remove punctuation except spaces and hyphens
        normalized_text = re.sub(r'[^\w\s-]', ' ', text.lower())
        
        # Split text into words
        words = normalized_text.split()
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if len(word) > 2:  # Skip very short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Extract top frequent words as potential hooks
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        single_word_hooks = [word for word, freq in sorted_words[:10] if word not in config.STOPWORDS]
        
        # Extract common phrases (2-3 word combinations)
        phrases = []
        for i in range(len(words) - 1):
            if words[i] not in config.STOPWORDS and len(words[i]) > 2:
                # 2-word phrases
                phrase = f"{words[i]} {words[i+1]}"
                phrases.append(phrase)
                
                # 3-word phrases if possible
                if i < len(words) - 2:
                    phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                    phrases.append(phrase)
        
        # Count phrase frequency
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Extract top frequent phrases
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        phrase_hooks = [phrase for phrase, freq in sorted_phrases[:10]]
        
        # Check for entities (names, locations, etc.) - simplified approach
        potential_entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        entity_hooks = [entity.lower() for entity in potential_entities if len(entity) > 2][:5]
        
        # Combine all hooks and remove duplicates
        all_hooks = single_word_hooks + phrase_hooks + entity_hooks
        
        # Filter hooks (remove duplicates and ensure minimum length)
        filtered_hooks = self.filter_hooks(all_hooks)
        
        return filtered_hooks