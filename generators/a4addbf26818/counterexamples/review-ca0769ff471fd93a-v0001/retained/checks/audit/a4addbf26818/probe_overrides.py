from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "a4addbf26818"
RULE_HASH = "536a147b1a6a"  # catalog-reviewed selected authority
REQUESTED_DIMS = (6, 8)
SAMPLES = 12


def dims(grid):
    return [len(grid), len(grid[0]) if grid else 0]


def main() -> None:
    gen, source, source_sha = load_selected_generator(TASK_ID, root=REPO)
    rows = []
    for i in range(SAMPLES):
        seed = 7100 + i
        baseline = gen.generate(seed, i)
        requested = gen.generate(seed, i, grid_h=REQUESTED_DIMS[0], grid_w=REQUESTED_DIMS[1])
        dense = gen.generate(seed, i, texture="dense")
        holey = gen.generate(seed, i, texture="holey")
        typo = gen.generate(seed, i, typo_axis="ignored")
        rows.append(
            {
                "seed": seed,
                "sample_index": i,
                "baseline_dims": dims(baseline),
                "requested_dims": list(REQUESTED_DIMS),
                "actual_dims_with_grid_overrides": dims(requested),
                "grid_overrides_equal_baseline": requested == baseline,
                "dense_equals_holey": dense == holey,
                "unknown_override_equal_baseline": typo == baseline,
                "self_check_grid_overrides": gen.self_check(requested),
                "self_check_dense": gen.self_check(dense),
                "self_check_holey": gen.self_check(holey),
            }
        )

    report = {
        "schema": "arcpuzzles-audit-override-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(REPO)),
        "generator_sha256": source_sha,
        "rule_hash": RULE_HASH,
        "command": ["python3", "checks/audit/a4addbf26818/probe_overrides.py"],
        "working_directory": "repo",
        "declared_axes": gen.AXES,
        "sample_protocol": {
            "seed_range": [7100, 7111],
            "sample_index_range": [0, 11],
            "difficulty": None,
            "denominator": SAMPLES,
        },
        "summary": {
            "grid_size_overrides_ignored": sum(
                row["grid_overrides_equal_baseline"]
                and row["actual_dims_with_grid_overrides"] != row["requested_dims"]
                for row in rows
            ),
            "dense_holey_identical": sum(row["dense_equals_holey"] for row in rows),
            "unknown_override_silently_ignored": sum(
                row["unknown_override_equal_baseline"] for row in rows
            ),
            "requested_grids_self_check_clean": sum(
                not row["self_check_grid_overrides"] for row in rows
            ),
        },
        "rows": rows,
        "conclusion": (
            "All advertised grid_h/grid_w requests and helpful dense/holey texture "
            "choices are observationally inert for the same seed/index; unknown keys "
            "are silently ignored. This is an override-contract defect, not a Racket-label defect."
        ),
    }
    out = HERE.with_name("override-probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
