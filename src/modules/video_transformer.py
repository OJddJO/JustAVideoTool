from abc import ABC, abstractmethod
import numpy as np

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
    def transform(self, frame: np.ndarray[np._AnyShape, np.uint8]) -> list[np.ndarray[np._AnyShape, np.uint8]]:
        """
        Accepts an interleaved RGB image array of shape (H, W, 3) with range [0, 255].
        Returns a list of processed interleaved RGB array of shape (New_H, New_W, 3).
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
