"""Native adapter; imports only its own adjacent prototype by absolute path."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py").resolve()
_name = "_visible_borders_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
predict = _prototype.predict
intermediate = _prototype.intermediate
