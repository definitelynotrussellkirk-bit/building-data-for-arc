from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO = Path.cwd().resolve()
OUT = (REPO / "../checks/audit/5a44a210e9ea").resolve()
TASK_ID = "5a44a210e9ea"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid: Any) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def decode_grid(grid: Any) -> list[list[int]]:
    if grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return [list(row) for row in grid]


def load_module():
    spec = importlib.util.spec_from_file_location("audit_5a_generator", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def position_order_rival(module, grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: palette follows frame top-left reading order, not area."""
    info = module._scene_analysis(grid)
    frames = sorted(info["frames"], key=lambda cells: min(cells))
    out = [[0 for _ in row] for row in info["body"]]
    for index, cells in enumerate(frames):
        colour = info["palette"][min(index, len(info["palette"]) - 1)]
        for row, col in cells:
            out[row][col] = colour
    return out


module = load_module()
record = None
for line in CANONICAL.read_text().splitlines():
    obj = json.loads(line)
    if obj.get("task_id") == TASK_ID:
        record = obj
        break
assert record is not None

canonical_rows = []
for split in ("train", "test"):
    split_pairs = record.get(split, [])
    if isinstance(split_pairs, dict):
        split_pairs = [split_pairs]
    for index, pair in enumerate(split_pairs):
        if "output" not in pair:
            continue
        grid = decode_grid(pair["input"])
        expected = decode_grid(pair["output"])
        rival = position_order_rival(module, grid)
        canonical_rows.append({
            "split": split,
            "index": index,
            "input_sha256": grid_hash(grid),
            "validator_errors": module.self_check(grid),
            "rival_matches_canonical_output": rival == expected,
            "mirror_matches_canonical_output": module.rule_mirror(grid) == expected,
        })

bands = ("easy", "medium", "hard")
generated_rows = []
profile_counts: dict[str, int] = {}
for band_index, difficulty in enumerate(bands):
    seed = 93000 + band_index
    for sample_index in range(100):
        grid = module.generate(seed, sample_index, difficulty=difficulty)
        info = module._scene_analysis(grid)
        profile = module.schedule_profile(seed, sample_index, difficulty)
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
        reading = sorted(info["frames"], key=lambda cells: min(cells))
        area = list(info["frames"])
        generated_rows.append({
            "difficulty": difficulty,
            "seed": seed,
            "sample_index": sample_index,
            "profile": profile,
            "input_sha256": grid_hash(grid),
            "validator_ok": not module.self_check(grid),
            "valid_frame_reading_order_equals_area_order": reading == area,
            "position_rival_matches_rule_mirror": position_order_rival(module, grid) == module.rule_mirror(grid),
        })

input_payload = json.loads((OUT / "input.json").read_text())
counterexample_input = input_payload["input"]
racket = json.loads((OUT / "racket.json").read_text())
racket_output = racket["results"][0]["output"]
rival_output = position_order_rival(module, counterexample_input)
mirror_output = module.rule_mirror(counterexample_input)

rival_doc = {
    "schema": "arcpuzzles-audit-rival-v1",
    "task_id": TASK_ID,
    "rival_name": "frame_top_left_reading_order",
    "description": "Assign palette colors to exact frames by top-left reading order, erasing malformed components and reusing the last palette color.",
    "output": rival_output,
    "output_sha256": grid_hash(rival_output),
}
(OUT / "rival.json").write_text(json.dumps(rival_doc, indent=2) + "\n")

diff_cells = [
    [r, c, racket_output[r][c], rival_output[r][c]]
    for r in range(len(racket_output))
    for c in range(len(racket_output[0]))
    if racket_output[r][c] != rival_output[r][c]
]

probe = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256_bytes(SOURCE.read_bytes()),
    "declared_rule_hash": module.RULE_HASH,
    "canonical_pairs_checked": len(canonical_rows),
    "canonical_position_rival_matches": sum(row["rival_matches_canonical_output"] for row in canonical_rows),
    "canonical_mirror_matches": sum(row["mirror_matches_canonical_output"] for row in canonical_rows),
    "canonical_rows": canonical_rows,
    "generated_policy": {
        "difficulties": list(bands),
        "seeds": {band: 93000 + i for i, band in enumerate(bands)},
        "sample_indices": [0, 99],
        "samples_per_band": 100,
        "total_samples": len(generated_rows),
    },
    "generated_unique_inputs": len({row["input_sha256"] for row in generated_rows}),
    "generated_validator_passes": sum(row["validator_ok"] for row in generated_rows),
    "generated_reading_order_equals_area_order": sum(row["valid_frame_reading_order_equals_area_order"] for row in generated_rows),
    "generated_position_rival_matches": sum(row["position_rival_matches_rule_mirror"] for row in generated_rows),
    "profile_counts": profile_counts,
    "counterexample": {
        "input_sha256": racket["results"][0]["input_sha256"],
        "selected_racket_output_sha256": racket["results"][0]["output_sha256"],
        "rival_output_sha256": grid_hash(rival_output),
        "mirror_matches_selected_racket": mirror_output == racket_output,
        "rival_matches_selected_racket": rival_output == racket_output,
        "differing_cell_count": len(diff_cells),
        "differing_cells": diff_cells,
        "validator_status": racket["results"][0]["generator_domain"],
        "interpretation": "The task authority handles disjoint frames by area, but the generated/canonical manifold only contains nested frames, where top-left reading order equals area order.",
    },
}
(OUT / "probe.json").write_text(json.dumps(probe, indent=2) + "\n")

counterexample = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK_ID,
    "finding_id": "A-5A-1",
    "generator_sha256": probe["generator_sha256"],
    "rule_hash": module.RULE_HASH,
    "generated": False,
    "seed": None,
    "sample_index": None,
    "overrides": {},
    "input": counterexample_input,
    "input_sha256": racket["results"][0]["input_sha256"],
    "actual_racket_output": racket_output,
    "actual_racket_output_sha256": racket["results"][0]["output_sha256"],
    "rival_name": rival_doc["rival_name"],
    "rival_output": rival_output,
    "rival_output_sha256": rival_doc["output_sha256"],
    "differing_cell_count": len(diff_cells),
    "validator_status": racket["results"][0]["generator_domain"],
    "generator_domain_membership": False,
    "command": racket["command"],
    "cwd": racket["cwd"],
    "evidence": [
        "checks/audit/5a44a210e9ea/input.json",
        "checks/audit/5a44a210e9ea/racket.json",
        "checks/audit/5a44a210e9ea/rival.json",
        "checks/audit/5a44a210e9ea/probe.json"
    ],
}
(OUT / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
print(json.dumps({
    "canonical": [probe["canonical_position_rival_matches"], probe["canonical_pairs_checked"]],
    "generated": [probe["generated_position_rival_matches"], probe["generated_policy"]["total_samples"]],
    "unique": probe["generated_unique_inputs"],
    "counterexample_diffs": len(diff_cells),
}, indent=2))
