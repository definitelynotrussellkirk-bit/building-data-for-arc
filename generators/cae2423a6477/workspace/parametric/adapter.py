"""Exact-path adapter for the task-local native selected-barrier family."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("cae2423a6477_native", Path(__file__).with_name("prototype.py"))
if _spec is None or _spec.loader is None:
    raise ImportError("task-local prototype unavailable")
_impl = module_from_spec(_spec)
_spec.loader.exec_module(_impl)
program = _impl.program
generate = _impl.generate
