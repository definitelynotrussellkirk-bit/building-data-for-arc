"""Bounded read-only audit; generated artifacts stay beside this script."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs

ID = "2c41c09ae1d5"
OUT = Path(__file__).resolve().parent


def points(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def signature(grid):
    one, two = points(grid, 1)[0], points(grid, 2)[0]
    payload = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1, 2, 3)]
    delta = (two[0] - one[0], two[1] - one[1])
    return {"height": len(grid), "width": len(grid[0]), "payload_size": len(payload),
            "payload_colors": sorted({v for r, c, v in payload}), "counter_k": len(points(grid, 3)),
            "delta": delta, "payload": payload}


def output(grid, *, blank_only=False):
    s = signature(grid)
    dr, dc = s["delta"]
    result = deepcopy(grid) if blank_only else [[v if v in (1, 2, 3) else 0 for v in row] for row in grid]
    for mult in range(s["counter_k"] + 1):
        for r, c, value in s["payload"]:
            rr, cc = r + mult * dr, c + mult * dc
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                if not blank_only or result[rr][cc] == 0:
                    result[rr][cc] = value
    return result


def overlap(grid):
    s = signature(grid)
    occupied = set()
    for mult in range(s["counter_k"] + 1):
        cells = {(r + mult * s["delta"][0], c + mult * s["delta"][1])
                 for r, c, value in s["payload"]}
        if occupied & cells:
            return True
        occupied.update(cells)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    source = root / "generators" / ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_vector_generator", source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(ID, root=root)
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    line = next(line for line in ledger.read_bytes().splitlines() if json.loads(line).get("task_id") == ID)
    record = json.loads(line)
    report = {"task_id": ID, "generator_version": gen.VERSION, "source_hashes": {
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "canonical_record_sha256": hashlib.sha256(line).hexdigest(),
        "canonical_program_sha256": hashlib.sha256(record["program_solution"].encode()).hexdigest(),
        "racket_prelude_sha256": hashlib.sha256((root / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt").read_bytes()).hexdigest(),
    }, "canonical": []}
    for pair in pairs:
        report["canonical"].append({"split": pair["split"], "index": pair["pair_index"],
            "profile": [len(pair["input"]), len(pair["input"][0])],
            "self_check": gen.self_check(pair["input"]),
            "python_oracle_matches_recorded": output(pair["input"]) == pair["output"],
            "blank_only_rival_matches_recorded": output(pair["input"], blank_only=True) == pair["output"]})
    baseline = gen.generate(29, 0)
    baseline_sig = signature(baseline)
    report["override_checks"] = []
    for overrides in ({"grid_h": 12}, {"grid_w": 12}, {"payload_size": 5}, {"counter_k": 4}):
        grid = gen.generate(29, 0, **overrides)
        report["override_checks"].append({"seed": 29, "sample_index": 0, "difficulty": None,
            "overrides": overrides, "identical_to_unpinned": grid == baseline,
            "observed": signature(grid), "self_check": gen.self_check(grid)})
    report["sampling"] = []
    canonical_profiles = {tuple(item["profile"]) for item in report["canonical"]}
    for band in ("easy", "medium", "hard"):
        profiles = Counter()
        counters = Counter()
        errors = []
        rival_matches = overlaps = exact = envelope = 0
        for index in range(64):
            seed = 1000 + index
            try:
                grid = gen.generate(seed, index, difficulty=band)
                s = signature(grid)
                profiles[(s["height"], s["width"])] += 1
                counters[s["counter_k"]] += 1
                rival_matches += output(grid) == output(grid, blank_only=True)
                overlaps += overlap(grid)
                exact += (s["height"], s["width"]) in canonical_profiles
                envelope += 8 <= s["height"] <= 9 and 8 <= s["width"] <= 10
                validation = gen.self_check(grid)
                if validation:
                    errors.append({"seed": seed, "sample_index": index, "errors": validation})
            except Exception as exc:
                errors.append({"seed": seed, "sample_index": index, "error": repr(exc)})
        report["sampling"].append({"difficulty": band, "attempted": 64,
            "seed_rule": "seed=1000+sample_index, sample_index=0..63", "overrides": {},
            "canonical_dimension_hits": exact, "canonical_envelope_hits": envelope,
            "overlapping_copy_examples": overlaps, "blank_only_rival_matches_python_oracle": rival_matches,
            "counter_histogram": dict(counters), "observed_profiles": [[*key, count] for key, count in sorted(profiles.items())],
            "errors": errors})
    witness = deepcopy(pairs[1]["input"])
    assert witness[3][5] == 6
    witness[3][5] = 4
    padded = [row + [0] * (12 - len(row)) for row in witness]
    padded.extend([[0] * 12 for _ in range(12 - len(padded))])
    report["witnesses"] = []
    for name, grid in (("one_cell_recolor_of_canonical_train_1", witness),
                       ("same_witness_padded_to_advertised_minimum_canvas", padded)):
        target = output(grid)
        rival = output(grid, blank_only=True)
        report["witnesses"].append({"name": name, "input": grid,
            "origin": "Canonical train 1 payload cell (3,5) changed from 6 to 4; second witness adds only right/bottom zero padding.",
            "seed": None, "sample_index": None, "overrides": None,
            "observed": signature(grid), "self_check": gen.self_check(grid),
            "copies_overlap": overlap(grid), "python_oracle_output": target,
            "blank_only_rival_output": rival,
            "differing_cells": [[r, c, target[r][c], rival[r][c]] for r in range(len(grid))
                                  for c in range(len(grid[0])) if target[r][c] != rival[r][c]]})
    report["baseline"] = {"seed": 29, "sample_index": 0, "difficulty": None, "overrides": {},
                          "observed": baseline_sig, "self_check": gen.self_check(baseline),
                          "input": baseline, "python_oracle_output": output(baseline),
                          "blank_only_rival_output": output(baseline, blank_only=True)}
    inputs = [witness, padded, baseline] + [pair["input"] for pair in pairs]
    report["racket_input_order"] = ["recolored_canonical", "padded_recolored", "generated_baseline"] + [f"canonical_{p['split']}_{p['pair_index']}" for p in pairs]
    (OUT / "input.json").write_text(json.dumps({"inputs": inputs}) + "\n")
    (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": report["source_hashes"]["generator_sha256"],
                      "canonical": report["canonical"], "sampling": report["sampling"],
                      "witness_differences": [w["differing_cells"] for w in report["witnesses"]]}, indent=2))


if __name__ == "__main__":
    main()
