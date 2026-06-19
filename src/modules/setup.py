import os, sys, glob

print("--- Registering DLL Paths ---")
search_pattern = os.path.join(sys.prefix, "**", "site-packages")
matches = glob.glob(search_pattern, recursive=True)

def app_target_is_set() -> bool:
    return os.environ.get("APP_TARGET_ARCH", False)

if matches:
    site_packages = matches[0]
    print(f"Discovered site-packages at: {site_packages}")

    # Check for TRT-RTX paths
    for trt_dir in ["tensorrt_rtx", "tensorrt_rtx_libs", "tensorrt_rtx_bindings"]:
        p = os.path.join(site_packages, trt_dir)
        if os.path.exists(p):
            print(f"Found TRT-RTX path: {p}")
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            if not app_target_is_set(): os.environ["APP_TARGET_ARCH"] = "TRT-RTX"

    # Check for TRT paths
    for trt_dir in ["tensorrt", "tensorrt_libs", "tensorrt_bindings"]:
        p = os.path.join(site_packages, trt_dir)
        if os.path.exists(p):
            print(f"Found TRT path: {p}")
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            if not app_target_is_set(): os.environ["APP_TARGET_ARCH"] = "TRT"

    # Check for CUDA/cuDNN paths
    nvidia_bins = glob.glob(os.path.join(site_packages, "nvidia", "*", "bin"))
    for p in nvidia_bins:
        if os.path.exists(p):
            print(f"Found NVIDIA path: {p}")
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            if not app_target_is_set(): os.environ["APP_TARGET_ARCH"] = "CUDA"
else:
    print("Could not locate site-packages using this pattern layout.")
print("\n")
