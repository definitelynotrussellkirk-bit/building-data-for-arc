"""Thin native adapter; load the exact adjacent reviewed family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("_native_overlay_0ae119475d57", _path)
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
