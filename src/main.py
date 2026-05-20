import flet as ft

from views.input import InputView
from views.transform import TransformView
from views.encoding import EncodingView
from views.console import ConsoleView

class VideoTool:
    def __init__(self):
        self.views_map: dict[ft.Container] = {}
        self.view_container: ft.Container = None


    def main(self, page: ft.Page):
        self.page = page
        page.title = "Just A Video Tool"

        self.init_ui()


    def evHandler_navbar(self, e: ft.Event[ft.NavigationRail]):
        self.view_container.content = self.views_map[e.control.selected_index]


    def init_ui(self):
        self.page.adaptive = True

        self.views_map = {
            0: InputView(),
            1: TransformView(),
            2: EncodingView(),
            3: ConsoleView()
        }

        nav_sidebar = ft.Container(ft.NavigationRail(
            selected_index=0,
            elevation=15,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.VIDEO_FILE, label="Input"),
                ft.NavigationRailDestination(icon=ft.Icons.MOVIE_EDIT, label="Transform"),
                ft.NavigationRailDestination(icon=ft.Icons.VIDEO_SETTINGS, label="Encoding"),
                ft.NavigationRailDestination(icon=ft.Icons.TERMINAL_ROUNDED, label="Console")
            ],
            on_change=self.evHandler_navbar,
            expand=True,
            bgcolor=ft.Colors.SURFACE
        ), margin=ft.Margin.only(right=10), border_radius=15, shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2)))

        self.view_container = ft.Container(content=self.views_map[0], expand=True)

        self.page.add(
            ft.Row([
                ft.Container(nav_sidebar),
                self.view_container
            ], expand=True, spacing=0)
        )


if __name__ == "__main__":
    app = VideoTool()
    ft.run(app.main)
