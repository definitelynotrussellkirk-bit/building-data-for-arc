from __future__ import annotations

import json
import sys
import time
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import load_selected_generator  # noqa: E402

TASK_ID = "5fdbbb5a53ef"
EXPECTED_SOURCE_SHA256 = "629d9f4e8580208d8f6d4f70a7ddaf2dcf5f648265e57d8cdd1d3b64946f87da"
PROBE_SEED = "6a5f8b572276a65ffcc103784487301478c0ca27ccfd63ad0c85721da947122b"
OUT = HERE.parent / "evidence.json"


def orientation_sensitive_rival(gen, grid):
    """Shortcut: compare exact painted orientation, not rotation class."""
    _, top_frames, left_frames, _ = gen._gallery_parts(grid)
    output = []
    for left in left_frames:
        row = []
        for top in top_frames:
            same_shape = left["shape"] == top["shape"]
            same_color = left["color"] == top["color"]
            row.append(8 if same_shape and same_color else 6 if same_shape else 3 if same_color else 0)
        output.append(row)
    return output


def main():
    started = time.perf_counter()
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=REPO)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash drift: {source_sha256}")

    seed = int(PROBE_SEED[:16], 16)
    witness = None
    attempts = 0
    for sample_index in range(96):
        difficulty = ("easy", "medium", "hard")[sample_index % 3]
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        attempts += 1
        errors = gen.self_check(deepcopy(grid), difficulty=difficulty)
        if errors:
            raise AssertionError({"sample_index": sample_index, "self_check": errors})
        oracle, _, _ = gen._relation_matrix(deepcopy(grid))
        rival = orientation_sensitive_rival(gen, deepcopy(grid))
        if oracle != rival:
            differing_cells = [
                [row, col, oracle[row][col], rival[row][col]]
                for row in range(len(oracle))
                for col in range(len(oracle[0]))
                if oracle[row][col] != rival[row][col]
            ]
            witness = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": difficulty,
                "input": grid,
                "oracle_output": oracle,
                "orientation_sensitive_rival_output": rival,
                "differing_cells": differing_cells,
                "self_check": errors,
            }
            break

    elapsed = time.perf_counter() - started
    report = {
        "schema": "arcpuzzles-supplementary-ticket-evidence-v1",
        "ticket_id": "ticket-cb41b83356bb393f",
        "ticket_type": "adversarial_witness",
        "status": "completed" if witness else "unknown",
        "task_id": TASK_ID,
        "rule_hash": gen.RULE_HASH,
        "generator_source": str(source_path.relative_to(REPO)),
        "generator_sha256": source_sha256,
        "probe_seed": PROBE_SEED,
        "shortcut": "orientation-sensitive exact-shape matching (fails to quotient rotations)",
        "attempt_limit": 96,
        "attempts": attempts,
        "elapsed_seconds": round(elapsed, 6),
        "witness": witness,
        "conclusion": (
            "A lawful current-source input refutes the exact-orientation shortcut."
            if witness
            else "No witness found within the one bounded 96-draw probe."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "attempts", "elapsed_seconds", "conclusion")}, sort_keys=True))
    if witness:
        print(json.dumps({"sample_index": witness["sample_index"], "difficulty": witness["difficulty"], "differing_cells": witness["differing_cells"]}, sort_keys=True))
    return 0 if witness else 3


if __name__ == "__main__":
    raise SystemExit(main())
