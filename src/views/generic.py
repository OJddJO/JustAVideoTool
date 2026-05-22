import flet as ft

class GenericContainer(ft.Container):
    def __init__(self):
        super().__init__(padding=10, bgcolor=ft.Colors.SURFACE, border_radius=15, shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2)), expand=True)

class GenericView(GenericContainer):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.floating_action_button = None
