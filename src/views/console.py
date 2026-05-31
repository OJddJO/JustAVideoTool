import flet as ft
import os
import asyncio
import subprocess
import shlex
import time
import traceback
from views.generic import GenericView, GenericContainer, ViewTitle, TextField
from modules.modular_pipeline import ModularProcessingPipeline

@ft.control
class ConsoleView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.console_focused = False

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
        self.frame_progress = ft.ProgressBar(value=0)
        progress = GenericContainer(
            content=ft.Column([
                self.progress_status,
                self.progress_bar,
                self.frame_progress
            ])
        )
        progress.expand = False
        self.content = ft.Column([
            ViewTitle("Console"),
            GenericContainer(
                content=self.text_field,
                expand=True,
            ),
            progress
        ], expand=True, spacing=0)
        self.is_cancelled = False

    def did_mount(self):
        self.console_focused = True
        self.page.run_task(self.tail_log)

    def will_unmount(self):
        self.console_focused = False

    async def tail_log(self):
        if not self.log_file:
            self.log_file = await ft.StoragePaths().get_console_log_filename()

        while not os.path.exists(self.log_file) and self.console_focused:
            await asyncio.sleep(1)

        if not self.console_focused:
            return

        with open(self.log_file, "r") as f:
            self.text_field.value = f.read()
            self.text_field.update()

            while self.console_focused:
                new_data = f.read()
                if new_data:
                    self.text_field.value += new_data
                    self.text_field.update()
                else:
                    await asyncio.sleep(0.1)

    def run_pipeline(self, files: list, pipeline: ModularProcessingPipeline, ffmpeg_cmds: list[str], nb_frames: int):
        self.is_cancelled = False
        error = 0
        nb_of_files = len(files)

        self.progress_bar.value = 0
        if self.console_focused: self.progress_bar.update()

        for i, file in enumerate(files):
            if self.is_cancelled:
                self.progress_status.value = "Pipeline cancelled by user"
                if self.console_focused: self.progress_status.update()
                error = 0
                break

            self.progress_status.value = f"Processing {i+1}/{nb_of_files} files"
            if self.console_focused: self.progress_status.update()
            cmd = ffmpeg_cmds[i]
            ffmpeg_process = None

            print(f"Running the pipeline on {file['name']} ({file['path']})")
            start = time.time_ns()
            frame = 1
            self.frame_progress.value = 0
            if self.console_focused: self.frame_progress.update()
            try:
                for frame_bytes in pipeline.stream_pipeline(file["path"]):
                    if self.is_cancelled:
                        print("Cancellation detected! Terminating FFmpeg...")
                        if ffmpeg_process: ffmpeg_process.terminate()  # Instantly kills the FFmpeg process safely
                        break

                    if not ffmpeg_process:
                        ffmpeg_process = subprocess.Popen(
                            shlex.split(cmd), stdin=subprocess.PIPE, stderr=subprocess.PIPE
                        )

                    ffmpeg_process.stdin.write(frame_bytes)
                    ffmpeg_process.stdin.flush()

                    if frame%100 == 0 or frame == nb_frames:
                        self.frame_progress.value = frame/nb_frames
                        if self.console_focused: self.frame_progress.update()
                    frame += 1

                if ffmpeg_process and not self.is_cancelled:
                    print("Closing FFmpeg pipe and finalizing video container...")
                    ffmpeg_process.stdin.close()
                    while not ffmpeg_process.stdin.closed:
                        time.sleep(0.1)

            except Exception as pipe_err:
                error_traceback = traceback.format_exc()
                print(f"❌ Pipeline error on {file['name']}:\n{error_traceback}\n{pipe_err}")
                if ffmpeg_process and ffmpeg_process.stdin and not ffmpeg_process.stdin.closed:
                    ffmpeg_process.stdin.close()

            finally:
                if ffmpeg_process:
                    return_code = ffmpeg_process.wait()
                    if self.is_cancelled:
                        print(f"Process for {file['name']} was forcefully aborted.")
                        self.progress_status.value = "Pipeline cancelled by user"
                        if self.console_focused: self.progress_status.update()
                        error = 1
                        break

                    end = time.time_ns()

                    if return_code != 0:
                        stderr_bytes = ffmpeg_process.stderr.read()
                        ffmpeg_errors = stderr_bytes.decode().strip()
                        print(f"FFmpeg failed with exitcode {return_code} on {file['name']}")
                        print(f"FFmpeg Error Log:\n{ffmpeg_errors}")

                        self.progress_status.value = f"Failed on {file['name']}!"
                        if self.console_focused: self.progress_status.update()
                        error = 1
                        break
                else:
                    # If FFmpeg never even spawned
                    error = 1
                    break

            print(f"Video {file['name']} process complete!")
            print(f"Took {round((end - start) / 1e9, 4)} seconds.")

            self.progress_bar.value = (i+1)/nb_of_files
            if self.console_focused: self.progress_bar.update()

        if not error:
            self.progress_status.value = "Done !"
            if self.console_focused: self.progress_status.update()
        else:
            self.progress_bar.value = 1
            self.frame_progress.value = 0
            if self.console_focused:
                self.progress_bar.update()
                self.frame_progress.update()

        pipeline.clean_memory()

    def cancel_pipeline(self):
        self.is_cancelled = True
