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