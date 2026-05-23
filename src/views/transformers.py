import flet as ft
from views.generic import GenericContainer, TextField, NumberInput

from modules.video_transformer import VideoTransformer
from modules.realCUGAN import RealCUGAN_TRT_CUDA
from modules.realESRGAN import RealESRGAN_TRT_CUDA

__all__ = [
    "TransformerLayer",
    "RealESRGAN_Layer",
    "RealCUGAN_Layer",
]

@ft.control
class TransformerLayer(GenericContainer):
    """Prototype class for all transformer UI layers"""
    def __init__(self, content: list = [], default_onnx = ""):
        super().__init__()
        self.file_picker = ft.FilePicker()
        self.onnx_model_path = TextField(label="ONNX path", expand=True, value=default_onnx)
        self.content = ft.Row(
            [
                ft.ReorderableDragHandle(
                    ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.ON_SURFACE),
                    mouse_cursor=ft.MouseCursor.MOVE
                ),
                ft.Column(
                    [
                        ft.Text("Model Path", size=16, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            self.onnx_model_path,
                            ft.Button("Select ONNX", icon=ft.Icons.FOLDER_OPEN_OUTLINED, on_click=self.select_onnx)
                        ], expand=True)
                    ] + content,
                    expand=True,
                    margin=5
                )
            ]
        )
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.margin = 10

    async def select_onnx(self, e: ft.Event[ft.Button]):
        file = await self.file_picker.pick_files(
            dialog_title="Select the .onnx model to use",
            initial_directory=".",
            allowed_extensions=["onnx"], allow_multiple=False
        )
        if file:
            self.onnx_model_path.value = file[0].path

    async def build_transformer(self) -> VideoTransformer:
        raise NotImplementedError("Transformer Layer shouldn't be directly used")

@ft.control
class RealESRGAN_Layer(TransformerLayer):
    desc = """A transformer for upscaling frames using RealESRGAN AI
GAN (Generative Adversarial Network): An AI architecture where two neural networks compete against each other. One network generates realistic data from scratch, while the other tries to spot flaws, forcing the system to continuously improve until the generated results look completely authentic.
ESRGAN (Enhanced Super-Resolution GAN): Optimized for real-world photos and realistic textures. It is incredibly good at reconstructing fine details like human hair, fabric weave, tree bark, and rock surfaces, making it a favorite for remastering old video games and photography."""

    def __init__(self):
        super().__init__([
            ft.Divider(),
            ft.Row([
                ft.Text(
                    "Tiling parameters",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Icon(
                    ft.Icons.HELP_OUTLINE,
                    tooltip="Tiling helps reducing VRAM usage at the cost of speed.\nThe smaller the tile, the less VRAM will be used. Bigger tile padding can help avoid tearing.",
                    size=18
                )
            ]),
            ft.Row([
                NumberInput(value="620", label="Tile width"),
                NumberInput(value="360", label="Tile height"),
                NumberInput(value="64", label="Tile padding")
            ])
        ], "models/RealESRGANv2/RealESRGANv2-animevideo-xsx2.onnx")

@ft.control
class RealCUGAN_Layer(TransformerLayer):
    desc = """A transformer for upscaling frames using RealCUGAN AI
GAN (Generative Adversarial Network): An AI architecture where two neural networks compete against each other. One network generates realistic data from scratch, while the other tries to spot flaws, forcing the system to continuously improve until the generated results look completely authentic.
CUGAN (Cascaded-U-Net GAN): Specifically optimized for Anime, Manga, and Cartoon art. It focuses on fixing the unique issues found in digital animation—like cleaning up jagged line art, removing compression noise, and preserving smooth color gradients without creating ugly artifacts."""

    def __init__(self):
        super().__init__([
            ft.Divider(),
            ft.Row([
                ft.Text(
                    "Tiling parameters",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Icon(
                    ft.Icons.HELP_OUTLINE,
                    tooltip="Tiling helps reducing VRAM usage at the cost of speed.\nThe smaller the tile, the less VRAM will be used. Bigger tile padding can help avoid tearing.",
                    size=18
                )
            ]),
            ft.Row([
                NumberInput(value="620", label="Tile width"),
                NumberInput(value="360", label="Tile height"),
                NumberInput(value="64", label="Tile padding")
            ])
        ], "models/cugan/pro-conservative-up2x.onnx")
