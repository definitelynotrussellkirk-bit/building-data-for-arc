"""Native promotion entrypoint; load the exact adjacent implementation."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_name = "_b98cdd1751a7_native_" + hashlib.sha256(str(_path).encode()).hexdigest()[:12]
_spec = importlib.util.spec_from_file_location(_name, _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)


def program(settings):
    return _native.program(settings)


def generate(seed, settings, demos, queries):
    return _native.generate(seed, settings, demos, queries)
