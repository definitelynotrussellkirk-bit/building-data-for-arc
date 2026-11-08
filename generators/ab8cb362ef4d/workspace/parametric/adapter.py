"""Native promotion adapter loading only the adjacent family."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_ab8_landed_cluster_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve = _MODULE.solve
teaching_check = _MODULE.teaching_check
public_turn = _MODULE.public_turn
dependency_trace = _MODULE.dependency_trace
wrong_order_solve = _MODULE.wrong_order_solve
rival_outputs = _MODULE.rival_outputs
sample_input = _MODULE.sample_input
