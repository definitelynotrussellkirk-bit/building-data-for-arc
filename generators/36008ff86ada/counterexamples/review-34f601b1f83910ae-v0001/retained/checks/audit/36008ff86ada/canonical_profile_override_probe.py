#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "36008ff86ada"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"


def load_source():
    spec = importlib.util.spec_from_file_location("audit_36008", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_source()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    report = {
        "task_id": TASK_ID,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "canonical_input_shapes": [[len(p["input"]), len(p["input"][0])] for p in pairs],
        "declared_axes": module.AXES,
        "draws_per_band": 10000,
        "bands": {},
        "override_probes": [],
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        shapes = Counter()
        marker_counts = Counter()
        errors = []
        for index in range(10000):
            seed = 880000 + band_index * 10000 + index
            try:
                grid = module.generate(seed, index, difficulty=band)
            except Exception as exc:
                errors.append({"seed": seed, "sample_index": index,
                               "error": f"{type(exc).__name__}: {exc}"})
                continue
            shapes[(len(grid), len(grid[0]))] += 1
            marker_counts[sum(value == 9 for row in grid for value in row)] += 1
        report["bands"][band] = {
            "generated": sum(shapes.values()),
            "generation_errors": len(errors),
            "canonical_height_6_hits": sum(count for (h, _), count in shapes.items() if h == 6),
            "canonical_shape_hits": sum(
                count for shape, count in shapes.items()
                if list(shape) in report["canonical_input_shapes"]
            ),
            "shape_histogram": {f"{h}x{w}": count for (h, w), count in sorted(shapes.items())},
            "marker_count_histogram": {str(k): v for k, v in sorted(marker_counts.items())},
            "error_examples": errors[:5],
        }
        for overrides in (
            {"grid_h": 6},
            {"grid_w": 6},
            {"n_markers": 4},
            {"grid_h": 12, "grid_w": 12, "n_markers": 4},
        ):
            row = {"band": band, "overrides": overrides}
            try:
                grid = module.generate(17, 3, difficulty=band, **overrides)
                row.update({
                    "status": "accepted",
                    "observed": {
                        "grid_h": len(grid),
                        "grid_w": len(grid[0]),
                        "n_markers": sum(value == 9 for values in grid for value in values),
                    },
                })
            except Exception as exc:
                row.update({"status": "rejected", "error": f"{type(exc).__name__}: {exc}"})
            report["override_probes"].append(row)
    report["summary"] = {
        "total_generated": sum(row["generated"] for row in report["bands"].values()),
        "canonical_height_6_hits": sum(row["canonical_height_6_hits"] for row in report["bands"].values()),
        "canonical_shape_hits": sum(row["canonical_shape_hits"] for row in report["bands"].values()),
        "rejected_advertised_override_probes": sum(
            row["status"] == "rejected" for row in report["override_probes"]
        ),
        "override_probe_count": len(report["override_probes"]),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
