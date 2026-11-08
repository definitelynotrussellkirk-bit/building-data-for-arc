"""Native adapter loaded by exact adjacent path; no cross-adapter module cache."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_f7c20cfd443f_halo_prototype", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

program = _module.program
generate = _module.generate
transform = _module.transform
dilate = _module.dilate
components = _module.components
validate_grid = _module.validate_grid
public_turn = _module.public_turn
teaching_check = _module.teaching_check
rival_names = _module.rival_names
rival_output = _module.rival_output
rival_program = _module.rival_program
