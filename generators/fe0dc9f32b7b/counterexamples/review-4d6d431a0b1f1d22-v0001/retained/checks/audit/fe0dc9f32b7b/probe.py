from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime"), str(REPO / "shared")]
TASK = "fe0dc9f32b7b"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_fe0", SOURCE)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def components8(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    out = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    comp.add(point)
                    stack.append(point)
        out.append(comp)
    return out


def bbox(comp):
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def perimeter(box):
    r0, c0, r1, c1 = box
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)}


def authority_positive(comp):
    r0, c0, r1, c1 = bbox(comp)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    return h >= 3 and w >= 3 and len(comp) == 2 * (h + w) - 4


def exact_or_single_inward_swap(comp):
    if not authority_positive(comp):
        return False
    border = perimeter(bbox(comp))
    missing = border - comp
    added = comp - border
    if not missing and not added:
        return True
    if len(missing) != 1 or len(added) != 1:
        return False
    r0, c0, r1, c1 = bbox(comp)
    r, c = next(iter(added))
    return r0 < r < r1 and c0 < c < c1


def palette(grid):
    return [row[0] for row in grid if row[0] not in (0, 8)]


def apply_boxes(grid, predicate):
    boxes = [bbox(comp) for comp in components8(grid) if predicate(comp)]
    colors = palette(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            depth = sum(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)
            if 0 < depth <= len(colors):
                out[r][c] = colors[depth - 1]
    return out


def draw_frame(grid, r0, c0, r1, c1):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                grid[r][c] = 8


def counterexample():
    grid = [[0] * 15 for _ in range(13)]
    grid[0][0], grid[1][0] = 1, 2
    draw_frame(grid, 1, 3, 11, 13)
    draw_frame(grid, 3, 5, 9, 11)
    # Two missing border cells and two interior replacements.  The added pair
    # bridges the upper gap, so the inner component remains 4-connected.
    grid[3][6] = 0
    grid[9][6] = 0
    grid[4][6] = 8
    grid[4][7] = 8
    return grid


def canonical_pairs():
    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row.get("train", []) + row.get("test", [])
    raise RuntimeError("canonical task missing")


def main():
    samples = 0
    self_check_errors = 0
    rival_matches = 0
    nonclean_positive = 0
    nonclean_not_single = 0
    for band_no, band in enumerate(("easy", "medium", "hard")):
        for index in range(300):
            grid = gen.generate(710000 + band_no * 10000 + index, index, difficulty=band)
            samples += 1
            self_check_errors += bool(gen.self_check(grid))
            expected = gen.rule_mirror(grid)
            rival = apply_boxes(grid, exact_or_single_inward_swap)
            rival_matches += rival == expected
            for comp in components8(grid):
                if authority_positive(comp) and comp != perimeter(bbox(comp)):
                    nonclean_positive += 1
                    nonclean_not_single += not exact_or_single_inward_swap(comp)

    grid = counterexample()
    comps = components8(grid)
    inner = min(comps, key=len)
    py_authority = apply_boxes(grid, authority_positive)
    rival = apply_boxes(grid, exact_or_single_inward_swap)
    assert authority_positive(inner)
    assert len(perimeter(bbox(inner)) - inner) == 2
    assert len(inner - perimeter(bbox(inner))) == 2
    assert not exact_or_single_inward_swap(inner)
    assert py_authority != rival

    canonical = canonical_pairs()
    canonical_fit = sum(
        apply_boxes(pair["input"], exact_or_single_inward_swap) == pair["output"]
        for pair in canonical
    )
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    summary = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "source_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "rival": "qualify only exact perimeter outlines or exactly one inward swap",
        "ordinary_samples": samples,
        "ordinary_self_check_errors": self_check_errors,
        "ordinary_rival_matches": rival_matches,
        "ordinary_nonclean_authority_positive_components": nonclean_positive,
        "ordinary_nonclean_components_beyond_one_swap": nonclean_not_single,
        "canonical_pairs": len(canonical),
        "canonical_rival_matches": canonical_fit,
        "counterexample": {
            "self_check_errors": gen.self_check(grid),
            "component_bbox": bbox(inner),
            "component_size": len(inner),
            "perimeter_size": len(perimeter(bbox(inner))),
            "missing_perimeter_cells": sorted(perimeter(bbox(inner)) - inner),
            "added_interior_cells": sorted(inner - perimeter(bbox(inner))),
            "python_authority_differs_from_rival": py_authority != rival,
        },
    }
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (HERE / "python_authority.json").write_text(json.dumps(py_authority, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "distribution_probe.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
