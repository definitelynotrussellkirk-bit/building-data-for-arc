"""Exact-path native adapter for the equality matrix component family."""
from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
_spec=spec_from_file_location('native_40e85135fbf8',Path(__file__).with_name('prototype.py'))
if _spec is None or _spec.loader is None:raise ImportError('task-local prototype unavailable')
_impl=module_from_spec(_spec);_spec.loader.exec_module(_impl)
program=_impl.program
generate=_impl.generate
