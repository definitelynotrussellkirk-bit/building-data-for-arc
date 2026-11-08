"""Thin exact-path native adapter for the winner-width relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_dc0a7662670b_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(settings)


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    return _PROTOTYPE.generate_episode(seed, settings, demos, queries)


analyze = _PROTOTYPE.analyze
transform = _PROTOTYPE.transform
public_turn = _PROTOTYPE.public_turn
public_bytes = _PROTOTYPE.public_bytes
public_id = _PROTOTYPE.public_id
finite_rival_audit = _PROTOTYPE.finite_rival_audit
causal_witness = _PROTOTYPE.causal_witness
counterfactual_program = _PROTOTYPE.counterfactual_program
