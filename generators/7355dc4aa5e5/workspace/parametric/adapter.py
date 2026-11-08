"""Native adapter reusing the retained radius prototype via the adjacent family."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_7355_native_family", Path(__file__).with_name("family.py"))
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
program = _family.program
generate = _family.generate
