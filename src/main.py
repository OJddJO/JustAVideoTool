import modules.setup

import flet as ft
import os
from fractions import Fraction
import asyncio
import threading

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
        self.console = ConsoleView()

        self.views_list = [self.input, self.transform, self.encode, self.console]
        for view in self.views_list:
            self.page.overlay.extend(view.overlay)

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

    async def run(self, e: ft.Event[ft.Button]):
        # ---- Setup the data ----
        pipeline = await self.transform.build_pipeline()
        files = self.input.build_files_data()
        enc = self.encode.get_params()

        if len(files) == 0:
            print("⚠️ No file selected")
            return

        print("\nℹ️ Setting up pipeline...")

        self.run_button.disabled = True
        self.run_button.update()

        os.makedirs(enc["out_dir"], exist_ok=True)
        ffmpeg_cmds = []
        for file in files:
            if pipeline:
                video_stream = None
                for s in file["streams"]:
                    if s.get("type", "") == "video":
                        video_stream = s
                        break

                if video_stream is None:
                    print(f"⚠️ File {file["name"]} ({file["path"]}) doesn't have video stream. Skipped")
                    continue

                width = video_stream["width"] * pipeline.width_factor
                height = video_stream["height"] * pipeline.height_factor
                fps: Fraction = video_stream["fps"]
                fps_num = fps.numerator * pipeline.framegen_factor
                fps_den = fps.denominator

                cmd = f'ffmpeg -y -f rawvideo -pix_fmt rgb24 -s {width}x{height} -r {fps_num}/{fps_den} -i - -i "{file["path"]}" '
                # Video
                cmd += '-map 0:v:0 '
                cmd += f'-c:v {enc["video"]["codec"]} -pix_fmt {enc["video"]["pix_fmt"]} -preset {enc["video"]["preset"]} '
                if enc["video"]["use_crf"]:
                    cmd += f'-crf {enc["video"]["crf"]} '
                else:
                    cmd += f'-b:v {enc["video"]["bitrate"]} '
                cmd += enc["video"]["custom"] + " "
                # Audio
                for stream in file["streams"]:
                    if stream["type"] == "audio" and stream["include"]:
                        cmd += f'-map 1:{stream["index"]} '
                cmd += f'-c:a {enc["audio"]["codec"]} -b:a {enc["audio"]["bitrate"]} -ar {enc["audio"]["samplerate"]} -af {enc["audio"]["filter"]} {enc["audio"]["custom"]} '
                # Subtitle
                for stream in file["streams"]:
                    if stream["type"] == "subtitle" and stream["include"]:
                        cmd += f'-map 1:{stream["index"]} '
                cmd += f'-c:s {enc["subtitle"]["codec"]} {enc["subtitle"]["custom"]} '

                cmd += f'-hide_banner -v error "{os.path.join(enc["out_dir"], file["name"])}"'
                ffmpeg_cmds.append(cmd)
        print("✅ Pipeline setup done !")
        # ------------------------

        self.run_button.visible = False
        self.stop_button.visible = True
        self.run_button.update()
        self.run_button.disabled = False
        self.stop_button.update()

        def thread_target():
            try:
                self.console.run_pipeline(
                    files, pipeline, ffmpeg_cmds, video_stream["nb_frames"] * pipeline.framegen_factor
                )
            finally:
                e.page.run_task(self.handle_natural_completion)

        self.pipeline_thread = threading.Thread(target=thread_target, daemon=True)
        self.pipeline_thread.start()

    async def handle_natural_completion(self):
        self.stop_button.visible = False
        self.stop_button.update()
        self.run_button.visible = True
        self.run_button.update()

    async def stop(self, e: ft.Event[ft.Button]):
        self.stop_button.disabled = True
        self.stop_button.update()

        self.console.cancel_pipeline()
        while self.pipeline_thread.is_alive():
            await asyncio.sleep(0.1)

        self.stop_button.visible = False
        self.run_button.visible = True
        self.stop_button.update()
        self.stop_button.disabled = False
        self.run_button.update()


if __name__ == "__main__":
    app = VideoTool()
    ft.run(app.main)
