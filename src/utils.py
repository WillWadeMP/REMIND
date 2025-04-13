"""
Utility functions for REMIND system.
"""
import logging
import re
import string
from datetime import datetime
from typing import List, Dict, Any, Optional

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

import config

logger = logging.getLogger(__name__)

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Input text
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove excessive punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:]', '', text)
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract important keywords from text.
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List[str]: List of extracted keywords
    """
    # Clean and normalize text
    text = clean_text(text.lower())
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english')).union(config.STOPWORDS)
    tokens = [token for token in tokens if token not in stop_words and token not in string.punctuation]
    
    # Count word frequencies
    word_freq = {}
    for token in tokens:
        word_freq[token] = word_freq.get(token, 0) + 1
    
    # Sort by frequency (most frequent first)
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top keywords
    keywords = [word for word, freq in sorted_words[:max_keywords]]
    
    # Extract significant phrases (bigrams)
    bigrams = []
    for i in range(len(tokens) - 1):
        if tokens[i] not in stop_words and tokens[i+1] not in stop_words:
            bigram = f"{tokens[i]} {tokens[i+1]}"
            bigrams.append(bigram)
    
    # Count bigram frequencies
    bigram_freq = {}
    for bigram in bigrams:
        bigram_freq[bigram] = bigram_freq.get(bigram, 0) + 1
    
    # Sort by frequency (most frequent first)
    sorted_bigrams = sorted(bigram_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top bigrams
    top_bigrams = [bigram for bigram, freq in sorted_bigrams[:5]]
    
    # Combine keywords and bigrams, ensure we don't exceed max_keywords
    combined = keywords + top_bigrams
    return combined[:max_keywords]

def extract_dates(text: str) -> List[str]:
    """
    Extract dates mentioned in text.
    
    Args:
        text: Input text
        
    Returns:
        List[str]: List of extracted date strings
    """
    # Common date patterns
    date_patterns = [
        # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        # YYYY-MM-DD
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',
        # Month DD, YYYY
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
        # DD Month YYYY
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b'
    ]
    
    # Find all date matches
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    
    return dates

def format_timestamp(timestamp: str, format: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format ISO timestamp to human-readable format.
    
    Args:
        timestamp: ISO format timestamp
        format: Output format
        
    Returns:
        str: Formatted timestamp
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime(format)
    except (ValueError, AttributeError):
        return timestamp

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Try to truncate at a sentence boundary
    sentences = re.split(r'(?<=[.!?])\s+', text)
    truncated = ""
    
    for sentence in sentences:
        if len(truncated) + len(sentence) <= max_length:
            truncated += sentence + " "
        else:
            break
    
    # If no complete sentence fits, truncate at word boundary
    if not truncated:
        words = text[:max_length].split()
        truncated = " ".join(words[:-1]) if len(words) > 1 else words[0]
    
    return truncated.strip() + "..."

def merge_tags(tag_lists: List[List[str]], max_tags: int = 10) -> List[str]:
    """
    Merge multiple tag lists with deduplication.
    
    Args:
        tag_lists: List of tag lists to merge
        max_tags: Maximum number of tags in result
        
    Returns:
        List[str]: Merged tag list
    """
    # Flatten all tag lists
    all_tags = []
    for tag_list in tag_lists:
        all_tags.extend(tag_list)
    
    # Count tag frequencies
    tag_freq = {}
    for tag in all_tags:
        tag_freq[tag] = tag_freq.get(tag, 0) + 1
    
    # Sort by frequency (most frequent first)
    sorted_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top tags
    top_tags = [tag for tag, freq in sorted_tags[:max_tags]]
    
    return top_tags