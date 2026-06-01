import os
import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as F
import gc

from modules.video_transformer import VideoTransformer

class RealESRGAN(VideoTransformer):
    def __init__(self, onnx_model_path="models/RealESRGANv2/RealESRGANv2-animevideo-xsx2.onnx", cache_dir="cache", tile_width=620, tile_height=360, tile_pad=32, scale=2):
        self.onnx_model_path = onnx_model_path
        self.cache_dir = cache_dir
        self.session = None

        # Tiling parameters
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tile_pad = tile_pad
        self.scale = scale

        self.gpu_input = None
        self.gpu_output = None
        self.io_binding = None

    def init_engine(self):
        print("Initializing RealESRGAN... (Compilation may take time if using TensorRT and will freeze the GUI)", flush=True)
        if not os.path.exists(self.onnx_model_path):
            raise FileNotFoundError(f"Model missing: {self.onnx_model_path}")

        temp_session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
        self.input_name = temp_session.get_inputs()[0].name
        self.output_name = temp_session.get_outputs()[0].name

        dim_w = self.tile_width + (2 * self.tile_pad)
        dim_h = self.tile_height + (2 * self.tile_pad)
        shape_str = f"{self.input_name}:1x3x{dim_h}x{dim_w}"

        cache = os.path.join(self.cache_dir, "ESRGAN", os.path.basename(self.onnx_model_path), f"{dim_w}x{dim_h}")
        os.makedirs(cache, exist_ok=True)
        providers = [
            ('TensorrtExecutionProvider', {
                'device_id': 0,
                'trt_max_workspace_size': 4294967296,
                'trt_fp16_enable': True,
                'trt_engine_cache_enable': True,
                'trt_engine_cache_path': cache,
                'trt_profile_min_shapes': shape_str,
                'trt_profile_opt_shapes': shape_str,
                'trt_profile_max_shapes': shape_str,
            }),
            ('CUDAExecutionProvider', {'device_id': 0}),
        ]
        self.session = ort.InferenceSession(self.onnx_model_path, providers=providers)

        io_in_shape = (1, 3, dim_h, dim_w)
        io_out_shape = (1, 3, dim_h * self.scale, dim_w * self.scale)

        self.gpu_input = torch.empty(io_in_shape, dtype=torch.float32, device='cuda').contiguous()
        self.gpu_output = torch.empty(io_out_shape, dtype=torch.float32, device='cuda').contiguous()

        # Build structural zero-copy IO-Binding pipeline object map
        self.io_binding = self.session.io_binding()

        self.io_binding.bind_input(
            name=self.input_name, device_type='cuda', device_id=0,
            element_type=np.float32, shape=io_in_shape, buffer_ptr=self.gpu_input.data_ptr()
        )
        self.io_binding.bind_output(
            name=self.output_name, device_type='cuda', device_id=0,
            element_type=np.float32, shape=io_out_shape, buffer_ptr=self.gpu_output.data_ptr()
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        print("RealESRGAN ready!")

    def get_info(self):
        return (self.scale, self.scale, 1)

    def transform(self, frame: torch.Tensor) -> list[torch.Tensor]:
        if not self.session:
            self.init_engine()

        _, c, h, w = frame.shape

        out_frame_t = torch.zeros((1, c, h * self.scale, w * self.scale), dtype=torch.float32, device='cuda')

        target_h = self.tile_height + (2 * self.tile_pad)
        target_w = self.tile_width + (2 * self.tile_pad)

        # Loop through the grid using respective height and width
        for y in range(0, h, self.tile_height):
            for x in range(0, w, self.tile_width):
                # Determine boundaries for this rectangular tile
                y_end = min(y + self.tile_height, h)
                x_end = min(x + self.tile_width, w)

                # Expand extraction bounds to grab REAL surrounding pixels for context
                y_ext_start = max(0, y - self.tile_pad)
                y_ext_end = min(h, y_end + self.tile_pad)
                x_ext_start = max(0, x - self.tile_pad)
                x_ext_end = min(w, x_end + self.tile_pad)

                # Extract the expanded patch natively on GPU
                patch = frame[:, :, y_ext_start:y_ext_end, x_ext_start:x_ext_end]

                # Calculate how much synthetic padding is still missing
                # (due to hitting the very edge of the video frame, or dead space on the right/bottom)
                pad_top = self.tile_pad - (y - y_ext_start)
                pad_left = self.tile_pad - (x - x_ext_start)

                pad_bot = target_h - (patch.shape[2] + pad_top)
                pad_right = target_w - (patch.shape[3] + pad_left)

                # Fill in the missing boundary/dead space with replication safely
                padded_patch = F.pad(patch, (pad_left, pad_right, pad_top, pad_bot), mode='replicate')

                # Copy current tile into the pre-bound GPU memory
                self.gpu_input.copy_(padded_patch)

                # Execute ONNX Runtime (Reads from VRAM, Writes to VRAM)
                torch.cuda.synchronize()
                self.session.run_with_iobinding(self.io_binding)

                # Crop out ONLY the valid region
                c_y_top = self.tile_pad * self.scale
                c_x_left = self.tile_pad * self.scale
                c_y_bot = c_y_top + (y_end - y) * self.scale
                c_x_right = c_x_left + (x_end - x) * self.scale

                valid_patch = self.gpu_output[:, :, c_y_top:c_y_bot, c_x_left:c_x_right]

                # Stitch the successfully upscaled chunk back into the master GPU frame
                out_frame_t[:, :, y * self.scale : y_end * self.scale,
                            x * self.scale : x_end * self.scale] = valid_patch.clamp(0, 1)

        return [out_frame_t]

    def release_memory(self):
        if self.session is not None:
            del self.session
            self.session = None

        self.gpu_input = None
        self.gpu_output = None
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        print("RealESRGAN memory released.")

    def __str__(self):
        return f"RealESRGAN(onnx_model_path={self.onnx_model_path}, cache_dir={self.cache_dir}, tile_width={self.tile_width}, tile_height={self.tile_height}, tile_pad={self.tile_pad}, scale={self.scale})"
