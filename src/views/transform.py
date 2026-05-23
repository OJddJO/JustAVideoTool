import flet as ft
from types import MethodType
from views.generic import GenericContainer, GenericView, GenericOverlay
from views.transformers import *

__all__ = ["TransformView"]

transformers = {
    "Upscalers": {
        "desc": "Increases frame resolution to produce sharp, high-definition output",
        "icon": ft.Icons.IMAGE_ASPECT_RATIO,
        "tr": {
            "RealESRGAN": {
                "desc": RealESRGAN_Layer.desc,
                "class": RealESRGAN_Layer
            },
            "RealCUGAN": {
                "desc": RealCUGAN_Layer.desc,
                "class": RealCUGAN_Layer
            },
        }
    }
}

@ft.control
class TransformerSelector(ft.ExpansionTile):
    def __init__(self, adder: MethodType, type: str, name: str):
        super().__init__(ft.Row([
            ft.Text(name, weight=ft.FontWeight.BOLD, expand=True),
            ft.IconButton(icon=ft.Icons.ADD_OUTLINED, on_click=self.add)
        ]))
        self.controls=ft.Text(transformers[type]["tr"][name]["desc"])
        self.controls_padding = 10
        self.expanded = False
        self.adder = adder
        self.type = type
        self.name = name

    async def add(self, e: ft.Event[ft.Button]):
        await self.adder(e, self.type, self.name)

@ft.control
class TransformerCategory(GenericContainer):
    def __init__(self, adder: MethodType, type: str):
        super().__init__()
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.content = ft.ExpansionTile(
            title=ft.Row([
                ft.Icon(transformers[type]["icon"]),
                ft.Text(type, weight=ft.FontWeight.BOLD, expand=True),
            ]),
            subtitle=ft.Text(transformers[type]["desc"], italic=True),
            expanded=False,
            shape=ft.RoundedRectangleBorder(radius=0),
            collapsed_shape=ft.RoundedRectangleBorder(radius=0),
            controls=ft.ListView(
                controls=[ TransformerSelector(adder, type, name) for name in transformers[type]["tr"] ],
                expand=True,
                spacing=10,
                padding=10,
                clip_behavior=ft.ClipBehavior.HARD_EDGE
            ),
        )

@ft.control
class SelectorView(GenericView):
    def __init__(self, transfromers_container: list[TransformerLayer]):
        super().__init__()
        self.wrapper: GenericOverlay
        self.content = ft.Column(
            [
                ft.ListView(
                    controls=[ TransformerCategory(self.add_transformer, type) for type in transformers ],
                    expand=True,
                    spacing=20,
                    padding=10,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                ),
                ft.Row(
                    [
                        ft.Button("Cancel", icon=ft.Icons.CANCEL_OUTLINED, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300, on_click=self.hide)
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ],
            expand=True
        )
        self.transformers_container = transfromers_container

    async def hide(self, e: ft.Event[ft.Button] = None):
        self.wrapper.visible = False

    async def add_transformer(self, e: ft.Event[ft.Button], type: str, name: str):
        self.transformers_container.append(transformers[type]["tr"][name]["class"]())
        await self.hide(e)

@ft.control
class TransformView(GenericView):
    def __init__(self):
        super().__init__()

        clear_transformers_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm"),
            content=ft.Text("Are you sure you want to clear the current selection ?"),
            actions=[
                ft.TextButton(ft.Text("Confirm", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_300), on_click=self.handle_clear_transformers),
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.transformers: list[TransformerLayer] = []
        self.selector_view = SelectorView(self.transformers)
        self.selector_view_wrapper = GenericOverlay(self.selector_view)
        self.overlay = [self.selector_view_wrapper]
        self.content = ft.Column(
            [
                ft.Text("Transform", size=28, weight=ft.FontWeight.BOLD),
                ft.ReorderableListView(
                    expand=True,
                    show_default_drag_handles=False,
                    controls=self.transformers,
                    on_reorder=self.handle_reorder
                ),
                ft.Row(
                    [
                        ft.Button("Add a transformer", icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=self.handle_add_transformer),
                        ft.Button("Remove all transformers", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300,
                                    on_click=lambda e: self.page.show_dialog(clear_transformers_dialog))
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
            ], expand=True
        )

    async def handle_add_transformer(self, e: ft.Event[ft.Button]):
        self.selector_view_wrapper.visible = True

    async def handle_clear_transformers(self, e: ft.Event[ft.Button]):
        self.transformers.clear()
        self.content.update()
        self.page.pop_dialog()

    async def handle_reorder(self, e: ft.OnReorderEvent):
        element = self.transformers.pop(e.old_index)
        self.transformers.insert(e.new_index, element)
        e.control.update()
