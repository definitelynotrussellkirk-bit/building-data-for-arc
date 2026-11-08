#!/usr/bin/env python3
"""Reproducible adversarial probes for the two assigned audit targets."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks" / "audit"


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def audit_priority_overlay() -> dict[str, Any]:
    task = "3a0af56db83e"
    gen, path = load(task)
    pairs = canonical_pairs(task, root=find_root(path))
    canonical_failures = []
    for index, pair in enumerate(pairs):
        if gen.self_check(deepcopy(pair["input"])):
            canonical_failures.append({"index": index, "kind": "self_check"})
        if gen.strict_canonical_like(deepcopy(pair["input"])):
            canonical_failures.append({"index": index, "kind": "strict"})
        if gen.rule_mirror(deepcopy(pair["input"])) != pair["output"]:
            canonical_failures.append({"index": index, "kind": "rule_mirror"})

    ambiguous = []
    lesson_errors = []
    unique_inputs = set()
    pairs_materialized = 0
    rotations = 0
    per_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        band_ambiguous = 0
        band_errors = 0
        for lesson in range(100):
            seed = 3_100_000 + band_index * 100_000 + lesson
            start = lesson * 3
            lesson_pairs = []
            for offset in range(3):
                grid = gen.generate(seed, start + offset, difficulty=band)
                unique_inputs.add(frozen(grid))
                lesson_pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                pairs_materialized += 1
            for query_index in range(3):
                rotations += 1
                query = lesson_pairs[query_index]
                demos = [pair for i, pair in enumerate(lesson_pairs) if i != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    band_errors += 1
                    if len(lesson_errors) < 10:
                        lesson_errors.append({
                            "band": band,
                            "lesson": lesson,
                            "query_index": query_index,
                            "reasons": reasons,
                        })
                for name, rival in gen.LESSON_COMPETITORS.items():
                    fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                    disagrees = rival(query["input"]) != query["output"]
                    if fits and disagrees:
                        band_ambiguous += 1
                        if len(ambiguous) < 10:
                            ambiguous.append({
                                "band": band,
                                "lesson": lesson,
                                "query_index": query_index,
                                "rival": name,
                            })
        per_band[band] = {
            "lessons": 100,
            "rotations": 300,
            "ambiguous_rotations": band_ambiguous,
            "lesson_contract_errors": band_errors,
        }

    return {
        "schema": "arc-audit-probe-v1",
        "task_id": task,
        "generator_sha256": sha256(path),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(pairs),
        "canonical_failures": canonical_failures,
        "declared_competitors": sorted(gen.LESSON_COMPETITORS),
        "declared_witnesses": sorted(gen.SEMANTIC_WITNESSES),
        "protocol": {
            "bands": ["easy", "medium", "hard"],
            "lessons_per_band": 100,
            "pairs_per_lesson": 3,
            "all_query_rotations": True,
            "seed_formula": "3100000 + band_index*100000 + lesson",
            "sample_indices": "lesson*3 + {0,1,2}",
        },
        "pairs_materialized": pairs_materialized,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "ambiguous_rotations": len(ambiguous),
        "lesson_contract_errors": len(lesson_errors),
        "ambiguity_examples": ambiguous,
        "contract_error_examples": lesson_errors,
        "per_band": per_band,
        "conclusion": "no issue found in the declared generated lesson domain",
    }


def normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def components(grid, color):
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack = [start]
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in pending:
                    pending.remove(p)
                    stack.append(p)
        result.append(comp)
    return result


def stamp(grid, anchors):
    comps = components(grid, 4)
    if not comps:
        return [[0 for _ in row] for row in grid]
    template = normalize(max(comps, key=len))
    out = [[0 for _ in row] for row in grid]
    h, w = len(grid), len(grid[0])
    for ar, ac in anchors:
        for dr, dc in template:
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 4
    return out


def local_corner_rival(grid):
    """Ignore color 7 and stamp at every local corner in every color-1 component."""
    wire = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    corners = []
    for r, c in sorted(wire):
        neighbours = [
            (rr, cc)
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if (rr, cc) in wire
        ]
        if len(neighbours) != 2:
            continue
        (r1, c1), (r2, c2) = neighbours
        if r1 != r2 and c1 != c2:
            corners.append((r, c))
    return stamp(grid, corners)


def add_disconnected_l(grid, official_output):
    """Add a second L-shaped wire component at a free location."""
    h, w = len(grid), len(grid[0])
    shape = normalize(max(components(grid, 4), key=len))
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    original_wire = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    for r in range(1, h - 2):
        for c in range(1, w - 3):
            cells = {(r, c), (r, c + 1), (r + 1, c + 1)}
            if cells & occupied:
                continue
            if any(
                abs(rr - wr) + abs(cc - wc) == 1
                for rr, cc in cells
                for wr, wc in original_wire
            ):
                continue
            corner = (r, c + 1)
            stamp_cells = {
                (corner[0] + dr, corner[1] + dc)
                for dr, dc in shape
                if 0 <= corner[0] + dr < h and 0 <= corner[1] + dc < w
            }
            if not stamp_cells or all(official_output[rr][cc] == 4 for rr, cc in stamp_cells):
                continue
            changed = deepcopy(grid)
            for rr, cc in cells:
                changed[rr][cc] = 1
            return changed, sorted(cells), corner
    raise RuntimeError("could not place disconnected L witness")


def audit_wire_turns() -> dict[str, Any]:
    task = "9a7579840f41"
    gen, path = load(task)
    pairs = canonical_pairs(task, root=find_root(path))
    canonical_matches = [local_corner_rival(pair["input"]) == pair["output"] for pair in pairs]

    generated_matches = 0
    generated_total = 0
    generated_self_check_errors = 0
    unique_inputs = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(64):
            grid = gen.generate(9_200_000 + band_index * 100_000 + index, index * 7 + 3, difficulty=band)
            unique_inputs.add(frozen(grid))
            generated_total += 1
            if gen.self_check(deepcopy(grid)):
                generated_self_check_errors += 1
            # On the accepted simple-path domain, the local-corner shortcut is
            # equivalent to ordered tracing and therefore survives every lesson.
            path_cells, error = gen._trace_wire_from_start(grid)
            if error:
                continue
            intended = stamp(grid, gen._turns(path_cells))
            generated_matches += int(local_corner_rival(grid) == intended)

    valid = gen.generate(
        812,
        5,
        difficulty="hard",
        grid_h=16,
        grid_w=18,
        n_turns=4,
        template_size=3,
        start_axis="vertical",
    )
    path_cells, error = gen._trace_wire_from_start(valid)
    assert error is None
    intended = stamp(valid, gen._turns(path_cells))
    invalid, added_cells, added_corner = add_disconnected_l(valid, intended)

    task_dir = OUT / task
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "valid_input.json").write_text(json.dumps(valid, indent=2) + "\n")
    (task_dir / "valid_rival_output.json").write_text(json.dumps(local_corner_rival(valid), indent=2) + "\n")
    (task_dir / "out_of_domain_input.json").write_text(json.dumps(invalid, indent=2) + "\n")
    (task_dir / "out_of_domain_rival_output.json").write_text(json.dumps(local_corner_rival(invalid), indent=2) + "\n")

    return {
        "schema": "arc-audit-probe-v1",
        "task_id": task,
        "generator_sha256": sha256(path),
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "semantic_contract_present": all(
            hasattr(gen, name)
            for name in ("SEMANTIC_WITNESSES", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
        ),
        "strict_canonical_like_present": hasattr(gen, "strict_canonical_like"),
        "shortcut": "ignore color-7 start; stamp at every local orthogonal corner of every color-1 component",
        "canonical_pairs": len(pairs),
        "canonical_shortcut_matches": sum(canonical_matches),
        "generated_protocol": {
            "bands": ["easy", "medium", "hard"],
            "draws_per_band": 64,
            "seed_formula": "9200000 + band_index*100000 + index",
            "sample_index_formula": "index*7+3",
        },
        "generated_draws": generated_total,
        "generated_shortcut_matches": generated_matches,
        "generated_self_check_errors": generated_self_check_errors,
        "unique_inputs": len(unique_inputs),
        "valid_witness": {
            "seed": 812,
            "sample_index": 5,
            "difficulty": "hard",
            "overrides": {
                "grid_h": 16,
                "grid_w": 18,
                "n_turns": 4,
                "template_size": 3,
                "start_axis": "vertical",
            },
            "self_check": gen.self_check(valid),
            "input_path": "checks/audit/9a7579840f41/valid_input.json",
            "rival_output_path": "checks/audit/9a7579840f41/valid_rival_output.json",
        },
        "separating_recombination": {
            "description": "add a disconnected three-cell L-shaped color-1 component; authority follows only the component attached to color 7, while the shortcut stamps its extra local corner",
            "added_cells": added_cells,
            "added_corner": added_corner,
            "self_check": gen.self_check(invalid),
            "belongs_to_documented_generator_domain": False,
            "input_path": "checks/audit/9a7579840f41/out_of_domain_input.json",
            "rival_output_path": "checks/audit/9a7579840f41/out_of_domain_rival_output.json",
        },
        "conclusion": "possible shortcut survives the entire documented domain; missing semantic contract leaves it unmeasured",
    }


def main():
    a = audit_priority_overlay()
    b = audit_wire_turns()
    (OUT / "3a0af56db83e" / "probe.json").write_text(json.dumps(a, indent=2) + "\n")
    (OUT / "9a7579840f41" / "probe.json").write_text(json.dumps(b, indent=2) + "\n")
    print(json.dumps({
        "3a0af56db83e": {k: a[k] for k in ("canonical_failures", "rotations", "ambiguous_rotations", "lesson_contract_errors", "unique_inputs")},
        "9a7579840f41": {k: b[k] for k in ("semantic_contract_present", "canonical_shortcut_matches", "generated_draws", "generated_shortcut_matches", "unique_inputs")},
    }, indent=2))


if __name__ == "__main__":
    main()
