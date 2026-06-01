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


import av
import numpy as np
import time
from modules.modular_pipeline import ModularProcessingPipeline
from modules.t import *

def run_test():
    pipeline = ModularProcessingPipeline()

    # tr1 = RealCUGAN(onnx_model_path="../models/cugan/pro-conservative-up2x.onnx", tile_width=960, tile_height=540, tile_pad=32)
    # pipeline.add_stage(tr1)
    # tr2 = RIFE(onnx_model_path="../models/rife/rife_v4.10.onnx")
    # pipeline.add_stage(tr2)

    tr = InterArea()
    pipeline.add_stage(tr)

    # Note: Replace 'sample.mov' with an actual short video path
    input_video = "sample.mkv"
    print(f"Starting pipeline on {input_video}...")
    os.makedirs("testing", exist_ok=True)

    # try:
    frame_count = 0

    start = time.time_ns()
    for frame in pipeline.stream_pipeline(input_video):
        frame_count += 1
        print(f"✅ Processed frame {frame_count}")

        av_frame = av.VideoFrame.from_ndarray(frame, format='rgb24')
        av_frame.to_image().save(f"testing/test_output_frame_{frame_count}.jpg")

        if frame_count >= 100:
            print("Test complete. Check the output image.")
            break
    end = time.time_ns()
    print(f"Took {round(end - start, 4)}")

    # except Exception as e:
    #     print(f"❌ Pipeline failed: {e}")

    # finally:
    #     await pipeline.clean_memory()

if __name__ == "__main__":
    run_test()
    input("Press ENTER to continue")
