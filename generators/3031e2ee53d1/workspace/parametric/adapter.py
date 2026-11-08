"""Native interface, loading only the exact adjacent prototype."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_3031_edge_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)
