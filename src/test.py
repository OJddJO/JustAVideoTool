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
from modules.modular_pipeline import ModularProcessingPipeline
from modules.real_cugan import RealCUGANTransformer


async def run_test():
    pipeline = ModularProcessingPipeline()
    
    # 1. Instantiate the transformer class
    cugan = RealCUGANTransformer(onnx_model_path="../models/cugan/pro-conservative-up2x.onnx")
    pipeline.add_stage(cugan)

    # Note: Replace 'sample.mov' with an actual short video path
    input_video = "sample.mp4" 
    print(f"Starting pipeline on {input_video}...")
    os.makedirs("testing", exist_ok=True)

    try:
        frame_count = 0
        
        # 2. Consume the asynchronous pipeline generator
        async for frame_bytes, w, h in pipeline.stream_pipeline(input_video):
            frame_count += 1
            print(f"✅ Processed frame {frame_count} | New resolution: {w}x{h}")
            
            # 3. Convert bytes back to a numpy array (RGB format)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((h, w, 3))
            
            # 4. Use PyAV to save the RGB numpy array directly as an image
            av_frame = av.VideoFrame.from_ndarray(frame_array, format='rgb24')
            av_frame.to_image().save(f"testing/test_output_frame_{frame_count}.jpg")
            
            # Break after 1 frame so you don't process the whole video during a test
            if frame_count >= 100:
                print("Test complete. Check the output image.")
                break

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())