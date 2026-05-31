import flet as ft
import os
import subprocess
import asyncio
import av
from views.generic import GenericView, ViewTitle, GenericContainer, Label

__all__ = ["InputView"]

def format_size(size_in_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"


def get_icon_from_stream_type(type: str):
    match type:
        case "video":
            return ft.Icons.MOVIE_OUTLINED
        case "audio":
            return ft.Icons.MUSIC_NOTE_OUTLINED
        case "subtitle":
            return ft.Icons.SUBTITLES_OUTLINED
        case _:
            return ft.Icons.DATA_OBJECT_OUTLINED

def get_all_metadata(file_path):
    metadata = []

    with av.open(file_path) as container:
        for stream in container.streams:
            stream_info = {
                "index": stream.index,
                "type": stream.type,
                "codec": stream.codec_context.name if stream.codec_context else "unknown",
                "duration": stream.duration,
                "metadata": stream.metadata,
            }

            match stream.type:
                case 'video':
                    # stream: av.VideoStream
                    frames = stream.frames
                    if not stream.frames:
                        duration = stream.duration
                        time_base = stream.time_base
                        fps = stream.average_rate
                        if duration and time_base and fps:
                            duration_seconds = float(duration * time_base)
                            calculated_frames = int(round(duration_seconds * float(fps)))
                            frames = calculated_frames
                        else:
                            demuxer = container.demux(stream)
                            frames = sum(1 for _ in demuxer)

                    stream_info.update({
                        "width": stream.width,
                        "height": stream.height,
                        "fps": stream.average_rate,
                        "nb_frames": frames,
                        "pix_fmt": stream.pix_fmt if stream.pix_fmt else "unknown",
                    })
                case 'audio':
                    # stream: av.AudioStream
                    stream_info.update({
                        "name": stream.name if stream.name else "",
                        "language": stream.language if stream.language else "",
                        "sample_rate": stream.sample_rate,
                        "channels": stream.channels,
                        "layout": stream.layout.name,
                    })
                case 'subtitle':
                    stream_info.update({
                        "name": stream.name if stream.name else "",
                        "language": stream.language if stream.language else "",
                    })

            metadata.append(stream_info)

    return metadata


@ft.control
class StreamMetadata(ft.Column):
    def __init__(self, metadata: dict, content: list = []):
        super().__init__()
        self.metadata = metadata
        self.include = ft.Checkbox(label=Label("Include in output"), value=True)
        self.controls = [
            ft.Row([
                Label("Codec:"),
                ft.Text(f"{metadata.get('codec', 'unknown')}"),
            ]),
            ft.Row([
                Label("Type:"),
                ft.Text(metadata.get("type", "unknown")),
            ])
        ] + content + [
            ft.Row([
                self.include
            ], alignment=ft.MainAxisAlignment.END)
        ]
        self.expand = True
        self.margin = 10

    def build_metadata(self):
        self.metadata["include"] = self.include.value
        return self.metadata


@ft.control
class VideoStreamMetadata(StreamMetadata):
    def __init__(self, metadata: dict):
        super().__init__(
            metadata,
            [
                ft.Row([
                    Label("Width:"),
                    ft.Text(metadata.get("width", "unknown")),
                ]),
                ft.Row([
                    Label("Height:"),
                    ft.Text(metadata.get("height", "unknown"))
                ]),
                ft.Row([
                    Label("FPS:"),
                    ft.Text(str(metadata.get("fps", "unknown")))
                ]),
                ft.Row([
                    Label("Number of frames:"),
                    ft.Text(metadata.get("nb_frames", "unknown"))
                ]),
                ft.Row([
                    Label("Pixel format:"),
                    ft.Text(metadata.get("pix_fmt", "unknown"))
                ])
            ]
        )
        self.include.disabled = True

@ft.control
class AudioStreamMetadata(StreamMetadata):
    def __init__(self, metadata: dict):
        super().__init__(
            metadata,
            [
                ft.Row([
                    Label("Name:"),
                    ft.Text(metadata.get('name', ""))
                ]),
                ft.Row([
                    Label("Language:"),
                    ft.Text(metadata.get('language', 'unknown'))
                ]),
                ft.Row([
                    Label("Sample rate:"),
                    ft.Text(metadata.get("sample_rate", "unknown"))
                ]),
                ft.Row([
                    Label("No. of channels:"),
                    ft.Text(metadata.get("channels", "unknown"))
                ]),
                ft.Row([
                    Label("Channel layout:"),
                    ft.Text(metadata.get("layout", "unknown"))
                ])
            ]
        )

@ft.control
class SubtitleStreamMetadata(StreamMetadata):
    def __init__(self, metadata: dict):
        super().__init__(
            metadata,
            [
                ft.Row([
                    Label("Name:"),
                    ft.Text(metadata.get('name', ""))
                ]),
                ft.Row([
                    Label("Language:"),
                    ft.Text(metadata.get('language', 'unknown'))
                ]),
            ]
        )


def build_metadata_view(type: str, metadata: dict):
    match type:
        case "video":
            return VideoStreamMetadata(metadata)
        case "audio":
            return AudioStreamMetadata(metadata)
        case "subtitle":
            return SubtitleStreamMetadata(metadata)
        case _:
            return StreamMetadata(metadata)


@ft.control
class FileStreams(ft.Tabs):
    def __init__(self, metadata: dict):
        self.streams = [ build_metadata_view(s.get("type", ""), s) for s in metadata ]
        super().__init__(
            length = len(metadata),
            content = ft.Column(
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(
                                label=f"Stream {s['index']}",
                                icon=ft.Icon(get_icon_from_stream_type(s.get("type", "")), size=18)
                            ) for s in metadata
                        ]
                    ),
                    ft.TabBarView(
                        controls=self.streams,
                        height=280,
                    )
                ]
            ),
            margin=ft.Margin(top=10)
        )

    def build_metadata(self):
        return [stream.build_metadata() for stream in self.streams]


@ft.control
class FileField(GenericContainer):
    def __init__(self, container: list["FileField"], file: ft.FilePickerFile, metadata: dict):
        super().__init__()
        self.filepath = file.path
        self.filename = file.name
        self.filesize = file.size
        self.metadata = metadata
        self.streams = FileStreams(metadata)

        self.container = container

        self.content = ft.ExpansionTile(
            title=ft.Row([
                ft.Icon(ft.Icons.VIDEO_FILE),
                ft.Text(self.filename, weight=ft.FontWeight.BOLD, expand=True),
            ]),
            subtitle=ft.Row([
                ft.Text("Filepath:", weight=ft.FontWeight.BOLD),
                ft.Text(self.filepath, italic=True, expand=True),
                ft.Text(format_size(self.filesize)),
            ]),
            expanded=False,
            shape=ft.RoundedRectangleBorder(radius=0),
            collapsed_shape=ft.RoundedRectangleBorder(radius=0),
            controls=[
                ft.Row([
                    ft.Button("Open in explorer", icon=ft.Icons.FOLDER_OPEN, expand=True, on_click=self.open_in_explorer),
                    ft.Button("Remove from selection", icon=ft.Icons.REMOVE, expand=True, icon_color=ft.Colors.RED_300,
                                color=ft.Colors.RED_300, on_click=self.remove_from_container)
                ], margin=ft.Margin(top=10, bottom=10)),
                ft.Row([
                    ft.Button("Include all streams in output", icon=ft.Icons.CHECK_OUTLINED, expand=True, on_click=self.include_all_stream),
                    ft.Button("Remove all streams from output", icon=ft.Icons.REMOVE_OUTLINED, expand=True, on_click=self.remove_all_stream),
                    ft.Button("Invert stream inlcusion", icon=ft.Icons.SWAP_HORIZONTAL_CIRCLE_OUTLINED, expand=True, on_click=self.invert_all_stream)
                ]),
                self.streams
            ]
        )

    async def include_all_stream(self, e: ft.Event[ft.Button]):
        for stream in self.streams.streams:
            stream.include.value = True
            stream.include.update()

    async def remove_all_stream(self, e: ft.Event[ft.Button]):
        for stream in self.streams.streams:
            if stream.metadata["type"] == "video":
                continue
            stream.include.value = False
            stream.include.update()

    async def invert_all_stream(self, e: ft.Event[ft.Button]):
        for stream in self.streams.streams:
            if stream.metadata["type"] == "video":
                continue
            stream.include.value = not stream.include.value
            stream.include.update()

    async def open_in_explorer(self, e: ft.Event[ft.Button]):
        if self.filepath and os.path.exists(self.filepath):
            subprocess.Popen(f'explorer /select,"{self.filepath}"')
        else:
            print("File path invalid")

    async def remove_from_container(self):
        self.container.remove(self)
        print(f"Removed {self.filename} ({self.filepath}) from selection")

    def get_file_attr(self) -> dict:
        return {
            "name": self.filename,
            "path": self.filepath,
            "size": self.filesize,
            "streams": self.streams.build_metadata()
        }


@ft.control
class InputView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file_picker = ft.FilePicker()
        self.picked_file: list[FileField] = []
        self.file_container = ft.ListView(self.picked_file, clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True)

        clear_selection_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm", weight=ft.FontWeight.BOLD),
            content=ft.Text("Are you sure you want to clear the current selection ?"),
            actions=[
                ft.TextButton(ft.Text("Confirm", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_300), on_click=self.handle_clear_selection),
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.loading_ring = ft.ProgressRing(width=16, height=16, stroke_width=5, visible=False)
        self.content = ft.Column(
            [
                ft.Row([
                    ViewTitle("Video Input"),
                    self.loading_ring
                ]),
                self.file_container,
                ft.Row(
                    [
                        ft.Button("Select Video(s)", icon=ft.Icons.FOLDER_OPEN, on_click=self.handle_file_selection),
                        ft.Button("Clear Selection", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300,
                                    on_click=lambda e: self.page.show_dialog(clear_selection_dialog))
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ]
        )

    async def handle_clear_selection(self, e: ft.Event[ft.Button]):
        self.picked_file.clear()
        self.file_container.update()
        print("Cleared input selection")
        self.page.pop_dialog()

    async def handle_file_selection(self, e: ft.Event[ft.Button]):
        e.page.disabled = True
        e.page.update()
        self.loading_ring.visible = True
        self.loading_ring.value = 0
        self.loading_ring.update()

        files = await self.file_picker.pick_files(
            dialog_title="Select the videos you want to edit",
            allowed_extensions=["mp4", "mkv", "mov"] , allow_multiple=True)

        existing_paths = [field.get_file_attr() for field in self.picked_file]

        for i, file in enumerate(files):
            self.loading_ring.value = i / len(files)
            self.loading_ring.update()

            if (file.name, file.path, file.size) in existing_paths:
                continue
            if not os.path.exists(str(file.path)):
                continue

            try:
                metadata = await asyncio.to_thread(get_all_metadata, file.path)
            except Exception as error:
                print(f"❌ Failed to parse metadata for {file.name} ({file.path}): {error}")

            self.picked_file.append(FileField(self.picked_file, file, metadata))
            print(f"Added {file.name} ({file.path}) to selection")
            self.file_container.update()

        self.loading_ring.visible = False
        self.loading_ring.update()
        self.file_container.update()
        e.page.disabled = False
        e.page.update()

    def build_files_data(self):
        return [file.get_file_attr() for file in self.picked_file]
