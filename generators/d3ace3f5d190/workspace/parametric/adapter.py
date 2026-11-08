"""Native adapter for the d3ace3f5d190 axis-selection family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_d3a_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"axis_rule"} or type(settings["axis_rule"]) is not str:
        raise ValueError("settings must be exactly axis_rule=main|anchor_selected")
    return family.setting(settings["axis_rule"])


def program(settings: object) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "main" else "anchor_selected.rkt"
    return (BASE / name).read_text(encoding="utf-8")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    mode = _mode(settings)
    episode = family.generate(seed, mode, demos, queries)
    episode["program_solution"] = program({"axis_rule": mode})
    return episode


def intermediate(grid: object) -> dict:
    return family.intermediate(grid)


def counterfactual_program() -> str:
    return (BASE / "always_anti.rkt").read_text(encoding="utf-8")


def dependency() -> dict[str, str]:
    return {
        "step_a": "Locate the unique color-8 corner anchor and infer whether it lies on the main or anti diagonal.",
        "intermediate": "The anchor coordinates and the input-dependent selected axis (main or anti).",
        "step_b": "Mirror all nonzero cells through the selected axis, with reflected nonzero values replacing counterparts.",
        "why_b_depends_on_a": "Under anchor_selected, the reflected coordinate used for every output cell changes with the corner anchor found in the current input.",
    }
