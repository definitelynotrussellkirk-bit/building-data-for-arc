#!/usr/bin/env python3
"""Independent review oracle and shortcut probe for ``dd3fa537fa22``.

This module intentionally does not import the selected generator when computing
objects or outputs.  It gives future reviewers one small, source-bound tool for:

* recognizing complete cyan rectangular frames and solid inserts;
* mirroring the selected Racket rule on ordinary ARC grids;
* evaluating the canonical-fitting but wrong horizontal-order shortcut; and
* recognizing the deliberately occluded invalid-frame branch.

Run it from a staged task runtime or the repository root.  With no arguments it
prints a compact canonical-pair report.  ``--generated N`` additionally probes N
samples from the selected generator in each difficulty band.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

TASK_ID = "dd3fa537fa22"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _rectangular_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a non-empty sequence"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "rows must be non-empty sequences"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    for row in grid:
        for value in row:
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 9:
                return "cells must be literal ARC integers 0..9"
    return None


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            records.append({"color": color, "cells": frozenset(cells), "bbox": bbox})
    return records


def _perimeter(bbox: tuple[int, int, int, int]) -> frozenset[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return frozenset(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    )


def _as_frame(record: dict[str, Any]) -> dict[str, Any] | None:
    r1, c1, r2, c2 = record["bbox"]
    outer_h, outer_w = r2 - r1 + 1, c2 - c1 + 1
    if record["color"] != 8 or outer_h < 3 or outer_w < 3:
        return None
    if record["cells"] != _perimeter(record["bbox"]):
        return None
    return {
        **record,
        "shape": (outer_h - 2, outer_w - 2),
        "center": ((r1 + r2) / 2, (c1 + c2) / 2),
    }


def _as_insert(record: dict[str, Any]) -> dict[str, Any] | None:
    if record["color"] in (0, 8):
        return None
    r1, c1, r2, c2 = record["bbox"]
    height, width = r2 - r1 + 1, c2 - c1 + 1
    expected = frozenset(
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    )
    if record["cells"] != expected:
        return None
    return {
        **record,
        "shape": (height, width),
        "center": ((r1 + r2) / 2, (c1 + c2) / 2),
    }


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    error = _rectangular_error(grid)
    if error:
        return {"errors": [error], "frames": [], "inserts": [], "invalid_cyan": []}
    components = _components(grid)
    frames: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    invalid_cyan: list[dict[str, Any]] = []
    invalid_noncyan: list[dict[str, Any]] = []
    for record in components:
        if record["color"] == 8:
            frame = _as_frame(record)
            (frames if frame is not None else invalid_cyan).append(frame or record)
        else:
            insert = _as_insert(record)
            (inserts if insert is not None else invalid_noncyan).append(insert or record)
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "frames": frames,
        "inserts": inserts,
        "invalid_cyan": invalid_cyan,
        "invalid_noncyan": invalid_noncyan,
    }


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected rule for a rectangular grid."""
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid grid: " + "; ".join(facts["errors"]))
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    frames = facts["frames"]
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    for insert in facts["inserts"]:
        target = next((frame for frame in frames if frame["shape"] == insert["shape"]), None)
        if target is None:
            continue
        r1, c1, r2, c2 = target["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                output[r][c] = insert["color"]
    return output


def horizontal_order_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: pair surviving frames/inserts by horizontal order."""
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid grid: " + "; ".join(facts["errors"]))
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    frames = sorted(facts["frames"], key=lambda item: item["center"][1])
    inserts = sorted(facts["inserts"], key=lambda item: item["center"][1])
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    if len(frames) == 1 and inserts:
        inserts = [min(inserts, key=lambda item: abs(item["center"][1] - frames[0]["center"][1]))]
    for frame, insert in zip(frames, inserts):
        r1, c1, r2, c2 = frame["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                output[r][c] = insert["color"]
    return output


def area_then_horizontal_output(grid: list[list[int]]) -> list[list[int]]:
    """Stronger wrong rule: match by area, then pair left-to-right.

    This rival deliberately ignores orientation.  It therefore agrees with
    exact dimension matching whenever object areas are unique and resolves
    equal-area ambiguity using the canonical examples' horizontal alignment.
    """
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid grid: " + "; ".join(facts["errors"]))
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    frames = sorted(facts["frames"], key=lambda item: item["center"][1])
    inserts = sorted(facts["inserts"], key=lambda item: item["center"][1])
    for frame in frames:
        for r, c in frame["cells"]:
            output[r][c] = 8
    areas = sorted({frame["shape"][0] * frame["shape"][1] for frame in frames})
    for area in areas:
        area_frames = [
            frame for frame in frames if frame["shape"][0] * frame["shape"][1] == area
        ]
        area_inserts = [
            insert for insert in inserts if insert["shape"][0] * insert["shape"][1] == area
        ]
        for frame, insert in zip(area_frames, area_inserts):
            r1, c1, r2, c2 = frame["bbox"]
            for r in range(r1 + 1, r2):
                for c in range(c1 + 1, c2):
                    output[r][c] = insert["color"]
    return output


def occluded_candidates(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return invalid cyan components completed to frames by a solid insert."""
    facts = analyze(grid)
    if facts["errors"]:
        return []
    found: list[dict[str, Any]] = []
    for cyan in facts["invalid_cyan"]:
        r1, c1, r2, c2 = cyan["bbox"]
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            continue
        perimeter = _perimeter(cyan["bbox"])
        if not cyan["cells"] <= perimeter:
            continue
        interior_shape = (r2 - r1 - 1, c2 - c1 - 1)
        for insert in facts["inserts"]:
            overlap = insert["cells"] & perimeter
            if (
                insert["shape"] == interior_shape
                and overlap
                and cyan["cells"] | overlap == perimeter
            ):
                found.append({"cyan": cyan, "insert": insert, "shape": interior_shape})
    return found


def scene_profile(grid: list[list[int]]) -> str | None:
    facts = analyze(grid)
    if facts["errors"] or facts["invalid_noncyan"]:
        return None
    frames = sorted(facts["frames"], key=lambda item: item["center"][1])
    inserts = sorted(facts["inserts"], key=lambda item: item["center"][1])
    if len(frames) == 1 and len(inserts) == 2 and len(occluded_candidates(grid)) == 1:
        return "occluded_decoy"
    if len(frames) != 2 or len(inserts) != 2 or facts["invalid_cyan"]:
        return None
    insert_shapes = [item["shape"] for item in inserts]
    frame_shapes = [item["shape"] for item in frames]
    if len(set(insert_shapes)) != 2 or sorted(insert_shapes) != sorted(frame_shapes):
        return None
    frame_below = sum(item["center"][0] for item in frames) > sum(item["center"][0] for item in inserts)
    relation = "aligned" if frame_shapes == insert_shapes else "crossed" if frame_shapes == list(reversed(insert_shapes)) else None
    if relation == "aligned" and frame_below:
        return "aligned_frames_below"
    if relation == "crossed" and frame_below:
        return "crossed_frames_below"
    if relation == "crossed" and not frame_below:
        return "crossed_frames_above"
    return None


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("review_dd3fa537fa22", source)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_report(generated: int = 0) -> dict[str, Any]:
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "canonical_pairs": len(pairs),
        "canonical_oracle_matches": sum(intended_output(pair["input"]) == pair["output"] for pair in pairs),
        "horizontal_shortcut_matches": sum(horizontal_order_output(pair["input"]) == pair["output"] for pair in pairs),
        "area_then_horizontal_shortcut_matches": sum(
            area_then_horizontal_output(pair["input"]) == pair["output"] for pair in pairs
        ),
        "canonical_profiles": [scene_profile(pair["input"]) for pair in pairs],
    }
    if generated:
        generator = _load_generator()
        rows = []
        for band in ("easy", "medium", "hard"):
            for index in range(generated):
                grid = generator.generate(91001, index, difficulty=band)
                rows.append({
                    "band": band,
                    "sample_index": index,
                    "profile": scene_profile(grid),
                    "self_check": generator.self_check(grid),
                    "shortcut_disagrees": horizontal_order_output(grid) != intended_output(grid),
                    "area_then_horizontal_disagrees": (
                        area_then_horizontal_output(grid) != intended_output(grid)
                    ),
                })
        report["generated"] = rows
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(max(0, args.generated))
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
