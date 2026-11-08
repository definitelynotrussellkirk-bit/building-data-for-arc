"""Native adapter for the d35dbdf1cfc2 motif-order prototype."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("motif_order.py")
_spec = importlib.util.spec_from_file_location("_d35dbdf1cfc2_motif_order", _path)
_prototype = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
