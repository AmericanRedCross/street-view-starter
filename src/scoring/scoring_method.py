from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

try:
    from typing import Optional
except ImportError:
    # for Python 3.9
    from typing_extensions import Optional


class ScoringMethod(ABC):
    score_name = ""

    @abstractmethod
    def get_score(self, image_path: Path) -> Optional[float]:
        """
        Gets the index score for an image
        Args:
            image_path: Path to the image file

        Returns: the index score as a float

        """
        raise NotImplementedError


class ScoringSelector(str, Enum):
    pixel_counting = "PIXELS"
    segmentation = "SEGMENTATION"
