from pathlib import Path

from loguru import logger as log
from PIL import Image
import torch
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation

try:
    from typing import Optional, override
except ImportError:
    # for Python 3.9
    from typing_extensions import Optional, override

from src.scoring.scoring_method import ScoringMethod


class Segmentation(ScoringMethod):
    score_name = "segmentation_gvi"

    def __init__(self, crop: float) -> None:
        """
        Initializes processor and segmentation model
        """

        self.crop = crop
        # Load the pretrained AutoImageProcessor from
        # "facebook/mask2former-swin-large-cityscapes-semantic"
        self.processor = AutoImageProcessor.from_pretrained(
            "facebook/mask2former-swin-large-cityscapes-semantic"
        )
        # Set the device to GPU if available, otherwise use CPU
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # Load the pretrained Mask2FormerForUniversalSegmentation
        # "facebook/mask2former-swin-large-cityscapes-semantic"
        model = Mask2FormerForUniversalSegmentation.from_pretrained(
            "facebook/mask2former-swin-large-cityscapes-semantic"
        )
        # Move the self.model to the specified device (GPU or CPU)
        self.model = model.to(device)

    @override
    def get_score(self, image_path: Path) -> Optional[float]:
        """
        Gets the segmentation GVI score for an image
        Args:
            image_path: Path to the image file

        Returns: the index score as a float

        """
        segmented_images_path = Path(Path(__file__).parent.parent, "data/interim/segmentations")

        try:
            # Fetch and process the image
            # image = Image.open(requests.get(image_path, stream=True).raw)
            image = Image.open(image_path)
            # Get the size of the image
            width, height = image.size
            # Crop the bottom 20% of the image to remove the band
            # at the bottom of the panoramic image
            bottom_crop = int(height * self.crop)
            image = image.crop((0, 0, width, height - bottom_crop))
            # Apply the semantic segmentation to the image
            segmentation = self._segment_images(image)
            # Cut panoramic image in 4 equal parts
            # Crop the image and its segmentation based on
            # the previously found road centers
            images, segmentations = self._crop_panoramic_images(image, segmentation)
            # Calculate the Green View Index (GVI) for the cropped segmentations
            gvi, segment_scores = self._get_gvi(segmentations)
            return gvi
        except Exception as ex:
            log.error(ex)

    def _segment_images(self, image: Image):
        """
        Applies semantic segmentation to an image
        Args:
            image: to apply segmentation to

        Returns: the segmentation as a torch tensor

        """
        # Preprocess the image using the image self.processor
        inputs = self.processor(images=image, return_tensors="pt")
        # Perform a forward pass through the self.model to obtain the segmentation
        with torch.no_grad():
            # Check if a GPU is available
            if torch.cuda.is_available():
                # Move the inputs to the GPU
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                # Perform the forward pass through the self.model
                outputs = self.model(**inputs)
                # Post-process the semantic segmentation outputs
                # using the processor and move the results to CPU
                segmentation = self.processor.post_process_semantic_segmentation(
                    outputs, target_sizes=[image.size[::-1]]
                )[0].to("cpu")
            else:
                # Perform the forward pass through the self.model
                outputs = self.model(**inputs)
                # Post-process the semantic segmentation outputs using the processor
                segmentation = self.processor.post_process_semantic_segmentation(
                    outputs, target_sizes=[image.size[::-1]]
                )[0]
        return segmentation

    def _crop_panoramic_images(self, image: Image, segmentation: torch.Tensor):
        """
        Crops the panoramic image and its segmentation based on road centers
        Args:
            image: opened image
            segmentation: segmentation of the image

        Returns: list of cropped images and their segmentations

        """
        width, height = image.size
        w4 = int(width / 4)
        h4 = int(height / 4)
        hFor43 = int(w4 * 3 / 4)
        images = []
        segmentations = []
        # Crop the panoramic image based on road centers
        for w in range(4):
            x_begin = w * w4
            x_end = (w + 1) * w4
            cropped_image = image.crop((x_begin, h4, x_end, h4 + hFor43))
            cropped_segmentation = segmentation[h4 : h4 + hFor43, x_begin:x_end]
            images.append(cropped_image)
            segmentations.append(cropped_segmentation)
        return images, segmentations

    def _get_gvi(self, segmentations: list[torch.Tensor]):
        """
        Calculates the Segmentation GVI for a list of segmentations
        Args:
            segmentations:

        Returns: overall GVI and a list of segment scores

        """
        total_pixels = 0
        vegetation_pixels = 0
        segment_scores = []
        for segment in segmentations:
            # Calculate the total number of pixels in the segmentation
            total_pixels += segment.numel()
            # Filter the pixels that represent vegetation (label 8) and count them
            vegetation_pixels += (segment == 8).sum().item()

            curr_segment_score = (segment == 8).sum().item() / segment.numel()
            segment_scores.append(curr_segment_score)

        # Calculate the percentage of green pixels in the segmentation
        return (vegetation_pixels / total_pixels), segment_scores
