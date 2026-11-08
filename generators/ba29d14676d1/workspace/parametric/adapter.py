"""Native adapter for all-tile versus densest-tile reflection."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("ba29_parametric_prototype", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def program(settings):
    return prototype.program(settings)


def generate(seed, settings, demos, queries):
    values = prototype.validate_settings(settings)
    return prototype.generate_episode(seed, tile_scope=values["tile_scope"], demos=demos, queries=queries)


analyze = prototype.analyze
apply_mode = prototype.apply_mode
public_turn = prototype.public_turn
public_bytes = prototype.public_bytes
public_id = prototype.public_id
causal_case = prototype.causal_case
counterfactual_program = prototype.counterfactual_program
