from pathlib import Path

import cv2
import numpy as np
from skimage.filters import threshold_otsu

from src.scoring.scoring_method import ScoringMethod

try:
    from typing import Optional, override
except ImportError:
    # for Python 3.9
    from typing_extensions import Optional, override


class PixelCounting(ScoringMethod):
    score_name = "pixel_counting_gvi"

    @override
    def get_score(self, image_path: Path) -> Optional[float]:
        """
        Calculate the Pixel-Counted Green View Index (GVI) for a given image file.

        Args:
            image_path (str): Path to the image file.

        Returns:
            float: The Green View Index (GVI) score for the given image.
        """

        # Load the image
        original_image = cv2.imread(str(image_path))
        # Convert to RGB color space
        rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

        # Calculate ExG (Excess Green)
        r, g, b = cv2.split(rgb_image.astype(np.float32) / 255)
        exg = 2 * g - r - b

        # Apply Otsu's thresholding on ExG
        threshold = threshold_otsu(exg)
        green_pixels = (exg > threshold).sum()
        total_pixels = original_image.shape[0] * original_image.shape[1]

        # Calculate the Green View Index (GVI)
        gvi_score = (green_pixels / total_pixels) * 100

        return gvi_score
