"""Native adapter; resolve the implementation from this exact adjacent path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_b28619e32f6f_parametric_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)
program = _impl.program
generate = _impl.generate
