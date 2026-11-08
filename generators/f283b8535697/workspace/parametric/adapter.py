"""Native adapter; load the adjacent implementation without global-name imports."""
from pathlib import Path
import importlib.util

_source = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_f283b8535697_parametric", _source)
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)


def program(settings):
    return core.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return core.generate(seed, settings, demos, queries)
