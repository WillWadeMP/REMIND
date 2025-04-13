"""
Claude API client for REMIND.

This module handles interactions with the Anthropic Claude API.
"""
import logging
import time
from typing import Dict, List, Optional, Any

import anthropic

import config

logger = logging.getLogger(__name__)

class ClaudeClient:
    """
    Handles interactions with the Anthropic Claude API.
    """
    
    def __init__(self):
        """Initialize the Claude client with the API key."""
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables or config.py")
        
        self.api_key = config.ANTHROPIC_API_KEY
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.default_model = config.CLAUDE_MODEL
        logger.info(f"ClaudeClient initialized with model {self.default_model}")
    
    def complete(self, prompt: str, model: Optional[str] = None, 
                temperature: float = 0.5, max_tokens: int = 1000) -> str:
        """
        Generate a completion from Claude.
        
        Args:
            prompt: The prompt text
            model: Optional model to use (defaults to configured model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            str: The generated text
        """
        # Use default model if none specified
        if not model:
            model = self.default_model
        
        try:
            # Use message API
            response = self.client.messages.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract text from response
            if hasattr(response, 'content') and response.content:
                return response.content[0].text
            else:
                logger.error("Empty response from Claude API")
                return ""
            
        except Exception as e:
            logger.error(f"Error in Claude API call: {e}")
            
            # Add exponential backoff for rate limits
            if "rate limit" in str(e).lower():
                retry_after = 2  # Start with 2 seconds
                max_retries = 3
                
                for attempt in range(max_retries):
                    logger.warning(f"Rate limited, retrying in {retry_after} seconds (attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    retry_after *= 2  # Exponential backoff
                    
                    try:
                        response = self.client.messages.create(
                            model=model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        if hasattr(response, 'content') and response.content:
                            return response.content[0].text
                    except Exception as retry_error:
                        logger.error(f"Retry {attempt+1} failed: {retry_error}")
            
            # Return empty string if all retries failed
            return ""
    
    def generate_response(self, query: str, memories: Dict[str, List[Dict[str, Any]]], 
                        conversation: Optional[Dict[str, Any]] = None,
                        model: Optional[str] = None) -> str:
        """
        Generate a response using memories as context.
        
        Args:
            query: The user query
            memories: Retrieved relevant memories
            conversation: Optional current conversation
            model: Optional model to use
            
        Returns:
            str: The generated response
        """
        # Use default model if none specified
        if not model:
            model = self.default_model
        
        # Prepare conversation context (last few messages)
        conversation_context = ""
        if conversation and conversation.get("messages"):
            # Get all messages EXCEPT the current query
            messages = conversation.get("messages", [])
            
            # For newly created conversations, we might only have the current query
            if len(messages) > 1:
                context_messages = messages[:-1]  # Exclude the current query
                
                # Format conversation context
                conversation_context = "Recent conversation history:\n"
                for msg in context_messages[-5:]:  # Last 5 previous messages
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    conversation_context += f"{role.capitalize()}: {content}\n"
        
        # Format memories by type
        memory_context = self._format_memories_for_context(memories)
        
        # Prepare the prompt
        prompt = f"""
        You are Claude, a helpful AI assistant with access to a memory system that stores past conversations and information.
        
        {memory_context}
        
        {conversation_context}
        
        Current user message: {query}
        
        Please provide a helpful response. If the memory context contains information relevant to the query, incorporate it naturally.
        If you're accessing information from memory, only mention this fact if it's directly relevant to do so.
        
        For example, if the user asks "What did we talk about last time?" or "Do you remember X?", then you should explicitly reference
        retrieving that information from memory. Otherwise, just use the memory naturally without drawing attention to the fact
        that you've remembered something.
        
        If this is a brand new conversation with no prior history, don't claim to "recall" or "remember" anything.
        
        Maintain a natural, helpful, and conversational tone.
        """
        
        # Generate response
        response = self.complete(
            prompt=prompt,
            model=model,
            temperature=0.7,  # Slightly higher temperature for more natural responses
            max_tokens=1000
        )
        
        return response
    
    def _format_memories_for_context(self, memories: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format retrieved memories for inclusion in prompt context.
        
        Args:
            memories: Dictionary with different types of memories
            
        Returns:
            str: Formatted context string
        """
        # Initialize context sections
        context_parts = []
        
        # Add conversation memory context if available (excluding current conversation)
        conversation_memories = memories.get("conversations", [])
        if conversation_memories:
            conversation_section = "Relevant past conversations:\n"
            for i, conv in enumerate(conversation_memories, 1):
                title = conv.get("title", "Untitled conversation")
                summary = conv.get("summary", "No summary available")
                conversation_section += f"{i}. {title}: {summary}\n"
                
                # Add a couple of key messages if available
                messages = conv.get("messages", [])
                if messages:
                    # Extract 2-3 representative messages to give more context
                    if len(messages) > 4:
                        # Get 3 evenly distributed messages from the conversation
                        indices = [len(messages) // 4, len(messages) // 2, 3 * len(messages) // 4]
                        sample_messages = [messages[i] for i in indices]
                    else:
                        sample_messages = messages
                    
                    conversation_section += "   Sample messages:\n"
                    for msg in sample_messages:
                        role = msg.get("role", "").capitalize()
                        content = msg.get("content", "")
                        # Truncate very long messages
                        if len(content) > 100:
                            content = content[:100] + "..."
                        conversation_section += f"   - {role}: {content}\n"
            
            context_parts.append(conversation_section)
        
        # Add episodic memory context if available
        episodic_memories = memories.get("episodic", [])
        if episodic_memories:
            episodic_section = "Relevant past interactions and events:\n"
            for i, mem in enumerate(episodic_memories, 1):
                content = mem.get("content", "No content available")
                episodic_section += f"{i}. {content}\n"
            
            context_parts.append(episodic_section)
        
        # Add non-episodic memory context if available
        non_episodic_memories = memories.get("non_episodic", [])
        if non_episodic_memories:
            non_episodic_section = "Relevant facts and information:\n"
            for i, mem in enumerate(non_episodic_memories, 1):
                content = mem.get("content", "No content available")
                non_episodic_section += f"{i}. {content}\n"
            
            context_parts.append(non_episodic_section)
        
        # Combine all context parts
        if context_parts:
            return "MEMORY CONTEXT:\n" + "\n".join(context_parts) + "\n"
        else:
            return "MEMORY CONTEXT: No relevant memories found.\n"