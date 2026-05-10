from typing import List, Dict, Any
from prism.metrics.clarification import ClarificationDetector

class UIVBuilder:
    """
    Builds and maintains a User Intent Vector (UIV) from conversation history.
    The UIV captures stable preferences across turns.
    """
    
    DEFAULT_UIV = {
        "format": "default",       
        "complexity": "default",  
        "style": "default"        
    }

    def __init__(self):
        self.detector = ClarificationDetector()

    def extract(self, history: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Analyzes the full history to produce a final UIV for the current state.
        """
        uiv = self.DEFAULT_UIV.copy()
        clarifications = self.detector.detect_in_history(history)
        
        for clar in clarifications:
            content = clar["content"].lower()
            
            if "bullet" in content or "list" in content:
                uiv["format"] = "bullets"
            elif "paragraph" in content:
                uiv["format"] = "paragraph"
            
            if "simple" in content or "layman" in content or "beginner" in content:
                uiv["complexity"] = "simple"
            elif "detail" in content or "expert" in content or "advanced" in content:
                uiv["complexity"] = "detailed"
                
            if "short" in content or "brief" in content or "concise" in content:
                uiv["style"] = "concise"
            elif "long" in content or "elaborate" in content:
                uiv["style"] = "detailed"
                
        return uiv

    def get_system_instructions(self, uiv: Dict[str, str]) -> str:
        """Converts a UIV into a string of system instructions."""
        instructions = []
        
        if uiv["format"] == "bullets":
            instructions.append("Use bullet points for lists and key information.")
        elif uiv["format"] == "paragraph":
            instructions.append("Use full, descriptive paragraphs.")
            
        if uiv["complexity"] == "simple":
            instructions.append("Explain concepts simply, as if to a beginner.")
        elif uiv["complexity"] == "detailed":
            instructions.append("Provide advanced, expert-level technical details.")
            
        if uiv["style"] == "concise":
            instructions.append("Be as brief and concise as possible.")
        elif uiv["style"] == "detailed":
            instructions.append("Provide thorough and elaborate explanations.")
            
        if not instructions:
            return ""
            
        return "ADAPTED USER PREFERENCES: " + " ".join(instructions)
