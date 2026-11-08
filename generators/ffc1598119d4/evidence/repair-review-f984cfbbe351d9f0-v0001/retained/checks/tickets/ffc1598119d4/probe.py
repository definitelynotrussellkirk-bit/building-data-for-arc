#!/usr/bin/env python3
"""Protected-Racket learnability probe for peer ffc1598119d4.

The probe is deliberately source-bound and narrow: it demonstrates one lesson in
which command 2 appears in the demonstrations only on motifs where clockwise
rotation and vertical reflection coincide, while the query uses an asymmetric
motif that separates those transformations.
"""
from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Iterable

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, load_selected_generator

TASK_ID = "ffc1598119d4"
EXPECTED_GENERATOR_SHA256 = "1d6b558856708e60097802e84857ad51b971217a9651e7ea038e6bbbb448a3c4"
SEED = 47
HERE = Path(__file__).resolve().parent

Grid = list[list[int]]
Cell = tuple[int, int]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rotate_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def flip_ud(grid: Grid) -> Grid:
    return [row[:] for row in grid[::-1]]


def literal(grid: Grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def components_of_color(grid: Grid, color: int) -> list[list[Cell]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[list[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        q: deque[Cell] = deque([start])
        component: list[Cell] = []
        while q:
            r, c = q.popleft()
            component.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    q.append((nr, nc))
        components.append(sorted(component))
    return sorted(components, key=lambda cells: min(cells))


def bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def source_motif(grid: Grid) -> Grid:
    components = components_of_color(grid, 9)
    if len(components) != 1:
        raise ValueError(f"expected one color-9 source frame, found {len(components)}")
    r1, c1, r2, c2 = bbox(components[0])
    if r2 - r1 < 2 or c2 - c1 < 2:
        raise ValueError("source frame has no interior")
    expected_border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if set(components[0]) != expected_border:
        raise ValueError("color-9 component is not a complete rectangular frame")
    return [row[c1 + 1 : c2] for row in grid[r1 + 1 : r2]]


def target_codes(grid: Grid) -> list[int]:
    codes: list[int] = []
    for cells in components_of_color(grid, 8):
        r1, c1, r2, c2 = bbox(cells)
        expected_border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if set(cells) != expected_border:
            raise ValueError("color-8 component is not a complete rectangular frame")
        if r1 == 0:
            raise ValueError("target frame has no command row")
        code = grid[r1 - 1][c1]
        if code not in (1, 2, 3, 4):
            raise ValueError(f"invalid target command {code}")
        codes.append(code)
    return codes


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise ValueError(
            f"peer source drift: expected {EXPECTED_GENERATOR_SHA256}, got {source_sha}"
        )

    programs = {
        row["program_solution"]
        for row in Catalog(root).get(TASK_ID)["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    if len(programs) != 1:
        raise ValueError("expected one selected canonical program")
    canonical = next(iter(programs))
    old = "[(= code 2) (rotate-cw motif)]"
    new = "[(= code 2) (flip-ud motif)]"
    if canonical.count(old) != 1:
        raise ValueError("canonical code-2 branch spelling changed")
    rival = canonical.replace(old, new)

    grids = [generator.generate(SEED, index) for index in range(4)]
    motifs = [source_motif(grid) for grid in grids]
    code_lists = [target_codes(grid) for grid in grids]
    expected_codes = [[4, 4, 2, 1], [2, 2, 3, 1], [3, 1], [1, 2, 1, 2]]
    if code_lists != expected_codes:
        raise AssertionError(f"source-bound schedule changed: {code_lists}")

    for index in range(3):
        if 2 in code_lists[index] and rotate_cw(motifs[index]) != flip_ud(motifs[index]):
            raise AssertionError(
                f"demonstration {index} no longer hides clockwise versus flip-UD for code 2"
            )
    if 2 not in code_lists[3]:
        raise AssertionError("selected query no longer exercises code 2")
    if rotate_cw(motifs[3]) == flip_ud(motifs[3]):
        raise AssertionError("selected query no longer distinguishes clockwise from flip-UD")

    with RacketBridge(timeout=30.0) as bridge:
        runtime = bridge.runtime_identity
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise RuntimeError("probe requires protected Racket")
        canonical_rule = wrap_rule(canonical)
        rival_rule = wrap_rule(rival)
        canonical_outputs = [
            bridge.eval_text(f"({canonical_rule} {literal(grid)})") for grid in grids
        ]
        rival_outputs = [
            bridge.eval_text(f"({rival_rule} {literal(grid)})") for grid in grids
        ]

    demo_matches = [canonical_outputs[i] == rival_outputs[i] for i in range(3)]
    query_differs = canonical_outputs[3] != rival_outputs[3]
    if demo_matches != [True, True, True] or not query_differs:
        raise AssertionError("rival did not fit all demos and disagree on query")

    result = {
        "schema": "arcpuzzles-peer-learnability-counterexample-v1",
        "task_id": TASK_ID,
        "status": "finding",
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha,
        },
        "lesson": {"seed": SEED, "demo_indices": [0, 1, 2], "query_index": 3},
        "observed_codes": code_lists,
        "canonical_mapping": "command 2 -> rotate clockwise",
        "rival_mapping": "command 2 -> flip vertically; all other branches unchanged",
        "why_rival_survives": (
            "Every demonstration containing command 2 uses a source motif for which clockwise "
            "rotation equals vertical reflection, so both rules produce identical labels."
        ),
        "why_query_disagrees": (
            "The command-2 query source is asymmetric under those transforms, so at least one "
            "target interior differs."
        ),
        "demo_matches": demo_matches,
        "query_differs": query_differs,
        "motifs": [
            {
                "index": index,
                "role": "demo" if index < 3 else "query",
                "commands": codes,
                "source_motif": motif,
                "cw_equals_flip_ud": rotate_cw(motif) == flip_ud(motif),
            }
            for index, (motif, codes) in enumerate(zip(motifs, code_lists))
        ],
        "canonical_program_sha256": sha(canonical),
        "rival_program_sha256": sha(rival),
        "canonical_program": canonical,
        "rival_program": rival,
        "pairs": [
            {
                "index": index,
                "role": "demo" if index < 3 else "query",
                "input": grids[index],
                "canonical_output": canonical_outputs[index],
                "rival_output": rival_outputs[index],
                "outputs_equal": canonical_outputs[index] == rival_outputs[index],
            }
            for index in range(4)
        ],
        "racket_runtime": runtime,
        "recommended_repair": (
            "For every transform code used by a query, require a demonstration whose source motif "
            "separates that transform from each competing transform; redraw the lesson or add a "
            "demonstration when a symmetry masks the distinction."
        ),
        "limits": "One source-bound four-pair lesson and one explicit rival; not a full census.",
    }
    (HERE / "rival-code2-flipud.rkt").write_text(rival + "\n", encoding="utf-8")
    (HERE / "counterexample.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "task_id": TASK_ID,
                "seed": SEED,
                "codes": code_lists,
                "demo_matches": demo_matches,
                "query_differs": query_differs,
                "counterexample": str(HERE / "counterexample.json"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
