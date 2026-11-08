#!/usr/bin/env python3
"""Read-only, source-bound audit probe for generator 0e32de8e7717."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2] / "repo"
TASK_ID = "0e32de8e7717"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def digest(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def one_step(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    for r in range(len(source) - 1):
        for c in range(len(source[0]) - 1):
            coords = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            values = [source[rr][cc] for rr, cc in coords]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and values.count(0) == 1:
                index = values.index(0)
                rr, cc = coords[index]
                out[rr][cc] = nonzero[0]
    return out


def closure(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    out = [list(row) for row in grid]
    for _ in range(len(out) * len(out[0])):
        new = one_step(out)
        if new == out:
            return out
        out = new
    raise RuntimeError("closure did not stabilize")


seed = 1729
sample_index = 3
baseline = mod.generate(seed, sample_index, difficulty="medium")
comparisons = {}
axis_pairs = {
    "palette_kind": ("warm", "cool"),
    "n_shapes": (1, 4),
    "palette_size": (1, 4),
    "n_distinct_colors": (1, 4),
    "texture_helpful": ("warm", "varied"),
}
for label, (a, b) in axis_pairs.items():
    key = "texture" if label == "texture_helpful" else label
    first = mod.generate(seed, sample_index, difficulty="medium", **{key: a})
    second = mod.generate(seed, sample_index, difficulty="medium", **{key: b})
    comparisons[label] = {
        "requests": [a, b],
        "identical": first == second,
        "sha256": [digest(first), digest(second)],
        "fillable_windows": [len(mod._fillable_windows(first)), len(mod._fillable_windows(second))],
    }

unknown = mod.generate(seed, sample_index, difficulty="medium", nonexistent_axis="ignored")
requested_one = mod.generate(seed, sample_index, difficulty="medium", n_shapes=1)

degenerate_request = {"texture": "no_l", "grid_h": 5, "grid_w": 6}
degenerate = mod.generate(seed, sample_index, difficulty="medium", **degenerate_request)

hard_five = None
for probe_seed in range(500):
    for index in range(12):
        candidate = mod.generate(probe_seed, index, difficulty="hard")
        count = len(mod._fillable_windows(candidate))
        if count == 5:
            hard_five = {
                "seed": probe_seed,
                "sample_index": index,
                "shape": [len(candidate), len(candidate[0])],
                "fillable_windows": count,
                "grid": candidate,
            }
            break
    if hard_five:
        break

one_pass_equivalence = {band: {"checked": 0, "equal": 0} for band in ("easy", "medium", "hard")}
for band in one_pass_equivalence:
    for probe_seed in range(20):
        for index in range(6):
            grid = mod.generate(probe_seed, index, difficulty=band)
            one_pass_equivalence[band]["checked"] += 1
            one_pass_equivalence[band]["equal"] += int(one_step(grid) == closure(grid))

chain_counterexample = [
    [1, 1, 0, 0, 0, 0],
    [1, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]
chain_one = one_step(chain_counterexample)
chain_closed = closure(chain_counterexample)

report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "version": mod.VERSION,
    "baseline_sha256": digest(baseline),
    "dead_axis_comparisons": comparisons,
    "unknown_override": {
        "accepted": True,
        "identical_to_baseline": unknown == baseline,
        "sha256": digest(unknown),
    },
    "n_shapes_one_request": {
        "requested": 1,
        "realized_fillable_windows": len(mod._fillable_windows(requested_one)),
        "self_check_with_meta": mod.self_check(
            requested_one,
            difficulty="medium",
            meta={"overrides": {"n_shapes": 1}},
        ),
    },
    "degenerate_override": {
        "request": degenerate_request,
        "realized_shape": [len(degenerate), len(degenerate[0])],
        "fillable_windows": len(mod._fillable_windows(degenerate)),
        "self_check_errors": mod.self_check(
            degenerate,
            difficulty="medium",
            meta={"overrides": degenerate_request},
        ),
    },
    "hard_axis_range_conflict": {
        "declared_n_shapes_valid": mod.AXES["n_shapes"]["valid"],
        "five_shape_witness": hard_five,
    },
    "iterative_shortcut": {
        "generated_one_pass_equals_closure": one_pass_equivalence,
        "counterexample_input": chain_counterexample,
        "one_pass_output": chain_one,
        "closure_output": chain_closed,
        "outputs_differ": chain_one != chain_closed,
    },
}

out = Path(__file__).with_name("0e32de8e7717_probe.json")
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
