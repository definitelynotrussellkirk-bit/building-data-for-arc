"""Native parametric adapter for 69dbf44065e2."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_PROTO_PATH = _HOME / "prototype.py"
_PROTO_NAME = "_arc69dbf44065e2_prototype_" + hashlib.sha256(str(_PROTO_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_PROTO_NAME, _PROTO_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PROTO_PATH}")
_PROTO = importlib.util.module_from_spec(_SPEC)
sys.modules[_PROTO_NAME] = _PROTO
_SPEC.loader.exec_module(_PROTO)

_PROGRAM_FILES = {
    "none": "canonical.rkt",
    "left": "turn-left.rkt",
    "right": "turn-right.rkt",
}
_PROGRAMS = {name: (_HOME / filename).read_text(encoding="utf-8") for name, filename in _PROGRAM_FILES.items()}


def _turn(settings) -> str:
    if type(settings) is not dict or set(settings) != {"turn"}:
        raise ValueError("settings must contain exactly the key 'turn'")
    return _PROTO.validate_turn(settings["turn"])


def program(settings):
    return _PROGRAMS[_turn(settings)]


def generate(seed, settings, demos, queries):
    turn = _turn(settings)
    episode = _PROTO.generate_episode(seed, turn, demos, queries)
    return {**episode, "program_solution": _PROGRAMS[turn]}


# Public test/audit helpers.  Qualification consumes only program/generate.
solve = _PROTO.solve
skip_stage_a = _PROTO.skip_stage_a
wrong_order = _PROTO.wrong_order
dependency_facts = _PROTO.dependency_facts
make_scene = _PROTO.make_scene
validate_grid = _PROTO.validate_grid
