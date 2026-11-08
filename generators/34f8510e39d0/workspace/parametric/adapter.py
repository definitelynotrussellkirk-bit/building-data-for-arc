"""Native adapter for the 34f8510e39d0 green-rectangle scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_34f_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _scope(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"scope"} or type(settings["scope"]) is not str:
        raise ValueError("settings must be exactly scope=all_green|largest_only")
    return family.setting(settings["scope"])


def program(settings: object) -> str:
    scope = _scope(settings)
    name = "canonical.rkt" if scope == "all_green" else "largest_only.rkt"
    return (BASE / name).read_text(encoding="utf-8")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    scope = _scope(settings)
    episode = family.generate(seed, scope, demos, queries)
    episode["program_solution"] = program({"scope": scope})
    return episode


def intermediate(grid: object) -> dict:
    return family.intermediate(grid)


def counterfactual_program() -> str:
    return (BASE / "smallest_only.rkt").read_text(encoding="utf-8")


def dependency() -> dict[str, str]:
    return {
        "step_a": "Segment all solid green rectangles and derive their input-dependent areas and ranking.",
        "intermediate": "The rectangle bounding boxes and area ranking, including the uniquely largest green rectangle.",
        "step_b": "Select rectangles according to the episode scope and recolor exactly each selected bounding-box perimeter cyan.",
        "why_b_depends_on_a": "The cells recolored by the scope cannot be known from the setting alone; they depend on the rectangles and ranking discovered in the current input.",
    }
