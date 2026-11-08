"""Native adapter for canonical gravity and a bottom-color relay variant."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
PROGRAMS = HOME / "programs"
_PROTOTYPE_PATH = HOME / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("_b5af3d6b3cd5_parametric_prototype", _PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)

CANONICAL_PROGRAM = (PROGRAMS / "canonical.rkt").read_text()
RELAY_PROGRAM = (PROGRAMS / "bottom_color_relay.rkt").read_text()
COUNTERFACTUAL_PROGRAM = (PROGRAMS / "raw_bottom_counterfactual.rkt").read_text()
_PROGRAMS = {"canonical": CANONICAL_PROGRAM, "bottom_color_relay": RELAY_PROGRAM}


def _mode(settings: dict) -> str:
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in _PROGRAMS:
        raise ValueError("unknown gravity mode")
    return mode


def program(settings: dict) -> str:
    return _PROGRAMS[_mode(settings)]


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    mode = _PROTOTYPE.validate_request(seed, settings, demos, queries)
    pairs = _PROTOTYPE.generate_pairs(seed, demos, queries, mode)
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
