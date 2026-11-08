"""Thin task-local adapter; protected qualification checks all claimed labels."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_room_marker_36b22ff07a2e", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
