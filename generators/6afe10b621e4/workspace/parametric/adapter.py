"""Native adapter, loaded only from the exact adjacent prototype source."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("parametric_6afe10b621e4", Path(__file__).with_name("prototype.py"))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
