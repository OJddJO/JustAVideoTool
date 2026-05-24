import os, sys, glob

site_packages = os.path.join(sys.prefix, "Lib", "site-packages")

print("--- Registering DLL Paths ---")
# Check for TRT paths
for trt_dir in ["tensorrt", "tensorrt_libs", "tensorrt_bindings"]:
    p = os.path.join(site_packages, trt_dir)
    if os.path.exists(p):
        print(f"Found TRT path: {p}")
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Check for CUDA/cuDNN paths
nvidia_bins = glob.glob(os.path.join(site_packages, "nvidia", "*", "bin"))
for p in nvidia_bins:
    if os.path.exists(p):
        print(f"Found NVIDIA path: {p}")
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
print("-----------------------------")


import asyncio
import av
import numpy as np
import time
from modules.modular_pipeline import ModularProcessingPipeline
from modules.realCUGAN import RealCUGAN_TRT_CUDA
from modules.realESRGAN import RealESRGAN_TRT_CUDA

async def run_test():
    pipeline = ModularProcessingPipeline()

    # 1. Instantiate the transformer class
    tr = RealCUGAN_TRT_CUDA(onnx_model_path="../models/cugan/pro-conservative-up2x.onnx", tile_width=960, tile_height=540, tile_pad=32)
    # tr = RealESRGAN_TRT_CUDA(onnx_model_path="../models/RealESRGANv2/RealESRGANv2-animevideo-xsx2.onnx", tile_width=310, tile_height=180)
    pipeline.add_stage(tr)

    # Note: Replace 'sample.mov' with an actual short video path
    input_video = "sample.mkv"
    print(f"Starting pipeline on {input_video}...")
    os.makedirs("testing", exist_ok=True)

    try:
        frame_count = 0

        # 2. Consume the asynchronous pipeline generator
        start = time.time_ns()
        async for frame_bytes, w, h in pipeline.stream_pipeline(input_video):
            frame_count += 1
            print(f"✅ Processed frame {frame_count} | New resolution: {w}x{h}")

            # 3. Convert bytes back to a numpy array (RGB format)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((h, w, 3))

            # 4. Use PyAV to save the RGB numpy array directly as an image
            av_frame = av.VideoFrame.from_ndarray(frame_array, format='rgb24')
            av_frame.to_image().save(f"testing/test_output_frame_{frame_count}.jpg")

            # Break after 1 frame so you don't process the whole video during a test
            if frame_count >= 1000:
                print("Test complete. Check the output image.")
                break
        end = time.time_ns()
        print(f"Took {round(end - start, 4)}")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")

    finally:
        await pipeline.clean_memory()

if __name__ == "__main__":
    asyncio.run(run_test())
    input("Press ENTER to continue")
