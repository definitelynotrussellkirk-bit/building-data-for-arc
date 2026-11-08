from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

TASK = "394fc1eaa85e"
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", REPO / "generators" / TASK / "generator.py")
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    inputs = []
    mirrors = []
    records = []
    difficulties = ("easy", "medium", "hard")
    for i in range(64):
        difficulty = difficulties[i % 3]
        height = 7 + (i % 3)
        width = 11 + ((i // 3) % 3)
        seed = 24680 + i // 16
        grid = GEN.generate(seed, i, difficulty=difficulty, grid_h=height, grid_w=width)
        mirror = GEN.rule_mirror(grid)
        obs = GEN.semantic_observables(grid)
        errors = GEN.self_check(grid, difficulty=difficulty, meta={"overrides": {"grid_h": height, "grid_w": width}})
        strict = GEN.strict_canonical_like(grid)
        inputs.append(grid)
        mirrors.append(mirror)
        records.append({
            "index": i,
            "seed": seed,
            "sample_index": i,
            "difficulty": difficulty,
            "requested_shape": [height, width],
            "input_sha256": digest(grid),
            "mirror_sha256": digest(mirror),
            "self_check": errors,
            "strict": strict,
            "observables": obs,
        })

    lesson_failures = []
    rival_survivals = []
    for difficulty in difficulties:
        for start in range(16):
            demos = []
            for idx in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(97531, idx, difficulty=difficulty)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            qidx = start + GEN.EXAMPLES_NEEDED
            qgrid = GEN.generate(97531, qidx, difficulty=difficulty)
            query = {"input": qgrid, "output": GEN.rule_mirror(qgrid)}
            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"difficulty": difficulty, "start": start, "reasons": reasons})
            for name, rival in GEN.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    rival_survivals.append({"difficulty": difficulty, "start": start, "rival": name})

    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(Path(GEN.__file__).read_bytes()).hexdigest(),
        "sample_count": len(inputs),
        "difficulty_counts": Counter(r["difficulty"] for r in records),
        "profile_counts": Counter(r["observables"]["wall_profile"] for r in records),
        "unique_inputs": len({r["input_sha256"] for r in records}),
        "self_check_failures": [r for r in records if r["self_check"]],
        "strict_failures": [r for r in records if r["strict"]],
        "invalid_mirror_cells": [
            {"index": i, "row": rr, "col": cc, "value": value}
            for i, grid in enumerate(mirrors)
            for rr, row in enumerate(grid)
            for cc, value in enumerate(row)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        ],
        "lesson_windows_checked": 48,
        "lesson_failures": lesson_failures,
        "rival_survivals": rival_survivals,
        "records": records,
    }
    (OUT / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (OUT / "mirror.json").write_text(json.dumps(mirrors, indent=2) + "\n")
    (OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2, sort_keys=True, default=dict))


if __name__ == "__main__":
    main()
