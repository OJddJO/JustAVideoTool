import torch
import torch.nn.functional as F

from modules.video_transformer import VideoTransformer

class Bilinear(VideoTransformer):
    def __init__(self, scale=0.5):
        self.scale = scale

    def get_info(self):
        return (self.scale, self.scale, 1)

    def transform(self, frame: torch.Tensor) -> torch.Tensor:
        return F.interpolate(frame, scale_factor=self.scale, mode='bilinear')

    def release_memory(self):
        return

    def __str__(self):
        return f"Bilinear(scale={self.scale})"
