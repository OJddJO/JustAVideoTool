# Just A Video Tool
[![Build Desktop Application](https://github.com/OJddJO/JustAVideoTool/actions/workflows/build_app.yml/badge.svg)](https://github.com/OJddJO/JustAVideoTool/actions/workflows/build_app.yml)

<div align="center">
  <img src="src/assets/icon.svg" width="200" alt="logo">
  <h3>Just A Video Tool</h3>
  <p>A simple tool for video manipulations, such as encoding, downscaling, upscaling, frame interpolation, ...</p>
</div>

<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/6c21354e-0b64-4074-9a5d-598d871f5266" />
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/7d4b8e8f-5e49-4fd3-a9ce-c6a8f086c8b4" />
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/c50a0f71-faf1-4f9f-bf35-fa29b638f999" />

## Goals
The main goal is to make an app for video alterations using AI with `.onnx` models (such as `RealCUGAN`, `RealESRGAN`, `Waifu2x`, `RIFE`, ...) and `Nvidia`'s acceleration technologies (CUDA/TensorRT) in a modular pipelining approach. It would also encode the final result using [ffmpeg](https://ffmpeg.org/) with [AV1](https://aomedia.org/specifications/av1/) codec.

- ✅ FINISHING THE APP
- ⬛ Non-Nvidia GPU support
- ⬛ Linux support (should be natif, but NixOS have some problems with dependencies)

## Requirements
- an NVidia gpu
- [ffmpeg](https://ffmpeg.org/) installed and added to the **PATH**

## Installation
- Go to the releases
- Download
- Extract with all the files in the **SAME** folder
- Enjoy

## Implemented Transformer
### Upscaling
- RealESRGAN
- RealCUGAN

### Interpolation
- RIFE

## Frameworks Used
- [flet](https://flet.dev/): a simple framework for building [Flutter](https://flutter.dev/) apps in Python
- [PyTorch](https://pytorch.org/): a widely used Python deep learning library
- [numpy](https://numpy.org/): a well-known Python library for multi-dimensionnal arrays/matrices computing
- [ONNX runtime](https://onnxruntime.ai/): a performance-focused AI engine for `.onnx` models
- [PyAV](https://github.com/PyAV-Org/PyAV): a fast Python FFmpeg binding

## AI Models Used
All AI models are from this beautiful [repository](https://github.com/AmusementClub/vs-mlrt). Thanks to AmusementClub !

## License
This project is under MIT License, see [LICENSE](/LICENSE) for more informations.
