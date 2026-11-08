"""Bounded source-bound teaching probe; run from WORK/repo through review.py run."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
TASK = "7ed082a6d9e0"
SOURCE = ROOT / "generators" / TASK / "generator.py"
EXPECTED_SOURCE = "02504b1db943e9f5ca9422ebe7290680df58476ecc92711903c9a2875de17188"
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def main():
    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_sha256 == EXPECTED_SOURCE, "Audited source has changed"
    canonical_rows = [json.loads(line) for line in
        (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK]
    programs = {row["program_solution"] for row in canonical_rows}
    assert len(programs) == 1
    program = next(iter(programs))
    rival = program.replace("(- (+ ar br) 3)", "(- (+ ar br) 2)").replace(
        "(- (+ ac bc) 3)", "(- (+ ac bc) 2)")
    assert rival != program
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, runtime):
        spec = importlib.util.spec_from_file_location("peer_midpoint_generator", SOURCE)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        grids = [generator.generate(3, index, difficulty=None) for index in range(4)]
        assert all(generator.self_check(grid) == [] for grid in grids)
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            rows = []
            for index, grid in enumerate(grids):
                actual = _grid(apply(program, grid))
                alternate = _grid(apply(rival, grid))
                markers = [[r, c, value] for r, row in enumerate(grid)
                           for c, value in enumerate(row) if value]
                vertical = markers[0][1] == markers[1][1]
                along_sum = sum(marker[0 if vertical else 1] for marker in markers)
                rows.append({"sample_index": index, "split": "train" if index < 3 else "test",
                             "input": grid, "output": actual, "rival_output": alternate,
                             "rival_matches": actual == alternate, "markers": markers,
                             "orientation": "vertical" if vertical else "horizontal",
                             "canonical_box_start": (along_sum - 3) // 2,
                             "rival_box_start": (along_sum - 2) // 2})
            seen = set()
            canonical_checks = []
            for record in canonical_rows:
                for split in ("train", "test"):
                    for pair in record.get(split, []):
                        key = json.dumps(pair["input"])
                        if key in seen:
                            continue
                        seen.add(key)
                        actual = _grid(apply(program, pair["input"]))
                        alternate = _grid(apply(rival, pair["input"]))
                        assert actual == pair["output"]
                        canonical_checks.append({"input": pair["input"],
                            "canonical_matches_saved_label": True,
                            "rival_matches": alternate == actual})
        finally:
            bridge.close()
    assert all(row["rival_matches"] for row in rows[:3])
    assert rows[3]["rival_matches"] is False
    assert all(row["rival_matches"] for row in canonical_checks)
    report = {
        "schema": "arcpuzzles-bounded-teaching-probe-v1", "task_id": TASK,
        "status": "reproduced_teaching_gap", "resolution": "unresolved",
        "source_sha256": source_sha256,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rival": "Round the four-cell box midpoint toward the later marker instead of the earlier marker when exact centering is impossible.",
        "program": program, "rival_program": rival,
        "seed": 3, "difficulty": None, "demo_indices": [0, 1, 2], "query_indices": [3],
        "all_demonstrations_fit": True, "query_disagrees": True,
        "canonical_unique_inputs_checked": len(canonical_checks),
        "canonical_checks": canonical_checks, "pairs": rows,
        "racket": identity, "protected_executions": 2 * (len(rows) + len(canonical_checks)),
        "suggested_repair": "Select at least one demonstration with an even sum of marker coordinates along their shared axis before a query requires this midpoint tie break; retain both orientations.",
        "limits": ["One declared rival and one three-demo/one-query generated lesson; not a full battery.",
                   "No generator or rule repair, owner acceptance, or universal uniqueness claim."]}
    out = Path(__file__).with_name("midpoint-rounding.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "source_sha256": source_sha256,
        "demo_matches": [r["rival_matches"] for r in rows[:3]],
        "query_matches": rows[3]["rival_matches"],
        "canonical_unique_inputs_checked": len(canonical_checks),
        "racket": identity, "output": str(out.resolve())}, sort_keys=True))


if __name__ == "__main__":
    main()
