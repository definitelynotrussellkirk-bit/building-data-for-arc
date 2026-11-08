"""Native adapter; the exact adjacent prototype owns sampling and semantics."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_area_scale_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)

program = prototype.program
generate = prototype.generate
