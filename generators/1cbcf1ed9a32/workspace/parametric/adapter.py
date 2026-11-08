"""Thin native adapter for the task-local common-pair member family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_1cbcf1ed9a32_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent common-pair prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)

OUTPUT_MODES = prototype.OUTPUT_MODES
HYPOTHESES = prototype.HYPOTHESES
STEP_A = prototype.STEP_A
INTERMEDIATE = prototype.INTERMEDIATE
STEP_B = prototype.STEP_B
WHY_DEPENDS = prototype.WHY_DEPENDS
canonical_program = prototype.canonical_program
program = prototype.program
generate = prototype.generate
solve = prototype.solve
analyze = prototype.analyze
certificate = prototype.certificate
public_turn = prototype.public_turn
causal_case = prototype.causal_case
counterfactual_program = prototype.counterfactual_program
