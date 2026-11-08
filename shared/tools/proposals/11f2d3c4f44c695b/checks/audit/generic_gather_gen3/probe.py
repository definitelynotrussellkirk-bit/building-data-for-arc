#!/usr/bin/env python3
"""Find/replay a generic native lesson against explicit, finite rivals.

Run from WORK through run_with_racket.py; its payload cwd is WORK/repo.
Search uses the native generate_task API. Verify uses Catalog.generate, which
executes the generator's actual emitted program in Racket. No canonical rule
is substituted for the emitted program.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

TASK = "generic_gather_gen3"
ROOT = Path.cwd()
HOME = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"


def save(name, data):
    (HOME / name).write_text(json.dumps(data, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parameters(task):
    program = task.get("emitted_program", task["program"])
    match = re.search(r"\(recolor g ([0-9]) ([0-9])\)", program)
    return ("lr" if "left-half" in program else "ud",
            tuple(map(int, match.groups())) if match else None)


def rival(grid, task, kind):
    axis, mapping = parameters(task)
    colors = sorted({cell for row in grid for cell in row} - {0})
    if mapping is not None and kind in {"recolor_minimum", "recolor_maximum"}:
        mapping = (colors[0] if kind == "recolor_minimum" else colors[-1], mapping[1])
    if kind == "no_recolor":
        mapping = None
    values = [[mapping[1] if mapping and cell == mapping[0] else cell for cell in row]
              for row in grid]
    h, w = len(values), len(values[0])
    if axis == "lr":
        left = [row[:w // 2] for row in values]
        right = [row[(w + 1) // 2:] for row in values]
    else:
        left, right = values[:h // 2], values[(h + 1) // 2:]

    def merge(a, b):
        if kind == "first_panel_priority":
            return a or b
        if kind == "larger_color_priority":
            return max(a, b)
        if kind == "smaller_color_priority":
            return min(a, b) if a and b else a or b
        return b or a

    return [[merge(a, b) for a, b in zip(arow, brow)] for arow, brow in zip(left, right)]


RIVALS = ("first_panel_priority", "larger_color_priority", "smaller_color_priority",
          "no_recolor", "recolor_minimum", "recolor_maximum")


def score(task):
    records = {}
    for name in RIVALS:
        train = [rival(p["input"], task, name) == p["output"] for p in task["train"]]
        test = [rival(p["input"], task, name) == p["output"] for p in task["test"]]
        records[name] = {"train_matches": train, "test_matches": test}
    return records


def search(limit):
    spec = importlib.util.spec_from_file_location("audit_gather_source", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    counts = Counter()
    examined = []
    # Easy has the smallest panels, so fewer overlaps distinguish priority.
    for seed in range(limit):
        task = module.generate_task(seed, difficulty="easy")
        records = score(task)
        counts.update([task["meta"]["axis"]])
        counts.update(["recolor" if parameters(task)[1] else "no_recolor"])
        examined.append({"seed": seed, "native_train": len(task["train"]),
                         "native_test": len(task["test"]), "scores": records})
        for name, result in records.items():
            if all(result["train_matches"]) and not all(result["test_matches"]):
                witness = {"seed": seed, "difficulty": "easy", "rival": name,
                           "source_sha256": digest(SOURCE), "task": task,
                           "scores": records,
                           "checked_seed_range_inclusive": [0, seed]}
                save("search-witness.json", witness)
                save("search-report.json", {"status": "candidate_found", "counts": counts,
                     "source_sha256": digest(SOURCE), "examined": examined})
                print(json.dumps({key: value for key, value in witness.items()
                                  if key not in {"task", "scores"}}))
                return
    save("search-report.json", {"status": "no_witness_in_bound", "limit": limit,
         "counts": counts, "source_sha256": digest(SOURCE), "examined": examined})
    print(json.dumps({"status": "no_witness_in_bound", "seeds": limit}))


def verify():
    from arcpuzzles import Catalog
    witness = json.loads((HOME / "search-witness.json").read_text())
    assert witness["source_sha256"] == digest(SOURCE), "audited source changed"
    native = witness["task"]
    task = Catalog().generate(TASK, seed=witness["seed"], difficulty=witness["difficulty"],
                              n_train=len(native["train"]), n_test=len(native["test"]),
                              allow_unapproved=True, timeout=120)[0]
    save("racket-episode.json", task)
    assert task["train"] == native["train"] and task["test"] == native["test"]
    name = witness["rival"]
    records = score(task)
    result = records[name]
    assert all(result["train_matches"]), "rival does not fit all demonstrations"
    assert not all(result["test_matches"]), "rival agrees on all queries"
    query_index = result["test_matches"].index(False)
    pair = task["test"][query_index]
    prediction = rival(pair["input"], task, name)
    differing = [{"row": r, "column": c, "racket": cell, "rival": prediction[r][c]}
                 for r, row in enumerate(pair["output"])
                 for c, cell in enumerate(row) if cell != prediction[r][c]]
    save("input.json", pair["input"])
    save("racket-output.json", pair["output"])
    save("rival-output.json", prediction)
    report = {"status": "reproduced", "task_id": TASK, "rival": name,
              "seed": witness["seed"], "difficulty": witness["difficulty"],
              "source_sha256": digest(SOURCE), "program": task["program"],
              "emitted_program": task.get("emitted_program"),
              "executed_rule_hash": task["executed_rule_hash"],
              "native_train_count": len(task["train"]), "native_test_count": len(task["test"]),
              "query_index": query_index, "scores": records,
              "differing_cells_zero_based": differing,
              "legal_input": "unchanged native-generated grids; public Catalog.generate accepted every pair and executed the emitted program in Racket",
              "limitation": "One deterministic native lesson and six explicit rivals; this is not a full battery or exhaustive domain/seed audit."}
    save("verification.json", report)
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["search", "verify"])
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    search(args.limit) if args.mode == "search" else verify()
