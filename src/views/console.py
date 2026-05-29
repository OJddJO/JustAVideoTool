import flet as ft
import os
import asyncio
import shlex
import time
from views.generic import GenericView, GenericContainer, ViewTitle, TextField
from modules.modular_pipeline import ModularProcessingPipeline

@ft.control
class ConsoleView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.log_running = False

        self.text_field = TextField(
            expand=True,
            multiline=True,
            read_only=True,
            border_color=ft.Colors.TRANSPARENT,
            border_radius=15,
            text_size=14
        )

        self.progress_status = ft.Text("Waiting run...")
        self.progress_bar = ft.ProgressBar()
        self.content = ft.Column([
            ViewTitle("Console"),
            GenericContainer(
                content=self.text_field,
                expand=True,
            ),
            GenericContainer(
                content=ft.Column([
                    self.progress_status,
                    self.progress_bar
                ])
            )
        ], expand=True)

        self.ffmpeg_process = None

    def did_mount(self):
        self.log_running = True
        self.page.run_task(self.tail_log)

    def will_unmount(self):
        self.log_running = False

    async def tail_log(self):
        if not self.log_file:
            self.log_file = await ft.StoragePaths().get_console_log_filename()

        while not os.path.exists(self.log_file) and self.log_running:
            await asyncio.sleep(1)

        if not self.log_running:
            return

        with open(self.log_file, "r") as f:
            self.text_field.value = f.read()
            self.text_field.update()

            while self.log_running:
                new_data = f.read()
                if new_data:
                    self.text_field.value += new_data
                    self.text_field.update()
                else:
                    await asyncio.sleep(0.1)

    async def run_pipeline(files: list[str], pipeline: ModularProcessingPipeline, ffmpeg_cmds: list[str]):
        for i, file in enumerate(files):
            cmd = ffmpeg_cmds[i]
            ffmpeg_process = await asyncio.create_subprocess_exec(
                *shlex.split(cmd), stdin=asyncio.subprocess.PIPE
            )

            print(f"▶️ Running the pipeline on {file}")
            start = time.thread_time_ns()
            async for frame_bytes, w ,h in pipeline.stream_pipeline(file):
                ffmpeg_process.stdin.write(frame_bytes)
                await ffmpeg_process.stdin.drain()

            print("🔄️ Closing FFmpeg pipe and finalizing video container...")
            ffmpeg_process.stdin.close()
            await ffmpeg_process.stdin.wait_closed()
            await ffmpeg_process.wait()
            print(f"🎉 Video {file} process complete!")
            end = time.time_ns()
            print(f"ℹ️ Took {round((end - start) / 1e9, 4)} seconds.")
