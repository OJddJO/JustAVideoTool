import os
__arch = os.environ.get("APP_TARGET_ARCH")

match __arch:
    case "TRT-RTX":
        from .tensorRT_RTX import *
    case "TRT":
        from .tensorRT import *
    case _:
        print("Device architecture not found !")

from .bilinear import Bilinear
from .bicubic import Bicubic
from .interarea import InterArea
from .lanczos import Lanczos
