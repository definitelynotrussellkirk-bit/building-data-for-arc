#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_path, load_selected_generator  # noqa: E402

TASK_ID = "f898eb5adb5d"
EXPECTED_SHA = "88e0a833d995bbe7d50035c0df0ba0f5925d61111d247220b8e02e7c74d67e54"

module, source, digest = load_selected_generator(TASK_ID, root=REPO)
if digest != EXPECTED_SHA:
    raise RuntimeError(f"source hash drift: expected {EXPECTED_SHA}, got {digest}")

seed = 0
sample_index = 0
difficulty = "easy"
overrides = {"grid_h": 8, "grid_w": 10, "n_walls": 0, "n_waypoints": 3}
with_overrides = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
control = module.generate(seed, sample_index, difficulty=difficulty)

waypoint_colors = {4, 6, 7, 9}
observed = {
    "grid_h": len(with_overrides),
    "grid_w": len(with_overrides[0]),
    "n_walls": sum(value == 5 for row in with_overrides for value in row),
    "n_waypoints": sum(value in waypoint_colors for row in with_overrides for value in row),
}

program = None
with canonical_path(REPO).open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            break
if program is None:
    raise KeyError(TASK_ID)

report = {
    "schema": "review-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(REPO)),
    "generator_sha256": digest,
    "canonical_rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "overrides": overrides,
    "observed": observed,
    "input_identical_to_no_override": with_overrides == control,
    "override_contract_satisfied": observed == overrides,
    "self_check": (
        "unavailable: generator defines no self_check"
        if not hasattr(module, "self_check")
        else module.self_check(with_overrides)
    ),
    "input": with_overrides,
    "no_override_input": control,
}

(HERE / "input.json").write_text(json.dumps({"input": with_overrides}, indent=2) + "\n", encoding="utf-8")
(HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in (
    "task_id", "generator_sha256", "observed", "input_identical_to_no_override",
    "override_contract_satisfied", "self_check")}, indent=2))
