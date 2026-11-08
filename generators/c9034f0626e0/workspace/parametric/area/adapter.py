"""Native API loaded by exact adjacent path, without a shared module-name cache."""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_spec = importlib.util.spec_from_file_location("_c9034f0626e0_native", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
