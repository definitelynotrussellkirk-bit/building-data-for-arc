"""Native entry point; load only the exact adjacent task-local implementation."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("fb7f02aa9ab0_parametric_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
exec(compile(_path.read_bytes(), str(_path), "exec"), _impl.__dict__)
program = _impl.program
generate = _impl.generate
