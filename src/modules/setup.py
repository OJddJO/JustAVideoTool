import os, sys, glob

print("--- Registering DLL Paths ---")
search_pattern = os.path.join(sys.prefix, "**", "site-packages")
matches = glob.glob(search_pattern, recursive=True)

if matches:
    site_packages = matches[0]
    print(f"Discovered site-packages at: {site_packages}")
else:
    print("Could not locate site-packages using this pattern layout.")

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
print("\n")
