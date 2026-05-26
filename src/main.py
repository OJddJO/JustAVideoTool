import os, sys, glob

print("--- Registering DLL Paths ---")
search_pattern = os.path.join(sys.prefix, "**", "site-packages")
matches = glob.glob(search_pattern, recursive=True)

if matches:
    site_packages = matches[0]
    print(f"Discovered site-packages at: {site_packages}")
else:
    print("Could not locate site-packages using this pattern layout.")

# Check for TRT paths
for trt_dir in ["tensorrt", "tensorrt_libs", "tensorrt_bindings"]:
    p = os.path.join(site_packages, trt_dir)
    if os.path.exists(p):
        print(f"Found TRT path: {p}")
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Check for CUDA/cuDNN paths
nvidia_bins = glob.glob(os.path.join(site_packages, "nvidia", "*", "bin"))
for p in nvidia_bins:
    if os.path.exists(p):
        print(f"Found NVIDIA path: {p}")
        os.add_dll_directory(p)
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
print("\n")

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

    def main(self, page: ft.Page):
        self.page = page
        page.title = "Just A Video Tool"

        self.init_ui()

    def init_ui(self):
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.adaptive = True

        self.views_map = {
            VideoTool.ViewIndex.INPUT: InputView(),
            VideoTool.ViewIndex.TRANSFORM: TransformView(),
            VideoTool.ViewIndex.ENCODING: EncodingView(),
            VideoTool.ViewIndex.CONSOLE: ConsoleView()
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

    async def evHandler_navbar(self, e: ft.Event[ft.NavigationRail]):
        self.view_container.content = self.views_map[e.control.selected_index]
        self.page.overlay.clear()
        self.page.overlay.extend(self.views_map[e.control.selected_index].overlay)


if __name__ == "__main__":
    app = VideoTool()
    ft.run(app.main)
