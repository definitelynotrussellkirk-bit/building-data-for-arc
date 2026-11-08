"""Native promotion entry point, loaded from exact adjacent source paths."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("native.py")
_name = "_c9034_native_" + hashlib.sha256(str(_path).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _path)
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

MODES = core.MODES
program = core.program
generate = core.generate
public_challenge = core.public_challenge
