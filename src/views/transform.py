import flet as ft
from views.generic import GenericContainer

__all__ = ["TransformView"]

class TransformerLayer(GenericContainer):
    def __init__(self):
        super().__init__()
        self.content=ft.Row(
            [
                ft.ReorderableDragHandle(ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.ON_SURFACE)),
                ft.Column(
                    [
                        ft.Text(f"hello"),
                        ft.Text("this is an item")
                    ]
                )
            ]
        )
        self.bgcolor=ft.Colors.SURFACE_CONTAINER
        self.padding=10
        self.margin=ft.Margin.all(5)

class TransformView(GenericContainer):
    def __init__(self):
        super().__init__()

        self.transformers: list[ft.Container] = [
            TransformerLayer()
            for i in range(1, 6)
        ]
        self.content = ft.Column(
            [
                ft.Text("Transform", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    ft.Button("Add a transformer", icon=ft.Icons.ADD_CIRCLE_OUTLINE),
                    alignment=ft.MainAxisAlignment.END
                ),
                ft.ReorderableListView(
                    expand=True,
                    show_default_drag_handles=False,
                    padding=10,
                    controls=self.transformers
                )
            ], expand=True
        )
