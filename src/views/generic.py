import flet as ft

class GenericContainer(ft.Container):
    def __init__(self):
        super().__init__(padding=20, bgcolor=ft.Colors.SURFACE, border_radius=15, shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2)))
