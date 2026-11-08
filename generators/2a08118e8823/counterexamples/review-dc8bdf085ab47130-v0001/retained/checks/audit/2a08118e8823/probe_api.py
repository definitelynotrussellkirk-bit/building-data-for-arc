from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "2a08118e8823"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks/audit/2a08118e8823/probe_result.json"


def attempt(fn, *args, **kwargs):
    try:
        value = fn(*args, **kwargs)
    except Exception as exc:
        return {"accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {
        "accepted": True,
        "dims": [len(value), len(value[0])],
        "nonzero_colors": sorted({cell for row in value for cell in row if cell}),
    }


gen, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
from puzzle_generators import base  # bound to the same selected tree by the loader

baseline = gen.generate(17, 3, difficulty="medium")
ignored_controls = {}
for axis, value in (
    ("palette_kind", "warm"),
    ("palette_size", 2),
    ("position_bias", "two_motif_pairs"),
    ("n_distinct_colors", 2),
    ("density", "sparse"),
    ("texture", "cool"),
):
    ignored_controls[axis] = gen.generate(17, 3, difficulty="medium", **{axis: value}) == baseline

seen = []
base.set_ctx_observer(lambda ctx: seen.append(ctx))
try:
    grid = gen.generate(522, 0, difficulty="medium")
finally:
    base.set_ctx_observer(None)
draws = seen[-1].recorded_draws()
colors = sorted({cell for row in grid for cell in row if cell})

result = {
    "schema": "arcpuzzles-peer-api-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "canonical_rule_hash": "97f36ecbb2bc",
    "cwd": str(ROOT),
    "command": ["python3", "../checks/audit/2a08118e8823/probe_api.py"],
    "override_cases": {
        "advertised_grid_h_min_easy": attempt(gen.generate, 1, 0, difficulty="easy", grid_h=6),
        "advertised_grid_w_min_easy": attempt(gen.generate, 1, 0, difficulty="easy", grid_w=9),
        "unknown_override": attempt(gen.generate, 1, 0, typo_axis="accepted?"),
        "invalid_palette_size": attempt(gen.generate, 1, 0, palette_size=999),
        "invalid_n_distinct_colors": attempt(gen.generate, 1, 0, n_distinct_colors=99),
        "invalid_density": attempt(gen.generate, 1, 0, density="dense"),
        "invalid_position_bias": attempt(gen.generate, 1, 0, position_bias="anything"),
    },
    "declared_controls_identical_to_no_override": ignored_controls,
    "silent_decoy_omission": {
        "seed": 522,
        "sample_index": 0,
        "difficulty": "medium",
        "recorded_draws": draws,
        "requested_decoys": draws.get("n_decoy"),
        "expected_object_count": 2 + draws.get("n_decoy", 0),
        "returned_object_count": len(colors),
        "nonzero_colors": colors,
        "self_check": gen.self_check(grid),
        "input": grid,
        "racket_evidence": "checks/audit/2a08118e8823/racket_seed522.json",
    },
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
