#!/usr/bin/env python3
"""Racket-backed sequential travel rule for ARC family c181f41a09f0.

The exact canonical default moves every recovered source-end 3x3 block to the
opposite end of its strip.  The alternative keeps the same strip/source-side
inference, then uses a genuine input-dependent intermediate: the number of
marker cells in the recovered source block.  That count determines how many
three-cell blocks the payload travels from its source.  Thus step B cannot pick
the destination until step A has recovered and measured the source block.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import itertools
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "c181f41a09f0"
ROOT = find_root(__file__)
TRAVEL_RULES = ("opposite_end", "marker_count_steps")
DEFAULT_TRAVEL_RULE = "opposite_end"
STATUS = "reviewer-ready prototype; owner acceptance pending"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
ROLE_SCHEDULE = (
    ("horizontal", "low"),
    ("horizontal", "high"),
    ("vertical", "low"),
    ("vertical", "high"),
)
DEMO_SIZES = ((15, 18), (15, 18), (18, 15), (18, 15), (20, 24), (24, 20))
DEMO_CAP_SIZES = ((1, 2, 3), (3, 1, 2), (2, 3, 1), (1, 3, 2), (1, 2, 3), (2, 1, 3))
DEMO_CAP_PATTERNS = (
    ((0,), (0, 2), (0, 1, 2)),
    ((0, 1, 2), (2,), (0, 1)),
    ((0, 2), (0, 1, 2), (1,)),
    ((1,), (0, 1, 2), (0, 2)),
    ((2,), (0, 2), (0, 1, 2)),
    ((0, 1), (2,), (0, 1, 2)),
)
DEMO_MARKED_INDICES = ((0, 1, 3),) * 6
DEMO_ROLES = (
    ("horizontal", "low"),
    ("horizontal", "low"),
    ("vertical", "high"),
    ("vertical", "high"),
    ("horizontal", "high"),
    ("vertical", "low"),
)
QUERY_SIZES = ((8, 12), (14, 14), (24, 28), (30, 30))
_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_HORIZONTAL_ANCHOR = "(dst-c (if (zero? d) (- c2 2) c1))"
_VERTICAL_ANCHOR = "(dst-r (if (zero? d) (- r2 2) r1))"
_HORIZONTAL_COUNT_STEPS = """(marker-count (score-rect r1 src-c r2 (+ src-c 2)))
                            (max-steps (max 1 (/ (- ww 3) 3)))
                            (steps (min max-steps (max 1 marker-count)))
                            (dst-c (if (zero? d)
                                       (+ c1 (* 3 steps))
                                       (- c2 2 (* 3 steps))))"""
_VERTICAL_COUNT_STEPS = """(marker-count (score-rect src-r c1 (+ src-r 2) c2))
                            (max-steps (max 1 (/ (- hh 3) 3)))
                            (steps (min max-steps (max 1 marker-count)))
                            (dst-r (if (zero? d)
                                       (+ r1 (* 3 steps))
                                       (- r2 2 (* 3 steps))))"""
_HORIZONTAL_WRONG_STEPS = _HORIZONTAL_COUNT_STEPS.replace(
    "(steps (min max-steps (max 1 marker-count)))", "(steps 1)"
)
_VERTICAL_WRONG_STEPS = _VERTICAL_COUNT_STEPS.replace(
    "(steps (min max-steps (max 1 marker-count)))", "(steps 1)"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid: list[list[int]]) -> str:
    return digest(json.dumps(grid, separators=(",", ":")).encode("utf-8"))


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def _validate_rule(travel_rule: str) -> None:
    if type(travel_rule) is not str or travel_rule not in TRAVEL_RULES:
        raise ValueError(f"travel_rule must be one of {TRAVEL_RULES}")


def validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be an integer in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(queries) is not int or not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be an integer in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"canonical {label} anchor changed; prototype needs review")
    return source.replace(old, new, 1)


def _count_steps_program(canonical: str, *, wrong_intermediate: bool = False) -> str:
    horizontal = _HORIZONTAL_WRONG_STEPS if wrong_intermediate else _HORIZONTAL_COUNT_STEPS
    vertical = _VERTICAL_WRONG_STEPS if wrong_intermediate else _VERTICAL_COUNT_STEPS
    program = _replace_once(canonical, _HORIZONTAL_ANCHOR, horizontal, "horizontal travel")
    return _replace_once(program, _VERTICAL_ANCHOR, vertical, "vertical travel")


def program_for(
    travel_rule: str = DEFAULT_TRAVEL_RULE,
    *,
    root: Path | str = ROOT,
) -> str:
    """Return exact canonical source or the marker-count sequential variant."""
    _validate_rule(travel_rule)
    canonical = canonical_record(root=root)["program_solution"]
    if travel_rule == DEFAULT_TRAVEL_RULE:
        return canonical
    return _count_steps_program(canonical)


def counterfactual_program(*, root: Path | str = ROOT) -> str:
    """A wrong-intermediate ablation: every payload travels exactly one block."""
    return _count_steps_program(canonical_record(root=root)["program_solution"], wrong_intermediate=True)


def _callable_text(program: str) -> str:
    return wrap_rule(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 columns")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return len(grid), width


def _zero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _strip_records(grid: list[list[int]], *, strict_scene: bool = True) -> list[dict[str, Any]]:
    h, w = _validate_grid(grid)
    components = _zero_components(grid)
    records: list[dict[str, Any]] = []
    for component in components:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        if r2 - r1 + 1 == 3 and c1 == 0 and c2 == w - 1 and w >= 8:
            orientation = "horizontal"
        elif c2 - c1 + 1 == 3 and r1 == 0 and r2 == h - 1 and h >= 8:
            orientation = "vertical"
        else:
            if strict_scene:
                raise ValueError(f"black component is not a full-span three-cell strip: {(r1,c1,r2,c2)}")
            continue
        bbox_cells = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        marker_cells = [p for p in bbox_cells if grid[p[0]][p[1]] not in (0, 7)]
        if orientation == "horizontal":
            low = [p for p in marker_cells if p[1] <= c1 + 2]
            high = [p for p in marker_cells if p[1] >= c2 - 2]
            middle = [p for p in marker_cells if c1 + 3 <= p[1] <= c2 - 3]
        else:
            low = [p for p in marker_cells if p[0] <= r1 + 2]
            high = [p for p in marker_cells if p[0] >= r2 - 2]
            middle = [p for p in marker_cells if r1 + 3 <= p[0] <= r2 - 3]
        if middle:
            raise ValueError("strip marker lies outside both source-end blocks")
        if low and high:
            raise ValueError("strip cannot be marked at both ends")
        if len(marker_cells) > 3:
            raise ValueError("a source cap may contain at most three marker cells")
        records.append(
            {
                "bbox": (r1, c1, r2, c2),
                "orientation": orientation,
                "source_side": "low" if low else "high" if high else None,
                "marker_count": len(marker_cells),
                "marker_cells": sorted(marker_cells),
                "cells": bbox_cells,
            }
        )
    if strict_scene and len(records) != len(components):
        raise ValueError("one or more black components is not a valid strip")
    if not records:
        raise ValueError("input contains no full-span three-cell strips")
    records.sort(key=lambda row: row["bbox"])
    if strict_scene:
        if not 2 <= len(records) <= 4:
            raise ValueError("input must contain 2..4 strips")
        orientations = {record["orientation"] for record in records}
        if len(orientations) != 1:
            raise ValueError("all strips must have one common orientation")
        marked = [record for record in records if record["source_side"] is not None]
        if not marked or len(marked) >= len(records):
            raise ValueError("input requires at least one marked and one unmarked strip")
        sides = {record["source_side"] for record in marked}
        if len(sides) != 1:
            raise ValueError("marked strips must share one source side")
        marker_colors = {cell for row in grid for cell in row if cell not in (0, 7)}
        if len(marker_colors) != 1:
            raise ValueError("input requires exactly one marker color")
        union = set().union(*(record["cells"] for record in records))
        decoys = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value not in (0, 7) and (r, c) not in union
        ]
        if len(decoys) > 6:
            raise ValueError("input permits at most six stationary marker decoys")
    return records


def _fallback_side(records: list[dict[str, Any]], orientation: str) -> str:
    sides = [
        record["source_side"]
        for record in records
        if record["orientation"] == orientation and record["source_side"] is not None
    ]
    if not sides:
        return "low"
    counts = Counter(sides)
    return max((count, side) for side, count in counts.items())[1]


def strip_intermediates(grid: list[list[int]], travel_rule: str) -> list[dict[str, Any]]:
    """Return A's recovered payload measurement and B's destination for each strip."""
    _validate_rule(travel_rule)
    records = _strip_records(grid)
    fallback = _fallback_side(records, records[0]["orientation"])
    rows: list[dict[str, Any]] = []
    for record in records:
        r1, c1, r2, c2 = record["bbox"]
        side = record["source_side"] or fallback
        if record["orientation"] == "horizontal":
            source_start = c1 if side == "low" else c2 - 2
            major_length = c2 - c1 + 1
            marker_count = sum(
                grid[r][c] not in (0, 7)
                for r in range(r1, r2 + 1)
                for c in range(source_start, source_start + 3)
            )
            max_steps = max(1, (major_length - 3) // 3)
            steps = min(max_steps, max(1, marker_count))
            if travel_rule == "opposite_end":
                destination = c2 - 2 if side == "low" else c1
            else:
                destination = c1 + 3 * steps if side == "low" else c2 - 2 - 3 * steps
        else:
            source_start = r1 if side == "low" else r2 - 2
            major_length = r2 - r1 + 1
            marker_count = sum(
                grid[r][c] not in (0, 7)
                for r in range(source_start, source_start + 3)
                for c in range(c1, c2 + 1)
            )
            max_steps = max(1, (major_length - 3) // 3)
            steps = min(max_steps, max(1, marker_count))
            if travel_rule == "opposite_end":
                destination = r2 - 2 if side == "low" else r1
            else:
                destination = r1 + 3 * steps if side == "low" else r2 - 2 - 3 * steps
        rows.append(
            {
                "bbox": record["bbox"],
                "orientation": record["orientation"],
                "source_side": side,
                "marked": record["source_side"] is not None,
                "source_start": source_start,
                "marker_count": marker_count,
                "max_steps": max_steps,
                "travel_steps": steps if travel_rule == "marker_count_steps" else None,
                "destination_start": destination,
            }
        )
    return rows


def transform(grid: list[list[int]], travel_rule: str) -> list[list[int]]:
    """Independent Python mirror; qualification labels are executed by Racket."""
    _validate_rule(travel_rule)
    records = _strip_records(grid)
    intermediates = strip_intermediates(grid, travel_rule)
    output = [row[:] for row in grid]
    for record in records:
        r1, c1, r2, c2 = record["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                output[r][c] = 7
    for record, intermediate in zip(records, intermediates):
        r1, c1, r2, c2 = record["bbox"]
        if record["orientation"] == "horizontal":
            src_c = intermediate["source_start"]
            dst_c = intermediate["destination_start"]
            for r in range(r1, r2 + 1):
                for offset in range(3):
                    output[r][dst_c + offset] = grid[r][src_c + offset]
        else:
            src_r = intermediate["source_start"]
            dst_r = intermediate["destination_start"]
            for offset in range(3):
                for c in range(c1, c2 + 1):
                    output[dst_r + offset][c] = grid[src_r + offset][c]
    return output


def _strip_starts(span: int, count: int, rng: random.Random) -> tuple[int, ...]:
    choices = [
        starts
        for starts in itertools.combinations(range(span - 2), count)
        if all(right - left >= 4 for left, right in zip(starts, starts[1:]))
    ]
    if not choices:
        raise ValueError(f"cannot place {count} strips in span {span}")
    return rng.choice(choices)


def _validate_cap_sizes(cap_sizes: tuple[int, ...] | None, marked_count: int) -> tuple[int, ...] | None:
    if cap_sizes is None:
        return None
    if type(cap_sizes) is not tuple or len(cap_sizes) != marked_count:
        raise ValueError(f"cap_sizes must be a tuple of length {marked_count}")
    if any(type(value) is not int or not 1 <= value <= 3 for value in cap_sizes):
        raise ValueError("cap_sizes entries must be exact integers in 1..3")
    return cap_sizes


def sample_input(
    seed: int,
    index: int,
    *,
    size: tuple[int, int] | None = None,
    cap_sizes: tuple[int, ...] | None = None,
    cap_patterns: tuple[tuple[int, ...], ...] | None = None,
    marked_indices: tuple[int, ...] | None = None,
    orientation: str | None = None,
    source_side: str | None = None,
    cap_color: int | None = None,
    decoy_count: int | None = None,
    root: Path | str = ROOT,
) -> list[list[int]]:
    """Build a setting-neutral scene with crossed marker-count/nuisance controls."""
    del root
    if type(seed) is not int or seed < 0 or type(index) is not int or index < 0:
        raise ValueError("seed and index must be nonnegative Python integers")
    if size is None:
        size = DEMO_SIZES[index % len(DEMO_SIZES)]
    if (
        type(size) is not tuple
        or len(size) != 2
        or any(type(value) is not int or not 8 <= value <= 30 for value in size)
    ):
        raise ValueError("size must be a (height, width) pair in 8..30")
    h, w = size
    scheduled_orientation, scheduled_side = ROLE_SCHEDULE[index % len(ROLE_SCHEDULE)]
    chosen_orientation = scheduled_orientation if orientation is None else orientation
    chosen_source_side = scheduled_side if source_side is None else source_side
    if chosen_orientation not in {"horizontal", "vertical"}:
        raise ValueError("orientation must be horizontal or vertical")
    if chosen_source_side not in {"low", "high"}:
        raise ValueError("source_side must be low or high")
    orientation = chosen_orientation
    source_side = chosen_source_side
    minor = h if orientation == "horizontal" else w
    strip_count = min(4, (minor + 1) // 4)
    if strip_count < 2:
        raise ValueError("size cannot hold two separated strips")
    marked_count = strip_count - 1
    requested_sizes = _validate_cap_sizes(cap_sizes, marked_count)
    if cap_patterns is not None:
        if type(cap_patterns) is not tuple or len(cap_patterns) != marked_count:
            raise ValueError(f"cap_patterns must be a tuple of length {marked_count}")
        normalized_patterns = []
        for pattern in cap_patterns:
            if (
                type(pattern) is not tuple
                or not pattern
                or tuple(sorted(set(pattern))) != pattern
                or any(type(value) is not int or not 0 <= value <= 2 for value in pattern)
            ):
                raise ValueError("each cap pattern must be a sorted unique tuple from 0..2")
            normalized_patterns.append(pattern)
        cap_patterns = tuple(normalized_patterns)
        if requested_sizes is None:
            requested_sizes = tuple(len(pattern) for pattern in cap_patterns)
        if tuple(len(pattern) for pattern in cap_patterns) != requested_sizes:
            raise ValueError("cap_patterns lengths must match cap_sizes")
    if marked_indices is not None:
        if (
            type(marked_indices) is not tuple
            or len(marked_indices) != marked_count
            or any(type(value) is not int or not 0 <= value < strip_count for value in marked_indices)
            or tuple(sorted(set(marked_indices))) != marked_indices
        ):
            raise ValueError(
                f"marked_indices must be a sorted unique tuple of length {marked_count}"
            )
    if cap_color is not None and (type(cap_color) is not int or cap_color not in _MARKER_COLORS):
        raise ValueError("cap_color must be an exact marker color")
    if decoy_count is not None and (type(decoy_count) is not int or not 0 <= decoy_count <= 6):
        raise ValueError("decoy_count must be an exact integer in 0..6")

    rng = random.Random(int(digest(f"{seed}|{index}|c181-sequential".encode())[:16], 16))
    starts = _strip_starts(minor, strip_count, rng)
    chosen_marked_indices = (
        list(marked_indices)
        if marked_indices is not None
        else sorted(rng.sample(range(strip_count), marked_count))
    )
    if requested_sizes is None:
        sizes = [rng.randint(1, 3) for _ in range(marked_count)]
        major = w if orientation == "horizontal" else h
        max_steps = max(1, (major - 3) // 3)
        canonical_start = major - 3
        if all(3 * min(max_steps, count) == canonical_start for count in sizes):
            sizes[rng.randrange(marked_count)] = 1
        requested_sizes = tuple(sizes)
    chosen_color = cap_color if cap_color is not None else rng.choice(_MARKER_COLORS)
    chosen_decoys = decoy_count if decoy_count is not None else min(6, (index % 4) * 2)

    grid = [[7 for _ in range(w)] for _ in range(h)]
    strip_cells: set[tuple[int, int]] = set()
    size_by_index = dict(zip(chosen_marked_indices, requested_sizes))
    pattern_by_index = (
        dict(zip(chosen_marked_indices, cap_patterns)) if cap_patterns is not None else {}
    )
    for strip_index, start in enumerate(starts):
        if orientation == "horizontal":
            cells = [(r, c) for r in range(start, start + 3) for c in range(w)]
        else:
            cells = [(r, c) for r in range(h) for c in range(start, start + 3)]
        for r, c in cells:
            grid[r][c] = 0
        strip_cells.update(cells)
        if strip_index not in size_by_index:
            continue
        local_major_offsets = list(
            pattern_by_index.get(
                strip_index,
                tuple(sorted(rng.sample(range(3), size_by_index[strip_index]))),
            )
        )
        for local_major in local_major_offsets:
            if source_side == "high":
                local_major = 2 - local_major
            if orientation == "horizontal":
                r = start + 1
                c = local_major if source_side == "low" else w - 1 - local_major
            else:
                r = local_major if source_side == "low" else h - 1 - local_major
                c = start + 1
            grid[r][c] = chosen_color

    candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) not in strip_cells]
    for r, c in rng.sample(candidates, chosen_decoys):
        grid[r][c] = chosen_color
    profile = input_profile(grid)
    if (
        profile["strip_count"] != strip_count
        or profile["marked_count"] != marked_count
        or tuple(profile["cap_sizes"]) != tuple(requested_sizes)
    ):
        raise AssertionError("constructed strip profile changed during parsing")
    return grid


def input_profile(grid: list[list[int]]) -> dict[str, Any]:
    records = _strip_records(grid)
    h, w = len(grid), len(grid[0])
    strip_cells = set().union(*(record["cells"] for record in records))
    marker_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 7)
    }
    marked = [record for record in records if record["source_side"] is not None]
    source_sides = {record["source_side"] for record in marked}
    colors = {grid[r][c] for r, c in marker_cells}
    return {
        "grid_h": h,
        "grid_w": w,
        "orientation": records[0]["orientation"],
        "source_side": next(iter(source_sides)),
        "strip_count": len(records),
        "marked_count": len(marked),
        "cap_sizes": [record["marker_count"] for record in marked],
        "decoy_count": len(marker_cells - strip_cells),
        "cap_color": next(iter(colors)),
        "strip_bboxes": [list(record["bbox"]) for record in records],
    }


def _distinct_input(
    seed: int,
    index: int,
    size: tuple[int, int],
    seen: set[str],
    *,
    root: Path | str,
    cap_sizes: tuple[int, ...] | None = None,
    cap_patterns: tuple[tuple[int, ...], ...] | None = None,
    marked_indices: tuple[int, ...] | None = None,
    orientation: str | None = None,
    source_side: str | None = None,
) -> list[list[int]]:
    for retry in range(32):
        grid = sample_input(
            seed + retry * 1_000_003,
            index,
            size=size,
            cap_sizes=cap_sizes,
            cap_patterns=cap_patterns,
            marked_indices=marked_indices,
            orientation=orientation,
            source_side=source_side,
            root=root,
        )
        key = grid_digest(grid)
        if key not in seen:
            seen.add(key)
            return grid
    raise ValueError("distinct input budget exhausted; no partial episode")


def query_schedule(seed: int) -> list[tuple[int, tuple[int, int]]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative Python integer")
    schedule = list(enumerate(QUERY_SIZES))
    rng = random.Random(int(digest(f"{seed}|query-bank-order".encode())[:16], 16))
    rng.shuffle(schedule)
    return schedule


def episode_inputs(
    seed: int,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    validate_counts(demos, queries)
    seen: set[str] = set()
    demo_grids = [
        _distinct_input(
            seed,
            index,
            DEMO_SIZES[index],
            seen,
            root=root,
            cap_sizes=DEMO_CAP_SIZES[index],
            cap_patterns=DEMO_CAP_PATTERNS[index],
            marked_indices=DEMO_MARKED_INDICES[index],
            orientation=DEMO_ROLES[index][0],
            source_side=DEMO_ROLES[index][1],
        )
        for index in range(demos)
    ]
    query_grids = [
        _distinct_input(seed ^ 0xC181F41A, source_index, size, seen, root=root)
        for source_index, size in query_schedule(seed)[:queries]
    ]
    return demo_grids, query_grids


def _settings_surviving(
    train_inputs: list[list[list[int]]],
    train_outputs: list[list[list[int]]],
) -> list[dict[str, str]]:
    return [
        {"travel_rule": rule}
        for rule in TRAVEL_RULES
        if all(transform(grid, rule) == output for grid, output in zip(train_inputs, train_outputs))
    ]


def validate_public(public: dict[str, Any]) -> None:
    if type(public) is not dict or set(public) != {"train", "test"}:
        raise ValueError("public challenge must contain only train and test")
    if type(public["train"]) is not list or type(public["test"]) is not list:
        raise ValueError("public train/test must be lists")
    if not public["train"] or not public["test"]:
        raise ValueError("public train/test must be nonempty")
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in public["train"]):
        raise ValueError("public demonstrations require only input and output")
    if any(type(pair) is not dict or set(pair) != {"input"} for pair in public["test"]):
        raise ValueError("public query must contain only input")
    for pair in public["train"]:
        input_shape = _validate_grid(pair["input"])
        output_shape = _validate_grid(pair["output"])
        if input_shape != output_shape:
            raise ValueError("demonstration input/output dimensions must match")
    for pair in public["test"]:
        _validate_grid(pair["input"])
    public_challenge_bytes(public)


def _presentation_order(public: dict[str, Any], presentation_seed: int) -> list[int]:
    if type(presentation_seed) is not int or presentation_seed < 0:
        raise ValueError("presentation_seed must be a nonnegative Python integer")
    material = "|".join(grid_digest(pair["input"]) for pair in public["test"])
    rng = random.Random(int(digest(f"{presentation_seed}|{material}".encode())[:16], 16))
    order = list(range(len(public["test"])))
    rng.shuffle(order)
    return order


def sequential_views(public: dict[str, Any], *, presentation_seed: int = 0) -> list[dict[str, Any]]:
    validate_public(public)
    return [
        {"train": deepcopy(public["train"]), "test": [{"input": deepcopy(public["test"][index]["input"])}]}
        for index in _presentation_order(public, presentation_seed)
    ]


def generate_claimed_episode(
    seed: int,
    travel_rule: str,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    _validate_rule(travel_rule)
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    train = [{"input": grid, "output": transform(grid, travel_rule)} for grid in demo_grids]
    test = [{"input": grid, "output": transform(grid, travel_rule)} for grid in query_grids]
    survivors = _settings_surviving(demo_grids, [pair["output"] for pair in train])
    if survivors != [{"travel_rule": travel_rule}]:
        raise ValueError(f"demonstrations do not identify travel_rule: {survivors}")
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(travel_rule, root=root),
    }


def _rival_checks(
    all_grids: list[list[list[int]]],
    selected_outputs: list[list[list[int]]],
    demos: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    checks: dict[str, Any] = {}
    for rule in TRAVEL_RULES:
        predictions = [transform(grid, rule) for grid in all_grids]
        differing = [index for index in range(demos) if predictions[index] != selected_outputs[index]]
        checks[rule] = {
            "matches_all_demonstrations": not differing,
            "distinguishing_demo_indices": differing,
            "demonstration_predictions": predictions[:demos],
            "query_predictions": predictions[demos:],
        }
    survivors = [
        {"travel_rule": rule}
        for rule in TRAVEL_RULES
        if checks[rule]["matches_all_demonstrations"]
    ]
    return checks, survivors


def generate_episode(
    seed: int,
    bridge,
    *,
    travel_rule: str | None = None,
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative Python integer")
    validate_counts(demos, queries)
    selected = TRAVEL_RULES[seed % len(TRAVEL_RULES)] if travel_rule is None else travel_rule
    _validate_rule(selected)
    programs = {rule: program_for(rule, root=root) for rule in TRAVEL_RULES}
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    all_grids = demo_grids + query_grids
    predictions = {
        rule: [execute(bridge, programs[rule], grid) for grid in all_grids]
        for rule in TRAVEL_RULES
    }
    for rule in TRAVEL_RULES:
        for grid, output in zip(all_grids, predictions[rule]):
            if output != transform(grid, rule):
                raise ValueError(f"Python/Racket disagreement for travel_rule={rule}")
    selected_outputs = predictions[selected]
    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(demo_grids, selected_outputs[:demos])
        ],
        "test": [{"input": grid} for grid in query_grids],
    }
    rival_checks, survivors = _rival_checks(all_grids, selected_outputs, demos)
    if survivors != [{"travel_rule": selected}]:
        raise ValueError(f"demonstrations do not identify travel_rule: {survivors}")
    presentation_seed = seed ^ 0x51A7E
    private = {
        "schema": "c181f41a09f0-parametric-marker-count-travel-v2",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"travel_rule": selected},
        "program_sha256": digest(programs[selected].encode("utf-8")),
        "query_answers": selected_outputs[demos:],
        "surviving_settings": survivors,
        "rival_checks": rival_checks,
        "demo_count": demos,
        "query_count": queries,
        "query_profiles": [input_profile(grid) for grid in query_grids],
        "query_source_indices": [row[0] for row in query_schedule(seed)[:queries]],
        "presentation_seed": presentation_seed,
        "public_id": public_challenge_id(public),
        "sequential_public_ids": [
            public_challenge_id(view)
            for view in sequential_views(public, presentation_seed=presentation_seed)
        ],
    }
    verify_episode(public, private, root=root)
    return public, private


def verify_episode(public: dict[str, Any], private: dict[str, Any], *, root: Path | str = ROOT) -> None:
    validate_public(public)
    if type(private) is not dict:
        raise ValueError("private record must be a dictionary")
    required = {
        "schema",
        "status",
        "task_id",
        "seed",
        "parameter",
        "program_sha256",
        "query_answers",
        "surviving_settings",
        "rival_checks",
        "demo_count",
        "query_count",
        "query_profiles",
        "query_source_indices",
        "presentation_seed",
        "public_id",
        "sequential_public_ids",
    }
    if set(private) != required:
        raise ValueError(f"private record fields changed: {sorted(set(private) ^ required)}")
    if private["schema"] != "c181f41a09f0-parametric-marker-count-travel-v2":
        raise ValueError("private schema mismatch")
    if private["task_id"] != TASK_ID:
        raise ValueError("private task id mismatch")
    seed = private["seed"]
    if type(seed) is not int or seed < 0:
        raise ValueError("private seed must be a nonnegative exact integer")
    if type(private["parameter"]) is not dict or set(private["parameter"]) != {"travel_rule"}:
        raise ValueError("private parameter must contain exactly travel_rule")
    rule = private["parameter"]["travel_rule"]
    _validate_rule(rule)
    expected_program_hash = digest(program_for(rule, root=root).encode("utf-8"))
    if private["program_sha256"] != expected_program_hash:
        raise ValueError("private program hash does not match current rule")
    validate_counts(len(public["train"]), len(public["test"]))
    if private["demo_count"] != len(public["train"]) or private["query_count"] != len(public["test"]):
        raise ValueError("private count certificate does not match public episode")
    all_inputs = [pair["input"] for pair in public["train"] + public["test"]]
    keys = [grid_digest(grid) for grid in all_inputs]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate input in demonstration/query episode")
    answers = private["query_answers"]
    if type(answers) is not list or len(answers) != len(public["test"]):
        raise ValueError("query answer count does not match public queries")
    for index, pair in enumerate(public["train"]):
        if pair["output"] != transform(pair["input"], rule):
            raise ValueError(f"demonstration label {index} does not match selected rule")
    for index, (pair, answer) in enumerate(zip(public["test"], answers)):
        _validate_grid(answer)
        if answer != transform(pair["input"], rule):
            raise ValueError(f"query answer {index} does not match selected rule")
    selected_outputs = [pair["output"] for pair in public["train"]] + answers
    expected_checks, survivors = _rival_checks(all_inputs, selected_outputs, len(public["train"]))
    if private["surviving_settings"] != survivors or survivors != [{"travel_rule": rule}]:
        raise ValueError(f"demonstrations are underidentified or survivor certificate is forged: {survivors}")
    if private["rival_checks"] != expected_checks:
        raise ValueError("private rival certificate does not match current episode")
    if private["query_profiles"] != [input_profile(pair["input"]) for pair in public["test"]]:
        raise ValueError("private query profile certificate does not match inputs")
    expected_indices = [row[0] for row in query_schedule(seed)[: len(public["test"])]]
    if private["query_source_indices"] != expected_indices:
        raise ValueError("private query source order does not match seed")
    if private["public_id"] != public_challenge_id(public):
        raise ValueError("public identifier does not match visible bytes")
    presentation_seed = private["presentation_seed"]
    expected_ids = [
        public_challenge_id(view)
        for view in sequential_views(public, presentation_seed=presentation_seed)
    ]
    if private["sequential_public_ids"] != expected_ids:
        raise ValueError("sequential view certificate does not match visible bytes")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public(path: Path, public: dict[str, Any]) -> None:
    validate_public(public)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(public))


def _crossed_control_evidence(*, root: Path | str = ROOT) -> dict[str, Any]:
    kwargs = dict(seed=911, index=3, size=(30, 30), root=root)
    counts_a = sample_input(**kwargs, cap_sizes=(1, 2, 3), cap_color=2, decoy_count=2)
    counts_b = sample_input(**kwargs, cap_sizes=(2, 1, 3), cap_color=2, decoy_count=2)
    nuisance = sample_input(**kwargs, cap_sizes=(1, 2, 3), cap_color=8, decoy_count=6)
    rows_a = strip_intermediates(counts_a, "marker_count_steps")
    rows_b = strip_intermediates(counts_b, "marker_count_steps")
    rows_nuisance = strip_intermediates(nuisance, "marker_count_steps")
    destinations = lambda rows: {
        str(row["bbox"]): row["destination_start"] for row in rows if row["marked"]
    }
    if destinations(rows_a) == destinations(rows_b):
        raise AssertionError("count control failed to change a destination")
    if destinations(rows_a) != destinations(rows_nuisance):
        raise AssertionError("nuisance control changed count-derived destinations")
    return {
        "schema": "c181f41a09f0-crossed-controls-v1",
        "fixed": {"size": [30, 30], "seed": 911, "index": 3},
        "count_control": {
            "cap_sizes_a": [1, 2, 3],
            "cap_sizes_b": [2, 1, 3],
            "destinations_a": destinations(rows_a),
            "destinations_b": destinations(rows_b),
        },
        "nuisance_control": {
            "cap_sizes": [1, 2, 3],
            "colors": [2, 8],
            "decoy_counts": [2, 6],
            "destination_map": destinations(rows_a),
        },
        "inputs": {"counts_a": counts_a, "counts_b": counts_b, "nuisance": nuisance},
    }


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    validate_counts(demos, queries)
    out = Path(out)
    root = Path(root)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory is not empty: {out}")
    for folder in ("public", "private", "rules", "sequential", "adversarial"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    programs = {rule: program_for(rule, root=root) for rule in TRAVEL_RULES}
    for rule, program in programs.items():
        (out / "rules" / f"travel-{rule}.rkt").write_text(program, encoding="utf-8")
    (out / "rules" / "counterfactual-constant-one.rkt").write_text(
        counterfactual_program(root=root), encoding="utf-8"
    )

    from arc_repl.racket_bridge import RacketBridge

    episodes = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            public, private = generate_episode(seed, bridge, demos=demos, queries=queries, root=root)
            public_id = public_challenge_id(public)
            _write_public(out / "public" / f"{public_id}.json", public)
            _write_json(out / "private" / f"{public_id}.json", private)
            sequential_ids = []
            for view in sequential_views(public, presentation_seed=private["presentation_seed"]):
                view_id = public_challenge_id(view)
                _write_public(out / "sequential" / f"{view_id}.json", view)
                sequential_ids.append(view_id)
            episodes.append(
                {
                    "public_id": public_id,
                    "seed": seed,
                    "parameter": private["parameter"],
                    "demos": demos,
                    "queries": queries,
                    "query_source_indices": private["query_source_indices"],
                    "sequential_public_ids": sequential_ids,
                }
            )

        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute(bridge, programs[DEFAULT_TRAVEL_RULE], pair["input"])
            if actual != pair["output"] or actual != transform(pair["input"], DEFAULT_TRAVEL_RULE):
                raise ValueError("canonical default failed a labeled canonical pair")
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "output": actual,
                }
            )
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

        witness = sample_input(
            991,
            3,
            size=(30, 30),
            cap_sizes=(1, 2, 3),
            decoy_count=6,
            root=root,
        )
        actual = execute(bridge, programs["marker_count_steps"], witness)
        counterfactual = execute(bridge, counterfactual_program(root=root), witness)
        if actual == counterfactual:
            raise ValueError("wrong-intermediate witness failed to change final output")
        _write_json(
            out / "adversarial" / "wrong-intermediate-witness.json",
            {
                "input": witness,
                "settings": {"travel_rule": "marker_count_steps"},
                "intermediate_value": strip_intermediates(witness, "marker_count_steps"),
                "output": actual,
                "counterfactual_output": counterfactual,
                "ablation": "wrong_intermediate",
            },
        )

    _write_json(out / "adversarial" / "crossed-controls.json", _crossed_control_evidence(root=root))
    _, generator_source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    manifest = {
        "schema": "c181f41a09f0-parametric-marker-count-evidence-v2",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameters": {"travel_rule": list(TRAVEL_RULES)},
        "default": {"travel_rule": DEFAULT_TRAVEL_RULE},
        "limits": {"demos": list(DEMO_LIMITS), "queries": list(QUERY_LIMITS)},
        "materialized_request": {"demos": demos, "queries": queries},
        "episodes": episodes,
        "canonical_default_unchanged": programs[DEFAULT_TRAVEL_RULE]
        == canonical_record(root=root)["program_solution"],
        "program_sha256": {rule: digest(program.encode("utf-8")) for rule, program in programs.items()},
        "counterfactual_program_sha256": digest(counterfactual_program(root=root).encode("utf-8")),
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": digest(Path(__file__).read_bytes()),
        "racket_runtime": runtime_identity,
        "sequential_dependency": {
            "step_a": "infer each strip's source end, recover its complete 3x3 source block, and count marker cells in that block",
            "intermediate": "the exact per-strip source marker count (1..3 for marked strips; zero for inherited unmarked strips)",
            "step_b": "move the recovered block by that many three-cell steps from the source, clipped only by the strip's lawful capacity",
            "why_b_depends_on_a": "the destination coordinate is computed from the recovered source block's marker count; a constant-one wrong intermediate changes protected-Racket outputs",
        },
        "bounded_adversarial_pass": {
            "attempted": [
                "wrong-intermediate constant-one protected-Racket ablation",
                "crossed count controls at fixed size/strip geometry/source side",
                "crossed color/decoy nuisances at fixed count intermediate",
                "2-demo teaching minimum against all declared setting programs",
                "8x12 minimum, axis swap, boundary sources and substantive 30x30 scenes",
                "duplicate input, forged program hash, mutated label, leaked output and boolean-cell verifier attacks",
            ],
            "result": "all retained attacks reject or distinguish on current bytes; finite rivals do not prove universal uniqueness",
        },
        "limitations": [
            "reviewer-ready only; owner qualification and exact-source acceptance remain pending",
            "finite evidence covers declared settings and sampled shortcut rivals, not every possible rule",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        demos=args.demos,
        queries=args.queries,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
