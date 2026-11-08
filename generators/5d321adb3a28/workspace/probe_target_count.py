from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5d321adb3a28"
GEN_PATH = Path("generators") / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def changed_count(grid, output):
    return sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    )


def axis_targets(grid):
    counts = gen._analyze_grid(grid)["counts"]
    return {
        "horizontal": counts[gen._H_TARGET],
        "vertical": counts[gen._V_TARGET],
    }


canonical = []
for index, pair in enumerate(canonical_pairs(TASK_ID, root=find_root(__file__))):
    canonical.append(
        {
            "pair_index": index,
            "shape": [len(pair["input"]), len(pair["input"][0])],
            "changed_cells": changed_count(pair["input"], pair["output"]),
            "axis_targets": axis_targets(pair["input"]),
        }
    )

generated = {}
for band in ("easy", "medium", "hard"):
    rows = []
    for sample_index in range(100):
        grid = gen.generate(51000 + sample_index, sample_index, difficulty=band)
        output = gen.rule_mirror(grid)
        rows.append(
            {
                "sample_index": sample_index,
                "changed_cells": changed_count(grid, output),
                "axis_targets": axis_targets(grid),
                "shape": [len(grid), len(grid[0])],
                "objects": gen._object_count(grid),
            }
        )
    generated[band] = {
        "draws": len(rows),
        "changed_cells_histogram": dict(sorted(Counter(r["changed_cells"] for r in rows).items())),
        "axis_target_histogram": {
            f'{r["axis_targets"]["horizontal"]}h{r["axis_targets"]["vertical"]}v': sum(
                other["axis_targets"] == r["axis_targets"] for other in rows
            )
            for r in rows
        },
        "object_count_histogram": dict(sorted(Counter(r["objects"] for r in rows).items())),
        "shape_histogram": dict(sorted(Counter("x".join(map(str, r["shape"])) for r in rows).items())),
    }

report = {
    "schema": "arcpuzzles-review-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "canonical": canonical,
    "canonical_changed_cells_histogram": dict(
        sorted(Counter(row["changed_cells"] for row in canonical).items())
    ),
    "canonical_axis_target_histogram": dict(
        sorted(
            Counter(
                f'{row["axis_targets"]["horizontal"]}h{row["axis_targets"]["vertical"]}v'
                for row in canonical
            ).items()
        )
    ),
    "generated": generated,
    "finding": {
        "canonical_changed_cells": dict(
            sorted(Counter(row["changed_cells"] for row in canonical).items())
        ),
        "generated_changed_cells_by_band": {
            band: values["changed_cells_histogram"]
            for band, values in generated.items()
        },
        "canonical_axis_profiles": dict(
            sorted(
                Counter(
                    f'{row["axis_targets"]["horizontal"]}h{row["axis_targets"]["vertical"]}v'
                    for row in canonical
                ).items()
            )
        ),
        "generated_axis_profiles_by_band": {
            band: values["axis_target_histogram"]
            for band, values in generated.items()
        },
    },
}
print(json.dumps(report, indent=2, sort_keys=True))
