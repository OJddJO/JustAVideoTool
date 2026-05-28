import flet as ft

@ft.control
class GenericContainer(ft.Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.padding = 15
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.border_radius = 15
        self.shadow = ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2))
        self.expand = True
        self.margin = 10

@ft.control
class GenericView(GenericContainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bgcolor = ft.Colors.SURFACE
        self.padding = 20
        self.margin = 0
        self.overlay: list[ft.Control] = []

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
class ViewTitle(ft.Text):
    def __init__(self, title: str, *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        self.size = 28
        self.weight = ft.FontWeight.BOLD

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

@ft.control
class Label(ft.Text):
    def __init__(self, label: str, *args, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.size = 16
        self.weight = ft.FontWeight.BOLD
