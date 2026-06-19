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

    def run_pipeline(self, files: list, pipeline: ModularProcessingPipeline, ffmpeg_cmds: tuple[str], nb_frames: int):
        self.is_cancelled = False
        error = False
        nb_of_files = len(files)

        # UI Update Helper
        def update_ui(control: ft.Control, value: str | float):
            control.value = value
            if self.console_focused:
                control.update()

        update_ui(self.progress_bar, 0)

        for i, file in enumerate(files):
            if self.is_cancelled:
                update_ui(self.progress_status, "Pipeline cancelled by user")
                break

            update_ui(self.progress_status, f"Processing {i+1}/{nb_of_files} files")

            # Unpack the commands (cmd_audio can now be a list of separate command strings or a single string)
            cmd_video, cmd_audio, cmd_merge = ffmpeg_cmds[i]
            video_process = None
            start_time = time.time_ns()

            print(f"\nRunning pipeline on: {file['name']} ({file['path']})")
            update_ui(self.frame_progress, 0)

            try:
                print("Processing video frames...")
                for frame, frame_bytes in enumerate(pipeline.stream_pipeline(file["path"]), start=1):
                    if self.is_cancelled:
                        print("Cancellation detected! Killing video worker...")
                        if video_process: video_process.terminate()
                        break

                    if not video_process:
                        video_process = subprocess.Popen(
                            shlex.split(cmd_video),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )

                    video_process.stdin.write(frame_bytes)
                    video_process.stdin.flush()

                    if frame % 100 == 0 or frame == nb_frames:
                        update_ui(self.frame_progress, frame / nb_frames)

                # Finalize Video Track Container
                if video_process and not self.is_cancelled:
                    print("Closing FFmpeg pipe and finalizing video container...")
                    video_process.stdin.close()
                    video_process.wait()

            except Exception as pipe_err:
                print(f"Pipeline processing crash on {file['name']}:\n{traceback.format_exc()}\n{pipe_err}")
                if video_process and video_process.stdin and not video_process.stdin.closed:
                    video_process.stdin.close()
                error = True

            if self.is_cancelled or (video_process and video_process.returncode != 0):
                if self.is_cancelled:
                    print("Pipeline cancelled by user")
                    update_ui(self.progress_status, "Pipeline cancelled by user")
                elif video_process and video_process.returncode != 0:
                    print(f"Video process failed with exitcode {video_process.returncode}!\nFFmpeg error logs:\n{video_process.stderr.read().decode().strip()}")
                    update_ui(self.progress_status, f"Failed on {file['name']}!")
                error = True
                break

            # Demux audios
            print("Extracting audio from source file...")
            update_ui(self.progress_status, "Extracting audio from source file")

            audio_process = subprocess.run(
                shlex.split(cmd_audio),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if audio_process.returncode != 0:
                print(f"Failed to extract audio from source with exitcode {audio_process.returncode} !\nFFmpeg error logs:\n{audio_process.stderr.decode().strip()}")
                update_ui(self.progress_status, f"Failed on {file['name']}!")
                error = True
                break

            # Mux streams
            print("Merging streams to video stream...")
            update_ui(self.progress_status, "Merging streams to video stream")

            merge_process = subprocess.run(
                shlex.split(cmd_merge),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if merge_process.returncode != 0:
                print(f"Merge process failed with exitcode {merge_process.returncode}!\nFFmpeg error logs:\n{merge_process.stderr.decode().strip()}")
                update_ui(self.progress_status, f"Failed on {file['name']}!")
                error = True
                break

            end_time = time.time_ns()
            print(f"Video {file['name']} processed successfully in {round((end_time - start_time) / 1e9, 4)}s!")
            update_ui(self.progress_bar, (i + 1) / nb_of_files)

        if not error:
            update_ui(self.progress_status, "Done !")
        else:
            update_ui(self.progress_bar, 1)
            update_ui(self.frame_progress, 0)

        if os.path.exists("temp"):
            for temp_file in os.listdir("temp"):
                file_path = os.path.join("temp", temp_file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        pipeline.clean_memory()

    def cancel_pipeline(self):
        self.is_cancelled = True
