"""Source-bound centroid shortcut audit; run through packet review.py run.

prepare writes <=64 inputs using public portable helpers. verify consumes only
the retained result of the public arcpuzzles apply command, never a Python label
substitute. No selected generator, rule, catalog, or test source is modified.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "92f4d4eb0dbb"
OUT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def stats(grid):
    rows = [r for r, row in enumerate(grid) for v in row if v == 1]
    lo, hi = min(rows), max(rows)
    counts = [rows.count(r) for r in range(lo, hi + 1)]
    return {
        "row_min": lo, "row_max": hi,
        "bbox_midpoint": str(Fraction(lo + hi, 2)),
        "pixel_centroid_row": str(Fraction(sum(rows), len(rows))),
        "occupied_row_counts": counts,
        "row_counts_palindromic": counts == counts[::-1],
    }


def bbox_output(grid):
    rows = [r for r, row in enumerate(grid) for v in row if v == 1]
    return [[2 if v == 1 and 2 * r > min(rows) + max(rows) else v
             for v in row] for r, row in enumerate(grid)]


def centroid_output(grid):
    rows = [r for r, row in enumerate(grid) for v in row if v == 1]
    count, total = len(rows), sum(rows)
    return [[2 if v == 1 and r * count > total else v
             for v in row] for r, row in enumerate(grid)]


def context():
    root = find_root(__file__)
    gen, source, sha = load_selected_generator(TASK, root=root)
    records = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if line.strip() and json.loads(line).get("task_id") == TASK]
    rules = [{
        "variant": i,
        "exact_text_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "normalized_sha256": hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest(),
    } for i, row in enumerate(records)]
    binding = {
        "task_id": TASK, "generator_source": str(source.relative_to(root)),
        "generator_sha256": sha, "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH, "canonical_rules": rules,
        "canonical_data_path": str(canonical_path(root).relative_to(root)),
        "provenance": "Fresh current-source audit; inherited review receipts are not rerun evidence.",
    }
    assert all(row["normalized_sha256"][:12] == gen.RULE_HASH for row in rules)
    return root, gen, binding


def prepare():
    root, gen, binding = context()
    grids, cases = [], []

    def add(grid, **metadata):
        cases.append({"input_index": len(grids), "input_sha256": digest(grid),
                      "self_check": gen.self_check(grid),
                      "strict_canonical_like": gen.strict_canonical_like(grid),
                      **stats(grid), **metadata})
        grids.append(grid)

    canonical = canonical_pairs(TASK, root=root)
    for pair in canonical:
        add(pair["input"], category="canonical", seed=None, sample_index=None,
            overrides=None, canonical_identity={k: pair[k] for k in ("variant", "split", "pair_index")},
            canonical_output=pair["output"])
    for band in ("easy", "medium", "hard"):
        for index in range(16):
            grid = gen.generate(0, index, difficulty=band)
            add(grid, category="generated", seed=0, sample_index=index,
                difficulty=band, overrides={}, observed=gen.observe_overrides(grid))
    fixture = [[0] * 7 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 6):
            if r in (1, 5) or c in (1, 5):
                fixture[r][c] = 1
    fixture[5][3] = 0
    add(fixture, category="counterexample", seed=None, sample_index=None, overrides=None,
        construction="Hand-built 7x7 frame at rows/columns 1..5, then remove bottom cell (5,3).",
        validator_domain=True, current_sampler_support=False,
        domain_explanation="Passes the documented structural envelope; absent from the four emitted morphology templates.")
    assert len(grids) <= 64
    assert all(not row["self_check"] and not row["strict_canonical_like"] for row in cases)
    write("input.json", grids)
    write("cases.json", {"binding": binding, "cases": cases})
    print(json.dumps({"prepared": len(grids), "categories": dict(Counter(c["category"] for c in cases)),
                      "binding": binding}, indent=2))


def verify():
    _, gen, binding = context()
    saved = json.loads((OUT / "cases.json").read_text())
    assert binding == saved["binding"], "Audited generator/rule changed since preparation"
    grids = json.loads((OUT / "input.json").read_text())
    actual = json.loads((OUT / "racket.json").read_text())
    assert actual["schema"] == "arcpuzzles-apply-v1"
    assert actual["generator_sha256"] == binding["generator_sha256"]
    assert actual["executed_rule_hash"] == binding["rule_hash"]
    assert actual["rule_hash_matches_catalog"]
    assert all(row["valid_output"] and row["error"] is None for row in actual["results"])
    assert [row["input"] for row in actual["results"]] == grids
    outputs = [row["output"] for row in actual["results"]]
    assert len(outputs) == len(grids) == len(saved["cases"])
    rows = []
    for metadata, grid, output in zip(saved["cases"], grids, outputs):
        assert metadata["input_sha256"] == digest(grid)
        row = {**metadata, "actual_output_sha256": digest(output),
               "rival_matches_racket": centroid_output(grid) == output,
               "bbox_mirror_matches_racket": bbox_output(grid) == output}
        if "canonical_output" in row:
            row["canonical_matches_racket"] = row.pop("canonical_output") == output
            row["declared_canonical_shortcuts_fit"] = {
                name: rival(deepcopy(grid)) == output for name, rival in gen.CANONICAL_SHORTCUTS.items()}
        rows.append(row)
    assert all(row["bbox_mirror_matches_racket"] for row in rows)
    canonical = [row for row in rows if row["category"] == "canonical"]
    generated = [row for row in rows if row["category"] == "generated"]
    assert all(row["canonical_matches_racket"] and row["rival_matches_racket"] for row in canonical)
    assert all(row["rival_matches_racket"] and row["row_counts_palindromic"] for row in generated)
    assert all(all(row["declared_canonical_shortcuts_fit"].values()) for row in canonical)
    templates = {}
    for row in generated:
        key = f"{row['observed']['shape_kind']}:{row['observed']['span']}"
        templates[key] = row["occupied_row_counts"]
    assert len(templates) == 12
    lessons = []
    for band in ("easy", "medium", "hard"):
        sequence = [row for row in generated if row["difficulty"] == band]
        for start in range(13):
            indexes = [row["input_index"] for row in sequence[start:start + 4]]
            pairs = [{"input": grids[i], "output": outputs[i]} for i in indexes]
            lessons.append({
                "difficulty": band, "seed": 0, "start": start, "input_indexes": indexes,
                "production_contract_errors": gen.lesson_identifiable(pairs[:3], pairs[3]),
                "rotation_contract_errors": [gen.lesson_identifiable([p for j, p in enumerate(pairs) if j != q], pairs[q]) for q in range(4)],
                "centroid_fits_all_four_pairs": all(centroid_output(p["input"]) == p["output"] for p in pairs),
            })
    assert all(not row["production_contract_errors"] and not any(row["rotation_contract_errors"])
               and row["centroid_fits_all_four_pairs"] for row in lessons)
    witness = next(row for row in rows if row["category"] == "counterexample")
    i = witness["input_index"]
    expected, rival = outputs[i], centroid_output(grids[i])
    assert expected != rival
    witness.update({"input": grids[i], "actual_racket_output": expected,
                    "expected_output_basis": "Public arcpuzzles apply selected Racket output",
                    "rival_output": rival,
                    "differing_cells": [{"row": r, "column": c, "racket": expected[r][c], "rival": rival[r][c]}
                                        for r in range(len(expected)) for c in range(len(expected[0]))
                                        if expected[r][c] != rival[r][c]]})
    report = {
        "schema": "review-audit-centroid-shortcut-v1", "binding": binding,
        "racket_binding": {key: actual[key] for key in (
            "schema", "reference", "rule_task_id", "rule_file", "executed_rule_hash",
            "catalog_rule_hash", "rule_hash_matches_catalog", "rule_text_sha256",
            "generator_sha256", "command", "cwd")},
        "source_anchors": [
            {"path": "generators/92f4d4eb0dbb/generator.py", "lines": [155, 189], "purpose": "Four palindromic-row-count morphology formulas"},
            {"path": "generators/92f4d4eb0dbb/generator.py", "lines": [192, 217], "purpose": "Only horizontal reflection and translation applied to each morphology"},
            {"path": "generators/92f4d4eb0dbb/generator.py", "lines": [246, 319], "purpose": "Structural validator permits the asymmetric witness"},
            {"path": "generators/92f4d4eb0dbb/generator.py", "lines": [388, 412], "purpose": "Declared lesson rival covers inclusivity but omits centroid threshold"},
        ],
        "finding": "Possible shortcut / teaching-support gap, not a generated-label mismatch",
        "rival": "Recolor a color-1 cell when its row is strictly greater than the mean row of every color-1 pixel (exact rational comparison).",
        "summary": {
            "canonical_rival_fit": [len(canonical), len(canonical)],
            "generated_rival_fit": [len(generated), len(generated)],
            "generated_unique_inputs": len({row["input_sha256"] for row in generated}),
            "generated_seed": 0, "sample_indexes": [0, 15], "difficulty_bands": ["easy", "medium", "hard"],
            "templates_covered": len(templates), "accepted_inputs": [len(rows), len(rows)],
            "racket_vs_bbox_mirror_matches": [len(rows), len(rows)],
            "overlapping_ordered_lessons": len(lessons),
            "rotated_assemblies_including_original_query": 4 * len(lessons),
            "lesson_policy": "Three consecutive demonstrations, fourth pair query; starts 0..12 at seed 0 in each band; rotation positions 0..3.",
            "centroid_query_ambiguities_within_generated_lessons": 0,
            "centroid_status_on_generated_lessons": "survived_all; answer-equivalent including each query",
            "canonical_shortcut_names": list(gen.CANONICAL_SHORTCUTS),
            "lesson_competitor_names": list(gen.LESSON_COMPETITORS),
        },
        "support_argument": "Each of the four source morphology formulas gives palindromic row counts for every advertised span 5..7. Therefore the pixel centroid equals the occupied bounding-box midpoint. Horizontal reflection, placement, canvas dimensions and difficulty preserve the equality. The generator cannot emit a counterexample to this rival under its present formulas.",
        "templates": templates,
        "counterexample": witness,
        "cases": rows[:-1], "lessons": lessons,
        "limitations": [
            "The separating input is hand-built and validator-accepted, but outside current emitted morphology support.",
            "No centroid ambiguity is claimed for production queries generated by this unchanged sampler.",
            "48 current-source generated inputs and 4 canonical inputs received fresh Racket labels; universal support equivalence is a separate source argument, not an all-seed runtime census.",
            "Inherited 56-test, 12-stage battery and 300-lesson results in notes.md were read but not rerun or claimed as fresh evidence.",
            "No generator, selected rule, tests, shared tool or catalog source was edited; no approval or audit resolution is claimed.",
        ],
        "racket_evidence": {"path": "checks/audit/92f4d4eb0dbb/racket.json",
                            "sha256": hashlib.sha256((OUT / "racket.json").read_bytes()).hexdigest()},
    }
    write("evidence.json", report)
    print(json.dumps({"binding": binding, "summary": report["summary"],
                      "counterexample_differences": witness["differing_cells"]}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
