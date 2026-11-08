"""Audit b2d6e6b60917 for an untested 8-vs-4-connectivity shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs

TASK_ID = "b2d6e6b60917"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def components4(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    p = (rr + dr, cc + dc)
                    if (
                        0 <= p[0] < h and 0 <= p[1] < w
                        and p not in seen and grid[p[0]][p[1]] != 0
                    ):
                        seen.add(p)
                        stack.append(p)
            ordered = tuple(sorted(cells))
            box = bbox(ordered)
            result.append({
                "cells": ordered,
                "bbox": box,
                "height": box[2] - box[0] + 1,
                "width": box[3] - box[1] + 1,
                "size": len(ordered),
                "color": grid[ordered[0][0]][ordered[0][1]],
            })
    return result


def direction(source: dict, marker: dict) -> tuple[int, int]:
    sr1, sc1, sr2, sc2 = source["bbox"]
    mr1, mc1, mr2, mc2 = marker["bbox"]
    dr = -1 if mr1 + mr2 < sr1 + sr2 else (1 if mr1 + mr2 > sr1 + sr2 else 0)
    dc = -1 if mc1 + mc2 < sc1 + sc2 else (1 if mc1 + mc2 > sc1 + sc2 else 0)
    return dr, dc


def largest_4_connected_source_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: use 4-connectivity when selecting the source object."""
    comps = components4(grid)
    ranked = sorted(enumerate(comps), key=lambda item: (-item[1]["size"], item[0]))
    source = ranked[0][1]
    markers = [component for _, component in ranked[1:]]
    out = [row[:] for row in grid]
    stride_h, stride_w = source["height"] + 1, source["width"] + 1
    for marker in markers:
        dr, dc = direction(source, marker)
        for step in range(1, 10):
            for r, c in source["cells"]:
                rr = r + step * dr * stride_h
                cc = c + step * dc * stride_w
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]) and out[rr][cc] == 0:
                    out[rr][cc] = marker["color"]
    return out


def build_counterexample() -> list[list[int]]:
    grid = [[0] * 21 for _ in range(21)]
    # This five-cell source is one 8-connected object but two 4-connected objects.
    source = ((0, 0), (1, 1), (1, 2), (2, 2), (2, 3))
    top, left = 8, 7
    for r, c in source:
        grid[top + r][left + c] = 2
    fragment = ((1, 1), (1, 2))
    for r, c in fragment:
        grid[top + r - 4][left + c] = 3  # up, source height + 1
        grid[top + r][left + c + 5] = 4  # right, source width + 1
    return grid


def is_4_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for p in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if p in cells and p not in seen:
                seen.add(p)
                stack.append(p)
    return seen == cells


def main() -> None:
    gen = load_generator()
    grid = build_counterexample()
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    rival_output = largest_4_connected_source_rival(grid)
    intended = gen.rule_mirror(grid)
    (HERE / "rival_output.json").write_text(json.dumps(rival_output, indent=2) + "\n")
    (HERE / "mirror_output.json").write_text(json.dumps(intended, indent=2) + "\n")

    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_matches = sum(
        largest_4_connected_source_rival(pair["input"]) == pair["output"]
        for pair in canonical
    )
    canonical_sources_4_connected = sum(
        is_4_connected(gen._analyze_grid(pair["input"])["source"]["cells"])
        for pair in canonical
    )

    generated_total = 0
    generated_matches = 0
    generated_sources_4_connected = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(100):
            sample = gen.generate(
                880_000 + band_index * 10_000 + i,
                19 * i + 5,
                difficulty=band,
            )
            generated_total += 1
            generated_matches += int(
                largest_4_connected_source_rival(sample) == gen.rule_mirror(sample)
            )
            generated_sources_4_connected += int(
                is_4_connected(gen._analyze_grid(sample)["source"]["cells"])
            )

    racket_path = HERE / "racket.json"
    racket = json.loads(racket_path.read_text()) if racket_path.exists() else None
    racket_output = racket["results"][0]["output"] if racket else None
    differing = [
        [r, c, intended[r][c], rival_output[r][c]]
        for r in range(len(intended))
        for c in range(len(intended[0]))
        if intended[r][c] != rival_output[r][c]
    ]
    evidence = {
        "schema": "arcpuzzles-audit-connectivity-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "select the source as the largest 4-connected nonzero object, then apply the same ray rule",
        "canonical": {
            "rival_matches": f"{canonical_matches}/{len(canonical)}",
            "sources_4_connected": f"{canonical_sources_4_connected}/{len(canonical)}",
        },
        "generated": {
            "sampler": "100 each easy/medium/hard; seed=880000+band*10000+i; sample_index=19*i+5",
            "rival_matches": f"{generated_matches}/{generated_total}",
            "sources_4_connected": f"{generated_sources_4_connected}/{generated_total}",
        },
        "counterexample": {
            "self_check": gen.self_check(grid),
            "strict_canonical_like": gen.strict_canonical_like(grid),
            "intended_source_is_8_connected_not_4_connected": (
                len(gen._analyze_grid(grid)["source"]["cells"]) == 5
                and not is_4_connected(gen._analyze_grid(grid)["source"]["cells"])
            ),
            "rival_matches_intended": rival_output == intended,
            "differing_cell_count": len(differing),
            "differing_cells": differing,
            "racket_present": racket is not None,
            "racket_matches_mirror": racket_output == intended if racket else None,
            "racket_matches_rival": racket_output == rival_output if racket else None,
        },
        "domain_note": (
            "The input passes self_check and the documented broad 21x21/size/bbox/palette invariants, "
            "but strict_canonical_like rejects its non-3x3 source and the finite source-shape libraries never emit it. "
            "This is a teaching-support/domain question, not a generated-label mismatch."
        ),
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
