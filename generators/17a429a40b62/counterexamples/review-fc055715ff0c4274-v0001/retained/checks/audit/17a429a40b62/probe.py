from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "17a429a40b62"
ROOT = Path.cwd()
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def grid_sha(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def call(label: str, *, difficulty: Any = "medium", **kwargs: Any) -> dict[str, Any]:
    try:
        grid = gen.generate(20261019, 5, difficulty=difficulty, **kwargs)
    except Exception as exc:  # evidence records both acceptance and rejection
        return {"label": label, "accepted": False, "exception": f"{type(exc).__name__}: {exc}"}
    return {
        "label": label,
        "accepted": True,
        "self_check": gen.self_check(grid),
        "grid_shape": [len(grid), len(grid[0])],
        "grid_sha256": grid_sha(grid),
        "observed": gen.observe_overrides(grid),
    }


invalid_calls = [
    call("fractional n_pairs", n_pairs=2.75),
    call("string n_pairs", n_pairs="2"),
    call("fractional grid_h", grid_h=5.75),
    call("boolean unchanged_body_colors", unchanged_body_colors=True),
    call("unknown override", ignored_control=123),
    call("unknown difficulty", difficulty="impossible"),
]

baseline = gen.generate(20261019, 0, difficulty="medium")
unknown = gen.generate(20261019, 0, difficulty="medium", ignored_control=123)
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_source": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "rule_hash": gen.RULE_HASH,
    "invalid_calls": invalid_calls,
    "accepted_invalid_count": sum(item["accepted"] for item in invalid_calls),
    "accepted_and_self_check_valid_count": sum(
        item["accepted"] and not item.get("self_check") for item in invalid_calls
    ),
    "unknown_override_schedule_witness": {
        "seed": 20261019,
        "sample_index": 0,
        "difficulty": "medium",
        "baseline": {
            "shape": [len(baseline), len(baseline[0])],
            "observed": gen.observe_overrides(baseline),
            "grid_sha256": grid_sha(baseline),
            "self_check": gen.self_check(baseline),
        },
        "with_ignored_control": {
            "shape": [len(unknown), len(unknown[0])],
            "observed": gen.observe_overrides(unknown),
            "grid_sha256": grid_sha(unknown),
            "self_check": gen.self_check(unknown),
        },
        "grids_equal": baseline == unknown,
    },
}
Path("../checks/audit/17a429a40b62/probe.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": source_sha256,
    "accepted_invalid_count": report["accepted_invalid_count"],
    "accepted_and_self_check_valid_count": report["accepted_and_self_check_valid_count"],
    "unknown_override_changes_grid": baseline != unknown,
}, indent=2))
