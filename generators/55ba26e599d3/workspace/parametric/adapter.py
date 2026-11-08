"""Native adapter; import the adjacent implementation without module-cache aliasing."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_arc_55ba26e599d3_first_hit_prototype", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

program = _prototype.program
generate = _prototype.generate
solve_python = _prototype.solve_python
