from typing import List, Dict, Any
from prism.extractor.uiv_builder import UIVBuilder

class PrismAdapter:
    """
    Model-agnostic adapter that injects PRISM preferences into LLM prompts.
    """
    
    def __init__(self):
        self.builder = UIVBuilder()

    def wrap_prompt(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        """
        Takes a raw prompt and history, extracts UIV, 
        and returns an optimized prompt with injected preferences.
        """
        if not history:
            return prompt
            
        uiv = self.builder.extract(history)
        instructions = self.builder.get_system_instructions(uiv)
        
        if not instructions:
            return prompt
            
        return f"[PRISM Preference Injection: {instructions}]\n\n{prompt}"

    def wrap_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Standardizes message list format (OpenAI/Anthropic style) 
        by injecting preferences into the latest turn or system prompt.
        """
        if len(messages) < 2:
            return messages
            
        history = messages[:-1]
        uiv = self.builder.extract(history)
        instructions = self.builder.get_system_instructions(uiv)
        
        if not instructions:
            return messages
            
        new_messages = [msg.copy() for msg in messages]
        
        if new_messages[0]["role"] == "system":
            new_messages[0]["content"] += f"\n\n{instructions}"
        else:
            new_messages.insert(0, {"role": "system", "content": instructions})
            
        return new_messages
