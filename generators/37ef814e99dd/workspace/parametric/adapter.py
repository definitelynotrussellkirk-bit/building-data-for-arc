"""Native adapter for the 37ef814e99dd object-boundary scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_37ef_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _scope(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"scope"}
        or type(settings["scope"]) is not str
    ):
        raise ValueError("settings must be exactly scope=all_objects|largest_only")
    return family.setting(settings["scope"])


def program(settings: object) -> str:
    scope = _scope(settings)
    name = "canonical.rkt" if scope == "all_objects" else "largest_only.rkt"
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
        "step_a": "Segment the input into actual same-color cardinal objects and derive their input-dependent sizes.",
        "intermediate": "The object cell sets and their size ranking, including the uniquely largest component.",
        "step_b": "Select objects according to the episode scope and keep each selected object's true 4-neighbor boundary.",
        "why_b_depends_on_a": "The selected cells and their boundary neighborhoods come from the segmented input objects; the scope value alone cannot identify either the object or its outline.",
    }
