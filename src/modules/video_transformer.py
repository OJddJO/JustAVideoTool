from abc import ABC, abstractmethod
import torch
from typing import Any

class VideoTransformer(ABC):
    @abstractmethod
    def get_info(self) -> tuple[int, int, int]:
        """
        Returns the information of the transformations done by the transformer.
        The tuple should be (width_factor, height_factor, framegen_factor) where
        width_factor is the width scaling factor
        height_factor is the height scaling factor
        framegen_factor is the factor of frame interpolation (frame generation)
        """
        pass

    @abstractmethod
    def transform(self, frame: torch.Tensor) -> list[torch.Tensor]:
        """
        Accepts an interleaved RGB image array of shape (1, 3, H, W) with range [0, 1].
        Returns a list of processed interleaved RGB array of shape (1, 3, New_H, New_W).
        """
        pass

    @abstractmethod
    def release_memory(self):
        """
        Frees up GPU VRAM and system memory used by the transformer models.
        Override this in subclasses to clear execution providers and CUDA caches.
        """
        pass

    @abstractmethod
    def __str__(self):
        """
        Returns a string representing the class with the parameters
        """
        pass
