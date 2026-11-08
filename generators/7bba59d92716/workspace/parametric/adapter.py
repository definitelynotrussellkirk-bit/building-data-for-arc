"""Native promotion entry points, loaded from this exact task-local source."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_marker_size_native_prototype", Path(__file__).with_name("prototype.py")
)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
