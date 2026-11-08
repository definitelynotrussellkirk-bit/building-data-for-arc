"""Native adapter loading only the adjacent proposed block-sort family."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("blocksort_3108da8bf9e8_native", _path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent block-sort prototype")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos=demos, queries=queries)
