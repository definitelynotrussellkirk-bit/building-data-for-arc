#!/usr/bin/env python3
"""Recheck the retained density-order teaching lead on unchanged selected source.

Run from the packet root:
  WORK/.venv/bin/python review.py run ../.venv/bin/python \
    ../checks/audit/d5178d26d905/probe.py

This is an intentional rival audit, not a solve attempt. The independent parser
below calls no generator parsing/mirror helpers. Fresh labels come from public
Catalog.apply (canonical inputs) and Catalog.generate (the actual lesson).
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "d5178d26d905"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def facts(grid):
    """Independent structural reading of the reference/template row rule."""
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(row[c] == 5 for row in grid)]
    assert len(dividers) == 1
    d = dividers[0]

    def panel(start, stop):
        return [row[start:stop] for row in grid if any(value != 5 for value in row[start:stop])]

    left, right = panel(0, d), panel(d + 1, w)
    if all(value in (0, 4) for row in left for value in row):
        reference, template = left, right
    else:
        reference, template = right, left
    signatures = Counter(map(tuple, template))
    modal = [row for row, count in signatures.items() if count == max(signatures.values())]
    assert len(modal) == 1
    normal = list(modal[0])
    template_columns = [c for c, value in enumerate(normal) if value]
    colors = [normal[c] for c in template_columns]
    off_line = [c for c in range(len(normal)) if c not in template_columns]
    specials = [row for row in template if row != normal]
    positive = [row for row in reference if 4 in row]
    reference_normal = min(positive, key=lambda row: row.count(4))
    reference_columns = [c for c, value in enumerate(reference_normal) if value == 4]
    reference_special_rows = [r for r, row in enumerate(reference) if 4 in row and row != reference_normal]
    assert len(reference_columns) == len(template_columns)
    assert len(reference_special_rows) == len(specials)
    return {
        "reference": reference, "columns": reference_columns, "colors": colors,
        "special_rows": reference_special_rows,
        "yellow_counts": [reference[r].count(4) for r in reference_special_rows],
        "fills": [row[off_line[0]] for row in specials],
        "retention": [[row[c] == color for c, color in zip(template_columns, colors)] for row in specials],
    }


def predict(grid, *, density_order=False):
    info = facts(grid)
    rows = info["special_rows"]
    if density_order:
        rows = sorted(rows, key=lambda r: (info["reference"][r].count(4), r))
    index_for = {row: index for index, row in enumerate(rows)}
    result = []
    for r, reference_row in enumerate(info["reference"]):
        if r in index_for:
            index = index_for[r]
            row = [info["fills"][index]] * len(reference_row)
            for k, c in enumerate(info["columns"]):
                if info["retention"][index][k]:
                    row[c] = info["colors"][k]
        else:
            row = [0] * len(reference_row)
            for c, color in zip(info["columns"], info["colors"]):
                row[c] = color
        result.append(row)
    return result


def differences(expected, observed):
    return [[r, c, expected[r][c], observed[r][c]] for r in range(len(expected))
            for c in range(len(expected[0])) if expected[r][c] != observed[r][c]]


def main():
    report_path = OUT / "evidence.json"
    if report_path.exists():
        raise FileExistsError("Preserve prior evidence; use a fresh directory for a repeated audit")
    gen, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    catalog = Catalog(ROOT)
    canonical_receipt = catalog.apply(TASK_ID, [pair["input"] for pair in canonical], timeout=180)
    (OUT / "canonical-racket.json").write_text(json.dumps(canonical_receipt, indent=2) + "\n")
    episodes = catalog.generate(TASK_ID, count=1, seed=0, sample_index=7, difficulty="medium",
                                n_train=3, n_test=1, overrides={}, allow_unapproved=True, timeout=180)
    (OUT / "generated-lesson.json").write_text(json.dumps(episodes, indent=2) + "\n")
    assert len(episodes) == 1
    episode = episodes[0]
    lesson = episode["train"] + episode["test"]
    recipe = {"seed": 0, "sample_index": 7, "difficulty": "medium", "overrides": {}, "n_train": 3, "n_test": 1}
    canonical_results = []
    for pair, authority in zip(canonical, canonical_receipt["results"], strict=True):
        canonical_results.append({
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "input_sha256": digest(pair["input"]),
            "self_check": gen.self_check(deepcopy(pair["input"])),
            "strict_canonical_like": gen.strict_canonical_like(deepcopy(pair["input"])),
            "retained_label_matches_racket": pair["output"] == authority["output"],
            "independent_mirror_matches_racket": predict(pair["input"]) == authority["output"],
            "density_order_rival_fits_racket": predict(pair["input"], density_order=True) == authority["output"],
        })
    lesson_results = []
    for index, pair in zip(episode["sample_indices"], lesson, strict=True):
        info = facts(pair["input"])
        rival = predict(pair["input"], density_order=True)
        lesson_results.append({
            "sample_index": index, "input": pair["input"], "authoritative_output": pair["output"],
            "rival_output": rival, "independent_mirror_matches_racket": predict(pair["input"]) == pair["output"],
            "density_order_rival_fits_racket": rival == pair["output"],
            "self_check": gen.self_check(deepcopy(pair["input"])),
            "strict_canonical_like": gen.strict_canonical_like(deepcopy(pair["input"])),
            "special_reference_rows": info["special_rows"], "special_reference_yellow_counts": info["yellow_counts"],
            "density_order": sorted(info["special_rows"], key=lambda r: (info["reference"][r].count(4), r)),
            "diff_cells_authority_then_rival": differences(pair["output"], rival),
        })
    declarations = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        entries = getattr(gen, namespace, {})
        assert isinstance(entries, dict) and all(callable(fn) for fn in entries.values())
        declarations[namespace] = list(entries)
    declared_scores = {
        name: {"demonstration_refuting_positions": [i for i, pair in enumerate(episode["train"])
                                                     if rival(deepcopy(pair["input"])) != pair["output"]],
               "query_matches": rival(deepcopy(episode["test"][0]["input"])) == episode["test"][0]["output"]}
        for name, rival in gen.LESSON_COMPETITORS.items()
    }
    sweep = Counter()
    first_difference = None
    for band in ("easy", "medium", "hard"):
        for seed in range(3):
            for sample_index in range(15):
                grid = gen.generate(seed, sample_index, difficulty=band)
                sweep["inputs"] += 1
                sweep["self_check_passed"] += gen.self_check(grid) == []
                sweep["strict_passed"] += gen.strict_canonical_like(grid) == []
                sweep["independent_mirror_matches_generator_mirror"] += predict(grid) == gen.rule_mirror(grid)
                match = predict(grid, density_order=True) == predict(grid)
                sweep["density_rival_fits_independent_python_mirror"] += match
                if not match and first_difference is None:
                    first_difference = {"seed": seed, "sample_index": sample_index, "difficulty": band}
    checks = {
        "source_binding": canonical_receipt["generator_sha256"] == episode["provenance"]["generator_sha256"] == source_sha,
        "rule_binding": canonical_receipt["rule_hash_matches_catalog"] and canonical_receipt["executed_rule_hash"] == episode["executed_rule_hash"] == gen.RULE_HASH,
        "canonical_fit": len(canonical_results) == 10 and all(row["density_order_rival_fits_racket"] for row in canonical_results),
        "canonical_parity": all(row["retained_label_matches_racket"] and row["independent_mirror_matches_racket"] for row in canonical_results),
        "actual_production_indices": episode["sample_indices"] == [7, 8, 9, 10] and not episode["rejections"],
        "lesson_domain": all(row["self_check"] == row["strict_canonical_like"] == [] for row in lesson_results),
        "lesson_mirror_parity": all(row["independent_mirror_matches_racket"] for row in lesson_results),
        "three_demo_ambiguity": [row["density_order_rival_fits_racket"] for row in lesson_results] == [True, True, True, False],
        "existing_hook_accepts": gen.lesson_identifiable(deepcopy(episode["train"]), deepcopy(episode["test"][0])) == [],
    }
    report = {
        "schema": "d5178d26d905-density-order-audit-v1", "task_id": TASK_ID,
        "classification": "reproduced_teaching_defect" if all(checks.values()) else "reproduction_not_confirmed",
        "reproduction_checks": checks,
        "lead": "Independently rechecked the unresolved same-source density-order finding in review_index.json",
        "source": {"generator_path": str(source.relative_to(ROOT)), "generator_sha256": source_sha,
                   "generator_version": gen.VERSION,
                   "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "canonical_path": str(canonical_path(ROOT).relative_to(ROOT)),
                   "canonical_pairs_sha256": digest(canonical),
                   "executed_rule_hash": canonical_receipt["executed_rule_hash"],
                   "rule_text_sha256": canonical_receipt["rule_text_sha256"]},
        "canonical": canonical_results,
        "canonical_unique_inputs": len({digest(pair["input"]) for pair in canonical}),
        "production_recipe": recipe, "accepted_sample_indices": episode["sample_indices"],
        "rejections": episode["rejections"], "lesson": lesson_results,
        "declared_inventory": declarations, "declared_lesson_scores": declared_scores,
        "declared_lesson_hook_reasons": gen.lesson_identifiable(deepcopy(episode["train"]), deepcopy(episode["test"][0])),
        "python_only_sweep": {"seed_range": [0, 2], "sample_index_range": [0, 14],
                              "bands": ["easy", "medium", "hard"], "counts": dict(sweep),
                              "first_density_rival_disagreement": first_difference,
                              "labels": "Independent Python mirror; not fresh Racket labels"},
        "fresh_racket_scope": "10 canonical records through Catalog.apply plus the four accepted production pairs through Catalog.generate",
        "limits": "One reproduced production lesson; overlapping random support and other rivals not exhausted. No audited source changed.",
    }
    (OUT / "query-input.json").write_text(json.dumps({"input": lesson[-1]["input"]}, indent=2) + "\n")
    (OUT / "query-rival.json").write_text(json.dumps(lesson_results[-1]["rival_output"], indent=2) + "\n")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    assert all(checks.values()), checks
    print(json.dumps({"classification": report["classification"], "generator_sha256": source_sha,
                      "canonical_racket_fit": f"{sum(row['density_order_rival_fits_racket'] for row in canonical_results)}/{len(canonical_results)}",
                      "accepted_indices": episode["sample_indices"], "rejections": len(episode["rejections"]),
                      "query_differing_cells": len(lesson_results[-1]["diff_cells_authority_then_rival"]),
                      "declared_lesson_hook_reasons": report["declared_lesson_hook_reasons"],
                      "python_only_sweep": dict(sweep)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
