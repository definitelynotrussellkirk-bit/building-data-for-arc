"""Native adapter for the beb87e1c1b19 transform-composition family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_name = "_family_beb87e1c1b19_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def _composition(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {"composition"}
            or type(settings["composition"]) is not str):
        raise ValueError("settings must be exactly composition=union|xor")
    return family.setting(settings["composition"])


def program(settings: object) -> str:
    mode = _composition(settings)
    name = "canonical.rkt" if mode == "union" else "xor.rkt"
    return (BASE / name).read_text(encoding="utf-8")


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    mode = _composition(settings)
    episode = family.generate(seed, mode, demos, queries)
    episode["program_solution"] = program({"composition": mode})
    return episode


def intermediate(grid: object) -> dict:
    return family.intermediate(grid)


def counterfactual_program() -> str:
    return (BASE / "wrong_identity_intermediate.rkt").read_text(encoding="utf-8")


def dependency() -> dict[str, str]:
    return {
        "step_a": "Infer the unique dihedral transform that maps panel A's support to panel B's support, then apply it to panel C.",
        "intermediate": "The input-dependent transformed copy T(C), with the same dimensions and color values as panel C.",
        "step_b": "Compose original C with T(C) using the episode-fixed union or symmetric-difference rule.",
        "why_b_depends_on_a": "Stage B needs the occupancy of T(C) at every output cell; replacing it with C itself erases every XOR output and changes union whenever C is asymmetric.",
    }
