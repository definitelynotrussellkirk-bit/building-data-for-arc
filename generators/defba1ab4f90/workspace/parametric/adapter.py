"""Native adapter; bind to this exact adjacent implementation, never sys.path."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name('prototype.py')
_spec = importlib.util.spec_from_file_location('_defba1ab4f90_stream_core', _path)
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)
program = core.program
generate = core.generate
