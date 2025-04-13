"""
Handler for user prompts.
"""
import logging
import re
from datetime import datetime
from src.summarizer import Summarizer
from src.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)

class PromptHandler:
    """Handles user prompts and extracts relevant information."""
    
    def __init__(self):
        """Initialize the PromptHandler."""
        self.summarizer = Summarizer()
        self.metadata_extractor = MetadataExtractor()
        logger.info("PromptHandler initialized")
    
    def process(self, prompt):
        """
        Process a user prompt and extract relevant information.
        
        Args:
            prompt (str): The user prompt.
            
        Returns:
            dict: A dictionary containing processed prompt information:
                - original_prompt: The original user prompt.
                - summary: A summary of the prompt.
                - metadata: Extracted metadata (keywords, dates, etc.).
                - timestamp: The timestamp of when the prompt was processed.
        """
        logger.debug(f"Processing prompt: {prompt}")
        
        # FIXED: Check for empty or invalid prompts
        if not prompt or not isinstance(prompt, str) or prompt.strip() == "":
            logger.warning("Empty or invalid prompt received")
            return {
                "original_prompt": prompt if isinstance(prompt, str) else "",
                "summary": "",
                "metadata": {"keywords": [], "dates": [], "themes": [], "sentiment": "neutral"},
                "timestamp": datetime.now().isoformat()
            }
        
        # Create a summary of the prompt
        summary = self.summarizer.summarize(prompt)
        
        # Extract metadata from the prompt
        metadata = self.metadata_extractor.extract(prompt)
        
        # FIXED: Enhance metadata with additional preprocessing
        # Detect if this is a memory-related query
        memory_keywords = ["remember", "recall", "memory", "forget", "remembered", 
                          "mentioned", "said", "told", "talked about", "discussed",
                          "previous", "earlier", "before", "last time"]
        
        is_memory_query = False
        for keyword in memory_keywords:
            if keyword in prompt.lower():
                is_memory_query = True
                # Add memory-related keywords if not already present
                if "keywords" in metadata and "memory" not in metadata["keywords"]:
                    metadata["keywords"].append("memory")
                if "keywords" in metadata and "recall" not in metadata["keywords"]:
                    metadata["keywords"].append("recall")
                break
        
        # FIXED: Detect if this is a date-specific query
        date_pattern = r'\b(?:on|at|in|during)\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{4}-\d{2}-\d{2})\b'
        date_match = re.search(date_pattern, prompt, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1)
            if "dates" in metadata and date_str not in metadata["dates"]:
                metadata["dates"].append(date_str)
        
        # FIXED: Add additional processing for "what did we talk about" queries
        talk_about_patterns = [
            r'what did (?:we|you|I) (?:talk|discuss|say|mention) about',
            r'what (?:was|were) (?:we|you|I) (?:talking|discussing|saying|mentioning) about',
            r'what have (?:we|you|I) (?:talked|discussed|said|mentioned) about'
        ]
        
        for pattern in talk_about_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                # This is definitely a memory-related query
                if "keywords" in metadata and "conversation history" not in metadata["keywords"]:
                    metadata["keywords"].append("conversation history")
                if "themes" in metadata and "past conversations" not in metadata["themes"]:
                    metadata["themes"].append("past conversations")
                break
                
        # Create a timestamp for the prompt
        timestamp = datetime.now().isoformat()
        
        # Combine all information into a structured format
        processed_prompt = {
            "original_prompt": prompt,
            "summary": summary,
            "metadata": metadata,
            "timestamp": timestamp,
            "is_memory_query": is_memory_query
        }
        
        logger.debug(f"Processed prompt: {processed_prompt}")
        return processed_prompt