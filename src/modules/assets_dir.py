from pathlib import Path
import os

__all__ = [
    "assets_dir"
]

assets_dir = Path(os.environ.get("FLET_ASSETS_DIR", str(Path(__file__).parent / "assets"))).resolve()
