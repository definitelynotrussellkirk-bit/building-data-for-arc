#!/usr/bin/env python3
"""Task-local candidate-rival investigation; Racket labels come from public apply.

prepare writes inputs and predictions; compare joins an existing public apply
receipt.  Local mirror predictions are diagnostics, never reference labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    for relative in ("shared/runtime", "."):
        helper_root = ancestor / relative
        if (helper_root / "reviewer_support.py").is_file():
            sys.path.insert(0, str(helper_root))
            break
    else:
        continue
    break
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "139d29b1283d"
ROOT = find_root(HERE)


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 3}
    found = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        stack, component = [first], {first}
        while stack:
            r, c = stack.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen:
                    unseen.remove(p)
                    component.add(p)
                    stack.append(p)
        found.append(component)
    return found


def parts(grid, *, component="largest", origin="bbox", limit=None):
    groups = components(grid)
    if component == "first":
        template = groups[0]
    elif component == "first_at_least_four":
        template = next((group for group in groups if len(group) >= 4), max(groups, key=len))
    else:
        template = max(groups, key=len)
    if origin == "first_cell":
        r0, c0 = min(template)
    else:
        r0, c0 = min(r for r, _ in template), min(c for _, c in template)
    shape = sorted((r - r0, c - c0) for r, c in template)
    if limit is not None:
        shape = shape[:limit]
    anchors = [next((r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == target) for target in (1, 2)]
    stamps = [{(ar + r, ac + c) for r, c in shape} for ar, ac in anchors]
    return shape, anchors, stamps


def paint(grid, cells):
    out = [[0] * len(grid[0]) for _ in grid]
    for r, c in cells:
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


def mirror(grid, **kwargs):
    _, _, stamps = parts(grid, **kwargs)
    return paint(grid, stamps[0] & stamps[1])


def bbox_second(grid):
    shape, anchors, stamps = parts(grid)
    ar, ac = anchors[1]
    sh, sw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
    return paint(grid, {(r, c) for r, c in stamps[0] if ar <= r < ar + sh and ac <= c < ac + sw})


def quadrant_second(grid):
    _, anchors, stamps = parts(grid)
    ar, ac = anchors[1]
    return paint(grid, {(r, c) for r, c in stamps[0] if r >= ar and c >= ac})


def overlap_bbox(grid):
    _, _, stamps = parts(grid)
    overlap = stamps[0] & stamps[1]
    if not overlap:
        return paint(grid, set())
    r0, r1 = min(r for r, _ in overlap), max(r for r, _ in overlap)
    c0, c1 = min(c for _, c in overlap), max(c for _, c in overlap)
    return paint(grid, {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)})


CANDIDATE_RIVALS = {
    "first_stamp_clipped_to_second_bbox": bbox_second,
    "first_stamp_southeast_of_second_anchor": quadrant_second,
    "first_occupied_template_cell_origin": lambda grid: mirror(grid, origin="first_cell"),
    "first_four_template_cells": lambda grid: mirror(grid, limit=4),
    "first_color3_component": lambda grid: mirror(grid, component="first"),
    "fill_overlap_bbox": overlap_bbox,
    "first_component_at_least_four": lambda grid: mirror(grid, component="first_at_least_four"),
}


def draw(shape, *, height=8, width=8, template_origin=(1, 1), a1=(4, 4), a2=(5, 4), distractor=False):
    grid = [[0] * width for _ in range(height)]
    if distractor:
        grid[0][0] = 3
    tr, tc = template_origin
    for r, c in shape:
        grid[tr + r][tc + c] = 3
    for point, color in ((a1, 1), (a2, 2)):
        assert grid[point[0]][point[1]] == 0
        grid[point[0]][point[1]] = color
    return grid


def source_identity():
    source = ROOT / "generators" / TASK_ID / "generator.py"
    if not source.is_file():
        source = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("semantic_probe_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rule = next(json.loads(line)["program_solution"] for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK_ID)
    return gen, {
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "probe_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
    }


def rival_fit(rivals, pairs):
    results = {}
    for name, fn in rivals.items():
        matches, errors = [], []
        for i, pair in enumerate(pairs):
            try:
                if fn(pair["input"]) == pair["output"]:
                    matches.append(i)
            except Exception as exc:
                errors.append({"pair": i, "error": f"{type(exc).__name__}: {exc}"})
        results[name] = {"fits": len(matches), "denominator": len(pairs), "matching_indices": matches, "errors": errors}
    return results


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    gen, identity = source_identity()
    plus = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
    cases = [
        ("plus5_no_distractor", draw(plus), "original advertised grid/template domain; hand constructed"),
        ("plus5_earlier_small_distractor", draw(plus, distractor=True), "proposed unique-largest-template extension; outside old one-object distribution"),
    ]
    for size in (6, 7, 8):
        shape = plus | {(r, 1) for r in range(3, size - 2)}
        assert len(shape) == size
        cases.append((f"plus_stem{size}_earlier_small_distractor", draw(shape, height=12, width=12, a1=(4, 7), a2=(5, 7), distractor=True), "proposed unique-largest-template extension; original template_size override domain"))
    for size in (5, 6, 7, 8):
        shape = {(0, 1), (0, 2)} | {(1, c) for c in range(size - 2)}
        assert len(shape) == size
        cases.append((f"horizontal_hook{size}", draw(shape, height=12, width=12, a1=(4, 4), a2=(4, 5), distractor=True), "proposed strong lesson profile; unique largest template and earlier singleton distractor"))
        transposed = {(c, r) for r, c in shape}
        cases.append((f"vertical_hook{size}", draw(transposed, height=12, width=12, a1=(4, 4), a2=(5, 4), distractor=True), "proposed strong lesson profile; unique largest template and earlier singleton distractor"))
    cases.extend([
        ("antiL3_empty_corner", draw({(0, 1), (1, 0), (1, 1)}, a1=(4, 4), a2=(4, 5)), "original advertised grid/template domain; hand constructed"),
        ("plus5_clipped_stamps", draw(plus, a1=(6, 5), a2=(7, 5)), "proposed clipping extension; original random stamps always fit"),
        ("plus5_no_overlap", draw(plus, a1=(4, 0), a2=(4, 5)), "original no_overlap semantic texture; hand constructed"),
    ])
    cutoff = [[0] * 14 for _ in range(12)]
    for c in range(2, 9):
        cutoff[1][c] = 3
    for c in range(2, 10):
        cutoff[3][c] = 3
    cutoff[7][5], cutoff[7][6] = 1, 2
    cases.append(("size7_distractor_before_size8_template", cutoff, "validator-valid unique-largest-template domain; exposes the old distractor-size cutoff"))
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    declared = {}
    for attribute in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, fn in getattr(gen, attribute, {}).items():
            declared[f"{attribute}:{name}"] = fn
    report = {
        "schema": "task-semantic-investigation-v1", "task_id": TASK_ID, **identity,
        "canonical_pairs": [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"]} for p in pairs],
        "candidate_rival_fit": rival_fit(CANDIDATE_RIVALS, pairs),
        "declared_rival_fit": rival_fit(declared, pairs),
        "reference_label_status": "awaiting public Racket apply; mirror diagnostics are not reference labels",
        "cases": [],
    }
    for name, grid, domain in cases:
        report["cases"].append({"name": name, "input": grid, "domain_note": domain, "self_check_findings": gen.self_check(grid), "local_mirror_output": mirror(grid), "candidate_predictions": {key: fn(grid) for key, fn in CANDIDATE_RIVALS.items()}, "declared_predictions": {key: fn(grid) for key, fn in declared.items()}})
    (output / "input.json").write_text(json.dumps([grid for _, grid, _ in cases], indent=2) + "\n")
    (output / "predictions.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output), **identity, "cases": len(cases), "canonical_pairs": len(pairs), "candidate_fit": report["candidate_rival_fit"], "declared_fit": report["declared_rival_fit"]}, indent=2))


def compare(output, receipt):
    report = json.loads((output / "predictions.json").read_text())
    actual = json.loads(receipt.read_text())
    report["racket_receipt"] = str(receipt)
    report["racket_receipt_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    report["reference_label_status"] = "public Racket apply outputs compared"
    rows = actual.get("results", [])
    assert len(rows) == len(report["cases"]), (actual.keys(), len(rows))
    for case, result in zip(report["cases"], rows):
        case["racket_output"] = result["output"]
        case["racket_error"] = result.get("error")
        case["mirror_matches_racket"] = case["local_mirror_output"] == result["output"]
        case["candidate_refuted"] = [name for name, prediction in case["candidate_predictions"].items() if prediction != result["output"]]
        case["declared_refuted"] = [name for name, prediction in case["declared_predictions"].items() if prediction != result["output"]]
    (output / "verified.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"identity": {key: report[key] for key in ("generator_sha256", "rule_hash")}, "cases": [{"name": case["name"], "racket_error": case["racket_error"], "mirror_matches_racket": case["mirror_matches_racket"], "candidate_refuted": case["candidate_refuted"], "declared_refuted": case["declared_refuted"]} for case in report["cases"]]}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "compare"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.out)
    else:
        compare(args.out, args.racket)


if __name__ == "__main__":
    main()
