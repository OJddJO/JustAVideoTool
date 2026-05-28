import os
import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as F
import gc

from modules.video_transformer import VideoTransformer

class RealCUGAN(VideoTransformer):
    def __init__(self, onnx_model_path="models/cugan/pro-conservative-up2x.onnx", cache_dir="cache", tile_width=620, tile_height=360, tile_pad=32, scale=2):
        self.onnx_model_path = onnx_model_path
        self.cache_dir = cache_dir
        self.session = None

        # Tiling parameters
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tile_pad = tile_pad
        self.scale = scale

    def init_engine(self):
        if not os.path.exists(self.onnx_model_path):
            raise FileNotFoundError(f"Model missing: {self.onnx_model_path}")

        temp_session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
        self.input_name = temp_session.get_inputs()[0].name
        self.output_name = temp_session.get_outputs()[0].name

        dim_w = self.tile_width + (2 * self.tile_pad)
        dim_h = self.tile_height + (2 * self.tile_pad)
        shape_str = f"{self.input_name}:1x3x{dim_h}x{dim_w}"

        cache = os.path.join(self.cache_dir, "CUGAN", f"{dim_w}x{dim_h}")
        os.makedirs(cache)
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
        print("⏳ Initializing RealCUGAN... (Compilation may take time if using TensorRT)")
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

        print("✅ RealCUGAN ready!")

    def get_info(self):
        return (self.scale, self.scale, 1)

    def transform(self, frame: np.ndarray) -> list[np.ndarray]:
        if not self.session:
            self.init_engine()

        H, W, C = frame.shape

        # 1. Move the raw frame to the GPU immediately
        frame_t = torch.from_numpy(frame).to('cuda')

        # 2. Create an empty blank canvas for the upscaled output on the GPU
        out_frame_t = torch.zeros((H * self.scale, W * self.scale, C), dtype=torch.uint8, device='cuda')

        # Loop through the grid using respective height and width
        for y in range(0, H, self.tile_height):
            for x in range(0, W, self.tile_width):
                # Determine boundaries for this rectangular tile
                y_end = min(y + self.tile_height, H)
                x_end = min(x + self.tile_width, W)

                # Expand extraction bounds to grab REAL surrounding pixels for context
                y_ext_start = max(0, y - self.tile_pad)
                y_ext_end = min(H, y_end + self.tile_pad)
                x_ext_start = max(0, x - self.tile_pad)
                x_ext_end = min(W, x_end + self.tile_pad)

                # Extract the expanded patch natively on GPU
                patch = frame_t[y_ext_start:y_ext_end, x_ext_start:x_ext_end, :]

                # Format layout converting: (H, W, C) -> (C, H, W)
                patch_chw = patch.permute(2, 0, 1)

                # Calculate how much synthetic padding is still missing
                # (due to hitting the very edge of the video frame, or dead space on the right/bottom)
                pad_top = self.tile_pad - (y - y_ext_start)
                pad_left = self.tile_pad - (x - x_ext_start)

                target_h = self.tile_height + (2 * self.tile_pad)
                target_w = self.tile_width + (2 * self.tile_pad)

                pad_bot = target_h - (patch_chw.shape[1] + pad_top)
                pad_right = target_w - (patch_chw.shape[2] + pad_left)

                # Fill in the missing boundary/dead space with replication safely
                padded_patch = F.pad(patch_chw, (pad_left, pad_right, pad_top, pad_bot), mode='replicate')

                # Normalize and add batch dimension -> (1, C, H, W)
                input_tensor = (padded_patch.unsqueeze(0).float() / 255.0)

                # Copy current tile into the pre-bound GPU memory
                self.gpu_input.copy_(input_tensor, non_blocking=True)

                torch.cuda.synchronize()

                # Execute ONNX Runtime (Reads from VRAM, Writes to VRAM)
                self.session.run_with_iobinding(self.io_binding)

                # torch.cuda.synchronize()

                # Reconstruct output mapping natively on GPU from the bound output tensor
                out_patch = self.gpu_output.squeeze(0).permute(1, 2, 0)
                out_patch = torch.clamp(out_patch * 255.0, 0, 255).byte()

                # Crop out ONLY the valid region
                c_y_top = self.tile_pad * self.scale
                c_x_left = self.tile_pad * self.scale
                c_y_bot = c_y_top + (y_end - y) * self.scale
                c_x_right = c_x_left + (x_end - x) * self.scale

                valid_patch = out_patch[c_y_top:c_y_bot, c_x_left:c_x_right, :]

                # Stitch the successfully upscaled chunk back into the master GPU frame
                out_frame_t[y * self.scale : y_end * self.scale,
                            x * self.scale : x_end * self.scale, :] = valid_patch

        # 3. Transfer the final stitched frame back to the CPU/NumPy just once
        return [out_frame_t.cpu().numpy()]


    def release_memory(self):
        # 1. Delete the ONNX Runtime session to free the TensorRT VRAM context
        if self.session is not None:
            del self.session
            self.session = None

        # 2. Force Python to clean up deleted object references
        gc.collect()

        # 3. Force PyTorch to release its reserved VRAM back to the OS
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        print("🧹 RealCUGAN memory released.")
