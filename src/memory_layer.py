"""
Memory layer for storing and retrieving memories.
"""
import os
import json
import logging
import re
from datetime import datetime, timedelta
import config
from src.utils import (
    save_to_json_file,
    load_from_json_file,
    list_files_in_directory,
    get_days_since_timestamp,
    generate_unique_filename
)

logger = logging.getLogger(__name__)

class MemoryLayer:
    """Manages episodic and non-episodic memories."""
    
    def __init__(self):
        """Initialize the MemoryLayer."""
        self.episodic_dir = config.EPISODIC_MEMORY_DIR
        self.non_episodic_dir = config.NON_EPISODIC_MEMORY_DIR
        
        # Ensure memory directories exist
        os.makedirs(self.episodic_dir, exist_ok=True)
        os.makedirs(self.non_episodic_dir, exist_ok=True)
        
        logger.info(f"MemoryLayer initialized with directories: {self.episodic_dir}, {self.non_episodic_dir}")
    
    def store_episodic_memory(self, memory_data):
        """
        Store an episodic memory.
        
        Args:
            memory_data (dict): The memory data to store.
            
        Returns:
            str: The path to the stored memory file.
        """
        # Generate a unique filename based on timestamp
        filename = generate_unique_filename("episodic")
        file_path = os.path.join(self.episodic_dir, filename)
        
        # Add timestamp if not present
        if "timestamp" not in memory_data:
            memory_data["timestamp"] = datetime.now().isoformat()
        
        # FIXED: Ensure hooks are properly formatted and indexed
        if "hooks" in memory_data:
            memory_data["hooks"] = [hook.lower().strip() for hook in memory_data["hooks"] if isinstance(hook, str)]
        
        # Save the memory to a JSON file
        save_to_json_file(memory_data, file_path)
        
        # Prune old memories if necessary
        self._prune_episodic_memories()
        
        logger.info(f"Stored episodic memory: {file_path}")
        return file_path
    
    def store_non_episodic_memory(self, memory_data):
        """
        Store a non-episodic memory.
        
        Args:
            memory_data (dict): The memory data to store.
            
        Returns:
            str: The path to the stored memory file.
        """
        # Check if memory_data has hooks
        if "hooks" not in memory_data or not memory_data["hooks"]:
            logger.warning("No hooks found in non-episodic memory data")
            return None
        
        # FIXED: Ensure hooks are properly formatted
        memory_data["hooks"] = [hook.lower().strip() for hook in memory_data["hooks"] if isinstance(hook, str)]
        
        # Generate a filename based on the first hook (for better organization)
        primary_hook = memory_data["hooks"][0].replace(" ", "_").lower()
        filename = f"non_episodic_{primary_hook}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(self.non_episodic_dir, filename)
        
        # Add timestamp if not present
        if "timestamp" not in memory_data:
            memory_data["timestamp"] = datetime.now().isoformat()
        
        # Save the memory to a JSON file
        save_to_json_file(memory_data, file_path)
        
        # Prune if we exceed the maximum number of non-episodic memories
        self._prune_non_episodic_memories()
        
        logger.info(f"Stored non-episodic memory: {file_path}")
        return file_path
    
    def get_episodic_memories(self, hooks=None, max_count=None, date_filter=None):
        """
        Retrieve episodic memories, optionally filtered by hooks or date.
        
        Args:
            hooks (list, optional): List of hooks to filter by. Defaults to None.
            max_count (int, optional): Maximum number of memories to retrieve. Defaults to None.
            date_filter (str, optional): Date string to filter by. Defaults to None.
            
        Returns:
            list: A list of episodic memories, sorted by timestamp (most recent first).
        """
        memory_files = list_files_in_directory(self.episodic_dir, ".json")
        memories = []
        
        # FIXED: Better error handling for file loading
        for file_path in memory_files:
            try:
                memory = load_from_json_file(file_path)
                if memory is None:
                    logger.warning(f"Failed to load memory from {file_path}")
                    continue
                
                # Add the file path for reference
                memory["file_path"] = file_path
                
                # Apply hook filtering if specified
                if hooks and "hooks" in memory:
                    # FIXED: Normalize hooks for case-insensitive comparison
                    memory_hooks = [h.lower() for h in memory["hooks"] if isinstance(h, str)]
                    normalized_hooks = [h.lower() for h in hooks if isinstance(h, str)]
                    
                    if not any(h in memory_hooks for h in normalized_hooks):
                        continue
                
                # Apply date filtering if specified
                if date_filter and "timestamp" in memory:
                    if not self._match_date_filter(memory["timestamp"], date_filter):
                        continue
                
                memories.append(memory)
            except Exception as e:
                logger.error(f"Error processing memory file {file_path}: {e}")
                continue
        
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit the number of memories if specified
        if max_count is not None:
            memories = memories[:max_count]
        
        logger.debug(f"Retrieved {len(memories)} episodic memories")
        return memories
    
    def get_non_episodic_memories(self, hooks=None, max_count=None, date_filter=None):
        """
        Retrieve non-episodic memories, optionally filtered by hooks or date.
        
        Args:
            hooks (list, optional): List of hooks to filter by. Defaults to None.
            max_count (int, optional): Maximum number of memories to retrieve. Defaults to None.
            date_filter (str, optional): Date string to filter by. Defaults to None.
            
        Returns:
            list: A list of non-episodic memories.
        """
        memory_files = list_files_in_directory(self.non_episodic_dir, ".json")
        memories = []
        
        # FIXED: Better error handling for file loading
        for file_path in memory_files:
            try:
                memory = load_from_json_file(file_path)
                if memory is None:
                    logger.warning(f"Failed to load memory from {file_path}")
                    continue
                
                # Add the file path for reference
                memory["file_path"] = file_path
                
                # Apply hook filtering if specified
                if hooks and "hooks" in memory:
                    # FIXED: Normalize hooks for case-insensitive comparison
                    memory_hooks = [h.lower() for h in memory["hooks"] if isinstance(h, str)]
                    normalized_hooks = [h.lower() for h in hooks if isinstance(h, str)]
                    
                    if not any(h in memory_hooks for h in normalized_hooks):
                        continue
                
                # Apply date filtering if specified
                if date_filter and "timestamp" in memory:
                    if not self._match_date_filter(memory["timestamp"], date_filter):
                        continue
                
                memories.append(memory)
            except Exception as e:
                logger.error(f"Error processing memory file {file_path}: {e}")
                continue
        
        # Limit the number of memories if specified
        if max_count is not None:
            memories = memories[:max_count]
        
        logger.debug(f"Retrieved {len(memories)} non-episodic memories")
        return memories
    
    def _match_date_filter(self, timestamp, date_filter):
        """
        Check if a timestamp matches a date filter.
        
        Args:
            timestamp (str): The ISO format timestamp.
            date_filter (str): The date filter string.
            
        Returns:
            bool: True if the timestamp matches the filter, False otherwise.
        """
        # FIXED: Enhanced date filtering with better patterns
        try:
            # Convert timestamp to datetime
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp)
            else:
                return False
            
            # Handle common date formats
            date_filter = date_filter.lower()
            
            # Handle relative dates
            if date_filter == "today":
                today = datetime.now().date()
                return dt.date() == today
            elif date_filter == "yesterday":
                yesterday = (datetime.now() - timedelta(days=1)).date()
                return dt.date() == yesterday
            elif date_filter == "this week":
                today = datetime.now().date()
                start_of_week = today - timedelta(days=today.weekday())
                return start_of_week <= dt.date() <= today
            elif date_filter == "last week":
                today = datetime.now().date()
                end_of_last_week = today - timedelta(days=today.weekday() + 1)
                start_of_last_week = end_of_last_week - timedelta(days=6)
                return start_of_last_week <= dt.date() <= end_of_last_week
            
            # Handle specific dates (assuming YYYY-MM-DD format)
            if re.match(r'\d{4}-\d{2}-\d{2}', date_filter):
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                return dt.date() == filter_date
            
            # Handle month and year formats
            month_year_match = re.match(r'(\w+) (\d{4})', date_filter)
            if month_year_match:
                month_name, year = month_year_match.groups()
                months = {
                    "january": 1, "february": 2, "march": 3, "april": 4,
                    "may": 5, "june": 6, "july": 7, "august": 8,
                    "september": 9, "october": 10, "november": 11, "december": 12,
                    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, 
                    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, 
                    "nov": 11, "dec": 12
                }
                
                if month_name in months and year.isdigit():
                    return dt.month == months[month_name] and dt.year == int(year)
            
            # If nothing matched, check if the date filter appears in the formatted date
            formatted_date = dt.strftime("%B %d, %Y").lower()  # e.g., "april 13, 2025"
            alternative_format = dt.strftime("%d %B %Y").lower()  # e.g., "13 april 2025"
            iso_format = dt.strftime("%Y-%m-%d").lower()  # e.g., "2025-04-13"
            
            return (date_filter in formatted_date or 
                    date_filter in alternative_format or 
                    date_filter in iso_format)
            
        except Exception as e:
            logger.error(f"Error matching date filter {date_filter} with timestamp {timestamp}: {e}")
            return False
    
    def get_all_hooks(self):
        """
        Get all unique hooks from all memories.
        
        Returns:
            list: A list of unique hooks.
        """
        episodic_memories = self.get_episodic_memories()
        non_episodic_memories = self.get_non_episodic_memories()
        
        # Collect all hooks
        all_hooks = []
        for memory in episodic_memories + non_episodic_memories:
            if "hooks" in memory:
                all_hooks.extend(memory["hooks"])
        
        # Return unique hooks
        unique_hooks = list(set(all_hooks))
        logger.debug(f"Retrieved {len(unique_hooks)} unique hooks")
        return unique_hooks
    
    def delete_memory(self, file_path):
        """
        Delete a memory file.
        
        Args:
            file_path (str): The path to the memory file.
            
        Returns:
            bool: True if the memory was deleted successfully, False otherwise.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted memory: {file_path}")
                return True
            else:
                logger.warning(f"Memory file does not exist: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting memory {file_path}: {e}")
            return False
    
    def _prune_episodic_memories(self):
        """
        Prune old episodic memories based on retention policy.
        """
        memory_files = list_files_in_directory(self.episodic_dir, ".json")
        
        # If we're under the limit, no need to prune
        if len(memory_files) <= config.MAX_EPISODIC_MEMORIES:
            return
        
        memories = []
        for file_path in memory_files:
            memory = load_from_json_file(file_path)
            if memory is None:
                continue
            
            # Add the file path for reference
            memory["file_path"] = file_path
            
            # Calculate the age of the memory in days
            if "timestamp" in memory:
                days_old = get_days_since_timestamp(memory["timestamp"])
                memory["days_old"] = days_old
            else:
                memory["days_old"] = float('inf')  # Very old if no timestamp
            
            memories.append(memory)
        
        # Sort by age (oldest first)
        memories.sort(key=lambda x: x.get("days_old", float('inf')), reverse=True)
        
        # Delete memories that are too old or exceed the maximum count
        for memory in memories:
            # Delete if too old
            if memory.get("days_old", 0) > config.MEMORY_RETENTION_DAYS:
                self.delete_memory(memory["file_path"])
            # Delete if we still have too many memories
            elif len(memories) > config.MAX_EPISODIC_MEMORIES:
                self.delete_memory(memory["file_path"])
                memories.remove(memory)
            else:
                # We've pruned enough
                break
    
    def _prune_non_episodic_memories(self):
        """
        Prune non-episodic memories if we exceed the maximum count.
        We keep the ones with the most hooks (assumed to be more useful).
        """
        memory_files = list_files_in_directory(self.non_episodic_dir, ".json")
        
        # If we're under the limit, no need to prune
        if len(memory_files) <= config.MAX_NON_EPISODIC_MEMORIES:
            return
        
        memories = []
        for file_path in memory_files:
            memory = load_from_json_file(file_path)
            if memory is None:
                continue
            
            # Add the file path for reference
            memory["file_path"] = file_path
            
            # Count the number of hooks
            hook_count = len(memory.get("hooks", []))
            memory["hook_count"] = hook_count
            
            memories.append(memory)
        
        # Sort by hook count (fewest first)
        memories.sort(key=lambda x: x.get("hook_count", 0))
        
        # Delete memories until we're under the limit
        excess_count = len(memories) - config.MAX_NON_EPISODIC_MEMORIES
        for i in range(excess_count):
            if i < len(memories):
                self.delete_memory(memories[i]["file_path"])