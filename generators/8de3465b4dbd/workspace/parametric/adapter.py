"""Load the native family from its own adjacent path, never another task."""
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
_spec=spec_from_file_location('native_8de3465b4dbd_adapter',Path(__file__).with_name('native.py'))
_native=module_from_spec(_spec)
_spec.loader.exec_module(_native)
program=_native.program
generate=_native.generate
