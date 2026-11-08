"""Public-parent entry point delegating to the independently usable native home."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_7b5033c1'
TASK_ID = GENERATOR_ID = 'public_eval_7b5033c1'
_spec = importlib.util.spec_from_file_location('_7b5033c1_entry_family', Path(__file__).resolve().parent/'workspace/parametric/family.py')
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)
VERSION = _family.VERSION
SUMMARY = _family.SUMMARY
validate_grid = _family.validate_grid
trace = _family.trace
stages = _family.stages
solve = _family.solve
generate = _family.generate
self_check = _family.self_check
