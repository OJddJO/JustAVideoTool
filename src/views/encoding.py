import flet as ft
from views.generic import GenericView, GenericContainer, ViewTitle, TextField, Label

@ft.control
class GeneralParams(GenericContainer):
    def __init__(self):
        super().__init__()
        self.audio_codec = ft.Dropdown(label="Audio codec", expand=True)
        self.audio_bitrate = TextField(value="96000", label="Audio bitrate", expand=True)
        self.audio_samplerate = TextField(value="48000", label="Audio sample rate", expand=True)
        self.audio_custom = TextField(label="Custom arguments for audio", expand=True)

        self.video_codec = ft.Dropdown(label="Video codec", expand=True)
        self.video_bitrate = TextField(value="3000k", label="Video bitrate", expand=True)
        self.__video_bitrate_settings = ft.Row([Label("Bitrate:"), self.video_bitrate])
        self.video_use_crf = ft.Switch(
            label=ft.Row([Label("Use CRF/CQ"), ft.Icon(ft.Icons.HELP_OUTLINE, size=18)]),
            label_position=ft.LabelPosition.LEFT,
            on_change=self.handle_use_crf,
            tooltip="Constant Rate Factor/Constant Quality use variable bitrate to have the same video quality on average"
        )
        self.video_crf = TextField(
            value="25",
            label="Constant Rate Factor/Constant Quality",
            expand=True
        )
        self.__video_crf_settings = ft.Row([Label("CRF/CQ:"), self.video_crf], visible=False)
        self.pixel_format = TextField(value="yuv420p10le", label="Pixel format", expand=True)
        self.preset = TextField(value="4", label="Encoder prest", expand=True)
        self.video_custom = TextField(label="Custom arguments for video", expand=True)

        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.content = ft.Column(
            [
                ft.Text("Audio settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    Label("Codec:"),
                    self.audio_codec,
                ]),
                ft.Row([
                    Label("Bitrate:"), self.audio_bitrate,
                    Label("Sample rate:"), self.audio_samplerate,
                ]),
                self.audio_custom,
                ft.Divider(),
                ft.Text("Video settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([Label("Codec:"), self.video_codec]),
                ft.Row([
                    ft.Stack([
                        self.__video_bitrate_settings,
                        self.__video_crf_settings
                    ], expand=True),
                    self.video_use_crf
                ], expand=True),
                ft.Row([ Label("Pixel format:"), self.pixel_format, Label("Preset:"), self.preset ]),
                self.video_custom
            ]
        )
        self.padding = 15
        self.expand = False

    def handle_use_crf(self, e: ft.Event[ft.Switch]):
        if e.control.value:
            self.__video_bitrate_settings.visible = False
            self.__video_crf_settings.visible = True
        else:
            self.__video_bitrate_settings.visible = True
            self.__video_crf_settings.visible = False

@ft.control
class EncodingView(GenericView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general_params = GeneralParams()
        self.content = ft.Column(
            [
                ViewTitle("Encoding"),
                self.general_params,
            ]
        )
