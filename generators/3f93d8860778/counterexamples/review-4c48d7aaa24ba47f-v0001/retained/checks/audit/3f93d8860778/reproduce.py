"""Reproduce the source-bound spans=None lesson ambiguity, without private runners."""
from argparse import ArgumentParser
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = ArgumentParser()
parser.add_argument("--repo", required=True, type=Path)
args = parser.parse_args()
root = args.repo.resolve()
destination = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "shared" / "runtime"))
from reviewer_support import canonical_pairs, find_root

source = root / "generators" / "3f93d8860778" / "generator.py"
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == "966b81f54c5130ca20546ff4a973bdbe58b8530d6f0b749291ca614b0b515b91", source_hash
spec = importlib.util.spec_from_file_location("audit_3f93d8860778", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def fill(grid, *, one_colour=False):
    result = deepcopy(grid)
    pairs = []
    for column in range(len(grid[0])):
        nonzero = [(row, grid[row][column]) for row in range(len(grid)) if grid[row][column]]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            pairs.append((column, nonzero[0][0], nonzero[1][0], nonzero[0][1]))
    for column, top, bottom, colour in pairs:
        if one_colour:
            colour = min(pair[3] for pair in pairs)
        for row in range(top, bottom + 1):
            result[row][column] = colour
    return result


canonical = canonical_pairs("3f93d8860778", root=find_root(source))
assert all(fill(pair["input"]) == pair["output"] for pair in canonical)
assert all(fill(pair["input"], one_colour=True) != pair["output"] for pair in canonical)
lesson = []
for index in (1, 2, 3, 4):
    grid = generator.generate(6, index, difficulty="easy", spans=None)
    expected = fill(grid)
    rival = fill(grid, one_colour=True)
    artifact = "racket.json" if index == 3 else f"racket-demo-{index}.json"
    actual_receipt = json.loads((destination / artifact).read_text())
    actual = actual_receipt["results"][0]["output"]
    assert actual_receipt["executed_rule_hash"] == "abdf780ecbe7"
    assert actual_receipt["generator_sha256"] == source_hash
    assert actual == expected
    assert actual_receipt["results"][0]["input"] == grid
    assert generator.self_check(grid) == []
    assert generator.LESSON_COMPETITORS["paint_all_intervals_one_colour"](grid) == rival
    omitted = generator.generate(6, index, difficulty="easy")
    row = {"seed": 6, "sample_index": index, "difficulty": "easy", "overrides": {"spans": None},
           "input": grid, "self_check": generator.self_check(grid),
           "observed": generator.observe_overrides(grid),
           "omitted_overrides_observed": generator.observe_overrides(omitted),
           "actual_racket_output": actual, "rival_prediction": rival,
           "rival_matches_racket": rival == actual,
           "rule_text_sha256": actual_receipt["rule_text_sha256"]}
    lesson.append(row)

assert all(pair["rival_matches_racket"] for pair in lesson if pair["sample_index"] != 3)
assert not lesson[2]["rival_matches_racket"]
query = lesson[2]
changed = [{"row": r, "column": c, "racket": query["actual_racket_output"][r][c],
            "rival": query["rival_prediction"][r][c]}
           for r in range(len(query["input"])) for c in range(len(query["input"][0]))
           if query["actual_racket_output"][r][c] != query["rival_prediction"][r][c]]
record = {"task_id": "3f93d8860778", "generator_sha256": source_hash,
          "executed_rule_hash": "abdf780ecbe7", "query_sample_index": 3,
          "canonical_reference_pairs_checked": len(canonical), "lesson": lesson,
          "query_mismatch_cells": changed,
          "hook_reasons": generator.lesson_identifiable(
              [{"input": pair["input"], "output": pair["actual_racket_output"]}
               for pair in lesson if pair["sample_index"] != 3],
              {"input": query["input"], "output": query["actual_racket_output"]})}
(destination / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"generator_sha256": source_hash, "canonical_pairs": len(canonical),
                  "racket_outputs_verified": len(lesson), "query_mismatch_cells": changed,
                  "hook_reasons": record["hook_reasons"]}, indent=2))
