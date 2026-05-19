import asyncio
import av

from modules.video_transformer import VideoTransformer

class ModularProcessingPipeline:
    def __init__(self):
        self.transformers: list[VideoTransformer] = []

    def add_stage(self, transformer: VideoTransformer):
        """Appends a new transformer block stage to the processing assembly line."""
        self.transformers.append(transformer)
        return self

    async def stream_pipeline(self, input_path):
        try:
            container = av.open(input_path)
            video_stream = container.streams.video[0]
            video_stream.thread_type = "AUTO" # Enable multi-threaded decoding
        except Exception as e:
            raise ValueError(f"Unable to read input source video file stream targets: {e}")

        try:
            for frame in container.decode(video_stream):
                # PyAV extracts directly to a numpy array in RGB format mapping
                processed_frame = frame.to_ndarray(format='rgb24')

                # Route frame arrays sequentially along the chained processing sequence
                for stage in self.transformers:
                    # Offload compute bounds safely over to concurrent thread pools
                    processed_frame = stage.transform(processed_frame)

                # Extract spatial attributes dynamically (in case resolution changed)
                h, w, c = processed_frame.shape

                # Yield structural frame data alongside raw frame arrays
                yield processed_frame.tobytes(), w, h
                await asyncio.sleep(0)
        finally:
            container.close()