"""Native promotion adapter; load only the implementation next to this file."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_name = "_be5d9fa6fec1_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
solve = _prototype.solve
run_table = _prototype.run_table
selected_runs = _prototype.selected_runs
visible_turn = _prototype.visible_turn
teaching_report = _prototype.teaching_report
rival_output = _prototype.rival_output
rival_names = _prototype.rival_names
write_batch = _prototype.write_batch
