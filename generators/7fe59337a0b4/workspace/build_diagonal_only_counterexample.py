#!/usr/bin/env python3
"""Rebuild the retained cardinal-source counterexample for 7fe59337a0b4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
OUT = TASK_DIR / "counterexamples" / "diagonal_only_shortcut.json"

spec = importlib.util.spec_from_file_location("counterexample_7fe59337a0b4", GENERATOR_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

reproducer = {
    "seed": 7703,
    "sample_index": 0,
    "difficulty": "easy",
    "canvas_size": 9,
    "motif_color": 4,
    "scene_profile": "canonical_north_l3",
}
grid = gen.generate(**reproducer)
canonical = gen.rule_mirror(grid)
rival = gen.SEMANTIC_RIVALS["diagonal_source_only"](grid)
analysis = gen._analyze(grid)
assert analysis["source_sector"] == "north"
assert canonical != rival

record = {
    "schema": "7fe59337a0b4-counterexample-v1",
    "task_id": gen.TASK_ID,
    "generator_version": gen.VERSION,
    "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
    "baseline_generator_sha256": "7c720cc7d53b427d74f714533601bc5f9aaaf3362436b0aa7dc567aca2b657a2",
    "finding": (
        "Version 2 sampled only diagonal source sectors, so a shortcut that applies "
        "the true rotation rule only to diagonal sources fit every production sample "
        "while failing canonical north-aligned inputs. Version 3 schedules cardinal "
        "and diagonal sectors alternately."
    ),
    "rival": "diagonal_source_only",
    "reproducer": reproducer,
    "observed": gen.observe_overrides(grid),
    "source_sector": analysis["source_sector"],
    "input": grid,
    "canonical_output": canonical,
    "rival_output": rival,
}
OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUT)
