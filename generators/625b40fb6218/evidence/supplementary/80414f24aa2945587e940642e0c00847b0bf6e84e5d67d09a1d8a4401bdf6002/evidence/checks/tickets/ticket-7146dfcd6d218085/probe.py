"""One bounded adversarial probe: yellow-priority overlap versus left priority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import signal
import time
import traceback

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TICKET = "ticket-7146dfcd6d218085"
TASK = "625b40fb6218"
PINNED_SOURCE = "686b9f2d186723ef95a977fe43eb0f3829c023ab1de49e19e51272b89eceb632"
PINNED_RULE = "53f987296312"
PINNED_SEED = "9b295158a88608aa32cfcc4583c31772b057d32b2259f2657b2b1da0ba97b671"
SEED = int(PINNED_SEED[:16], 16)
MAX_DRAWS = 32
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
started = time.monotonic()
authoring_started = json.loads((HERE / "start.json").read_text())["started_unix"]


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def shortcut(grid):
    """Occupied overlaps prefer yellow; every other branch follows left priority."""
    half = (len(grid[0]) - 1) // 2
    result = []
    for row in grid:
        output = []
        for left, right in zip(row[:half], row[half + 1:]):
            if left and not right:
                value = 2
            elif right and not left:
                value = 1
            elif left and right and 4 in (left, right):
                value = 4
            else:
                value = left
            output.append(value)
        result.append(output)
    return result


def independent_left_priority(grid):
    half = (len(grid[0]) - 1) // 2
    return [[2 if left and not right else 1 if right and not left else left
             for left, right in zip(row[:half], row[half + 1:])]
            for row in grid]


def deadline(signum, frame):
    raise TimeoutError("Single targeted probe exceeded its 115-second internal allowance")


signal.signal(signal.SIGALRM, deadline)
signal.setitimer(signal.ITIMER_REAL, 115)
report = {"ticket_id": TICKET, "type": "adversarial_witness", "task_id": TASK,
          "pinned_seed": PINNED_SEED, "seed_derivation": "int(pinned_seed[:16], 16)",
          "generation_seed": SEED, "generator_sha256": PINNED_SOURCE,
          "rule_hash": PINNED_RULE, "maximum_generated_inputs": MAX_DRAWS,
          "shortcut": "Occupied overlaps prefer color 4 (yellow); otherwise left priority.",
          "command_from_WORK_repo": f"python3 ../../review.py run python3 ../checks/tickets/{TICKET}/probe.py",
          "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "scope": "One rival; at most 32 ordinary default draws and 28 consecutive four-demo/one-query windows; no battery or census."}
try:
    module, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == PINNED_SOURCE, (source_hash, PINNED_SOURCE)
    assert module.RULE_HASH == PINNED_RULE
    catalog = Catalog(ROOT)
    description = catalog.describe(TASK)
    assert description["generator_sha256"] == PINNED_SOURCE
    assert description["rule_hash"] == PINNED_RULE
    canonical = canonical_pairs(TASK, root=ROOT)
    report["canonical_ledger_sha256"] = hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest()
    samples = []
    for index in range(MAX_DRAWS):
        grid = module.generate(SEED, index)
        errors = module.self_check(grid)
        assert not errors, (index, errors)
        expected = independent_left_priority(grid)
        samples.append({"input": grid, "output": expected, "sample_index": index,
                        "rival_matches_python": shortcut(grid) == expected,
                        "self_check": errors})
    report["sample_results"] = [{"sample_index": item["sample_index"],
                                  "input_sha256": sha(item["input"]),
                                  "rival_matches_python": item["rival_matches_python"]}
                                 for item in samples]
    candidate = None
    for start in range(MAX_DRAWS - 4):
        window = samples[start:start + 5]
        if all(row["rival_matches_python"] for row in window[:4]) and not window[4]["rival_matches_python"]:
            candidate = window
            break
    selected = candidate if candidate is not None else samples[:5]
    inputs = [pair["input"] for pair in canonical] + [pair["input"] for pair in selected]
    racket = catalog.apply(TASK, inputs, reference="canonical", timeout=85,
                           check_generator_domain=True)
    write("racket.json", racket)
    assert racket["generator_sha256"] == PINNED_SOURCE
    assert racket["catalog_rule_hash"] == racket["executed_rule_hash"] == PINNED_RULE
    assert racket["rule_hash_matches_catalog"] is True
    assert all(row["error"] is None for row in racket["results"])
    canonical_results = racket["results"][:len(canonical)]
    selected_results = racket["results"][len(canonical):]
    assert all(result["output"] == pair["output"] for pair, result in zip(canonical, canonical_results, strict=True))
    report["canonical_pairs_racket_verified"] = len(canonical)
    report["canonical_shortcut_matches"] = sum(shortcut(pair["input"]) == result["output"] for pair, result in zip(canonical, canonical_results, strict=True))
    assert report["canonical_shortcut_matches"] == len(canonical)
    for sample, result in zip(selected, selected_results, strict=True):
        assert sample["output"] == result["output"]
        sample["output"] = result["output"]
    report["racket_receipt_sha256"] = hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest()
    if candidate is None:
        report.update(status="unknown", summary="No four-demo/one-query yellow-priority counterexample in the first 32 pinned-seed ordinary draws; this bounded search does not establish safety.")
    else:
        demos = [{"input": row["input"], "output": row["output"]} for row in candidate[:4]]
        query = {"input": candidate[4]["input"], "output": candidate[4]["output"]}
        assert all(shortcut(row["input"]) == row["output"] for row in demos)
        rival_output = shortcut(query["input"])
        assert rival_output != query["output"]
        lesson_errors = module.lesson_identifiable(demos, query)
        changes = [{"row": r, "col": c, "racket": query["output"][r][c], "shortcut": rival_output[r][c]}
                   for r in range(len(rival_output)) for c in range(len(rival_output[0]))
                   if rival_output[r][c] != query["output"][r][c]]
        witness = {"task_id": TASK, "generator_sha256": PINNED_SOURCE, "rule_hash": PINNED_RULE,
                   "pinned_seed": PINNED_SEED, "generation_seed": SEED, "difficulty": None,
                   "overrides": {}, "sample_indices": [row["sample_index"] for row in candidate],
                   "train": demos, "test": query, "shortcut_output": rival_output,
                   "mismatched_cells": changes, "self_check_results": [row["self_check"] for row in candidate],
                   "lesson_identifiable": lesson_errors,
                   "racket_result_indices": list(range(len(canonical), len(canonical) + 5))}
        write("witness.json", witness)
        report.update(status="finding" if not lesson_errors else "completed",
                      summary=("Yellow-priority overlap fits all 8 canonical occurrences and four consecutive ordinary demonstrations but changes the following Racket-labeled query; lesson_identifiable returns no rejection." if not lesson_errors else "A lawful yellow-priority witness was found, and the existing lesson gate rejected it."),
                      sample_indices=witness["sample_indices"], lesson_identifiable=lesson_errors,
                      mismatched_cells=changes,
                      witness_sha256=hashlib.sha256((HERE / "witness.json").read_bytes()).hexdigest())
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == PINNED_SOURCE
except Exception as error:
    report.update(status="blocked", summary=f"Single targeted probe stopped: {type(error).__name__}: {error}",
                  error_traceback=traceback.format_exc()[-5000:])
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
    report["probe_elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["elapsed_minutes"] = round((time.time() - authoring_started) / 60, 3)
    write("result.json", report)
    print(json.dumps({key: report.get(key) for key in ("ticket_id", "status", "summary", "sample_indices", "mismatched_cells", "lesson_identifiable", "probe_elapsed_seconds", "elapsed_minutes")}, indent=2))
