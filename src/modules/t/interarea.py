import cv2
import torch
from modules.video_transformer import VideoTransformer

class InterArea(VideoTransformer):
    def __init__(self, scale=0.5):
        self.scale = scale

    def get_info(self):
        return (self.scale, self.scale, 1)

    def transform(self, frame: torch.Tensor) -> torch.Tensor:
        _, _, h, w = frame.shape
        cpu_frame = (frame.squeeze(0).permute(1, 2, 0) * 255.0).to(torch.uint8).cpu().numpy()
        cpu_frame = cv2.resize(cpu_frame, (int(round(w * self.scale)), int(round(h * self.scale))), interpolation=cv2.INTER_AREA)
        return torch.from_numpy(cpu_frame).to('cuda', non_blocking=True).permute(2, 0, 1).unsqueeze(0).float() / 255.0

    def release_memory(self):
        return

    def __str__(self):
        return f"InterArea(scale={self.scale})"
