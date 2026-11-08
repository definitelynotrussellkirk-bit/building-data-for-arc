"""Thin adapter loading the exact adjacent proposed implementation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_lookup_depth_native", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
