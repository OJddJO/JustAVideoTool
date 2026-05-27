import flet as ft
import os
import asyncio
from views.generic import GenericView, GenericContainer, ViewTitle, TextField

@ft.control
class ConsoleView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.running = False

        self.text_field = TextField(
            expand=True,
            multiline=True,
            read_only=True,
            border_color=ft.Colors.TRANSPARENT,
            border_radius=15,
            text_size=14
        )
        self.content = ft.Column([
            ViewTitle("Console"),
            GenericContainer(
                content=self.text_field,
                expand=True,
                bgcolor=ft.Colors.SURFACE_CONTAINER,
            )
        ], expand=True)

    def did_mount(self):
        self.running = True
        self.page.run_task(self.tail_log)

    def will_unmount(self):
        self.running = False

    async def tail_log(self):
        if not self.log_file:
            self.log_file = await ft.StoragePaths().get_console_log_filename()

        while not os.path.exists(self.log_file) and self.running:
            await asyncio.sleep(1)

        if not self.running:
            return

        with open(self.log_file, "r") as f:
            self.text_field.value = f.read()
            self.text_field.update()

            while self.running:
                new_data = f.read()
                if new_data:
                    self.text_field.value += new_data
                    self.text_field.update()
                else:
                    await asyncio.sleep(0.1)
