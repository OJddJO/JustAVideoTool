import flet as ft
from views.generic import GenericContainer

__all__ = ["InputView"]

def format_size(size_in_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

class FilePathField(GenericContainer):
    def __init__(self, file: ft.FilePickerFile):
        super().__init__()
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.filepath = file.path
        self.filename = file.name
        self.filesize = file.size

        self.content = ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.VIDEO_FILE),
                    ft.Text(self.filename, weight=ft.FontWeight.BOLD),
                ]),
                ft.Row([
                    ft.Text("Filepath:", weight=ft.FontWeight.BOLD),
                    ft.Text(self.filename, italic=True, expand=True),
                    ft.Text(format_size(self.filesize)),
                ])
            ]
        )

    def get_file_attr(self) -> tuple:
        return (self.filename, self.filepath, self.filesize)


class InputView(GenericContainer):
    def __init__(self):
        super().__init__()

        self.file_picker = ft.FilePicker()
        self.picked_file_paths: list[FilePathField] = []
        self.file_container = ft.ListView(self.picked_file_paths, spacing=10, padding=20, clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True)
        self.content = ft.Column(
            [
                ft.Text("Video Input", size=24, weight=ft.FontWeight.BOLD),
                self.file_container,
                ft.Row(
                    [
                        ft.Button("Select Video(s)", icon=ft.Icons.FOLDER_OPEN, on_click=self.handle_file_selection),
                        ft.Button("Clear Selection", icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, color=ft.Colors.RED_300, on_click=self.handle_clear_selection)
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ]
        )

    async def handle_clear_selection(self, e: ft.Event[ft.Button]):
        self.picked_file_paths.clear()
        self.file_container.update()

    async def handle_file_selection(self, e: ft.Event[ft.Button]):
        files = await self.file_picker.pick_files(
            dialog_title="Select the videos you want to edit",
            allowed_extensions=["mp4", "mov", "mkv"] , allow_multiple=True)

        existing_paths = [field.get_file_attr() for field in self.picked_file_paths]

        for file in files:
            if (file.name, file.path, file.size) in existing_paths:
                continue
            self.picked_file_paths.append(FilePathField(file))


        self.file_container.update()
