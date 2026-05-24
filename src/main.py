import flet as ft
from enum import IntEnum
from views.generic import GenericView
from views.input import InputView
from views.transform import TransformView
from views.encoding import EncodingView
from views.console import ConsoleView

class VideoTool:
    class ViewIndex(IntEnum):
        INPUT = 0
        TRANSFORM = 1
        ENCODING = 2
        CONSOLE = 3

    def __init__(self):
        self.views_map: dict[int, GenericView] = {}
        self.view_container: ft.Container = None
        self.log_file = None

    async def main(self, page: ft.Page):
        self.page = page
        page.title = "Just A Video Tool"
        log_file = await ft.StoragePaths().get_console_log_filename()

        self.init_ui(log_file)

    async def evHandler_navbar(self, e: ft.Event[ft.NavigationRail]):
        self.view_container.content = self.views_map[e.control.selected_index]
        self.page.overlay.clear()
        self.page.overlay.extend(self.views_map[e.control.selected_index].overlay)

    def init_ui(self, log_file: str):
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.adaptive = True

        self.views_map = {
            VideoTool.ViewIndex.INPUT: InputView(),
            VideoTool.ViewIndex.TRANSFORM: TransformView(),
            VideoTool.ViewIndex.ENCODING: EncodingView(),
            VideoTool.ViewIndex.CONSOLE: ConsoleView(log_file)
        }

        nav_sidebar = ft.Container(
            ft.NavigationRail(
                selected_index=0,
                elevation=15,
                destinations=[
                    ft.NavigationRailDestination(icon=ft.Icons.VIDEO_FILE_OUTLINED, label="Input"),
                    ft.NavigationRailDestination(icon=ft.Icons.MOVIE_EDIT, label="Transform"),
                    ft.NavigationRailDestination(icon=ft.Icons.VIDEO_SETTINGS, label="Encoding"),
                    ft.NavigationRailDestination(icon=ft.Icons.TERMINAL_ROUNDED, label="Console")
                ],
                on_change=self.evHandler_navbar,
                expand=True,
                bgcolor=ft.Colors.SURFACE
            ),
            margin=ft.Margin.only(right=10),
            border_radius=15,
            shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2))
        )

        self.view_container = ft.Container(content=self.views_map[0], expand=True)

        self.page.add(
            ft.SafeArea(
                ft.Row(
                    [
                        ft.Container(nav_sidebar),
                        self.view_container
                    ],
                    expand=True,
                    spacing=0
                ),
                expand=True
            )
        )


if __name__ == "__main__":
    app = VideoTool()
    ft.run(app.main)
