"""Native adapter for the separate enclosed-area family."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().parent / "native_family.py"
if _path.is_symlink() or _path.resolve().parent != Path(__file__).resolve().parent:
    raise ValueError("Native family must be a regular adjacent source")
_data = _path.read_bytes()
_name = "_hole_family_" + hashlib.sha256(str(_path).encode() + _data).hexdigest()
if _name not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = _module
    try:
        exec(compile(_data, str(_path), "exec"), _module.__dict__)
    except BaseException:
        sys.modules.pop(_name, None)
        raise
_family = sys.modules[_name]
program = _family.program
generate = _family.generate
