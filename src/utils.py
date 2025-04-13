"""
Utility functions for the REMIND system.
"""
import re
import json
import logging
import os
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

def extract_dates_from_text(text):
    """
    Extract dates from text using regular expressions.
    
    Args:
        text (str): The text to extract dates from.
        
    Returns:
        list: A list of date strings found in the text.
    """
    # Common date formats
    date_patterns = [
        # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        # YYYY-MM-DD
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',
        # Month DD, YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]? \d{1,2}(?:st|nd|rd|th)?[.,]? \d{2,4}\b',
        # DD Month YYYY
        r'\b\d{1,2}(?:st|nd|rd|th)? (?:of )?(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]? \d{2,4}\b',
        # Today, yesterday, tomorrow
        r'\b(?:today|yesterday|tomorrow)\b',
        # Next/last week/month/year
        r'\b(?:next|last) (?:week|month|year)\b',
        # X days/weeks/months/years ago
        r'\b\d+ (?:day|week|month|year)s? ago\b'
    ]
    
    all_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        all_dates.extend(matches)
    
    return all_dates

def save_to_json_file(data, file_path):
    """
    Save data to a JSON file.
    
    Args:
        data (dict): The data to save.
        file_path (str): The path to the file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")

def load_from_json_file(file_path):
    """
    Load data from a JSON file.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        dict: The loaded data, or None if the file doesn't exist or can't be loaded.
    """
    if not os.path.exists(file_path):
        logger.debug(f"File does not exist: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.debug(f"Data loaded from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {e}")
        return None

def list_files_in_directory(directory, extension=None):
    """
    List all files in a directory, optionally filtered by extension.
    
    Args:
        directory (str): The directory to list files from.
        extension (str, optional): The file extension to filter by (e.g., '.json').
        
    Returns:
        list: A list of file paths.
    """
    if not os.path.exists(directory):
        logger.debug(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if extension is None or filename.endswith(extension):
                files.append(os.path.join(root, filename))
    
    return files

def get_days_since_timestamp(timestamp_str):
    """
    Calculate the number of days since a timestamp.
    
    Args:
        timestamp_str (str): An ISO format timestamp string.
        
    Returns:
        float: The number of days since the timestamp, or None if the timestamp is invalid.
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - timestamp
        return delta.total_seconds() / (60 * 60 * 24)  # Convert seconds to days
    except (ValueError, TypeError) as e:
        logger.error(f"Error calculating days since timestamp {timestamp_str}: {e}")
        return None

def generate_unique_filename(prefix, extension='.json'):
    """
    Generate a unique filename using the current timestamp.
    
    Args:
        prefix (str): The filename prefix.
        extension (str, optional): The file extension. Defaults to '.json'.
        
    Returns:
        str: A unique filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}{extension}"