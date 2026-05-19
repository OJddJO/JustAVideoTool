import flet as ft

class VideoTool:
    def __init__(self):
        self.views_map: dict[ft.Container] = {}
        self.view_container: ft.Container = None


    def main(self, page: ft.Page):
        self.page = page
        page.title = "Video Tool"

        self.init_ui()


    def evHandler_navbar(self, e: ft.Event[ft.NavigationRail]):
        self.view_container.content = self.views_map[e.control.selected_index]


    def init_ui(self):
        self.page.adaptive = True

        view_transform = ft.Container(
            content=ft.Column([
                ft.Text("Execution Control Center", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Configure your input scripts and initialize the transcode pipeline below."),
                ft.Button("Start Processing Pass", icon=ft.Icons.PLAY_ARROW),
            ], spacing=15),
            padding=20
        )

        self.views_map = {
            0: view_transform
        }

        nav_sidebar = ft.NavigationRail(
            selected_index=0,
            width=100,
            elevation=15,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.MOVIE_EDIT, label="Transform"),
                ft.NavigationRailDestination(icon=ft.Icons.TERMINAL_ROUNDED, label="Console")
            ],
            on_change=self.evHandler_navbar,
            expand=True,
        )

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
