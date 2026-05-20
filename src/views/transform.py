import flet as ft
from views.generic import GenericContainer

__all__ = ["TransformView"]

_content = (
    ft.Row(
        [
            ft.Text("Transform", size=24, weight=ft.FontWeight.BOLD),
        ],
        spacing=15
    )
)

class TransformView(GenericContainer):

    def __init__(self):
        super().__init__()
