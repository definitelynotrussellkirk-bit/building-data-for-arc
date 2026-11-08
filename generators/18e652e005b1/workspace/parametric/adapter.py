"""Source-bound adapter for the 18e652e005b1 native family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_18e652e005b1_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent 18e652e005b1 family")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
_SPEC.loader.exec_module(family)

program = family.program
generate = family.generate


def dependency(settings):
    layout = family._setting(settings)
    if layout == "gapped":
        return {"steps": ["crop motif and broadcast gapped recolored copies"]}
    return {
        "steps": [
            "crop motif and place command-recolored copies at width-minus-one stride",
            "derive contributor multiplicity for every output cell",
            "recolor true multi-copy intersections to 8",
        ],
        "intermediate_required": True,
    }


def counterfactual_program(settings):
    family._setting(settings)
    return family.counterfactual_program()


def intermediate(grid, settings):
    family._setting(settings)
    return family.analyze(grid)["contributors"]
