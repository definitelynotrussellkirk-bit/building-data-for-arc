"""Input generator for completing exact three-corner rectangles.

The immutable Racket authority acts independently on each nonzero color.  It
fills the fourth axis-aligned rectangle corner only when that color has exactly
three cells spanning exactly two rows and two columns.  This sampler includes
legal no-op colors that distinguish that rule from bounding-box shortcuts:
bent three-cell sets, diagonal pairs, collinear triples, and complete rectangles.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f0f02eb1d2e0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bf8c9dd4f7fa"

SUMMARY = (
    "For each nonzero color with exactly three cells on exactly two rows and "
    "two columns, fill its missing fourth rectangle corner in the same color. "
    "Other per-color configurations remain unchanged. Four linked profiles "
    "include canonical anchors plus bent triples, diagonal pairs, collinear "
    "triples, complete rectangles, larger target counts, and long-span targets."
)

INVARIANTS = [
    "background is 0 and every nonzero color is used for exactly one configuration",
    "every input has at least one exact three-corner rectangle target",
    "target fourth corners are reserved background cells before the rule runs",
    "bent three-cell and diagonal-pair decoys remain unchanged",
    "every four consecutive default samples cover one canonical anchor and three redundant teaching profiles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "6..12",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "9..14",
        "doc": "Input grid width.",
    },
    "n_targets": {
        "type": "int",
        "default": "2, 1, 3, 3 by profile",
        "valid": "1..4",
        "doc": "Number of colors that the rule completes.",
    },
    "n_bent_decoys": {
        "type": "int",
        "default": "0, 1, 1, 2 by profile",
        "valid": "0..2",
        "doc": "Three-cell colors spanning 3x2 or 2x3; the exact rule leaves them unchanged.",
    },
    "n_other_decoys": {
        "type": "int",
        "default": "0, 0, 2, 1 by profile",
        "valid": "0..2",
        "doc": "Diagonal-pair plus collinear/full-rectangle no-op colors.",
    },
    "corner_offset": {
        "type": "int",
        "default": "profile index 0..3",
        "valid": "0..3",
        "doc": "Missing-corner orientation of the lowest-colored target; later targets cycle clockwise.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (0, 1, 2, 3)

_CANONICAL_DIMS = {(6, 10), (7, 9), (8, 10)}
_CANONICAL_PALETTES = {
    frozenset({2, 3}),
    frozenset({4, 6}),
    frozenset({5, 8}),
}
_CORNER_OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Seed-independent four-profile curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    return difficulty


def _profile_defaults(profile: int, difficulty: str | None) -> dict[str, int]:
    band = _band(difficulty)
    canonical = {
        "easy": (6, 10),
        "medium": (7, 9),
        "hard": (8, 10),
    }[band]
    broad_dims = {
        "easy": ((7, 11), (8, 11), (9, 12)),
        "medium": ((8, 11), (9, 12), (10, 13)),
        "hard": ((10, 12), (11, 13), (12, 14)),
    }[band]
    if profile == 0:
        h, w = canonical
        return {
            "grid_h": h,
            "grid_w": w,
            "n_targets": 2,
            "n_bent_decoys": 0,
            "n_other_decoys": 0,
            "corner_offset": 0,
        }
    if profile == 1:
        # A second canonical-envelope profile keeps morphology support above the
        # clean-gate floor while teaching that a non-rectangular three-cell color
        # is a no-op. One target plus one bent decoy preserves palette size 3.
        h, w = canonical
        return {
            "grid_h": h,
            "grid_w": w,
            "n_targets": 1,
            "n_bent_decoys": 1,
            "n_other_decoys": 0,
            "corner_offset": 1,
        }
    h, w = broad_dims[profile - 1]
    return {
        "grid_h": h,
        "grid_w": w,
        "n_targets": 3,
        "n_bent_decoys": (1, 2)[profile - 2],
        "n_other_decoys": (2, 1)[profile - 2],
        "corner_offset": profile,
    }


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _corners(r0: int, r1: int, c0: int, c1: int):
    return ((r0, c0), (r0, c1), (r1, c0), (r1, c1))


@lru_cache(maxsize=512)
def _candidates(h: int, w: int, kind: str, orientation: int = 0):
    """Return immutable (painted, reserved, metadata) placement candidates."""
    rows = []
    if kind == "target":
        for r0 in range(h - 1):
            for r1 in range(r0 + 1, h):
                for c0 in range(w - 1):
                    for c1 in range(c0 + 1, w):
                        corners = _corners(r0, r1, c0, c1)
                        painted = tuple(
                            point for index, point in enumerate(corners) if index != orientation
                        )
                        rows.append(
                            (
                                frozenset(painted),
                                frozenset(corners),
                                (r1 - r0, c1 - c0),
                            )
                        )
    elif kind == "bent":
        for row in range(h - 2):
            for col in range(w - 1):
                footprint = frozenset(
                    (r, c)
                    for r in range(row, row + 3)
                    for c in range(col, col + 2)
                )
                rows.append(
                    (
                        frozenset(((row, col), (row + 1, col + 1), (row + 2, col))),
                        footprint,
                        None,
                    )
                )
                rows.append(
                    (
                        frozenset(((row, col + 1), (row + 1, col), (row + 2, col + 1))),
                        footprint,
                        None,
                    )
                )
        for row in range(h - 1):
            for col in range(w - 2):
                footprint = frozenset(
                    (r, c)
                    for r in range(row, row + 2)
                    for c in range(col, col + 3)
                )
                rows.append(
                    (
                        frozenset(((row, col), (row + 1, col + 1), (row, col + 2))),
                        footprint,
                        None,
                    )
                )
                rows.append(
                    (
                        frozenset(((row + 1, col), (row, col + 1), (row + 1, col + 2))),
                        footprint,
                        None,
                    )
                )
    elif kind == "diagonal":
        for row in range(h - 1):
            for col in range(w - 1):
                footprint = frozenset(
                    ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
                )
                rows.append(
                    (frozenset(((row, col), (row + 1, col + 1))), footprint, None)
                )
                rows.append(
                    (frozenset(((row, col + 1), (row + 1, col))), footprint, None)
                )
    elif kind == "line":
        for row in range(h):
            for col in range(w - 2):
                cells = frozenset(((row, col), (row, col + 1), (row, col + 2)))
                rows.append((cells, cells, None))
        for row in range(h - 2):
            for col in range(w):
                cells = frozenset(((row, col), (row + 1, col), (row + 2, col)))
                rows.append((cells, cells, None))
    elif kind == "full_rectangle":
        for row in range(h - 1):
            for col in range(w - 1):
                cells = frozenset(
                    ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
                )
                rows.append((cells, cells, None))
    else:
        raise ValueError(f"unknown placement kind {kind!r}")
    return tuple(rows)


def _other_kind(profile: int, index: int) -> str:
    if index == 0:
        return "diagonal"
    return "full_rectangle" if profile == 3 else "line"


def _place_specs(ctx, h: int, w: int, specs: list[dict[str, Any]]):
    rng = ctx.draw_rng("placement")
    candidate_rows = []
    for spec_index, spec in enumerate(specs):
        choices = list(_candidates(h, w, spec["kind"], spec.get("orientation", 0)))
        if spec["kind"] == "target" and spec.get("require_long"):
            choices = [row for row in choices if max(row[2]) >= 2]
        rng.shuffle(choices)
        candidate_rows.append((spec_index, choices))
    candidate_rows.sort(key=lambda item: (len(item[1]), item[0]))

    placed: list[Any] = [None] * len(specs)

    def search(depth: int, reserved: frozenset[tuple[int, int]]) -> bool:
        if depth == len(candidate_rows):
            return True
        spec_index, choices = candidate_rows[depth]
        for candidate in choices:
            painted, footprint, _ = candidate
            if not footprint.isdisjoint(reserved):
                continue
            placed[spec_index] = candidate
            if search(depth + 1, reserved | footprint):
                return True
            placed[spec_index] = None
        return False

    if not search(0, frozenset()):
        raise RuntimeError(
            f"constructive placement failed for {h}x{w} with "
            f"{len(specs)} color configurations"
        )
    return placed


def _canonical_palette(difficulty: str | None) -> tuple[int, int]:
    return {
        "easy": (2, 3),
        "medium": (4, 6),
        "hard": (5, 8),
    }[_band(difficulty)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    _band(difficulty)
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 6, 12)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 9, 14)
    n_targets = _draw_int_axis(
        ctx, overrides, "n_targets", defaults["n_targets"], 1, 4
    )
    n_bent = _draw_int_axis(
        ctx, overrides, "n_bent_decoys", defaults["n_bent_decoys"], 0, 2
    )
    n_other = _draw_int_axis(
        ctx, overrides, "n_other_decoys", defaults["n_other_decoys"], 0, 2
    )
    corner_offset = _draw_int_axis(
        ctx, overrides, "corner_offset", defaults["corner_offset"], 0, 3
    )

    total_colors = n_targets + n_bent + n_other
    if total_colors > 8:
        raise RuntimeError("axis maxima exceed the eight supported nonzero colors")

    specs: list[dict[str, Any]] = []
    for index in range(n_targets):
        specs.append(
            {
                "kind": "target",
                "orientation": (corner_offset + index) % 4,
                "require_long": index == 0,
            }
        )
    specs.extend({"kind": "bent"} for _ in range(n_bent))
    specs.extend({"kind": _other_kind(profile, index)} for index in range(n_other))

    placed = _place_specs(ctx, h, w, specs)
    canonical_mode = (
        profile == 0
        and n_targets == 2
        and n_bent == 0
        and n_other == 0
        and (h, w) in _CANONICAL_DIMS
    )
    if canonical_mode:
        colors = _canonical_palette(difficulty)
    else:
        colors = tuple(
            sorted(ctx.draw_rng("palette").sample(range(1, 10), total_colors))
        )

    grid = full_grid(h, w, 0)
    for color, candidate in zip(colors, placed):
        painted, _, _ = candidate
        for row, col in painted:
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement collision")
            grid[row][col] = color
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or not 0 <= value <= 9
        },
        key=repr,
    )
    return [f"grid contains non-ARC values: {bad[:4]}"] if bad else []


def _normalized(cells: tuple[tuple[int, int], ...]):
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return frozenset((row - r0, col - c0) for row, col in cells)


_BENT_SHAPES = {
    frozenset(((0, 0), (1, 1), (2, 0))),
    frozenset(((0, 1), (1, 0), (2, 1))),
    frozenset(((0, 0), (1, 1), (0, 2))),
    frozenset(((1, 0), (0, 1), (1, 2))),
}


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    colors = sorted({value for row in grid for value in row if value != 0})
    records = []
    reasons = []
    for color in colors:
        cells = tuple(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        )
        rs = sorted({row for row, _ in cells})
        cs = sorted({col for _, col in cells})
        corners = (
            frozenset((row, col) for row in rs for col in cs)
            if len(rs) == 2 and len(cs) == 2
            else frozenset()
        )
        kind = "unknown"
        missing = None
        orientation = None
        if len(cells) == 3 and len(rs) == 2 and len(cs) == 2:
            kind = "target"
            missing_set = corners - set(cells)
            if len(missing_set) != 1:
                reasons.append(f"color {color}: target has no unique missing corner")
            else:
                missing = next(iter(missing_set))
                orientation = _CORNER_OFFSETS.index((rs.index(missing[0]), cs.index(missing[1])))
                if grid[missing[0]][missing[1]] != 0:
                    reasons.append(f"color {color}: target missing corner is occupied")
        elif (
            len(cells) == 3
            and (len(rs), len(cs)) in ((3, 2), (2, 3))
            and _normalized(cells) in _BENT_SHAPES
        ):
            kind = "bent"
        elif len(cells) == 3 and (len(rs) == 1 or len(cs) == 1):
            kind = "line"
        elif len(cells) == 2 and len(rs) == 2 and len(cs) == 2:
            kind = "diagonal"
        elif len(cells) == 4 and len(rs) == 2 and len(cs) == 2 and set(cells) == corners:
            kind = "full_rectangle"
        else:
            reasons.append(
                f"color {color}: unsupported configuration with {len(cells)} cells, "
                f"{len(rs)} rows, and {len(cs)} columns"
            )
        records.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "rows": tuple(rs),
                "cols": tuple(cs),
                "kind": kind,
                "missing": missing,
                "orientation": orientation,
                "row_span": rs[-1] - rs[0] if len(rs) >= 2 else 0,
                "col_span": cs[-1] - cs[0] if len(cs) >= 2 else 0,
            }
        )
    return {
        "errors": reasons,
        "grid_h": h,
        "grid_w": w,
        "colors": frozenset(colors),
        "records": records,
        "targets": [row for row in records if row["kind"] == "target"],
        "bent": [row for row in records if row["kind"] == "bent"],
        "other": [
            row
            for row in records
            if row["kind"] in ("line", "diagonal", "full_rectangle")
        ],
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    targets = analysis["targets"]
    if not targets:
        raise ValueError("cannot observe corner_offset without a target")
    first = min(targets, key=lambda row: row["color"])
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_targets": len(targets),
        "n_bent_decoys": len(analysis["bent"]),
        "n_other_decoys": len(analysis["other"]),
        "corner_offset": first["orientation"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if not analysis["targets"]:
        reasons.append("no exact three-corner rectangle target")
    if 0 not in {value for row in grid for value in row}:
        reasons.append("background color 0 is absent")
    overrides = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(overrides, dict):
        observed = observe_overrides(grid)
        for name, expected in overrides.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                reasons.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    """Recognize the three measured canonical input profiles."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons = []
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the canonical 6x10/7x9/8x10 set")
    if analysis["colors"] not in _CANONICAL_PALETTES:
        reasons.append("nonzero palette is not one of the three canonical pairs")
    if len(analysis["targets"]) != 2:
        reasons.append("canonical inputs have exactly two target colors")
    if analysis["bent"] or analysis["other"]:
        reasons.append("canonical inputs contain no decoy colors")
    return reasons


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    dims = (analysis["grid_h"], analysis["grid_w"])
    return {
        **observe_overrides(grid),
        "errors": [],
        "canonical_anchor": not strict_canonical_like(grid),
        "outside_canonical_dimensions": dims not in _CANONICAL_DIMS,
        "has_bent_three": bool(analysis["bent"]),
        "has_diagonal_pair": any(row["kind"] == "diagonal" for row in analysis["other"]),
        "has_long_target": any(
            max(row["row_span"], row["col_span"]) >= 2
            for row in analysis["targets"]
        ),
    }


def _copy_grid(grid):
    return [list(row) for row in grid]


def rule_mirror(grid):
    """Independent Python oracle for tests; Racket remains label authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = _copy_grid(grid)
    for target in analysis["targets"]:
        row, col = target["missing"]
        out[row][col] = target["color"]
    return out


def _fill_extreme_corners(out, record):
    r0, r1 = record["rows"][0], record["rows"][-1]
    c0, c1 = record["cols"][0], record["cols"][-1]
    for row, col in _corners(r0, r1, c0, c1):
        out[row][col] = record["color"]


def _rival_noncollinear_bbox(grid):
    """Wrongly completes every noncollinear three-cell bounding box."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = _copy_grid(grid)
    for record in analysis["records"]:
        if len(record["cells"]) == 3 and len(record["rows"]) >= 2 and len(record["cols"]) >= 2:
            _fill_extreme_corners(out, record)
    return out


def _rival_diagonal_pairs(grid):
    """Wrongly treats diagonal pairs as incomplete rectangles too."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = rule_mirror(grid)
    for record in analysis["other"]:
        if record["kind"] == "diagonal":
            _fill_extreme_corners(out, record)
    return out


def _rival_only_two_targets(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return rule_mirror(grid) if len(analysis["targets"]) == 2 else _copy_grid(grid)


def _rival_canonical_dimensions(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    dims = (analysis["grid_h"], analysis["grid_w"])
    return rule_mirror(grid) if dims in _CANONICAL_DIMS else _copy_grid(grid)


def _rival_adjacent_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = _copy_grid(grid)
    for target in analysis["targets"]:
        if target["row_span"] == 1 and target["col_span"] == 1:
            row, col = target["missing"]
            out[row][col] = target["color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "complete every noncollinear three-cell bounding box": _rival_noncollinear_bbox,
    "complete diagonal pairs as rectangles": _rival_diagonal_pairs,
    "apply the rule only when exactly two targets are present": _rival_only_two_targets,
    "apply the rule only at canonical dimensions": _rival_canonical_dimensions,
    "complete only adjacent 2x2 corner triplets": _rival_adjacent_only,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "complete every noncollinear three-cell bounding box",
        "complete diagonal pairs as rectangles",
        "apply the rule only when exactly two targets are present",
        "apply the rule only at canonical dimensions",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "bent_three_cell_decoy": lambda grid: semantic_observables(grid).get("has_bent_three", False),
    "diagonal_pair_decoy": lambda grid: semantic_observables(grid).get("has_diagonal_pair", False),
    "more_than_two_targets": lambda grid: semantic_observables(grid).get("n_targets", 0) > 2,
    "outside_canonical_dimensions": lambda grid: semantic_observables(grid).get("outside_canonical_dimensions", False),
    "long_span_target": lambda grid: semantic_observables(grid).get("has_long_target", False),
}
WITNESS_RIVALS = {
    "bent_three_cell_decoy": ["complete every noncollinear three-cell bounding box"],
    "diagonal_pair_decoy": ["complete diagonal pairs as rectangles"],
    "more_than_two_targets": ["apply the rule only when exactly two targets are present"],
    "outside_canonical_dimensions": ["apply the rule only at canonical dimensions"],
    "long_span_target": ["complete only adjacent 2x2 corner triplets"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require enough labelled contrasts to reject every declared competitor."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons = []
    rows = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the exact rectangle rule")
            continue
        rows.append(semantic_observables(demo["input"]))
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")
    if reasons:
        return reasons

    requirements = (
        ("has_bent_three", "demonstrations omit a bent three-cell counterexample"),
        ("has_diagonal_pair", "demonstrations omit a diagonal-pair counterexample"),
        ("outside_canonical_dimensions", "demonstrations stay inside canonical dimensions"),
        ("has_long_target", "demonstrations omit a long-span target rectangle"),
    )
    for key, message in requirements:
        if not any(row[key] for row in rows):
            reasons.append(message)
    if not any(row["n_targets"] > 2 for row in rows):
        reasons.append("demonstrations omit a case with more than two targets")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(f"competitor survives demonstrations and changes query: {name}")
    return reasons
