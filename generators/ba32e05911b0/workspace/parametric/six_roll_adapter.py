"""Native adapter; exact adjacent loading prevents cross-task module reuse."""
import importlib.util
from pathlib import Path
_path = Path(__file__).resolve().with_name('prototype.py')
_spec = importlib.util.spec_from_file_location('_rolling_ba32e05911b0', _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
