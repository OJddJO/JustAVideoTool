import av
import numpy as np
import torch

from modules.video_transformer import VideoTransformer

class ModularProcessingPipeline:
    def __init__(self):
        print(f"ℹ️ Initializing pipeline")
        self.transformers: list[VideoTransformer] = []
        self.width_factor = 1
        self.height_factor = 1
        self.framegen_factor = 1

    def add_stage(self, transformer: VideoTransformer):
        """Appends a new transformer block stage to the processing assembly line."""
        self.transformers.append(transformer)
        print(f"➕ Added {str(transformer)}")
        wf, hf, fgf = transformer.get_info()
        self.width_factor *= wf
        self.height_factor *= hf
        self.framegen_factor *= fgf
        return self

    def clean_memory(self):
        for transformer in self.transformers:
            transformer.release_memory()

    def stream_pipeline(self, input_path):
        try:
            container = av.open(input_path)
            video_stream = container.streams.video[0]
            video_stream.thread_type = "AUTO" # Enable multi-threaded decoding
        except Exception as e:
            raise ValueError(f"Unable to read input source video file stream targets: {e}")

        try:
            if self.transformers:
                for frame in container.decode(video_stream):
                    gpu_frames: list[torch.Tensor] = []
                    raw_frame = frame.to_ndarray(format='rgb24').astype(np.uint8)
                    gpu_frames.append(
                        torch
                        .from_numpy(raw_frame)
                        .to('cuda', non_blocking=True)
                        .permute(2, 0, 1).unsqueeze(0).float() / 255.0
                    )

                    for stage in self.transformers:
                        new_gpu_frames: list[torch.Tensor] = []
                        for gpu_frame in gpu_frames:
                            new_gpu_frames.extend(stage.transform(gpu_frame))
                        gpu_frames = new_gpu_frames

                    for gpu_frame in gpu_frames:
                        processed_frame = (gpu_frame.squeeze(0).permute(1, 2, 0) * 255.0).to(torch.uint8).contiguous().cpu().numpy()
                        yield processed_frame
            else:
                for frame in container.decode(video_stream):
                    raw_frame = frame.to_ndarray(format='rgb24').astype(np.uint8)
                    yield raw_frame
        finally:
            container.close()
