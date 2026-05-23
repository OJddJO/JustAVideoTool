import flet as ft
import os
import subprocess
from views.generic import GenericView, GenericContainer

__all__ = ["InputView"]

def format_size(size_in_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"


@ft.control
class FilePathField(GenericContainer):
    def __init__(self, file: ft.FilePickerFile, container: list["FilePathField"]):
        super().__init__()
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.filepath = file.path
        self.filename = file.name
        self.filesize = file.size

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
                ])
            ],
        )

    async def open_in_explorer(self, e: ft.Event[ft.Button]):
        if self.filepath and os.path.exists(self.filepath):
            subprocess.Popen(f'explorer /select,"{self.filepath}"')
        else:
            print("File path invalid")

    async def remove_from_container(self):
        self.container.remove(self)
        print(f"[INFO] Removed {self.filename} ({self.filepath}) from selection")

    def get_file_attr(self) -> tuple:
        return (self.filename, self.filepath, self.filesize)


@ft.control
class InputView(GenericView):
    def __init__(self):
        super().__init__()

        self.file_picker = ft.FilePicker()
        self.picked_file_paths: list[FilePathField] = []
        self.file_container = ft.ListView(self.picked_file_paths, spacing=20, padding=10, clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True)

        clear_selection_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm"),
            content=ft.Text("Are you sure you want to clear the current selection ?"),
            actions=[
                ft.TextButton(ft.Text("Confirm", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_300), on_click=self.handle_clear_selection),
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.content = ft.Column(
            [
                ft.Text("Video Input", size=28, weight=ft.FontWeight.BOLD),
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
        self.picked_file_paths.clear()
        self.file_container.update()
        print("[INFO] Cleared selection")
        self.page.pop_dialog()

    async def handle_file_selection(self, e: ft.Event[ft.Button]):
        files = await self.file_picker.pick_files(
            dialog_title="Select the videos you want to edit",
            allowed_extensions=["mp4", "mov", "mkv"] , allow_multiple=True)

        existing_paths = [field.get_file_attr() for field in self.picked_file_paths]

        for file in files:
            if (file.name, file.path, file.size) in existing_paths:
                continue
            self.picked_file_paths.append(FilePathField(file, self.picked_file_paths))
            print(f"[INFO] Added {file.name} ({file.path}) to selection")

        self.file_container.update()
