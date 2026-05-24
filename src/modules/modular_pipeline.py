import asyncio
import av
import numpy as np

from modules.video_transformer import VideoTransformer

class ModularProcessingPipeline:
    def __init__(self, batch_size: int = 32):
        self.transformers: list[VideoTransformer] = []
        self.batch_size = batch_size

    def add_stage(self, transformer: VideoTransformer):
        """Appends a new transformer block stage to the processing assembly line."""
        self.transformers.append(transformer)
        return self

    async def clean_memory(self):
        for transformer in self.transformers:
            transformer.release_memory()

    async def stream_pipeline(self, input_path):
        try:
            container = av.open(input_path)
            video_stream = container.streams.video[0]
            video_stream.thread_type = "AUTO" # Enable multi-threaded decoding
        except Exception as e:
            raise ValueError(f"Unable to read input source video file stream targets: {e}")

        try:
            batch: list[np.ndarray] = []
            for frame in container.decode(video_stream):

                # PyAV extracts directly to a numpy array in RGB format mapping
                raw_frame = frame.to_ndarray(format='rgb24')
                batch.append(raw_frame)

                if len(batch) == self.batch_size:
                    for stage in self.transformers:
                        for i in range(self.batch_size):
                            # Offload compute bounds safely over to concurrent thread pools
                            batch[i] = await asyncio.to_thread(stage.transform, batch[i])

                    # Unpack the batch and yield frames sequentially
                    for processed_frame in batch:
                        h, w, c = processed_frame.shape
                        yield processed_frame.tobytes(), w, h

                    batch.clear()

            # Process the remaining frames
            if batch:
                for stage in self.transformers:
                    for i in range(len(batch)):
                        batch[i] = await asyncio.to_thread(stage.transform, batch[i])

                for processed_frame in batch:
                    h, w, c = processed_frame.shape
                    yield processed_frame.tobytes(), w, h
        finally:
            container.close()
