import flet as ft
import json
from views.generic import GenericView, GenericContainer, ViewTitle, TextField, Label

@ft.control
class EncodingView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_picker = ft.FilePicker()

        self.output_extension = TextField(value="mkv", label="Container extension", expand=True, margin=ft.Margin(top=5))

        self.video_codec = TextField(value="libsvtav1", label="Video codec", expand=True)
        self.video_bitrate = TextField(value="3000k", label="Video bitrate", expand=True)
        self.__video_bitrate_settings = ft.Row([Label("Bitrate"), self.video_bitrate])
        self.video_use_crf = ft.Switch(
            label=ft.Row([Label("Use CRF/CQ"), ft.Icon(ft.Icons.HELP_OUTLINE, size=18)]),
            label_position=ft.LabelPosition.LEFT,
            on_change=self.handle_use_crf,
            tooltip="Constant Rate Factor/Constant Quality is an intelligent encoding mode that automatically adjusts bitrate frame-by-frame\nto maintain a constant, unvarying level of visual quality throughout the entire video"
        )
        self.video_crf = TextField(
            value="25",
            label="Constant Rate Factor/Constant Quality",
            expand=True
        )
        self.__video_crf_settings = ft.Row([Label("CRF/CQ"), self.video_crf], visible=False)
        self.video_pixel_format = TextField(value="yuv420p10le", label="Pixel format", expand=True)
        self.video_preset = TextField(value="4", label="Encoder preset", expand=True)
        self.video_custom = TextField(label="Custom arguments for video", expand=True)

        self.audio_codec = TextField(value="libopus", label="Audio codec", expand=True)
        self.audio_bitrate = TextField(value="96000", label="Audio bitrate", expand=True)
        self.audio_samplerate = TextField(value="48000", label="Audio sample rate", expand=True)
        self.audio_filter = TextField(value="aresample=async=1:first_pts=0", label="Audio Filter", expand=True)
        self.audio_custom = TextField(label="Custom arguments for audio", expand=True)

        self.subtitle_codec = TextField(value="ass", label="Sutitle codec", expand=True)
        self.subtitle_custom = TextField(label="Custom arguments for subtitles", expand=True)

        self.content = ft.Column(
            [
                ViewTitle("Encoding"),
                GenericContainer(
                    content=ft.Column(
                        [
                            ft.Row([ Label("Outputs extension"), self.output_extension ]),
                            ft.Divider(),
                            ft.Text("Video settings", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([Label("Codec"), self.video_codec]),
                            ft.Row([
                                ft.Stack([
                                    self.__video_bitrate_settings,
                                    self.__video_crf_settings
                                ], expand=True),
                                ft.Divider(),
                                self.video_use_crf
                            ], expand=True),
                            ft.Row([ Label("Pixel format"), self.video_pixel_format, ft.VerticalDivider() , Label("Preset"), self.video_preset ]),
                            self.video_custom,
                            ft.Divider(),
                            ft.Text("Audio settings", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([ Label("Codec"), self.audio_codec ]),
                            ft.Row([ Label("Bitrate"), self.audio_bitrate, ft.VerticalDivider(), Label("Sample rate"), self.audio_samplerate ]),
                            ft.Row([ Label("Filter"), self.audio_filter ]),
                            self.audio_custom,
                            ft.Divider(),
                            ft.Text("Sutitle settings", size=20, weight=ft.FontWeight.BOLD),
                            ft.Row([ Label("Codec"), self.subtitle_codec ]),
                            self.subtitle_custom
                        ],
                        scroll=ft.ScrollMode.ADAPTIVE,
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    expand=True,
                    padding=15
                ),
                ft.Row([
                    ft.Button("Load parameters", icon=ft.Icons.FILE_OPEN_OUTLINED, on_click=self.load_params),
                    ft.Button("Save parameters", icon=ft.Icons.SAVE_OUTLINED, on_click=self.save_params)
                ], alignment=ft.MainAxisAlignment.END)
            ]
        )

    def handle_use_crf(self, e: ft.Event[ft.Switch]):
        if e.control.value:
            self.__video_bitrate_settings.visible = False
            self.__video_crf_settings.visible = True
        else:
            self.__video_bitrate_settings.visible = True
            self.__video_crf_settings.visible = False

    def get_params(self):
        return {
            "ext": self.output_extension.value,
            "audio": {
                "codec": self.audio_codec.value,
                "bitrate": self.audio_bitrate.value,
                "samplerate": self.audio_samplerate.value,
                "filter": self.audio_filter.value,
                "custom": self.audio_custom.value
            },
            "video": {
                "codec": self.video_codec.value,
                "use_crf": self.video_use_crf.value,
                "bitrate": self.video_bitrate.value,
                "crf": self.video_crf.value,
                "pix_fmt": self.video_pixel_format.value,
                "preset": self.video_preset.value,
                "custom": self.video_custom.value
            },
            "subtitle": {
                "codec": self.subtitle_codec.value,
                "custom": self.subtitle_custom.value
            }
        }

    async def load_params(self, e: ft.Event[ft.Button]):
        files = await self.file_picker.pick_files(
            "Open encoding settings",
            allowed_extensions=["javt_param"],
            allow_multiple=False
        )
        if not files:
            return  # User cancelled

        file_path = files[0].path
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                params = json.load(f)
        except:
            return

        self.output_extension.value = params.get("ext", "")
        audio = params.get("audio", {})
        self.audio_codec.value = audio.get("codec", "")
        self.audio_bitrate.value = audio.get("bitrate", "")
        self.audio_samplerate.value = audio.get("samplerate", "")
        self.audio_filter.value = audio.get("filter", "")
        self.audio_custom.value = audio.get("custom", "")

        video = params.get("video", {})
        self.video_codec.value = video.get("codec", "")
        self.video_use_crf.value = video.get("use_crf", False)
        self.video_bitrate.value = video.get("bitrate", "")
        self.video_crf.value = video.get("crf", "")
        self.video_pixel_format.value = video.get("pix_fmt", "")
        self.video_preset.value = video.get("preset", "")
        self.video_custom.value = video.get("custom", "")

        subtitle = params.get("subtitle", {})
        self.subtitle_codec.value = subtitle.get("codec", "")
        self.subtitle_custom.value = subtitle.get("custom", "")

        self.handle_use_crf(ft.Event("handler", control=self.video_use_crf))

    async def save_params(self, e: ft.Event[ft.Button]):
        data = self.get_params()
        json_str = json.dumps(data, indent=2)
        await self.file_picker.save_file(
            "Save as",
            file_name="encoding_settings.javt_param",
            initial_directory=".",
            allowed_extensions=["javt_param"],
            src_bytes=json_str.encode("utf-8")
        )
