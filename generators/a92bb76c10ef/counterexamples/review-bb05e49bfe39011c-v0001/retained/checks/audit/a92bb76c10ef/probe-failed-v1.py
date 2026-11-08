"""Findings-only audit; selected source is never modified."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "a92bb76c10ef"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def counts(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = Counter()
    vertical = False
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        todo = [start]
        unseen.remove(start)
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen and grid[q[0]][q[1]] == color:
                    unseen.remove(q)
                    todo.append(q)
        result[color] += 1
        vertical |= len({r for r, c in cells}) > 1
    return result, vertical


def bar(counter):
    return [[2] * counter[2] + [0] + [3] * counter[3] + [0] + [4] * counter[4]]


def horizontal_runs(grid):
    counter = Counter()
    for row in grid:
        previous = 0
        for value in row:
            if value in (2, 3, 4) and value != previous:
                counter[value] += 1
            previous = value
    return bar(counter)


def main():
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    pairs = canonical_pairs(TASK, root=ROOT)
    witness = [[0] * 8 for _ in range(6)]
    witness[1][1] = witness[2][1] = 2
    witness[1][4] = witness[1][5] = 3
    witness[4][3] = 4
    (HERE / "vertical-input.json").write_text(json.dumps(witness) + "\n")
    population = []
    selected = []
    for band in ("easy", "medium", "hard"):
        tally = Counter()
        for seed in range(5):
            for index in range(20):
                grid = gen.generate(seed, index, difficulty=band)
                n, vertical = counts(grid)
                tally["draws"] += 1
                tally["accepted"] += not bool(gen.self_check(grid))
                tally["vertical_components"] += vertical
                tally["horizontal_rival_agrees_python_mirror"] += horizontal_runs(grid) == bar(n)
                if seed == 0 and index < 5:
                    selected.append({"input": grid, "seed": seed, "sample_index": index, "difficulty": band})
        population.append({"difficulty": band, **tally})
    inputs = [p["input"] for p in pairs] + [witness] + [p["input"] for p in selected]
    actual = Catalog(ROOT).apply(TASK, inputs)
    assert actual["generator_sha256"] == digest
    assert actual["rule_hash_matches_catalog"] is True
    outputs = [row["output"] for row in actual["results"]]
    assert len(outputs) == len(inputs) and all(o is not None for o in outputs)
    mismatches = []
    for index, pair in enumerate(pairs):
        if pair["output"] != outputs[index]:
            mismatches.append({"canonical_pair_index": index,
                               "variant": pair["variant"], "split": pair["split"],
                               "pair_index": pair["pair_index"], "input": pair["input"],
                               "stored_output": pair["output"], "racket_output": outputs[index],
                               "self_check_errors": gen.self_check(pair["input"])})
    wi = len(pairs)
    default = gen.generate(0, 0, difficulty="easy")
    override_probe = {
        "palette_kind_warm_equals_default": gen.generate(0, 0, difficulty="easy", palette_kind="warm") == default,
        "unknown_key_accepted": None,
    }
    try:
        gen.generate(0, 0, unknown_axis=True)
        override_probe["unknown_key_accepted"] = True
    except (ValueError, TypeError):
        override_probe["unknown_key_accepted"] = False
    report = {
        "schema": "a92bb76c10ef-findings-only-audit-v1",
        "task_id": TASK, "generator_sha256": digest,
        "canonical_file_sha256": hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),
        "rule_hash": actual["rule_hash"], "reference": actual["reference"],
        "prior_lead": "review-3e00dae96bf093a3:v0001 (horizontal-run coverage finding)",
        "canonical_labels": {"checked": len(pairs), "mismatches": mismatches,
                             "matched": len(pairs) - len(mismatches)},
        "generated_population": population,
        "vertical_witness": {"input": witness, "self_check_errors": gen.self_check(witness),
                             "racket_output": outputs[wi], "horizontal_rival_output": horizontal_runs(witness),
                             "domain": "validator-lawful; outside horizontal-only production support"},
        "generated_racket_cases": [{**meta, "racket_output": outputs[wi + 1 + i],
                                   "horizontal_rival_output": horizontal_runs(meta["input"])}
                                  for i, meta in enumerate(selected)],
        "override_probe": override_probe,
        "limitations": "300 Python-observed draws; 15 generated + 5 canonical + 1 hand-made actual Racket cases. No audited source edits.",
    }
    (HERE / "racket-batch.json").write_text(json.dumps(actual, indent=2) + "\n")
    (HERE / "findings.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": digest, "canonical_checked": len(pairs),
                      "canonical_mismatches": len(mismatches), "racket_cases": len(inputs),
                      "generated_population": population, "override_probe": override_probe}, indent=2))


if __name__ == "__main__":
    main()
