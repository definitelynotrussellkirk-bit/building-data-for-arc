"""Reproduce ignored exact controls for audit target b45771715d10."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "b45771715d10"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def main():
    spec = importlib.util.spec_from_file_location("audit_b45771715d10", GENERATOR)
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    requested = {"code1": 1, "code2": 1}
    grid = gen.generate(0, 0, **requested)
    baseline = gen.generate(0, 0)
    unknown = gen.generate(0, 0, __unknown_axis__=7)
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "seed": 0,
        "sample_index": 0,
        "difficulty": None,
        "requested_overrides": requested,
        "observed_header": grid[0][:2],
        "override_honored": grid[0][:2] == [1, 1],
        "self_check": gen.self_check(grid),
        "unknown_override_accepted": unknown == baseline,
        "finding": "code1/code2 are advertised exact controls but are ignored; an unknown key is also silently accepted.",
    }
    assert report["observed_header"] == [1, 4]
    assert report["override_honored"] is False
    assert report["self_check"] == []
    assert report["unknown_override_accepted"] is True
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (HERE / "observation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
