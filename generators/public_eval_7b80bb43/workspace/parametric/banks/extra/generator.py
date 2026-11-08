"""Registered entry point; the standalone native folder owns the implementation."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_7b80bb43'
TASK_ID = GENERATOR_ID = 'public_eval_7b80bb43'
_spec = importlib.util.spec_from_file_location('_7b80bb43_generator_impl', Path(__file__).resolve().parent/'workspace/parametric/family.py')
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)
VERSION = _impl.VERSION
SUMMARY = _impl.SUMMARY
validate_grid = _impl.validate_grid
stages = _impl.stages
solve = _impl.solve
generate = _impl.generate
self_check = _impl.self_check
