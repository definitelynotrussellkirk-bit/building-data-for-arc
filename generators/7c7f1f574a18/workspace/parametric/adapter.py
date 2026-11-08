"""Native adapter: load only the prototype adjacent to these exact bytes."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib
import sys

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_hole_area_prototype_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = spec_from_file_location(_name, _path)
_prototype = module_from_spec(_spec)
sys.modules[_name] = _prototype
# Execute the current bytes even if a same-size, same-timestamp .pyc exists.
# Qualification binds source content, so cached predecessor code is unsuitable.
exec(compile(_path.read_bytes(), str(_path), "exec"), _prototype.__dict__)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)
