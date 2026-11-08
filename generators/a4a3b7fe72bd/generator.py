"""Task-specific generator for ARC puzzle ``a4a3b7fe72bd``.

Each non-zero color is a single straight segment with a distinct length.  The
answer sorts colors by segment length, longest first, and paints concentric
rings in an ``N x N`` grid where ``N`` is the longest segment length.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4a3b7fe72bd"
VERSION = "3.0.0"
TASK_ID = "a4a3b7fe72bd"
RULE_HASH = "7db7ae0bc165"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A rectangular zero-background grid contains 2-4 differently colored, "
    "well-separated straight segments. Segment lengths are distinct. Sort "
    "the colors by descending segment length; let N be the longest length. "
    "Return an N by N grid whose rings, from outside inward, use those colors "
    "in descending-length order."
)

INVARIANTS = [
    "background is color 0 and all cells are ARC colors 0..9",
    "there are 2-4 non-zero colors",
    "each non-zero color forms exactly one horizontal, vertical, or unit segment",
    "segment lengths are pairwise distinct and the maximum is 3..8",
    "the number of colors is ceil(maximum segment length / 2)",
    "different colored segments do not touch, even diagonally",
]

LENGTH_PROFILES = ("step2", "consecutive", "irregular")
LINE_ORIENTATIONS = ("horizontal_only", "vertical_only", "mixed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors or keyed rng",
        "valid": "14..29",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors or keyed rng",
        "valid": "14..29",
    },
    "n_colors": {
        "type": "int",
        "default": "derived teaching profile",
        "valid": "2..4",
    },
    "max_length": {
        "type": "int",
        "default": "scheduled teaching profile",
        "valid": "3..8",
    },
    "length_profile": {
        "type": "str",
        "default": "scheduled teaching profile",
        "valid": "step2|consecutive|irregular",
    },
    "line_orientation": {
        "type": "str",
        "default": "scheduled teaching profile",
        "valid": "horizontal_only|vertical_only|mixed",
    },
}

# The first four slots deliberately mirror all four unique canonical shape /
# palette-count profiles.  run_one() consumes consecutive sample indices, so
# every generated lesson gets complementary demonstrations and a held-out query.
_ANCHOR_DIMENSIONS = {
    0: (21, 22),
    1: (23, 29),
    2: (24, 20),
    3: (21, 23),
}
_PROFILE_SCHEDULE = (
    (6, "step2", "vertical_only"),
    (5, "irregular", "horizontal_only"),
    (8, "step2", "mixed"),
    (7, "step2", "mixed"),
    (4, "consecutive", "horizontal_only"),
    (3, "consecutive", "vertical_only"),
    (6, "irregular", "mixed"),
    (8, "consecutive", "mixed"),
)
_IRREGULAR_LENGTHS = {
    4: (4, 1),
    5: (5, 4, 1),
    6: (6, 5, 2),
    7: (7, 6, 3, 1),
    8: (8, 7, 4, 1),
}


def _n_colors_for(max_length: int) -> int:
    return (max_length + 1) // 2


def _lengths_for(max_length: int, profile: str) -> tuple[int, ...]:
    n_colors = _n_colors_for(max_length)
    if profile == "step2":
        return tuple(max_length - 2 * index for index in range(n_colors))
    if profile == "consecutive":
        return tuple(max_length - index for index in range(n_colors))
    if profile == "irregular" and max_length in _IRREGULAR_LENGTHS:
        return _IRREGULAR_LENGTHS[max_length]
    raise ValueError(
        f"length_profile={profile!r} is incompatible with max_length={max_length}"
    )


def _valid_profile(max_length: int, profile: str, orientation: str) -> bool:
    try:
        lengths = _lengths_for(max_length, profile)
    except ValueError:
        return False
    if orientation == "mixed" and sum(length > 1 for length in lengths) < 2:
        return False
    return True


def _validate_override_types(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for name in ("grid_h", "grid_w", "n_colors", "max_length"):
        if name not in overrides:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name} must be an integer")

    ranges = {
        "grid_h": (14, 29),
        "grid_w": (14, 29),
        "n_colors": (2, 4),
        "max_length": (3, 8),
    }
    for name, (lo, hi) in ranges.items():
        if name in overrides and not lo <= overrides[name] <= hi:
            raise ValueError(f"override {name}={overrides[name]} outside {lo}..{hi}")

    if "length_profile" in overrides and overrides["length_profile"] not in LENGTH_PROFILES:
        raise ValueError(f"unknown length_profile {overrides['length_profile']!r}")
    if "line_orientation" in overrides and overrides["line_orientation"] not in LINE_ORIENTATIONS:
        raise ValueError(f"unknown line_orientation {overrides['line_orientation']!r}")


def _choose_profile(ctx, sample_index: int, overrides: dict[str, Any]) -> tuple[int, int, str, str]:
    semantic_keys = {"n_colors", "max_length", "length_profile", "line_orientation"}
    explicit = semantic_keys & set(overrides)
    candidates: list[tuple[int, int, str, str]] = []
    for max_length in range(3, 9):
        n_colors = _n_colors_for(max_length)
        for profile in LENGTH_PROFILES:
            for orientation in LINE_ORIENTATIONS:
                candidate = (max_length, n_colors, profile, orientation)
                if not _valid_profile(max_length, profile, orientation):
                    continue
                if any(
                    overrides.get(key, value) != value
                    for key, value in zip(
                        ("max_length", "n_colors", "length_profile", "line_orientation"),
                        candidate,
                    )
                    if key in explicit
                ):
                    continue
                candidates.append(candidate)
    if not candidates:
        detail = ", ".join(f"{key}={overrides[key]!r}" for key in sorted(explicit))
        raise ValueError(f"incompatible semantic overrides: {detail}")

    if not explicit:
        max_length, profile, orientation = _PROFILE_SCHEDULE[sample_index % len(_PROFILE_SCHEDULE)]
        chosen = (max_length, _n_colors_for(max_length), profile, orientation)
    else:
        chooser = ctx.draw_rng("profile_selector")
        chosen = candidates[chooser.randrange(len(candidates))]

    max_length, n_colors, profile, orientation = chosen
    # Every declared exact axis receives keyed provenance, including scheduled
    # values. Explicit overrides are consumed by the matching GenCtx draw.
    max_length = ctx.draw_int("max_length", max_length, max_length)
    n_colors = ctx.draw_int("n_colors", n_colors, n_colors)
    profile = ctx.draw_choice("length_profile", [profile])
    orientation = ctx.draw_choice("line_orientation", [orientation])
    return max_length, n_colors, profile, orientation


def _choose_dimension(ctx, name: str, sample_index: int, difficulty: str | None) -> int:
    if name in ctx.overrides:
        return ctx.draw_int(name, 14, 29)
    slot = sample_index % len(_PROFILE_SCHEDULE)
    if slot in _ANCHOR_DIMENSIONS:
        value = _ANCHOR_DIMENSIONS[slot][0 if name == "grid_h" else 1]
        return ctx.draw_int(name, value, value)
    bounds = {
        "easy": (14, 21),
        "medium": (18, 26),
        "hard": (22, 29),
        None: (18, 27),
    }[difficulty]
    return ctx.draw_int(name, *bounds)


def _orientations_for(lengths: tuple[int, ...], mode: str, rng) -> list[str]:
    orientations = ["p" if length == 1 else "" for length in lengths]
    nonpoints = [index for index, length in enumerate(lengths) if length > 1]
    if mode == "horizontal_only":
        for index in nonpoints:
            orientations[index] = "h"
    elif mode == "vertical_only":
        for index in nonpoints:
            orientations[index] = "v"
    else:
        if len(nonpoints) < 2:
            raise ValueError("mixed orientation needs at least two non-unit segments")
        order = list(nonpoints)
        rng.shuffle(order)
        orientations[order[0]] = "h"
        orientations[order[1]] = "v"
        for index in order[2:]:
            orientations[index] = rng.choice(("h", "v"))
    return orientations


def _candidate_cells(h: int, w: int, length: int, orientation: str) -> list[tuple[tuple[int, int], ...]]:
    if length == 1:
        return [((r, c),) for r in range(h) for c in range(w)]
    if orientation == "h":
        return [
            tuple((r, c + delta) for delta in range(length))
            for r in range(h)
            for c in range(w - length + 1)
        ]
    return [
        tuple((r + delta, c) for delta in range(length))
        for r in range(h - length + 1)
        for c in range(w)
    ]


def _well_separated(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        max(abs(r - rr), abs(c - cc)) > 1
        for r, c in cells
        for rr, cc in occupied
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _choose_dimension(ctx, "grid_h", sample_index, difficulty)
    w = _choose_dimension(ctx, "grid_w", sample_index, difficulty)
    max_length, n_colors, profile, orientation_mode = _choose_profile(
        ctx, sample_index, overrides
    )
    lengths = _lengths_for(max_length, profile)
    if len(lengths) != n_colors:
        raise AssertionError("profile/color-count invariant broken")

    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude=(0,))
    placement_rng = ctx.draw_rng("placement")
    orientations = _orientations_for(lengths, orientation_mode, placement_rng)
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()

    # Place long segments first; short segments then have many legal positions.
    for color, length, orientation in zip(palette, lengths, orientations):
        candidates = _candidate_cells(h, w, length, orientation)
        placement_rng.shuffle(candidates)
        chosen = next(
            (cells for cells in candidates if _well_separated(cells, occupied)),
            None,
        )
        if chosen is None:
            raise ValueError(
                f"could not place length-{length} segment in {h}x{w} grid "
                "with one-cell separation"
            )
        for r, c in chosen:
            grid[r][c] = color
        occupied.update(chosen)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def _line_info(cells: list[tuple[int, int]]) -> tuple[str, int] | None:
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    if len(cells) == 1:
        return "p", 1
    if len(rows) == 1 and cols == list(range(cols[0], cols[-1] + 1)):
        return "h", len(cells)
    if len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
        return "v", len(cells)
    return None


def _profile_name(lengths: tuple[int, ...]) -> str | None:
    max_length = lengths[0]
    for profile in LENGTH_PROFILES:
        try:
            if _lengths_for(max_length, profile) == lengths:
                return profile
        except ValueError:
            pass
    return None


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {}, ["grid must be a non-empty list of non-empty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {}, ["grid must be rectangular"]
    if not (14 <= h <= 29 and 14 <= w <= 29):
        errors.append(f"grid size {h}x{w} outside 14..29 by 14..29")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return {}, errors

    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                by_color.setdefault(color, []).append((r, c))
    if not 2 <= len(by_color) <= 4:
        errors.append(f"expected 2-4 non-zero colors, found {len(by_color)}")

    segment_info: dict[int, dict[str, Any]] = {}
    for color, cells in by_color.items():
        info = _line_info(cells)
        if info is None:
            errors.append(f"color {color} is not one contiguous straight segment")
            continue
        orientation, length = info
        segment_info[color] = {
            "cells": tuple(sorted(cells)),
            "orientation": orientation,
            "length": length,
        }

    lengths = tuple(sorted((item["length"] for item in segment_info.values()), reverse=True))
    if len(lengths) != len(by_color):
        pass
    elif len(set(lengths)) != len(lengths):
        errors.append(f"segment lengths must be pairwise distinct, observed {lengths}")

    max_length = lengths[0] if lengths else 0
    if lengths and not 3 <= max_length <= 8:
        errors.append(f"maximum segment length {max_length} outside 3..8")
    expected_n = _n_colors_for(max_length) if max_length else 0
    if lengths and len(by_color) != expected_n:
        errors.append(
            f"{len(by_color)} colors cannot fill all rings for max length {max_length}; "
            f"expected {expected_n}"
        )

    profile = _profile_name(lengths) if lengths else None
    if lengths and profile is None:
        errors.append(f"length tuple {lengths} is outside declared teaching profiles")

    colors = list(by_color)
    for i, left in enumerate(colors):
        for right in colors[i + 1 :]:
            if any(
                max(abs(r - rr), abs(c - cc)) <= 1
                for r, c in by_color[left]
                for rr, cc in by_color[right]
            ):
                errors.append(f"colors {left} and {right} touch")
                break

    nonpoint_orientations = {
        item["orientation"]
        for item in segment_info.values()
        if item["orientation"] != "p"
    }
    if nonpoint_orientations == {"h"}:
        orientation_mode = "horizontal_only"
    elif nonpoint_orientations == {"v"}:
        orientation_mode = "vertical_only"
    elif nonpoint_orientations == {"h", "v"}:
        orientation_mode = "mixed"
    else:
        orientation_mode = None
        if segment_info:
            errors.append("could not infer line_orientation")

    return {
        "grid_h": h,
        "grid_w": w,
        "n_colors": len(by_color),
        "max_length": max_length,
        "length_profile": profile,
        "line_orientation": orientation_mode,
        "segments": segment_info,
        "lengths": lengths,
    }, errors


def observe_overrides(grid) -> dict[str, int | str]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {axis: info[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    info, errors = _analyze(grid)
    requested = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if not errors and isinstance(requested, dict):
        for axis, expected in requested.items():
            if axis in AXES and info.get(axis) != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {info.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict linked manifold: valid separated segments and exact ring capacity."""
    return self_check(grid)


def canonical_profile_signature(grid) -> tuple[int, int, int]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return info["grid_h"], info["grid_w"], info["n_colors"]


def _ordered_colors(grid, key: Callable[[tuple[int, dict[str, Any]]], Any], reverse=False) -> list[int]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [color for color, _ in sorted(info["segments"].items(), key=key, reverse=reverse)]


def _ring_output(side: int, colors: list[int]) -> list[list[int]]:
    return [
        [colors[min(r, c, side - 1 - r, side - 1 - c)] for c in range(side)]
        for r in range(side)
    ]


def rule_mirror(grid) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    ordered = sorted(
        info["segments"],
        key=lambda color: info["segments"][color]["length"],
        reverse=True,
    )
    return _ring_output(info["max_length"], ordered)


def _first_cell(item: tuple[int, dict[str, Any]]) -> tuple[int, int]:
    return min(item[1]["cells"])


def _hypothesis_output(name: str, grid) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    segments = info["segments"]
    side = info["max_length"]
    items = list(segments.items())
    if name == "length_ascending":
        colors = [color for color, _ in sorted(items, key=lambda pair: pair[1]["length"])]
    elif name == "numeric_ascending":
        colors = sorted(segments)
    elif name == "numeric_descending":
        colors = sorted(segments, reverse=True)
    elif name == "row_major":
        colors = [color for color, _ in sorted(items, key=_first_cell)]
    elif name == "reverse_row_major":
        colors = [color for color, _ in sorted(items, key=_first_cell, reverse=True)]
    elif name == "horizontal_first":
        rank = {"h": 0, "p": 1, "v": 2}
        colors = [
            color
            for color, _ in sorted(
                items,
                key=lambda pair: (rank[pair[1]["orientation"]], pair[1]["cells"]),
            )
        ]
    elif name == "vertical_first":
        rank = {"v": 0, "p": 1, "h": 2}
        colors = [
            color
            for color, _ in sorted(
                items,
                key=lambda pair: (rank[pair[1]["orientation"]], pair[1]["cells"]),
            )
        ]
    elif name == "longest_fill":
        longest = max(segments, key=lambda color: segments[color]["length"])
        return [[longest for _ in range(side)] for _ in range(side)]
    else:
        raise KeyError(name)
    return _ring_output(side, colors)


_HYPOTHESES = (
    "length_ascending",
    "numeric_ascending",
    "numeric_descending",
    "row_major",
    "reverse_row_major",
    "horizontal_first",
    "vertical_first",
    "longest_fill",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a calibrated shortcut survives every demo."""
    reasons: list[str] = []
    for hypothesis in _HYPOTHESES:
        try:
            survives = all(
                _hypothesis_output(hypothesis, pair["input"]) == pair["output"]
                for pair in demos
            )
            query_differs = (
                _hypothesis_output(hypothesis, query["input"]) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"{hypothesis} audit failed: {type(exc).__name__}: {exc}")
            continue
        if survives and query_differs:
            reasons.append(f"shortcut {hypothesis} fits every demonstration")
    return reasons


def _facts(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    return info if not errors else {}


def _witness_n_colors(value: int):
    return lambda grid: _facts(grid).get("n_colors") == value


def _witness_orientation(value: str):
    return lambda grid: _facts(grid).get("line_orientation") == value


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "two_colors": _witness_n_colors(2),
    "three_colors": _witness_n_colors(3),
    "four_colors": _witness_n_colors(4),
    "odd_output_side": lambda grid: bool(_facts(grid).get("max_length", 0) % 2),
    "even_output_side": lambda grid: bool(_facts(grid).get("max_length", 0) % 2 == 0),
    "horizontal_only": _witness_orientation("horizontal_only"),
    "vertical_only": _witness_orientation("vertical_only"),
    "mixed_orientations": _witness_orientation("mixed"),
    "unit_segment": lambda grid: 1 in _facts(grid).get("lengths", ()),
    "nonconsecutive_lengths": lambda grid: _facts(grid).get("length_profile") != "consecutive",
}


def semantic_observables(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        return {"valid": False, "errors": errors}
    return {
        "valid": True,
        "output_side": info["max_length"],
        "ordered_lengths": list(info["lengths"]),
        "n_colors": info["n_colors"],
        "length_profile": info["length_profile"],
        "line_orientation": info["line_orientation"],
    }


def mutation_fixtures():
    """Minimal semantic impostors, including a negative recombination probe."""
    base = generate(
        9917,
        2,
        difficulty="medium",
        grid_h=24,
        grid_w=20,
        n_colors=4,
        max_length=8,
        length_profile="step2",
        line_orientation="mixed",
    )
    info, errors = _analyze(base)
    if errors:
        raise AssertionError(errors)
    ordered = sorted(
        info["segments"], key=lambda color: info["segments"][color]["length"], reverse=True
    )

    split_segment = deepcopy(base)
    long_color = ordered[0]
    long_cells = list(info["segments"][long_color]["cells"])
    middle = long_cells[len(long_cells) // 2]
    split_segment[middle[0]][middle[1]] = 0

    bent_segment = deepcopy(base)
    bend_color = ordered[1]
    bend_cells = list(info["segments"][bend_color]["cells"])
    endpoint = bend_cells[-1]
    bent_segment[endpoint[0]][endpoint[1]] = 0
    orientation = info["segments"][bend_color]["orientation"]
    anchor = bend_cells[-2]
    candidates = (
        [(anchor[0] - 1, anchor[1]), (anchor[0] + 1, anchor[1])]
        if orientation == "h"
        else [(anchor[0], anchor[1] - 1), (anchor[0], anchor[1] + 1)]
    )
    replacement = next(
        (cell for cell in candidates if 0 <= cell[0] < len(base) and 0 <= cell[1] < len(base[0]) and bent_segment[cell[0]][cell[1]] == 0),
        None,
    )
    if replacement is None:
        raise AssertionError("no bend fixture placement")
    bent_segment[replacement[0]][replacement[1]] = bend_color

    duplicate_lengths = deepcopy(base)
    second_color = ordered[1]
    second_cells = list(info["segments"][second_color]["cells"])
    target_length = info["segments"][ordered[2]]["length"]
    for r, c in second_cells[target_length:]:
        duplicate_lengths[r][c] = 0

    missing_ring_color = deepcopy(base)
    shortest_color = ordered[-1]
    for r, c in info["segments"][shortest_color]["cells"]:
        missing_ring_color[r][c] = 0

    unexplained_extra_color = deepcopy(base)
    empty = next(
        (cell for cell in ((0, 0), (0, len(base[0]) - 1), (len(base) - 1, 0)) if unexplained_extra_color[cell[0]][cell[1]] == 0),
        None,
    )
    if empty is None:
        raise AssertionError("no extra-color fixture placement")
    new_color = next(color for color in range(1, 10) if color not in info["segments"])
    unexplained_extra_color[empty[0]][empty[1]] = new_color

    # Negative recombination: replace a valid straight source with an L-shape,
    # a feature absent from every remaining scene component.
    absent_recombination = deepcopy(base)
    replace_color = ordered[-1]
    for r, c in info["segments"][replace_color]["cells"]:
        absent_recombination[r][c] = 0
    origin = next(
        (r, c)
        for r in range(1, len(base) - 2)
        for c in range(1, len(base[0]) - 2)
        if all(absent_recombination[r + dr][c + dc] == 0 for dr, dc in ((0, 0), (1, 0), (1, 1)))
    )
    for dr, dc in ((0, 0), (1, 0), (1, 1)):
        absent_recombination[origin[0] + dr][origin[1] + dc] = replace_color

    return [
        ("split_line_count_only", split_segment),
        ("bent_line_component_only", bent_segment),
        ("duplicate_lengths", duplicate_lengths),
        ("missing_center_ring_color", missing_ring_color),
        ("unexplained_extra_color", unexplained_extra_color),
        ("absent_l_shape_recombination", absent_recombination),
    ]
