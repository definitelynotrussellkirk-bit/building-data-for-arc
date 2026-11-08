"""Native adapter; import the exact adjacent prototype without module-cache reuse."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("f47990415137_parametric_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)
