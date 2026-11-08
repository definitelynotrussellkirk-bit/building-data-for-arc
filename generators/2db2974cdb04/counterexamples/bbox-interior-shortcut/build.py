#!/usr/bin/env python3
"""Regenerate the task-local bbox shortcut counterexample from pinned controls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]

spec = importlib.util.spec_from_file_location("counterexample_generator", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

overrides = {
    "layout_profile": "canonical_10x12",
    "n_objects": 2,
    "shape_profile": "stemmed",
    "border_profile": "edge",
    "contact_profile": "touching",
}
grid = gen.generate(71, 1, difficulty="medium", **overrides)
expected = gen.rule_mirror(grid)
rival = gen.SEMANTIC_RIVALS["bbox_interior"](grid)
assert gen.self_check(grid) == []
assert expected != rival

for name, value in (
    ("input.json", grid),
    ("python-oracle.json", expected),
    ("bbox-rival.json", rival),
):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

metadata = {
    "task_id": gen.TASK_ID,
    "generator_version": gen.VERSION,
    "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
    "rule_hash": gen.RULE_HASH,
    "seed": 71,
    "sample_index": 1,
    "difficulty": "medium",
    "overrides": overrides,
    "self_check": [],
    "witness": "stemmed_bbox_counterexample",
    "rival": "bbox_interior",
    "difference_cells": [
        [r, c, expected[r][c], rival[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if expected[r][c] != rival[r][c]
    ],
    "generation_command": [
        "env", "PYTHONPATH=shared/runtime", "python3",
        "generators/2db2974cdb04/counterexamples/bbox-interior-shortcut/build.py",
    ],
    "racket_command": [
        "python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply",
        "2db2974cdb04", "--input",
        "generators/2db2974cdb04/counterexamples/bbox-interior-shortcut/input.json",
        "--out",
        "generators/2db2974cdb04/counterexamples/bbox-interior-shortcut/racket.json",
    ],
}
(HERE / "metadata.json").write_text(
    json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
