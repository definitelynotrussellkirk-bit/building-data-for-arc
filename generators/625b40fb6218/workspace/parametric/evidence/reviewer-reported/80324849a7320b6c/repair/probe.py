"""Reproduce the color-priority gate repair with unchanged Racket authority."""
from pathlib import Path
import hashlib
import importlib.util
import json
import time

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, load_selected_generator

ROOT = Path(__file__).resolve().parents[2] / "repo"
HERE = Path(__file__).resolve().parent
TASK = "625b40fb6218"
SEED = 11180556991150295210
BASELINE = ROOT.parent / ".review/baseline/repo/generators" / TASK / "generator.py"
started = time.monotonic()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def favorite(grid, color):
    width = (len(grid[0]) - 1) // 2
    return [[2 if a and not b else 1 if b and not a else
             color if a and b and color in (a, b) else a
             for a, b in zip(row[:width], row[width + 1:])] for row in grid]


def scene(a, b, shift=0):
    grid = [[0] * 9 for _ in range(6)]
    for row in grid:
        row[4] = 5
    grid[0][0] = a
    grid[0][6] = b
    for row, col, color in ((1, 0, a), (1, 1, b), (1, 2, a)):
        grid[row][col] = grid[row][col + 5] = color
    grid[2 + shift][0] = a
    grid[2 + shift][5] = b
    return grid


current, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
baseline = load_file(BASELINE, "color_gate_before")
assert baseline.VERSION == current.VERSION == "2.0.0"
unchanged = 0
for band in (None, "easy", "medium", "hard"):
    for index in range(8):
        assert baseline.generate(1700 + index, index * 3, difficulty=band) == current.generate(
            1700 + index, index * 3, difficulty=band)
        unchanged += 1

canonical = canonical_pairs(TASK, root=ROOT)
witness_inputs = [current.generate(SEED, i) for i in range(6, 11)]
small_inputs = [scene(3, 6), scene(3, 4, shift=1)]
inputs = [row["input"] for row in canonical] + witness_inputs + small_inputs
assert all(current.self_check(grid) == [] for grid in inputs)
receipt = Catalog(ROOT).apply(TASK, inputs, reference="canonical", timeout=85,
                             check_generator_domain=True)
(HERE / "racket.json").write_text(json.dumps(receipt, indent=2) + "\n")
assert receipt["generator_sha256"] == source_hash
assert receipt["executed_rule_hash"] == receipt["catalog_rule_hash"] == "53f987296312"
assert receipt["rule_hash_matches_catalog"] is True
assert all(row["error"] is None for row in receipt["results"])
outputs = [row["output"] for row in receipt["results"]]
assert all(expected["output"] == observed for expected, observed in
           zip(canonical, outputs[:len(canonical)], strict=True))
assert all(current.rule_mirror(grid) == output for grid, output in zip(inputs, outputs, strict=True))
start = len(canonical)
witness = [{"input": grid, "output": output} for grid, output in
           zip(witness_inputs, outputs[start:start + 5], strict=True)]
before = baseline.lesson_identifiable(witness[:4], {"input": witness[4]["input"]})
after = current.lesson_identifiable(witness[:4], {"input": witness[4]["input"]})
assert before == []
assert any("color_priority_4" in reason for reason in after)
assert all(favorite(row["input"], 4) == row["output"] for row in witness[:4])
rival_query = favorite(witness[4]["input"], 4)
differences = [{"row": r, "col": c, "racket": a, "rival": b}
               for r, (ar, br) in enumerate(zip(witness[4]["output"], rival_query))
               for c, (a, b) in enumerate(zip(ar, br)) if a != b]
assert differences == [{"row": 1, "col": 6, "racket": 3, "rival": 4}]
small = [{"input": grid, "output": output} for grid, output in
         zip(small_inputs, outputs[-2:], strict=True)]
minimal = {"schema": "625b40fb6218-color-priority-gate-v1", "task_id": TASK,
           "baseline_generator_sha256": digest(BASELINE), "generator_sha256": source_hash,
           "canonical_rule_hash": "53f987296312", "favorite_color": 4,
           "demonstrations": small[:1], "query": small[1],
           "before_reasons": baseline.lesson_identifiable(small[:1], {"input": small[1]["input"]}),
           "after_reasons": current.lesson_identifiable(small[:1], {"input": small[1]["input"]})}
assert minimal["before_reasons"] == []
assert any("color_priority_4" in reason for reason in minimal["after_reasons"])
(ROOT / "generators" / TASK / "counterexamples/color-priority-gate.json").write_text(
    json.dumps(minimal, indent=2) + "\n")
(HERE / "witness.json").write_text(json.dumps({
    "seed": SEED, "sample_indices": list(range(6, 11)), "demonstrations": witness[:4],
    "query": witness[4], "before_reasons": before, "after_reasons": after,
    "differences": differences}, indent=2) + "\n")
report = {"task_id": TASK, "status": "passed", "scope": "canonical lesson gate only",
          "baseline_generator_sha256": digest(BASELINE), "generator_sha256": source_hash,
          "probe_sha256": digest(Path(__file__)), "rule_hash": "53f987296312",
          "canonical_occurrences_racket_verified": len(canonical),
          "generated_witness_pairs_racket_verified": len(witness_inputs),
          "minimal_pairs_racket_verified": len(small_inputs),
          "unchanged_input_comparisons": unchanged, "before_reasons": before,
          "after_reasons": after, "query_differences": differences,
          "racket_receipt_sha256": digest(HERE / "racket.json"),
          "elapsed_seconds": round(time.monotonic() - started, 3),
          "limitations": [
              "Ordinary sampling is unchanged and can emit color-underidentified lessons.",
              "A caller must enforce the lesson gate or construct distinguishing demonstrations.",
              "The finite eight-rival class does not establish arbitrary-program identifiability.",
              "No approval or training-admission record was changed."]}
(HERE / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
