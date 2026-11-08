"""Native adapter for the true-hole versus largest-hole color-relay family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "_629ec8fd452e_parametric_prototype", HERE / "prototype.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load task-local parametric prototype")
PROTOTYPE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOTYPE
SPEC.loader.exec_module(PROTOTYPE)

CANONICAL_SHA256 = PROTOTYPE.CANONICAL_SHA256


def program(settings: dict[str, Any]) -> str:
    return PROTOTYPE.program_for(PROTOTYPE.validate_settings(settings))


def generate(
    seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4
) -> dict[str, Any]:
    mode = PROTOTYPE.validate_settings(settings)
    return PROTOTYPE.generate_episode(seed, mode, demos, queries)


transform = PROTOTYPE.transform
transform_skip_hole_analysis = PROTOTYPE.transform_skip_hole_analysis
teaching_check = PROTOTYPE.teaching_check
explain = PROTOTYPE.explain
public_challenge = PROTOTYPE.public_challenge
public_filename = PROTOTYPE.public_filename
public_bytes = PROTOTYPE.public_bytes
