"""Native adapter for the adjacent proposed T-tally family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("tally_e971e0773705_native", _path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load the adjacent T-tally prototype")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=4, queries=4):
    return _prototype.generate(seed, settings, demos=demos, queries=queries)
