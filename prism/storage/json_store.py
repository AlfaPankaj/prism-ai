import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from prism.storage.base import ProfileStoreBase

class JSONProfileStore(ProfileStoreBase):
    """
    A persistent JSON-based storage for User Intent Vectors.
    Mimics a document store like MongoDB but simplified for local use.
    """
    
    def __init__(self, base_path: str = "data/profiles"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _to_iso(self, value: datetime) -> str:
        return value.isoformat()

    def _from_iso(self, value: str) -> datetime:
        return datetime.fromisoformat(value)

    def _get_path(self, user_id: str) -> str:
        return os.path.join(self.base_path, f"{user_id}.json")

    def _list_profile_files(self):
        return [name for name in os.listdir(self.base_path) if name.endswith(".json")]

    def _read_raw_profile(self, user_id: str) -> Optional[Dict[str, object]]:
        file_path = self._get_path(user_id)
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_raw_profile(self, user_id: str, profile: Dict[str, object]):
        file_path = self._get_path(user_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)

    def _normalize_profile(self, user_id: str, profile: Optional[Dict[str, object]]) -> Dict[str, object]:
        base_uiv = {"format": "default", "complexity": "default", "style": "default"}
        if not profile:
            return {
                "user_id": user_id,
                "version": 2,
                "uiv": base_uiv,
                "metadata": {
                    "confidence": 0.0,
                    "axis_confidence": {"format": 0.0, "complexity": 0.0, "style": 0.0},
                    "source": "none",
                    "updated_at": self._to_iso(self._utc_now()),
                },
                "override": None,
            }

        # Backward-compatibility with old schema
        if "metadata" not in profile:
            return {
                "user_id": profile.get("user_id", user_id),
                "version": 2,
                "uiv": profile.get("uiv", base_uiv),
                "metadata": {
                    "confidence": 0.0,
                    "axis_confidence": {"format": 0.0, "complexity": 0.0, "style": 0.0},
                    "source": "inferred",
                    "updated_at": self._to_iso(self._utc_now()),
                },
                "override": None,
            }

        return profile

    def _active_override(self, profile: Dict[str, object]) -> Optional[Dict[str, object]]:
        override = profile.get("override")
        if not override:
            return None
        expires_at = override.get("expires_at")
        if not expires_at:
            return override
        if self._from_iso(expires_at) > self._utc_now():
            return override
        return None

    def get_profile(self, user_id: str, include_expired_override: bool = False) -> Optional[Dict[str, object]]:
        profile = self._read_raw_profile(user_id)
        if not profile:
            return None
        normalized = self._normalize_profile(user_id, profile)

        if not include_expired_override and normalized.get("override"):
            active = self._active_override(normalized)
            if not active:
                normalized["override"] = None
                self._write_raw_profile(user_id, normalized)
        return normalized

    def save_profile(
        self,
        user_id: str,
        uiv: Dict[str, str],
        confidence: float = 0.0,
        axis_confidence: Optional[Dict[str, float]] = None,
        source: str = "inferred",
    ):
        """Saves a profile with metadata for a specific user."""
        current = self.get_profile(user_id) or self._normalize_profile(user_id, None)
        current["uiv"] = uiv
        current["version"] = 2
        current["metadata"] = {
            "confidence": confidence,
            "axis_confidence": axis_confidence or {"format": 0.0, "complexity": 0.0, "style": 0.0},
            "source": source,
            "updated_at": self._to_iso(self._utc_now()),
        }
        self._write_raw_profile(user_id, current)

    def save_uiv(self, user_id: str, uiv: Dict[str, str]):
        """Backward-compatible save method for UIV-only writes."""
        self.save_profile(user_id, uiv=uiv, confidence=0.0, axis_confidence=None, source="inferred")

    def get_uiv(self, user_id: str, use_override: bool = True) -> Optional[Dict[str, str]]:
        """Retrieves the base or effective UIV for a specific user."""
        profile = self.get_profile(user_id)
        if not profile:
            return None

        if use_override:
            override = self._active_override(profile)
            if override and override.get("uiv"):
                return override["uiv"]
        return profile.get("uiv")

    def update_uiv(self, user_id: str, new_uiv: Dict[str, str]):
        """Merges new UIV insights with existing ones."""
        existing = self.get_profile(user_id) or self._normalize_profile(user_id, None)
        existing_uiv = existing.get("uiv", {})
        # Simple merge: new values override old ones
        updated = {**existing_uiv, **new_uiv}
        self.save_profile(user_id, updated, source="inferred")

    def edit_uiv(self, user_id: str, partial_uiv: Dict[str, str]):
        """Manual user edit: highest precedence for base profile."""
        existing = self.get_profile(user_id) or self._normalize_profile(user_id, None)
        updated = {**existing.get("uiv", {}), **partial_uiv}
        self.save_profile(user_id, updated, confidence=1.0, axis_confidence=None, source="manual")

    def reset_profile(self, user_id: str):
        """Deletes a user profile completely."""
        self.delete_profile(user_id)

    def delete_profile(self, user_id: str):
        """Hard delete for privacy/compliance workflows."""
        file_path = self._get_path(user_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    def set_temporary_override(self, user_id: str, override_uiv: Dict[str, str], ttl_seconds: int = 3600):
        """Creates a temporary override UIV that expires automatically."""
        profile = self.get_profile(user_id) or self._normalize_profile(user_id, None)
        expires_at = self._to_iso(self._utc_now() + timedelta(seconds=ttl_seconds))
        profile["override"] = {
            "uiv": override_uiv,
            "expires_at": expires_at,
            "source": "temporary_override",
        }
        self._write_raw_profile(user_id, profile)

    def clear_temporary_override(self, user_id: str):
        profile = self.get_profile(user_id, include_expired_override=True)
        if not profile:
            return
        profile["override"] = None
        self._write_raw_profile(user_id, profile)

    def export_profile(self, user_id: str) -> Optional[Dict[str, object]]:
        """Returns full profile payload for data portability requests."""
        return self.get_profile(user_id, include_expired_override=True)

    def apply_retention_policy(self, max_age_days: int) -> int:
        """
        Deletes profiles older than max_age_days based on metadata.updated_at.
        Returns number of deleted profiles.
        """
        deleted = 0
        cutoff = self._utc_now() - timedelta(days=max_age_days)

        for file_name in self._list_profile_files():
            user_id = file_name[:-5]
            profile = self.get_profile(user_id, include_expired_override=True)
            if not profile:
                continue
            updated_at = profile.get("metadata", {}).get("updated_at")
            if not updated_at:
                continue
            if self._from_iso(updated_at) < cutoff:
                self.delete_profile(user_id)
                deleted += 1
        return deleted
