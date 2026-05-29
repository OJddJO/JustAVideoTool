import os
import numpy as np
import onnxruntime as ort
import torch
import torch.nn.functional as F
from math import exp
import gc

from modules.video_transformer import VideoTransformer

def gaussian(window_size, sigma):
    gauss = torch.Tensor([exp(-(x - window_size//2)**2/float(2*sigma**2)) for x in range(window_size)])
    return gauss/gauss.sum()

def create_window_3d(window_size, channel=1):
    _1D_window = gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t())
    _3D_window = _2D_window.unsqueeze(2) @ (_1D_window.t())
    window = _3D_window.expand(1, channel, window_size, window_size, window_size).contiguous().to('cuda')
    return window

def ssim_matlab(img1, img2, window_size=11, window=None, size_average=True, full=False, val_range=None):
    # Value range can be different from 255. Other common ranges are 1 (sigmoid) and 2 (tanh).
    if val_range is None:
        if torch.max(img1) > 128:
            max_val = 255
        else:
            max_val = 1

        if torch.min(img1) < -0.5:
            min_val = -1
        else:
            min_val = 0
        L = max_val - min_val
    else:
        L = val_range

    padd = 0
    (_, _, height, width) = img1.size()
    if window is None:
        real_size = min(window_size, height, width)
        window = create_window_3d(real_size, channel=1).to(img1.device)
        # Channel is set to 1 since we consider color images as volumetric images

    img1 = img1.unsqueeze(1)
    img2 = img2.unsqueeze(1)

    mu1 = F.conv3d(F.pad(img1, (5, 5, 5, 5, 5, 5), mode='replicate'), window, padding=padd, groups=1)
    mu2 = F.conv3d(F.pad(img2, (5, 5, 5, 5, 5, 5), mode='replicate'), window, padding=padd, groups=1)

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2

    sigma1_sq = F.conv3d(F.pad(img1 * img1, (5, 5, 5, 5, 5, 5), 'replicate'), window, padding=padd, groups=1) - mu1_sq
    sigma2_sq = F.conv3d(F.pad(img2 * img2, (5, 5, 5, 5, 5, 5), 'replicate'), window, padding=padd, groups=1) - mu2_sq
    sigma12 = F.conv3d(F.pad(img1 * img2, (5, 5, 5, 5, 5, 5), 'replicate'), window, padding=padd, groups=1) - mu1_mu2

    C1 = (0.01 * L) ** 2
    C2 = (0.03 * L) ** 2

    v1 = 2.0 * sigma12 + C2
    v2 = sigma1_sq + sigma2_sq + C2
    cs = torch.mean(v1 / v2)  # contrast sensitivity

    ssim_map = ((2 * mu1_mu2 + C1) * v1) / ((mu1_sq + mu2_sq + C1) * v2)

    if size_average:
        ret = ssim_map.mean()
    else:
        ret = ssim_map.mean(1).mean(1).mean(1)

    if full:
        return ret, cs
    return ret

class RIFE(VideoTransformer):
    def __init__(self, onnx_model_path="models/rife/rife_v4.10.onnx", cache_dir="cache"):
        super().__init__()
        self.onnx_model_path = onnx_model_path
        self.cache_dir = cache_dir
        self.session = None

        self.gpu_input = None
        self.gpu_output = None
        self.io_binding = None
        self.previous_frame = None

    def init_engine(self, width: int, height: int):
        if not os.path.exists(self.onnx_model_path):
            raise FileNotFoundError(f"Model missing: {self.onnx_model_path}")

        temp_session = ort.InferenceSession(self.onnx_model_path, providers=['CPUExecutionProvider'])
        self.input_name = temp_session.get_inputs()[0].name
        self.output_name = temp_session.get_outputs()[0].name

        shape_str = f"{self.input_name}:1x11x{height}x{width}"
        cache = os.path.join(self.cache_dir, "RIFE", os.path.basename(self.onnx_model_path), f"{width}x{height}")
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
        print("⏳ Initializing RIFE... (Compilation may take time if using TensorRT)")

        self.session = ort.InferenceSession(self.onnx_model_path, providers=providers)

        in_io_shape = (1, 11, height, width)
        out_io_shape = (1, 3, height, width)

        self.gpu_input = torch.empty(in_io_shape, dtype=torch.float32, device='cuda').contiguous()
        self.gpu_output = torch.empty(out_io_shape, dtype=torch.float32, device='cuda').contiguous()
        self.io_binding = self.session.io_binding()

        self.io_binding.bind_input(
            name=self.input_name, device_type='cuda', device_id=0,
            element_type=np.float32, shape=in_io_shape, buffer_ptr=self.gpu_input.data_ptr()
        )
        self.io_binding.bind_output(
            name=self.output_name, device_type='cuda', device_id=0,
            element_type=np.float32, shape=out_io_shape, buffer_ptr=self.gpu_output.data_ptr()
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

        self.timestep = torch.full((1, 1, height, width), 0.5, dtype=torch.float32, device='cuda')

        x_indices = np.arange(width, dtype=np.float32)
        y_indices = np.arange(height, dtype=np.float32)
        gx, gy = np.meshgrid(x_indices, y_indices)

        gx = 2.0 * gx / (width - 1) - 1.0
        gy = 2.0 * gy / (height - 1) - 1.0

        self.grid_x = torch.from_numpy(gx).cuda().unsqueeze(0).unsqueeze(0)
        self.grid_y = torch.from_numpy(gy).cuda().unsqueeze(0).unsqueeze(0)

        mx = np.full((height, width), 2.0 / (width - 1), dtype=np.float32)
        my = np.full((height, width), 2.0 / (height - 1), dtype=np.float32)

        self.mult_x = torch.from_numpy(mx).cuda().unsqueeze(0).unsqueeze(0)
        self.mult_y = torch.from_numpy(my).cuda().unsqueeze(0).unsqueeze(0)

        print("✅ RIFE ready!")

    def get_info(self):
        return (1, 1, 2)

    def transform(self, current_frame: np.ndarray) -> list[np.ndarray]:
        h, w, _ = current_frame.shape

        padded_height = ((h - 1) // 128 + 1) * 128
        padded_width = ((w - 1) // 128 + 1) * 128
        padding = (0, padded_width - w, 0, padded_height - h)
        if not self.session:
            self.init_engine(padded_width, padded_height)

        cur_frame_t = torch.from_numpy(current_frame).to('cuda').permute(2, 0, 1).unsqueeze(0).float() / 255.0

        # First frame, can't generate frame from nothing
        if self.previous_frame is None:
            self.previous_frame = cur_frame_t
            return [current_frame]

        ssim_prev_frame = F.interpolate(self.previous_frame, (32, 32), mode="bilinear", align_corners=False)
        ssim_cur_frame = F.interpolate(cur_frame_t, (32, 32), mode="bilinear", align_corners=False)
        ssim = ssim_matlab(ssim_prev_frame[:, :3], ssim_cur_frame[:, :3])

        if ssim < 0.05 or ssim > 0.996:
            self.previous_frame = cur_frame_t
            return [current_frame.copy(), current_frame]

        prev_frame_t_pad = F.pad(self.previous_frame, padding, mode="replicate")
        cur_frame_t_pad = F.pad(cur_frame_t, padding, mode="replicate")
        bundled = torch.cat((prev_frame_t_pad, cur_frame_t_pad, self.timestep, self.grid_x, self.grid_y, self.mult_x, self.mult_y), 1).contiguous()

        self.gpu_input.copy_(bundled, non_blocking=True)

        torch.cuda.synchronize()
        self.session.run_with_iobinding(self.io_binding)
        # torch.cuda.synchronize()

        output_tensor = self.gpu_output
        final_frame_tensor = output_tensor[:, :, :h, :w]
        final_frame_np = (final_frame_tensor.squeeze(0).permute(1, 2, 0).clamp(0, 1) * 255).byte().cpu().numpy()
        self.previous_frame = cur_frame_t

        return [final_frame_np, current_frame]

    def release_memory(self):
        if self.session is not None:
            del self.session
            self.session = None
        self.previous_frame = None
        self.gpu_input = None
        self.gpu_out = None
        self.io_binding = None
        self.timestep_mask = None
        self.grid_x = None
        self.grid_y = None
        self.mult_x = None
        self.mult_y = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        print("🧹 RIFE memory released.")

    def __str__(self):
        return f"RIFE(onnx_model_path={self.onnx_model_path}, cache_dir={self.cache_dir})"
