import flet as ft
from views.generic import GenericContainer, TextField, NumberInput

from modules.video_transformer import VideoTransformer
from modules.nvidia import *

__all__ = [
    "TransformerLayer",
    "RealESRGAN_Layer",
    "RealCUGAN_Layer",
    "RIFE_Layer"
]

@ft.control
class TransformerLayer(GenericContainer):
    """Prototype class for all transformer UI layers"""
    desc = ""

    def __init__(self, container: list["TransformerLayer"], title: list[ft.Control], default_onnx = "", content: list = [], advanced_settings: list = []):
        super().__init__()
        self.container = container
        self.file_picker = ft.FilePicker()
        self.onnx_model_path = TextField(label="ONNX path", expand=True, value=default_onnx)
        self.cache_dir = TextField(label="Cache path", expand=True, value="cache")
        self.content = ft.Row(
            [
                ft.ReorderableDragHandle(
                    ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.ON_SURFACE),
                    mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN
                ),
                ft.Column(
                    [
                        ft.Row(title + [
                            ft.Button("Remove", icon=ft.Icons.REMOVE, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300, on_click=self.remove)
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Model Path", size=16, weight=ft.FontWeight.BOLD),
                            self.onnx_model_path,
                            ft.Button("Select ONNX", icon=ft.Icons.FOLDER_OPEN_OUTLINED, on_click=self.select_onnx)
                        ], expand=True)
                    ]
                    + content
                    + ([
                        ft.Divider(),
                        ft.ExpansionTile(
                            title="Advanced Settings",
                            leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=18),
                            controls=ft.Column([
                                ft.Row([
                                    ft.Text("Cache directory", size=16, weight=ft.FontWeight.BOLD),
                                    self.cache_dir,
                                    ft.Button("Choose directory", icon=ft.Icons.FOLDER_OPEN_OUTLINED, on_click=self.choose_cache_dir)
                                ],expand=True)
                            ] + advanced_settings),
                            dense=True,
                            expanded=False,
                            shape=ft.RoundedRectangleBorder(radius=0),
                            collapsed_shape=ft.RoundedRectangleBorder(radius=0),
                            controls_padding=ft.Padding(top=10),
                        )
                    ]),
                    expand=True,
                    margin=5
                )
            ]
        )

    async def remove(self):
        self.container.remove(self)

    async def select_onnx(self, e: ft.Event[ft.Button]):
        file = await self.file_picker.pick_files(
            dialog_title="Select the .onnx model to use",
            initial_directory=".",
            allowed_extensions=["onnx"], allow_multiple=False
        )
        if file:
            self.onnx_model_path.value = file[0].path

    async def choose_cache_dir(self, e: ft.Event[ft.Button]):
        dir = await self.file_picker.get_directory_path("Choose the cache directory")
        if dir:
            self.cache_dir.value = dir

    async def build_transformer(self) -> VideoTransformer:
        raise NotImplementedError("Transformer Layer shouldn't be directly used")

@ft.control
class RealESRGAN_Layer(TransformerLayer):
    desc = """A transformer for upscaling frames using RealESRGAN AI
GAN (Generative Adversarial Network): An AI architecture where two neural networks compete against each other. One network generates realistic data from scratch, while the other tries to spot flaws, forcing the system to continuously improve until the generated results look completely authentic.
ESRGAN (Enhanced Super-Resolution GAN): Optimized for real-world photos and realistic textures. It is incredibly good at reconstructing fine details like human hair, fabric weave, tree bark, and rock surfaces, making it a favorite for remastering old video games and photography."""

    def __init__(self, container: list[TransformerLayer]):
        self.tile_width = NumberInput(value="620", label="Tile width", expand=True)
        self.tile_height = NumberInput(value="360", label="Tile height", expand=True)
        self.tile_pad = NumberInput(value="32", label="Tile padding", expand=True)
        self.scale_factor = NumberInput(value="2", label="Scale factor", expand=True)
        self.cache_dir = TextField(label="Cache path", expand=True, value="cache")
        super().__init__(
            container=container,
            title=[ft.Icon(ft.Icons.IMAGE_ASPECT_RATIO), ft.Text("RealESRGAN", size=20, weight=ft.FontWeight.BOLD, expand=True)],
            default_onnx="models/RealESRGANv2/RealESRGANv2-animevideo-xsx2.onnx",
            content=[
                ft.Divider(),
                ft.Row([
                    ft.Text("Tiling parameters", size=16, weight=ft.FontWeight.BOLD),
                    ft.Icon(
                        ft.Icons.HELP_OUTLINE,
                        size=18,
                        tooltip="Tiling helps reducing VRAM usage at the cost of speed.\nThe smaller the tile, the less VRAM will be used. Bigger tile padding can help avoid tearing.",
                    ),
                    self.tile_width,
                    self.tile_height,
                    self.tile_pad
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Text("Scale factor", size=16, weight=ft.FontWeight.BOLD),
                    ft.Icon(ft.Icons.HELP_OUTLINE, size=18, tooltip="Please choose the correct model if modifying the scale factor."),
                    self.scale_factor
                ], expand=True),
            ],
        )

    async def build_transformer(self):
        return RealESRGAN(
            onnx_model_path=self.onnx_model_path.value,
            cache_dir=self.cache_dir.value,
            tile_width=int(self.tile_width.value),
            tile_height=int(self.tile_height.value),
            tile_pad=int(self.tile_pad.value),
            scale=int(self.scale_factor.value)
        )

@ft.control
class RealCUGAN_Layer(TransformerLayer):
    desc = """A transformer for upscaling frames using RealCUGAN AI
GAN (Generative Adversarial Network): An AI architecture where two neural networks compete against each other. One network generates realistic data from scratch, while the other tries to spot flaws, forcing the system to continuously improve until the generated results look completely authentic.
CUGAN (Cascaded-U-Net GAN): Specifically optimized for Anime, Manga, and Cartoon art. It focuses on fixing the unique issues found in digital animation—like cleaning up jagged line art, removing compression noise, and preserving smooth color gradients without creating ugly artifacts."""

    def __init__(self, container: list[TransformerLayer]):
        self.tile_width = NumberInput(value="620", label="Tile width")
        self.tile_height = NumberInput(value="360", label="Tile height")
        self.tile_pad = NumberInput(value="32", label="Tile padding")
        self.scale_factor = NumberInput(value="2", label="Scale factor", expand=True)
        super().__init__(
            container,
            title = [ft.Icon(ft.Icons.IMAGE_ASPECT_RATIO), ft.Text("RealESRGAN", size=20, weight=ft.FontWeight.BOLD, expand=True)],
            default_onnx="models/cugan/pro-conservative-up2x.onnx",
            content=[
                ft.Divider(),
                ft.Row([
                    ft.Text("Tiling parameters", size=16, weight=ft.FontWeight.BOLD),
                    ft.Icon(
                        ft.Icons.HELP_OUTLINE,
                        size=18,
                        tooltip="Tiling helps reducing VRAM usage at the cost of speed.\nThe smaller the tile, the less VRAM will be used. Bigger tile padding can help avoid tearing.",
                    ),
                    self.tile_width,
                    self.tile_height,
                    self.tile_pad
                ]),
                ft.Divider(),
                ft.Row([
                    ft.Text("Scale factor", size=16, weight=ft.FontWeight.BOLD),
                    ft.Icon(ft.Icons.HELP_OUTLINE, size=18, tooltip="Please choose the correct model if modifying the scale factor."),
                    self.scale_factor
                ], expand=True)
            ]
        )

    async def build_transformer(self):
        return RealCUGAN(
            onnx_model_path=self.onnx_model_path.value,
            cache_dir=self.cache_dir.value,
            tile_width=int(self.tile_width.value),
            tile_height=int(self.tile_height.value),
            tile_pad=int(self.tile_pad.value),
            scale=int(self.scale_factor.value)
        )

@ft.control
class RIFE_Layer(TransformerLayer):
    desc = """A transformer for frame interpolation using RIFE AI.
RIFE (Real-Time Intermediate Flow Estimation) is a deep learning model designed to generate intermediate frames between existing video frames.
It excels at creating smooth slow-motion effects and increasing frame rates by predicting motion and synthesizing new frames, all while maintaining high visual quality and real-time performance."""

    def __init__(self, container: list[TransformerLayer]):
        super().__init__(
            container,
            title=[ft.Icon(ft.Icons.SLOW_MOTION_VIDEO_OUTLINED), ft.Text("RIFE", size=20, weight=ft.FontWeight.BOLD, expand=True)],
            default_onnx="models/rife/rife_v4.10.onnx"
        )

    async def build_transformer(self):
        return RIFE(onnx_model_path=self.onnx_model_path.value, cache_dir=self.cache_dir.value)
