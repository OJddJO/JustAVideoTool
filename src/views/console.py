import flet as ft
import os
import asyncio
from views.generic import GenericView

class ConsoleView(GenericView):
    def __init__(self, log_file: str):
        super().__init__()
        self.log_file = log_file
        self.running = False

        self.text_field = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
            border_color=ft.Colors.TRANSPARENT
        )
        self.content = ft.Column([
            ft.Text("Console", size=24, weight=ft.FontWeight.BOLD),
            self.text_field
        ])

    def did_mount(self):
        self.running = True
        self.page.run_task(self.tail_log)

    def will_unmount(self):
        self.running = False

    async def tail_log(self):
        while not os.path.exists(self.log_file) and self.running:
            await asyncio.sleep(0.5)

        if not self.running:
            return

        with open(self.log_file, "r") as f:
            self.text_field.value = f.read()
            self.text_field.update()

            # 2. Continuously loop and grab new data added to the file
            while self.running:
                new_data = f.read()
                if new_data:
                    self.text_field.value += new_data
                    self.text_field.update()
                else:
                    # Briefly pause so we don't max out the CPU while waiting for logs
                    await asyncio.sleep(0.1)
