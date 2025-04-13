"""
Summarizer that uses Claude to create concise summaries of text.
"""
import logging
import re
import config
from src.claude_client import create_claude_client

logger = logging.getLogger(__name__)

class Summarizer:
    """Creates summaries of text using Claude."""
    
    def __init__(self):
        """Initialize the Summarizer with Claude API client."""
        self.client = create_claude_client()
        # Use the faster model for summarization to reduce costs and improve speed
        self.model = config.CLAUDE_FAST_MODEL
        logger.info(f"Summarizer initialized with model: {self.model}")
    
    def summarize(self, text, max_length=200):
        """
        Create a concise summary of the given text.
        
        Args:
            text (str): The text to summarize.
            max_length (int, optional): Maximum length of the summary in characters. Defaults to 200.
            
        Returns:
            str: A concise summary of the text.
        """
        if not text:
            logger.warning("Empty text provided for summarization")
            return ""
        
        logger.debug(f"Summarizing text (length: {len(text)})")
        
        # FIXED: For very short texts, avoid API call and just return the text
        if len(text) <= max_length:
            logger.debug("Text already shorter than max_length, skipping summarization")
            return text
        
        # FIXED: Try rule-based summarization for simple cases first
        rule_based_summary = self._rule_based_summarize(text, max_length)
        if rule_based_summary:
            logger.debug("Using rule-based summary to avoid API call")
            return rule_based_summary
        
        # FIXED: Improved prompt with clear instructions
        prompt = f"""
        Please create a concise and accurate summary of the following text. 
        The summary should:
        1. Capture the main points and key information
        2. Be at most {max_length} characters
        3. Be written in third person, neutral tone
        4. Not include meta-commentary or self-references
        
        Text: {text}
        
        Summary (max {max_length} characters):
        """
        
        try:
            # Use the messages API through our wrapper
            response = self.client.messages_create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for more deterministic summaries
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the text from the response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                if isinstance(response.content[0], dict) and 'text' in response.content[0]:
                    summary = response.content[0]['text'].strip()
                elif hasattr(response.content[0], 'text'):
                    summary = response.content[0].text.strip()
                else:
                    summary = str(response.content[0]).strip()
            else:
                summary = str(response).strip()
            
            # FIXED: Post-process the summary to remove any potential meta-commentary
            summary = self._clean_summary(summary)
                
            logger.debug(f"Generated summary: {summary}")
            
            # Ensure the summary is within the max length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
                
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            # FIXED: Better fallback mechanism - extract first sentences
            return self._extract_first_sentences(text, max_length)
    
    def _rule_based_summarize(self, text, max_length):
        """
        Attempt to summarize text using rule-based methods.
        
        Args:
            text (str): The text to summarize.
            max_length (int): Maximum length of the summary.
            
        Returns:
            str: A summary, or None if rule-based summarization is not appropriate.
        """
        # Check if this is a conversation
        conversation_pattern = r"User:\s+(.+?)(?:\n+Assistant:\s+(.+?)(?:\n|$))"
        conversation_matches = re.findall(conversation_pattern, text, re.DOTALL)
        
        if conversation_matches:
            # This is a conversation, extract the main points
            summary = "Conversation about"
            topics = set()
            
            for user_msg, _ in conversation_matches:
                # Extract probable topics from user messages
                user_msg = user_msg.lower()
                
                # Check for common topics
                topic_keywords = {
                    "personal information": ["my name", "i am", "about me", "myself"],
                    "technology": ["computer", "software", "code", "program", "app"],
                    "health": ["health", "medical", "doctor", "sick", "illness"],
                    "food": ["food", "eat", "cook", "recipe", "restaurant"],
                    "travel": ["travel", "trip", "vacation", "visit", "country"],
                    "work": ["job", "work", "career", "employer", "company"]
                }
                
                for topic, keywords in topic_keywords.items():
                    if any(keyword in user_msg for keyword in keywords):
                        topics.add(topic)
            
            if topics:
                summary += " " + ", ".join(topics)
                if len(summary) <= max_length:
                    return summary
        
        # Try to extract key sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 3:
            # Very few sentences, just return the first one or two
            potential_summary = " ".join(sentences[:2])
            if len(potential_summary) <= max_length:
                return potential_summary
        
        # Rule-based approach not appropriate for this text
        return None
    
    def _extract_first_sentences(self, text, max_length):
        """
        Extract the first few sentences of the text as a fallback summary.
        
        Args:
            text (str): The text to summarize.
            max_length (int): Maximum length of the summary.
            
        Returns:
            str: The first few sentences, up to max_length.
        """
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) + 1 <= max_length:
                if summary:
                    summary += " " + sentence
                else:
                    summary = sentence
            else:
                break
        
        # If we couldn't fit even one sentence, truncate
        if not summary:
            summary = text[:max_length-3] + "..."
            
        return summary.strip()
    
    def _clean_summary(self, summary):
        """
        Clean the summary to remove any meta-commentary.
        
        Args:
            summary (str): The raw summary.
            
        Returns:
            str: The cleaned summary.
        """
        # Remove any meta-commentary patterns
        meta_patterns = [
            r"^(?:Here's|Here is) a (?:summary|concise summary|brief summary)[:.]\s*",
            r"^Summary:\s*",
            r"^The (?:text|conversation|passage|document) (?:is about|discusses|covers|describes)[:.]\s*",
            r"^This (?:text|conversation|passage|document)[^.]*?(?:talks about|covers|discusses|describes)[:.]\s*"
        ]
        
        cleaned = summary
        for pattern in meta_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Remove any closing statements
        closing_patterns = [
            r"\s+In summary,.*$",
            r"\s+To summarize,.*$",
            r"\s+This summary captures.*$",
            r"\s+This is a concise summary.*$"
        ]
        
        for pattern in closing_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()