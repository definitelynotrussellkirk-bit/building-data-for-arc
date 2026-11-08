"""Native adapter for the ca81880afbf3 square-hole relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_ca81880afbf3_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _finish_rule(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {"finish_rule"}
            or type(settings["finish_rule"]) is not str):
        raise ValueError("settings must be exactly finish_rule=fill_only|bridge_equal_area")
    return family.setting(settings["finish_rule"])


def program(settings: object) -> str:
    mode = _finish_rule(settings)
    name = "canonical.rkt" if mode == "fill_only" else "bridge_equal_area.rkt"
    return (BASE / name).read_text(encoding="utf-8")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    mode = _finish_rule(settings)
    episode = family.generate(seed, mode, demos, queries)
    episode["program_solution"] = program({"finish_rule": mode})
    return episode


def intermediate(grid: object) -> dict:
    return family.intermediate(grid)


def counterfactual_program() -> str:
    return (BASE / "wrong_shifted_centers.rkt").read_text(encoding="utf-8")


def dependency() -> dict[str, str]:
    return {
        "step_a": "Apply the canonical rule: identify color-5 components whose bbox-interior zero cells form a filled square and paint those cells color 2.",
        "intermediate": "The connected color-2 components produced by step A, including each component's area and derived center.",
        "step_b": "For every aligned pair of derived components with equal area, paint the inclusive center-to-center segment color 4.",
        "why_b_depends_on_a": "The relay endpoints and equality test are computed from step A's color-2 components; shifting those derived centers preserves the fills but moves every relay and changes the final grid.",
    }
