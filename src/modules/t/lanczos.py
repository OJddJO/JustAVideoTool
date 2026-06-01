import torch
import torchaudio.functional as TA_F

from modules.video_transformer import VideoTransformer

class Lanczos(VideoTransformer):
    def __init__(self, scale=0.5):
        self.scale = scale

    def get_info(self):
        return (self.scale, self.scale, 1)

    def transform(self, frame: torch.Tensor) -> torch.Tensor:
        _, c, h, w = frame.shape
        target_width = int(round(w * self.scale))
        target_height = int(round(h * self.scale))
        working_tensor = frame.squeeze(0).contiguous()

        resized_tensor = TA_F.resample(working_tensor, w, target_width)
        resized_tensor = resized_tensor.permute(0, 2, 1).contiguous()

        resized_tensor = TA_F.resample(resized_tensor, h, target_height)
        resized_tensor = resized_tensor.permute(0, 2, 1)

        return resized_tensor.unsqueeze(0)

    def release_memory(self):
        return

    def __str__(self):
        return f"Bilinear(scale={self.scale})"
