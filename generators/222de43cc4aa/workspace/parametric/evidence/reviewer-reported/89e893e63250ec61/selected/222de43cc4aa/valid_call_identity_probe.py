#!/usr/bin/env python3
"""Bounded compatibility probe for task 222de43cc4aa.

Loads the immutable packet baseline and the current generator as separate modules,
then compares 114 representative lawful generate() calls byte-for-byte.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK_ID = "222de43cc4aa"
BASELINE = WORK / ".review" / "baseline" / "repo" / "generators" / TASK_ID / "generator.py"
CURRENT = REPO / "generators" / TASK_ID / "generator.py"
OUT = Path(__file__).with_name("valid-call-identity.json")

for path in (REPO / "shared" / "runtime", REPO / "src"):
    sys.path.insert(0, str(path))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


before = load("baseline_222de43cc4aa", BASELINE)
after = load("current_222de43cc4aa", CURRENT)

calls: list[dict] = []
for difficulty in (None, "easy", "medium", "hard"):
    call = {"difficulty": difficulty}
    if difficulty is None:
        call["texture"] = None  # cover the explicit nullable declared override
    calls.append(call)
for texture in after.HELPFUL_TEXTURES + after.DEGENERATE_TEXTURES:
    calls.append({"difficulty": "medium", "texture": texture})
for axis, value in (
    ("grid_h", 3), ("grid_h", 8),
    ("grid_w", 9), ("grid_w", 21),
    ("n_fg_colors", 1), ("n_fg_colors", 2),
):
    calls.append({"difficulty": "hard", axis: value})
calls.extend([
    {"difficulty": "easy", "grid_h": 3, "grid_w": 9, "n_fg_colors": 1, "texture": "lattice"},
    {"difficulty": "hard", "grid_h": 8, "grid_w": 21, "n_fg_colors": 2, "texture": "clusters"},
    {"difficulty": "medium", "grid_h": 5, "grid_w": 17, "n_fg_colors": 1, "texture": "tight_rows"},
])
assert len(calls) == 19

mismatches = []
case_count = 0
for seed in range(6):
    for index, kwargs in enumerate(calls):
        case_count += 1
        sample_index = 100 + index
        left = before.generate(seed, sample_index, **kwargs)
        right = after.generate(seed, sample_index, **kwargs)
        if canonical_bytes(left) != canonical_bytes(right):
            mismatches.append({
                "seed": seed,
                "sample_index": sample_index,
                "kwargs": kwargs,
                "before_sha256": hashlib.sha256(canonical_bytes(left)).hexdigest(),
                "after_sha256": hashlib.sha256(canonical_bytes(right)).hexdigest(),
            })

result = {
    "schema": "valid-call-byte-identity-v1",
    "task_id": TASK_ID,
    "cases": case_count,
    "mismatches": len(mismatches),
    "mismatch_examples": mismatches[:5],
    "original_sha256": hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
    "modified_sha256": hashlib.sha256(CURRENT.read_bytes()).hexdigest(),
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(1 if mismatches else 0)
