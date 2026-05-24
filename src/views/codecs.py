import flet as ft
from views.generic import GenericContainer

@ft.control
class GenericCodec(GenericContainer):
    def __init__(self, content = []):
        super().__init__()
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.content = ft.Column(
            [
                ft.Text("")
            ] + content,
        )
