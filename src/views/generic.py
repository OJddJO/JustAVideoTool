import flet as ft

@ft.control
class GenericContainer(ft.Container):
    def __init__(self):
        super().__init__(padding=10, bgcolor=ft.Colors.SURFACE, border_radius=15, shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2)), expand=True)

@ft.control
class GenericView(GenericContainer):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.floating_action_button = None
        self.overlay = []

@ft.control
class GenericOverlay(ft.Stack):
    def __init__(self, content = ft.LayoutControl):
        super().__init__(
            expand=True,
            controls=[
                ft.Container(expand=True, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
                content
            ],
            visible=False
        )
        content.margin = 50
        content.wrapper = self

@ft.control
class TextField(ft.TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autocorrect = False
        self.enable_suggestions = False
        self.smart_dashes_type = False
        self.smart_quotes_type = False
        self.text_size = 14

@ft.control
class NumberInput(TextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_filter = ft.InputFilter("[0-9]*")
        self.keyboard_type = ft.KeyboardType.NUMBER
