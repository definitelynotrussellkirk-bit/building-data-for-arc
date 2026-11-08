"""Exact-path native adapter; no cross-task cached imports."""
import importlib.util
from pathlib import Path
_path=Path(__file__).resolve().with_name('prototype.py')
_spec=importlib.util.spec_from_file_location('completion_gain_'+str(_path),_path)
_impl=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_impl)
program=_impl.program
generate=_impl.generate
predict=_impl.predict
public_view=_impl.public_view
intermediate=_impl.intermediate
