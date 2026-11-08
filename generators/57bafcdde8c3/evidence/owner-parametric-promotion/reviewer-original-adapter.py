"""Thin proposed adapter; acceptance requires the separate protected owner route."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name('components.py')
_spec = importlib.util.spec_from_file_location('_task_57bafcdde8c3_components', _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
