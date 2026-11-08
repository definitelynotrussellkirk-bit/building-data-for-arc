from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    helper_root = ancestor / "repo" / "shared" / "runtime"
    if (helper_root / "reviewer_support.py").is_file():
        sys.path.insert(0, str(helper_root))
        break
else:
    raise FileNotFoundError("could not locate WORK/repo/shared/runtime")

from reviewer_support import find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper


def rule_application(source, grid):
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"({strip_rule_wrapper(source)} '({rows}))"

TASK_ID = "generic_waypoint_route_gen1"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
OUT = HERE.parent


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def erase_prior_panel_content(grid):
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    separators = [
        c for c in range(w)
        if grid[0][c] != bg and all(grid[r][c] == grid[0][c] for r in range(h))
    ]
    if not separators:
        raise AssertionError("expected a full-height separator")
    last_start = max(separators) + 1
    tampered = deepcopy(grid)
    removed = 0
    for r in range(h):
        for c in range(last_start):
            if c in separators:
                continue
            removed += tampered[r][c] != bg
            tampered[r][c] = bg
    return tampered, {
        "background": bg,
        "separator_columns": separators,
        "last_panel_start": last_start,
        "removed_nonbackground_cells": removed,
    }


task = GEN.generate_task(23, difficulty="medium")
tampered_task = deepcopy(task)
records = []
with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
    for index, pair in enumerate(task["train"] + task["test"]):
        original = pair["input"]
        tampered, mutation = erase_prior_panel_content(original)
        (tampered_task["train"] + tampered_task["test"])[index]["input"] = tampered
        original_output = bridge.eval_text(rule_application(GEN.PROGRAM, original))
        tampered_output = bridge.eval_text(rule_application(GEN.PROGRAM, tampered))
        records.append({
            "pair_index": index,
            "original_input_sha256": digest(original),
            "tampered_input_sha256": digest(tampered),
            "expected_output_sha256": digest(pair["output"]),
            "original_racket_output_sha256": digest(original_output),
            "tampered_racket_output_sha256": digest(tampered_output),
            "original_matches_label": original_output == pair["output"],
            "tampered_matches_original": tampered_output == original_output,
            **mutation,
        })

report = {
    "schema": "audit-dead-context-report-v1",
    "task_id": TASK_ID,
    "classification": "reproduced_dead_context_shortcut",
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "program_sha256": hashlib.sha256(GEN.PROGRAM.encode()).hexdigest(),
    "seed": 23,
    "difficulty": "medium",
    "tampered_self_check_task": GEN.self_check_task(tampered_task),
    "all_original_outputs_match_labels": all(r["original_matches_label"] for r in records),
    "all_outputs_unchanged": all(r["tampered_matches_original"] for r in records),
    "records": records,
    "tampered_task": tampered_task,
    "command": [
        "python3", "review.py", "run", "python3",
        "../checks/audit/generic_waypoint_route_gen1/dead_context_probe.py"
    ],
    "cwd": "packet_root",
}
(OUT / "dead-context-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in (
    "classification", "generator_sha256", "program_sha256",
    "tampered_self_check_task", "all_original_outputs_match_labels",
    "all_outputs_unchanged", "records"
)}, indent=2))
raise SystemExit(0 if report["all_outputs_unchanged"] and not report["tampered_self_check_task"] else 1)
