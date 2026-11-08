"""Source-bound adapter for the f98b43c1996b native family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_f98b43c1996b_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent f98b43c1996b family")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = family
_SPEC.loader.exec_module(family)

program = family.program
generate = family.generate


def dependency(settings):
    finish = family._setting(settings)
    if finish == "diagonalize_only":
        return {"steps": ["diagonalize exact monochrome 2x2 blocks"]}
    return {
        "steps": [
            "diagonalize exact monochrome 2x2 blocks",
            "count colors on the transformed intermediate",
            "recolor the unique most frequent surviving color to 8",
        ],
        "intermediate_required": True,
    }


def counterfactual_program(settings):
    family._setting(settings)
    return family.counterfactual_program()


def intermediate(grid, settings):
    family._setting(settings)
    return family.diagonalize(grid)
