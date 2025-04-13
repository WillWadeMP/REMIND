"""
Generates responses using Claude based on user input and relevant memories.
"""
import logging
import config
from src.claude_client import create_claude_client

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates responses using Claude based on user input and relevant memories."""
    
    def __init__(self):
        """Initialize the ResponseGenerator with Claude API client."""
        self.client = create_claude_client()
        # Use the full model for response generation for best quality
        self.model = config.CLAUDE_MODEL
        logger.info(f"ResponseGenerator initialized with model: {self.model}")
    
    def generate(self, user_input, relevant_memories):
        """
        Generate a response using Claude based on user input and relevant memories.
        
        Args:
            user_input (str): The user's input.
            relevant_memories (list): A list of relevant memories.
            
        Returns:
            str: The generated response.
        """
        logger.debug(f"Generating response for: {user_input}")
        
        # Format the memories for inclusion in the prompt
        memories_text = ""
        if relevant_memories:
            memories_text = "Here are some relevant memories that might help you provide a better response:\n\n"
            for i, memory in enumerate(relevant_memories):
                memory_content = memory.get("content", "")
                memory_summary = memory.get("summary", "")
                memory_timestamp = memory.get("timestamp", "")
                
                # Use summary if available, otherwise use content
                memory_text = memory_summary if memory_summary else memory_content
                
                memories_text += f"Memory {i+1} (from {memory_timestamp}):\n{memory_text}\n\n"
        
        # FIXED: Modified system prompt to prevent leaking of internal reasoning
        system_prompt = """
        You are an AI assistant with access to memories from past interactions. 
        Your task is to generate a helpful, coherent, and contextually appropriate response to the user's input.
        
        The memories provided to you are from past interactions or stored knowledge.
        Use these memories when they're relevant to provide more personalized and contextually aware responses.
        You don't need to explicitly mention that you're using memories unless it adds value to your response.
        
        IMPORTANT: DO NOT include your internal reasoning or thinking process in your response.
        DO NOT start your response with phrases like "I'll acknowledge..." or other meta-commentary.
        Just provide the direct response to the user as if you were in a natural conversation.
        
        Keep your answers natural and conversational, as if you remember the context.
        """
        
        try:
            # FIXED: Ensure user prompt is clear about expectations
            user_prompt = f"{memories_text}\n\nUser Input: {user_input}\n\nPlease provide a direct, helpful response without including your internal reasoning process."
            
            # Use the client wrapper
            response = self.client.messages_create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,  # Higher temperature for more creative responses
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract the text from the response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                if isinstance(response.content[0], dict) and 'text' in response.content[0]:
                    generated_response = response.content[0]['text'].strip()
                elif hasattr(response.content[0], 'text'):
                    generated_response = response.content[0].text.strip()
                else:
                    generated_response = str(response.content[0]).strip()
            else:
                generated_response = str(response).strip()
            
            # FIXED: Additional post-processing to remove any remaining internal reasoning
            # Look for patterns that might indicate internal reasoning
            patterns_to_check = [
                "I'll acknowledge", "Let me acknowledge", "I'll respond", 
                "I should", "I'm going to", "I will now", "Let me provide",
                "I'll give", "I need to", "I notice that", "I should respond",
                "My response should"
            ]
            
            # Check if response starts with any of these patterns
            for pattern in patterns_to_check:
                if generated_response.startswith(pattern):
                    # Try to find where the actual response begins (often in quotes)
                    quote_start = generated_response.find('"')
                    quote_end = generated_response.rfind('"')
                    
                    if quote_start != -1 and quote_end != -1 and quote_end > quote_start:
                        # Extract the content within quotes
                        direct_response = generated_response[quote_start+1:quote_end].strip()
                        generated_response = direct_response
                        break
                    
                    # Alternative: look for a clear sentence break
                    sentence_breaks = ['. ', '! ', '? ']
                    for break_char in sentence_breaks:
                        first_break = generated_response.find(break_char)
                        if first_break != -1:
                            # Skip the first sentence which might be internal reasoning
                            potential_direct = generated_response[first_break+2:].strip()
                            if len(potential_direct) > 20:  # Ensure we're not cutting too much
                                generated_response = potential_direct
                                break
            
            logger.debug(f"Generated response: {generated_response}")
            return generated_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Return a fallback response
            return "I'm having trouble generating a response right now. Let me try to help without accessing my memory. Could you please provide more details or ask your question in a different way?"