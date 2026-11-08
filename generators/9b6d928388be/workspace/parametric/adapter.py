"""Thin native adapter for assignment-basis episodes."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_9b6d928388be_parametric_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program(settings)


def generate(seed: int, settings: dict[str, Any], demos: int = 2, queries: int = 4):
    return _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)


def public_turn(episode, query_index=0):
    return _PROTOTYPE.public_turn(episode, query_index)


def counterfactual_program(settings, ablation="wrong_intermediate"):
    return _PROTOTYPE.counterfactual_program(settings, ablation)


def rival_programs():
    return _PROTOTYPE.rival_programs()
