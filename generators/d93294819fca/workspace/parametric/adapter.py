"""Native adapter; the adjacent prototype is the only implementation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_d93294819fca_gray_bridge", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
