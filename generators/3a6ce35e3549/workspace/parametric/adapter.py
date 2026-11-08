"""Native adapter for the 3a6ce35e3549 interior-mask family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_3a6_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _mask(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {"mask"}
            or type(settings["mask"]) is not str):
        raise ValueError("settings must be exactly mask=blob|gaps")
    return family.setting(settings["mask"])


def program(settings: object) -> str:
    mask = _mask(settings)
    name = "canonical.rkt" if mask == "blob" else "gaps.rkt"
    return (BASE / name).read_text(encoding="utf-8")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    mask = _mask(settings)
    episode = family.generate(seed, mask, demos, queries)
    episode["program_solution"] = program({"mask": mask})
    return episode


def intermediate(grid: object) -> dict:
    return family.intermediate(grid)


def counterfactual_program() -> str:
    return (BASE / "wrong_shifted_bounds.rkt").read_text(encoding="utf-8")


def dependency() -> dict[str, str]:
    return {
        "step_a": "Identify the four minority-color markers and infer their input-dependent rectangle bounds.",
        "intermediate": "The strict interior crop defined by those marker bounds, together with its marker and majority colors.",
        "step_b": "Apply the episode mask to that inferred crop and recolor the selected interior cells with the marker color.",
        "why_b_depends_on_a": "The output dimensions and every sampled source coordinate come from the marker rectangle; choosing the mask alone cannot determine which cells are projected.",
    }
