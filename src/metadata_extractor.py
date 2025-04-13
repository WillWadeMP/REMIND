"""
Extracts metadata from text, including keywords, dates, and semantic themes.
"""
import logging
import re
from datetime import datetime
import config
from src.claude_client import create_claude_client
from src.utils import extract_dates_from_text

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Extracts metadata from text using Claude and regex patterns."""
    
    def __init__(self):
        """Initialize the MetadataExtractor with Claude API client."""
        self.client = create_claude_client()
        # Use the faster model for metadata extraction to reduce costs and improve speed
        self.model = config.CLAUDE_FAST_MODEL
        logger.info(f"MetadataExtractor initialized with model: {self.model}")
    
    def extract(self, text):
        """
        Extract metadata from the given text.
        
        Args:
            text (str): The text to extract metadata from.
            
        Returns:
            dict: A dictionary containing extracted metadata:
                - keywords: List of keywords.
                - dates: List of dates mentioned in the text.
                - themes: List of semantic themes.
                - sentiment: Sentiment analysis of the text.
        """
        if not text:
            logger.warning("Empty text provided for metadata extraction")
            return {"keywords": [], "dates": [], "themes": [], "sentiment": "neutral"}
        
        logger.debug(f"Extracting metadata from text (length: {len(text)})")
        
        # Extract dates using regex
        dates = extract_dates_from_text(text)
        
        # Use Claude to extract keywords, themes, and sentiment
        prompt = f"""
        Please analyze the following text and extract:
        1. Keywords: Important nouns, verbs, and adjectives (max 10)
        2. Semantic themes: High-level topics or concepts present in the text (max 5)
        3. Sentiment: The overall emotional tone (positive, negative, neutral, or mixed)
        
        Format your response as a JSON object with keys: "keywords", "themes", and "sentiment".
        
        Text: {text}
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
            
            # Simple extraction of JSON from the response text
            # In a real implementation, you might want to use a more robust method
            # or have Claude return a more structured format
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start != -1 and json_end != -1:
                import json
                try:
                    extracted_data = json.loads(response_text[json_start:json_end])
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    extracted_data = {
                        "keywords": [],
                        "themes": [],
                        "sentiment": "neutral"
                    }
            else:
                # Fallback if JSON parsing fails
                extracted_data = {
                    "keywords": [],
                    "themes": [],
                    "sentiment": "neutral"
                }
                
                # Try to extract data from text if JSON fails
                if "keywords" in response_text.lower():
                    keywords_match = re.search(r"keywords[:\s]+(.*?)(?=themes|\n\n|$)", response_text, re.IGNORECASE | re.DOTALL)
                    if keywords_match:
                        keywords_text = keywords_match.group(1).strip()
                        extracted_data["keywords"] = [k.strip() for k in re.split(r'[,\n]', keywords_text) if k.strip()]
                
                if "themes" in response_text.lower():
                    themes_match = re.search(r"themes[:\s]+(.*?)(?=sentiment|\n\n|$)", response_text, re.IGNORECASE | re.DOTALL)
                    if themes_match:
                        themes_text = themes_match.group(1).strip()
                        extracted_data["themes"] = [t.strip() for t in re.split(r'[,\n]', themes_text) if t.strip()]
                
                if "sentiment" in response_text.lower():
                    sentiment_match = re.search(r"sentiment[:\s]+(.*?)(?=\n\n|$)", response_text, re.IGNORECASE)
                    if sentiment_match:
                        extracted_data["sentiment"] = sentiment_match.group(1).strip().lower()
            
            # Add dates to the extracted data
            extracted_data["dates"] = dates
            
            logger.debug(f"Extracted metadata: {extracted_data}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            # Return empty metadata as a fallback
            return {"keywords": [], "dates": dates, "themes": [], "sentiment": "neutral"}