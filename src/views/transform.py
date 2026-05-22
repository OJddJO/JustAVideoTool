import flet as ft
from views.generic import GenericView, GenericContainer

__all__ = ["TransformView"]

class TransformerLayer(GenericContainer):
    def __init__(self):
        super().__init__()
        self.content=ft.Row(
            [
                ft.ReorderableDragHandle(
                    ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.ON_SURFACE),
                    mouse_cursor=ft.MouseCursor.MOVE
                ),
                ft.Column(
                    [
                        ft.Text(f"hello"),
                        ft.Text("this is an item")
                    ]
                )
            ]
        )
        self.bgcolor=ft.Colors.SURFACE_CONTAINER
        self.margin=ft.Margin.all(5)

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

        self.transformers: list[ft.Container] = [
            TransformerLayer() for _ in range(10)
        ]
        self.content = ft.Column(
            [
                ft.Text("Transform", size=24, weight=ft.FontWeight.BOLD),
                ft.ReorderableListView(
                    expand=True,
                    show_default_drag_handles=False,
                    padding=10,
                    controls=self.transformers
                ),
                ft.Row(
                    [
                        ft.Button("Add a transformer", icon=ft.Icons.ADD_CIRCLE_OUTLINE),
                        ft.Button("Remove all transformers", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300,
                                    on_click=lambda e: self.page.show_dialog(clear_transformers_dialog))
                    ],
                    alignment=ft.MainAxisAlignment.END
                ),
            ], expand=True
        )

    async def handle_clear_transformers(self):
        self.page.pop_dialog()
