from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "2a43e4f3a796"


def main() -> None:
    packet = Path(__file__).resolve().parents[4]
    repo = packet / "WORK" / "repo"
    sys.path.insert(0, str(repo / "shared" / "runtime"))
    source = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target_" + TASK_ID, source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    probes = [
        {"name": "boolean_seed", "seed": True, "sample_index": 0},
        {"name": "float_seed", "seed": 1.75, "sample_index": 0},
        {"name": "string_seed", "seed": "1", "sample_index": 0},
        {"name": "boolean_sample_index", "seed": 0, "sample_index": True},
        {"name": "negative_sample_index", "seed": 0, "sample_index": -1},
    ]
    rows = []
    for probe in probes:
        try:
            grid = module.generate(
                probe["seed"], probe["sample_index"], difficulty="easy"
            )
            row = {
                **probe,
                "accepted": True,
                "shape": [len(grid), len(grid[0])],
                "self_check_errors": module.self_check(grid, difficulty="easy"),
                "schedule_profile": module.schedule_profile(
                    probe["seed"], probe["sample_index"], "easy"
                ),
            }
        except Exception as exc:  # retained honestly for completeness
            row = {
                **probe,
                "accepted": False,
                "exception": type(exc).__name__,
                "message": str(exc),
            }
        rows.append(row)

    report = {
        "schema": "arcpuzzles-audit-scalar-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "finding": (
            "generate accepts non-integer seed values, boolean sample indices, "
            "and negative sample indices instead of failing closed"
        ),
        "cases": rows,
        "accepted_invalid_count": sum(row["accepted"] for row in rows),
        "limits": (
            "This is an API-contract defect, not a label mismatch. The probe does "
            "not dispute that lawful endpoint grids belong to the compaction domain."
        ),
    }
    assert report["generator_sha256"] == "6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9"
    assert report["accepted_invalid_count"] == len(probes), rows
    output = Path(__file__).with_name("scalar_probe.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "accepted_invalid_count": report["accepted_invalid_count"],
        "generator_sha256": report["generator_sha256"],
        "out": str(output),
    }))


if __name__ == "__main__":
    main()
