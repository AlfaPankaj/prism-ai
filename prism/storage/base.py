from abc import ABC, abstractmethod
from typing import Dict, Optional


class ProfileStoreBase(ABC):
    @abstractmethod
    def get_profile(self, user_id: str, include_expired_override: bool = False) -> Optional[Dict[str, object]]:
        pass

    @abstractmethod
    def save_profile(
        self,
        user_id: str,
        uiv: Dict[str, str],
        confidence: float = 0.0,
        axis_confidence: Optional[Dict[str, float]] = None,
        source: str = "inferred",
    ):
        pass

    @abstractmethod
    def get_uiv(self, user_id: str, use_override: bool = True) -> Optional[Dict[str, str]]:
        pass

    @abstractmethod
    def delete_profile(self, user_id: str):
        pass
