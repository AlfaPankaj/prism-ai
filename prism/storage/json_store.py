import json
import os
from typing import Dict, Optional

class JSONProfileStore:
    """
    A persistent JSON-based storage for User Intent Vectors.
    Mimics a document store like MongoDB but simplified for local use.
    """
    
    def __init__(self, base_path: str = "data/profiles"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _get_path(self, user_id: str) -> str:
        return os.path.join(self.base_path, f"{user_id}.json")

    def save_uiv(self, user_id: str, uiv: Dict[str, str]):
        """Saves a UIV for a specific user."""
        file_path = self._get_path(user_id)
        data = {
            "user_id": user_id,
            "uiv": uiv,
            "last_updated": os.path.getmtime(file_path) if os.path.exists(file_path) else None
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_uiv(self, user_id: str) -> Optional[Dict[str, str]]:
        """Retrieves a UIV for a specific user."""
        file_path = self._get_path(user_id)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get("uiv")

    def update_uiv(self, user_id: str, new_uiv: Dict[str, str]):
        """Merges new UIV insights with existing ones."""
        existing = self.get_uiv(user_id) or {}
        # Simple merge: new values override old ones
        updated = {**existing, **new_uiv}
        self.save_uiv(user_id, updated)
