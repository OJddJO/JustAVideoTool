import modules.setup

import flet as ft
import os

from views.generic import GenericView
from views.input import InputView
from views.transform import TransformView
from views.encode import EncodeView
from views.console import ConsoleView

class RunnerControlButton(ft.Column):
    def __init__(self, name: str, icon: ft.Icons, color: ft.Colors, callback, visible=True):
        super().__init__(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, margin=ft.Margin(bottom=10))
        self.controls = [
            ft.Button(ft.Icon(icon, color=color), on_click=callback),
            ft.Text(name, text_align=ft.TextAlign.CENTER, size=12, weight=ft.FontWeight.BOLD),
        ]
        self.visible = visible

class VideoTool:
    def __init__(self):
        self.views_list: list[GenericView] = []
        self.view_container: ft.Container = None
        self.log_file = None

    def main(self, page: ft.Page):
        self.page = page
        self.page.title = "Just A Video Tool"

        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.adaptive = True

        self.input = InputView()
        self.transform = TransformView()
        self.encode = EncodeView()

        self.views_list = [self.input, self.transform, self.encode, ConsoleView()]

        self.run_button = RunnerControlButton("Run", ft.Icons.PLAY_ARROW_OUTLINED, None, self.run, True)
        self.stop_button = RunnerControlButton("Stop", ft.Icons.STOP_OUTLINED, ft.Colors.RED_300, self.stop, False)

        nav_sidebar = ft.Container(
            content = ft.NavigationRail(
                selected_index=0,
                elevation=15,
                destinations=[
                    ft.NavigationRailDestination(icon=ft.Icons.VIDEO_FILE_OUTLINED, label="Input"),
                    ft.NavigationRailDestination(icon=ft.Icons.MOVIE_EDIT, label="Transform"),
                    ft.NavigationRailDestination(icon=ft.Icons.VIDEO_SETTINGS, label="Encoding"),
                    ft.NavigationRailDestination(icon=ft.Icons.TERMINAL_ROUNDED, label="Console")
                ],
                trailing=ft.Stack([self.run_button, self.stop_button]),
                pin_trailing_to_bottom=True,
                on_change=self.evHandler_navbar,
                expand=True,
                bgcolor=ft.Colors.SURFACE
            ),
            margin=ft.Margin.only(right=10),
            border_radius=15,
            shadow=ft.BoxShadow(1, 10, ft.Colors.SHADOW, ft.Offset(2, 2))
        )

        self.view_container = ft.Container(content=self.views_list[0], expand=True)

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
        self.view_container.content = self.views_list[e.control.selected_index]
        del self.page.overlay[1:]
        self.page.overlay.extend(self.views_list[e.control.selected_index].overlay)

    async def run(self, e: ft.Event[ft.Button]):
        self.run_button.disabled = True
        self.run_button.update()

        # ---- Setup the data ----
        pipeline = await self.transform.build_pipeline()
        files = self.input.build_files_data()
        encoding_params = self.encode.get_params()

        os.makedirs(encoding_params["out_dir"], exist_ok=True)
        cmds = []
        for file in files:
            video_stream = None
            for s in file["streams"]:
                if s.get("codec_type", "") == "video":
                    video_stream = s
                    break

            if video_stream is None:
                print(f"⚠️ File {file.name} ({file.path}) doesn't have video stream. Skipped")
                continue

            width = video_stream.width * pipeline.width_factor
            height = video_stream.height * pipeline.height_factor
            fps: str = video_stream.avg_frame_rate
            if fps.find("/") == -1:
                fps_num = int(fps) * pipeline.framegen_factor
            else:
                fps_num, fps_den, *_ = video_stream.avg_frame_rate.split("/")
                fps_num = int(fps_num) * pipeline.framegen_factor

            cmd = f"ffmpeg -hide_banner -v error -y -i - -f rawvideo -pix_fmt rgb24 -s {width}x{height} -r {fps_num}/{fps_den} "
            print(cmd)

        # ------------------------

        self.run_button.visible = False
        self.stop_button.visible = True
        self.run_button.update()
        self.run_button.disabled = False
        self.stop_button.update()

    async def stop(self, e: ft.Event[ft.Button]):
        self.stop_button.disabled = True
        self.stop_button.update()

        self.stop_button.visible = False
        self.run_button.visible = True
        self.stop_button.update()
        self.stop_button.disabled = False
        self.run_button.update()


if __name__ == "__main__":
    app = VideoTool()
    ft.run(app.main)
