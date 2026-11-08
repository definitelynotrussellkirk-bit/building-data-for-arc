"""Exact-path adapter; never reuses another task's cached prototype module."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
_spec = spec_from_file_location('ada76e18c19c_native_prototype', Path(__file__).with_name('prototype.py'))
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
program = _module.program
generate = _module.generate
