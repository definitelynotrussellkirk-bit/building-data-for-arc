"""Exact-adjacent native adapter; safe under multiple adapters in one process."""
import importlib.util
from pathlib import Path
_path = Path(__file__).resolve().with_name('native.py')
_spec = importlib.util.spec_from_file_location('_native_cross_' + str(_path), _path)
_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_native)
program = _native.program
generate = _native.generate
