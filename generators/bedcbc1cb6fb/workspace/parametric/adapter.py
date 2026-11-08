"""Load this task's exact adjacent source without a generic module cache."""
from pathlib import Path
from types import ModuleType

_path = Path(__file__).with_name("prototype.py")
_module = ModuleType("_bedcbc1cb6fb_native_adapter_source")
_module.__file__ = str(_path)
exec(compile(_path.read_bytes(), str(_path), "exec"), _module.__dict__)
program = _module.program
generate = _module.generate
