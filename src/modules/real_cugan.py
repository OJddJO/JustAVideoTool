import os
import numpy as np
import onnxruntime as ort

from modules.video_transformer import VideoTransformer

class RealCUGANTransformer(VideoTransformer):
    def __init__(self, onnx_model_path="models/realcugan_pro_x2.onnx", cache_dir="trt_cache", tile_size=512, tile_pad=16, scale=2):
        if not (256 <= tile_size <= 768):
            raise ValueError(f"tile_size must be between 256 and 768. Received: {tile_size}")

        self.onnx_model_path = onnx_model_path
        self.cache_dir = cache_dir
        self.session = None

        # Tiling parameters
        self.tile_size = tile_size
        self.tile_pad = tile_pad
        self.scale = scale

    def init_engine(self):
        if not os.path.exists(self.onnx_model_path):
            raise FileNotFoundError(f"Model missing: {self.onnx_model_path}")

        temp_session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
        self.input_name = temp_session.get_inputs()[0].name
        self.output_name = temp_session.get_outputs()[0].name

        dim = self.tile_size + (2 * self.tile_pad)
        shape_str = f"{self.input_name}:1x3x{dim}x{dim}"

        providers = [
            ('TensorrtExecutionProvider', {
                'device_id': 0,
                'trt_max_workspace_size': 4294967296,
                'trt_fp16_enable': True,
                'trt_engine_cache_enable': True,
                'trt_engine_cache_path': self.cache_dir,
                'trt_profile_min_shapes': shape_str,
                'trt_profile_opt_shapes': shape_str,
                'trt_profile_max_shapes': shape_str,
            }),
            ('CUDAExecutionProvider', {'device_id': 0}),
            'CPUExecutionProvider'
        ]
        print("⏳ Initializing RealCUGAN... (Compilation may take time if using TensorRT)")
        self.session = ort.InferenceSession(self.onnx_model_path, providers=providers)
        print("✅ RealCUGAN ready!")
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def transform(self, frame: np.ndarray) -> np.ndarray:
        if not self.session:
            self.init_engine()

        H, W, C = frame.shape
        # Create an empty blank canvas for the upscaled output
        out_frame = np.zeros((H * self.scale, W * self.scale, C), dtype=np.uint8)

        # Loop through the grid
        for y in range(0, H, self.tile_size):
            for x in range(0, W, self.tile_size):
                
                # Determine boundaries for this tile
                y_end = min(y + self.tile_size, H)
                x_end = min(x + self.tile_size, W)
                patch = frame[y:y_end, x:x_end, :]

                # Define structural padding (overlap amount + filling out the edges)
                pad_top = self.tile_pad
                pad_left = self.tile_pad
                pad_bottom = self.tile_pad + (self.tile_size - (y_end - y))
                pad_right = self.tile_pad + (self.tile_size - (x_end - x))

                # Reflect padding creates fake bordering pixels so edge inferences look perfect
                padded_patch = np.pad(patch, ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)), mode='reflect')

                # Format layout converting: (H, W, C) -> (1, C, H, W) normalized
                input_tensor = np.transpose(padded_patch, (2, 0, 1))
                input_tensor = np.expand_dims(input_tensor, axis=0).astype(np.float32) / 255.0

                outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
                
                # Reconstruct output mapping
                out_patch = np.squeeze(outputs[0], axis=0)
                out_patch = np.transpose(out_patch, (1, 2, 0))
                out_patch = np.clip(out_patch * 255.0, 0, 255).astype(np.uint8)

                # Crop out ONLY the valid region (removes the protective padding entirely)
                c_y_top = pad_top * self.scale
                c_x_left = pad_left * self.scale
                c_y_bot = c_y_top + (y_end - y) * self.scale
                c_x_right = c_x_left + (x_end - x) * self.scale

                valid_patch = out_patch[c_y_top:c_y_bot, c_x_left:c_x_right, :]

                # Stitch the successfully upscaled chunk back into the master frame
                out_frame[y * self.scale : y_end * self.scale, 
                          x * self.scale : x_end * self.scale, :] = valid_patch

        return out_frame
