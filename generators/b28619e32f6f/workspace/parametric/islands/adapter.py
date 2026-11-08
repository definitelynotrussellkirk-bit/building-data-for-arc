"""Native adapter; load only the adjacent, source-bound implementation."""
from pathlib import Path
import importlib.util

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_b28619e32f6f_islands", _path)
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)

program = prototype.program
generate = prototype.generate
