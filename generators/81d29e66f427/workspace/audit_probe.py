"""Reproduce the two assignment audit findings without private runner imports.

Usage from packet root::

  python3 run_with_racket.py python3 generators/81d29e66f427/workspace/audit_probe.py prepare --out ../checks/audit
  python3 run_with_racket.py python3 -m arcpuzzles apply 15dd333aa99b --input ../checks/audit/15dd333aa99b/input.json --out ../checks/audit/15dd333aa99b/racket.json
  python3 run_with_racket.py python3 -m arcpuzzles apply d17f2bbc0878 --input ../checks/audit/d17f2bbc0878/input.json --out ../checks/audit/d17f2bbc0878/racket.json
  python3 run_with_racket.py python3 generators/81d29e66f427/workspace/audit_probe.py verify --out ../checks/audit

The Racket outputs are obtained only by the public ``arcpuzzles apply`` CLI.
This tool does not modify either audited generator.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

from reviewer_support import canonical_pairs, find_root

TARGET_BRIDGE = "15dd333aa99b"
TARGET_CROP = "d17f2bbc0878"
BANDS: tuple[str | None, ...] = (None, "easy", "hard")
CENSUS_SEED = 20261005
CENSUS_INDICES = range(100)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(root: Path, task_id: str) -> tuple[ModuleType, Path]:
    source = root / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def positions(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result[value].append((r, c))
    return dict(result)


def bridge_defects(grid: list[list[int]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for color, cells in positions(grid).items():
        if len(cells) != 2:
            findings.append({"color": color, "kind": "count", "count": len(cells), "cells": cells})
            continue
        (r1, c1), (r2, c2) = cells
        if r1 != r2 and c1 != c2:
            findings.append({"color": color, "kind": "unaligned", "cells": cells})
            continue
        if r1 == r2:
            interior = [(r1, c, grid[r1][c]) for c in range(min(c1, c2) + 1, max(c1, c2))]
        else:
            interior = [(r, c1, grid[r][c1]) for r in range(min(r1, r2) + 1, max(r1, r2))]
        blockers = [list(cell) for cell in interior if cell[2] != 0]
        if blockers:
            findings.append({"color": color, "kind": "blocked", "cells": cells, "blockers": blockers})
    return findings


def bridge_all_rival(grid: list[list[int]]) -> list[list[int]]:
    """Apply the generator summary literally, without the authority's clear-gap guard."""
    output = [row[:] for row in grid]
    by_color = positions(grid)
    order: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in order:
                order.append(value)
    for color in order:
        cells = by_color[color]
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                output[r1][c] = color
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                output[r][c1] = color
    return output


def counts_and_boxes(grid: list[list[int]]) -> tuple[dict[int, int], dict[int, tuple[int, int, int, int]]]:
    by_color = positions(grid)
    counts = {color: len(cells) for color, cells in by_color.items()}
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for color, cells in by_color.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        boxes[color] = min(rows), min(cols), max(rows), max(cols)
    return counts, boxes


def disjoint_two_boxes(boxes: dict[int, tuple[int, int, int, int]]) -> bool:
    if len(boxes) != 2:
        return False
    first, second = list(boxes.values())
    r1, c1, r2, c2 = first
    x1, y1, x2, y2 = second
    return r2 < x1 or x2 < r1 or c2 < y1 or y2 < c1


def crop_minority(grid: list[list[int]]) -> list[list[int]]:
    counts, boxes = counts_and_boxes(grid)
    color = min(counts, key=lambda value: (counts[value], value))
    r1, c1, r2, c2 = boxes[color]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def separation_shortcut(grid: list[list[int]]) -> list[list[int]]:
    """Plausible learned precondition encoded by the target validator/domain."""
    _, boxes = counts_and_boxes(grid)
    if not disjoint_two_boxes(boxes):
        return [row[:] for row in grid]
    return crop_minority(grid)


def prepare(root: Path, out: Path) -> None:
    # Reproduce the first deterministic bridge collision found by the audit.
    bridge, bridge_source = load_generator(root, TARGET_BRIDGE)
    grid = bridge.generate(0, 2, difficulty=None)
    defects = bridge_defects(grid)
    if not defects:
        raise AssertionError("expected seed=0/sample_index=2 bridge collision")
    folder = out / TARGET_BRIDGE
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    by_band = []
    bad_total = 0
    defect_kinds: Counter[str] = Counter()
    for band in BANDS:
        bad = 0
        for index in CENSUS_INDICES:
            generated = bridge.generate(CENSUS_SEED, index, difficulty=band)
            current = bridge_defects(generated)
            if current:
                bad += 1
                bad_total += 1
                defect_kinds.update(item["kind"] for item in current)
        by_band.append({"difficulty": band or "default", "draws": 100, "out_of_domain_draws": bad})
    bridge_record = {
        "task_id": TARGET_BRIDGE,
        "generator_sha256": sha256(bridge_source),
        "seed": 0,
        "sample_index": 2,
        "difficulty": None,
        "overrides": {},
        "input": grid,
        "self_check_errors": bridge.self_check(grid),
        "documented_invariant_violation": defects,
        "rival_name": "bridge_all_exact_pairs_without_clear_gap_precondition",
        "rival_output": bridge_all_rival(grid),
        "rival_interpretation": (
            "The generator summary says every same-color endpoint pair becomes a full segment; "
            "this rival applies that advertised transformation even when another color blocks the interior."
        ),
        "documented_domain_membership": False,
        "domain_note": (
            "The target generator emitted this grid and self_check accepts it, but it violates "
            "the declared clear-space invariant."
        ),
        "prevalence_probe": {
            "seed": CENSUS_SEED,
            "sample_indices": "0..99",
            "bands": by_band,
            "total_draws": 300,
            "out_of_domain_draws": bad_total,
            "defect_instances_by_kind": dict(defect_kinds),
        },
    }
    (folder / "pre-racket.json").write_text(json.dumps(bridge_record, indent=2) + "\n")

    crop, crop_source = load_generator(root, TARGET_CROP)
    pair = canonical_pairs(TARGET_CROP, root=root, labeled_only=True)[0]
    grid = pair["input"]
    expected = pair["output"]
    if crop_minority(grid) != expected:
        raise AssertionError("independent minority crop does not match canonical pair")
    folder = out / TARGET_CROP
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
    by_band = []
    disjoint_total = shortcut_total = accepted_total = 0
    for band in BANDS:
        disjoint = shortcut = accepted = 0
        for index in CENSUS_INDICES:
            generated = crop.generate(CENSUS_SEED, index, difficulty=band)
            _, boxes = counts_and_boxes(generated)
            disjoint += int(disjoint_two_boxes(boxes))
            shortcut += int(separation_shortcut(generated) == crop_minority(generated))
            accepted += int(not crop.self_check(generated))
        disjoint_total += disjoint
        shortcut_total += shortcut
        accepted_total += accepted
        by_band.append({
            "difficulty": band or "default",
            "draws": 100,
            "disjoint_bboxes": disjoint,
            "shortcut_matches_reference_mirror": shortcut,
            "self_check_accepts": accepted,
        })
    counts, boxes = counts_and_boxes(grid)
    crop_record = {
        "task_id": TARGET_CROP,
        "generator_sha256": sha256(crop_source),
        "canonical_pair": "first labeled canonical pair",
        "input": grid,
        "canonical_output": expected,
        "self_check_errors": crop.self_check(grid),
        "color_counts": counts,
        "color_bboxes": {str(color): box for color, box in boxes.items()},
        "bboxes_disjoint": disjoint_two_boxes(boxes),
        "canonical_task_domain_membership": True,
        "target_generator_documented_domain_membership": False,
        "rival_name": "require_disjoint_color_bboxes_then_crop_minority_else_noop",
        "rival_output": separation_shortcut(grid),
        "rival_interpretation": (
            "A learner can treat bbox separation as a necessary precondition because target "
            "self_check requires it and every sampled generated grid has it; the canonical task does not."
        ),
        "generated_domain_probe": {
            "seed": CENSUS_SEED,
            "sample_indices": "0..99",
            "bands": by_band,
            "total_draws": 300,
            "disjoint_bboxes": disjoint_total,
            "shortcut_matches_reference_mirror": shortcut_total,
            "self_check_accepts": accepted_total,
        },
    }
    (folder / "pre-racket.json").write_text(json.dumps(crop_record, indent=2) + "\n")
    print(json.dumps({TARGET_BRIDGE: bridge_record["prevalence_probe"], TARGET_CROP: crop_record["generated_domain_probe"]}, indent=2))


def verify(root: Path, out: Path) -> None:
    summary: dict[str, Any] = {}
    for task_id in (TARGET_BRIDGE, TARGET_CROP):
        module, source = load_generator(root, task_id)
        folder = out / task_id
        finding = json.loads((folder / "pre-racket.json").read_text())
        receipt = json.loads((folder / "racket.json").read_text())
        if finding["generator_sha256"] != sha256(source) or receipt["generator_sha256"] != sha256(source):
            raise AssertionError(f"source hash mismatch for {task_id}")
        results = receipt.get("results", [])
        if len(results) != 1 or results[0].get("error") is not None or not results[0].get("valid_output"):
            raise AssertionError(f"invalid Racket receipt for {task_id}")
        result = results[0]
        if result["input"] != finding["input"]:
            raise AssertionError(f"receipt input mismatch for {task_id}")
        if result["output"] == finding["rival_output"]:
            raise AssertionError(f"rival unexpectedly agrees with Racket for {task_id}")
        if task_id == TARGET_CROP and result["output"] != finding["canonical_output"]:
            raise AssertionError("canonical Racket output differs from retained canonical label")
        finding.update({
            "actual_racket_output": result["output"],
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
            "executed_rule_hash": receipt["executed_rule_hash"],
            "rule_text_sha256": receipt["rule_text_sha256"],
            "reference_command": receipt["command"],
            "reference_cwd": receipt["cwd"],
            "reference_report": f"checks/audit/{task_id}/racket.json",
            "reference_verified": True,
        })
        (folder / "counterexample.json").write_text(json.dumps(finding, indent=2) + "\n")
        summary[task_id] = {
            "status": "verified",
            "generator_sha256": sha256(source),
            "executed_rule_hash": receipt["executed_rule_hash"],
            "rival_differs": True,
            "counterexample": f"checks/audit/{task_id}/counterexample.json",
        }
    (out / "verification-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == "prepare":
        prepare(root, args.out)
    else:
        verify(root, args.out)


if __name__ == "__main__":
    main()
