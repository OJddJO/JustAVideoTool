from abc import ABC, abstractmethod
import numpy as np

class VideoTransformer(ABC):
    @abstractmethod
    def transform(self, frame: np.ndarray) -> np.ndarray:
        """
        Accepts an interleaved RGB image array of shape (H, W, 3) with range [0, 255].
        Returns a processed interleaved RGB array of shape (New_H, New_W, 3).
        """
        pass

    @abstractmethod
    def release_memory(self):
        """
        Frees up GPU VRAM and system memory used by the transformer models.
        Override this in subclasses to clear execution providers and CUDA caches.
        """
        pass
