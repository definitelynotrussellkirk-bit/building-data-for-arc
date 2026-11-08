"""Independent task-local oracle and curriculum probes for 033db13a9d37.

This file deliberately does not import production helpers when computing outputs.
It is useful to tests and future reviewers, and can be run as a small JSON probe.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "033db13a9d37"
HOME = Path(__file__).resolve().parents[1]
CANONICAL_SIZES = (3, 5, 9, 12)


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def nonzero_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def output_from_selected_cell(
    grid: list[list[int]], *, use_last: bool = False
) -> list[list[int]]:
    """Independent Python mirror of the selected Racket behavior.

    ``use_last=True`` is the plausible wrong rule that fits all public canonical
    pairs (which each contain one nonzero cell) but should be refuted by generated
    later-decoy examples.
    """
    cells = nonzero_cells(grid)
    if not cells:
        raise ValueError("grid has no nonzero seed")
    r, c, color = cells[-1] if use_last else cells[0]
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for rr in range(r + 1):
        for cc in range(c % 2, w, 2):
            out[rr][cc] = 4
    if r + 1 < h:
        out[r + 1][c] = color
    return out


def oracle_output(grid: list[list[int]]) -> list[list[int]]:
    return output_from_selected_cell(grid, use_last=False)


def last_nonzero_rival(grid: list[list[int]]) -> list[list[int]]:
    return output_from_selected_cell(grid, use_last=True)


def observed_axes(grid: list[list[int]]) -> dict[str, object]:
    cells = nonzero_cells(grid)
    if not cells:
        raise ValueError("grid has no nonzero seed")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "fg_color": cells[0][2],
        "scene_profile": "single" if len(cells) == 1 else "decoy",
    }


def lesson_rotation_report(gen, *, starts: Iterable[int], band: str) -> dict:
    """Exhaust every requested four-pair start and all four query rotations."""
    lessons = []
    failures = []
    for start in starts:
        grids = [gen.generate(99173, start + offset, difficulty=band) for offset in range(4)]
        pairs = [
            {
                "input": grid,
                "output": oracle_output(grid),
                "rival": last_nonzero_rival(grid),
            }
            for grid in grids
        ]
        row = {
            "start": start,
            "sample_indices": list(range(start, start + 4)),
            "profiles": [observed_axes(grid)["scene_profile"] for grid in grids],
            "rotations": [],
        }
        for query_index in range(4):
            train_indices = [i for i in range(4) if i != query_index]
            refuted = any(
                pairs[i]["rival"] != pairs[i]["output"] for i in train_indices
            )
            rotation = {
                "query_index": query_index,
                "train_indices": train_indices,
                "last_nonzero_refuted": refuted,
            }
            row["rotations"].append(rotation)
            if not refuted:
                failures.append({"start": start, **rotation})
        lessons.append(row)
    return {
        "task_id": TASK_ID,
        "band": band,
        "lessons": lessons,
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": [
            "Finite exhaustive starts supplied by the caller, not universal rule induction.",
            "Only the declared last-nonzero rival is tested.",
            "Outputs are computed by an independent Python mirror; use the Racket battery for authority binding.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=32, help="number of consecutive starts")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    reports = [
        lesson_rotation_report(gen, starts=range(args.starts), band=band)
        for band in ("easy", "medium", "hard")
    ]
    payload = {
        "schema": "033db13a9d37-curriculum-probe-v1",
        "reports": reports,
        "status": "pass" if all(row["status"] == "pass" for row in reports) else "fail",
    }
    text = json.dumps(payload, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
