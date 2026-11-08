"""Native promotion adapter for the 8b6a2892a064 rotation-scope family."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_native_8b6a2892a064_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
model_view = _IMPL.model_view
visible_turn = _IMPL.visible_turn
analyze = _IMPL.analyze
transform = _IMPL.transform
teaching_check = _IMPL.teaching_check
counterfactual_program = _IMPL.counterfactual_program
