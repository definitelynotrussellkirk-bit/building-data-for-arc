"""Native adapter; load only this adjacent, source-bound prototype."""
import hashlib
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location(
    "_rectangle_components_" + hashlib.sha256(str(_path).encode()).hexdigest(), _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
solve = _prototype.solve
validate_input = _prototype.validate_input
components = _prototype.components
observables = _prototype.observables
teaching_report = _prototype.teaching_report
rival_output = _prototype.rival_output
rival_names = _prototype.RIVALS
public_challenge = _prototype.public_challenge
visible_turn = _prototype.visible_turn
