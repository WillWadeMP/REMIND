"""
Utility module for creating an Anthropic client regardless of installed version.
"""
import logging
import os
import config

logger = logging.getLogger(__name__)

def create_claude_client():
    """
    Create an Anthropic client that works with the installed version.
    
    Returns:
        object: An Anthropic client object.
    """
    # Check that API key is set
    if not config.CLAUDE_API_KEY:
        logger.error("CLAUDE_API_KEY environment variable is not set")
        raise ValueError("CLAUDE_API_KEY environment variable is not set. Please set it before running the application.")
    
    # Import the anthropic module
    try:
        import anthropic
        logger.info(f"Found anthropic module version: {getattr(anthropic, '__version__', 'unknown')}")
    except ImportError:
        logger.error("anthropic module not found. Please install it with 'pip install anthropic'")
        raise ImportError("anthropic module not found. Please install it with 'pip install anthropic'")
    
    # Create a compatibility wrapper for the client
    class ClaudeClientWrapper:
        def __init__(self):
            self.api_key = config.CLAUDE_API_KEY
            self.model = config.CLAUDE_MODEL
            
            # Create the underlying client
            try:
                self._create_client()
            except Exception as e:
                logger.error(f"Failed to create Claude client: {e}")
                raise
        
        def _create_client(self):
            """Try different methods to create a client based on the installed SDK version."""
            try:
                # Modern SDK approach (anthropic>=0.5.0)
                try:
                    self._client = anthropic.Anthropic(api_key=self.api_key)
                    self._client_type = 'modern_anthropic'
                    logger.info("Created client with modern Anthropic SDK")
                    return
                except (TypeError, AttributeError) as e:
                    logger.debug(f"Could not create modern client: {e}")
                
                # Legacy approach (anthropic<0.5.0)
                try:
                    if hasattr(anthropic, 'Client'):
                        self._client = anthropic.Client(api_key=self.api_key)
                        self._client_type = 'legacy_client'
                        logger.info("Created client with legacy Anthropic SDK")
                        return
                except (TypeError, AttributeError) as e:
                    logger.debug(f"Could not create legacy client: {e}")
                
                # Last resort - message API implementation using requests
                logger.info("Using custom implementation via requests")
                self._client_type = 'custom_client'
                
            except Exception as e:
                logger.error(f"Failed to create any type of Claude client: {e}")
                raise
        
        def messages_create(self, model=None, messages=None, system=None, max_tokens=1000, temperature=0.7, **kwargs):
            """
            Compatibility method for message creation.
            
            Args:
                model (str): The model to use.
                messages (list): The messages to process.
                system (str): The system prompt.
                max_tokens (int): The maximum number of tokens to generate.
                temperature (float): The temperature to use.
                **kwargs: Additional parameters.
                
            Returns:
                object: The API response.
            """
            if not model:
                model = self.model
                
            if not messages:
                messages = []
                
            if self._client_type == 'modern_anthropic':
                # Modern SDK (anthropic>=0.5.0)
                try:
                    # FIXED: Ensure system is a string, not a list
                    if system is not None and not isinstance(system, str):
                        logger.warning(f"System prompt not a string: {type(system)}. Converting to string.")
                        system = str(system)
                        
                    return self._client.messages.create(
                        model=model,
                        messages=messages,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )
                except Exception as e:
                    logger.error(f"Error in modern client messages call: {e}")
                    # Fallback to direct API call
                    logger.info("Falling back to direct API call")
            
            elif self._client_type == 'legacy_client':
                # Legacy client that might have completion but not messages
                if hasattr(self._client, 'messages') and hasattr(self._client.messages, 'create'):
                    try:
                        # FIXED: Ensure system is a string
                        if system is not None and not isinstance(system, str):
                            logger.warning(f"System prompt not a string: {type(system)}. Converting to string.")
                            system = str(system)
                            
                        return self._client.messages.create(
                            model=model,
                            messages=messages,
                            system=system,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            **kwargs
                        )
                    except Exception as e:
                        logger.error(f"Error in legacy client messages call: {e}")
                        # Fallback to conversion to completion API
                        logger.info("Falling back to completion API")
                
                # Convert messages format to completion format
                prompt = ""
                if system:
                    # FIXED: Format system message correctly
                    if isinstance(system, str):
                        prompt += f"{system}\n\n"
                    else:
                        prompt += f"{str(system)}\n\n"
                
                for msg in messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    prompt += f"{role}: {content}\n\n"
                
                prompt += "assistant: "
                
                try:
                    completion_response = self._client.completion(
                        prompt=prompt,
                        model=model,
                        max_tokens_to_sample=max_tokens,
                        temperature=temperature
                    )
                    
                    # Create a response object that mimics the messages API
                    class MessageResponse:
                        def __init__(self, text):
                            self.content = [{"type": "text", "text": text}]
                    
                    return MessageResponse(completion_response.completion)
                except Exception as e:
                    logger.error(f"Error in completion fallback: {e}")
                    # Fallback to direct API call
                    logger.info("Falling back to direct API call")
            
            # Custom direct API implementation as a last resort
            import requests
            import json
            
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # FIXED: Ensure data structure is correct for the API
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            # FIXED: Ensure system is a string, not a list
            if system is not None:
                if isinstance(system, str):
                    data["system"] = system
                else:
                    data["system"] = str(system)
            
            try:
                logger.debug(f"Making direct API call with data: {json.dumps(data)[:500]}...")
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                
                # Create a response object similar to what the client would return
                class MessageResponse:
                    def __init__(self, content):
                        self.content = content
                
                # Extract the content from the response
                content = result.get("content", [])
                return MessageResponse(content)
                
            except Exception as e:
                logger.error(f"Error in direct API call: {e}")
                
                # FIXED: Better error handling with context
                logger.error(f"API Response status: {getattr(response, 'status_code', 'Unknown')}")
                logger.error(f"API Response text: {getattr(response, 'text', 'Unknown')[:500]}")
                
                # Return a default response object if all else fails
                class MessageResponse:
                    def __init__(self):
                        self.content = [{"type": "text", "text": "I'm sorry, I couldn't process your request due to an API error."}]
                
                return MessageResponse()
    
    # Create and return the client wrapper
    try:
        client = ClaudeClientWrapper()
        logger.info("Successfully created Claude client wrapper")
        return client
    except Exception as e:
        logger.error(f"Failed to create Claude client wrapper: {e}")
        raise