#!/usr/bin/env python3
"""Reproduce the strongest canonical-fitting shortcut counterexample."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("counterexample_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

input_grid = json.loads((HERE / "input.json").read_text())["input"]
authority = json.loads((HERE / "racket-output.json").read_text())
official = authority["results"][0]["output"]
rival = GEN.SEMANTIC_RIVALS["any_nonbackground_header_activates"](input_grid)
assert GEN._mirror(input_grid) == official
assert rival != official
assert official[1][1] == 5
assert official[1][2] == official[2][1] == official[2][2] == 0
assert rival[1][1] == rival[1][2] == rival[2][1] == rival[2][2] == 5

emitted = []
for texture in ("wrong_marker", "body_content", "corner_var"):
    grid = GEN.generate(871, 5, difficulty="hard", texture=texture)
    emitted.append(
        {
            "texture": texture,
            "wrong_header_witness": GEN.SEMANTIC_WITNESSES[
                "wrong_header_colors_are_inactive"
            ](grid),
            "rival_disagrees": GEN.SEMANTIC_RIVALS[
                "any_nonbackground_header_activates"
            ](grid)
            != GEN._mirror(grid),
        }
    )
assert all(row["wrong_header_witness"] and row["rival_disagrees"] for row in emitted)
print(json.dumps({"official": official, "rival": rival, "emitted": emitted}, indent=2))
