import flet as ft
from views.generic import GenericView, GenericContainer

@ft.control
class GeneralParams(GenericContainer):
    def __init__(self):
        super().__init__()
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.content = ft.Column(
            [
                ft.Text("General Options", size=16, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Text()
                ])
            ]
        )

@ft.control
class EncodingView(GenericView):
    def __init__(self):
        super().__init__()
        self.content = ft.Column(
            [
                ft.Text("Encoding", size=28, weight=ft.FontWeight.BOLD),
            ]
        )
