"""Exact adjacent adapter for the native 156bae9e7b79 family."""
import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("native_family.py")
_SPEC = importlib.util.spec_from_file_location("native_family_156bae9e7b79", _PATH)
_NATIVE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_NATIVE)
program = _NATIVE.program
generate = _NATIVE.generate
