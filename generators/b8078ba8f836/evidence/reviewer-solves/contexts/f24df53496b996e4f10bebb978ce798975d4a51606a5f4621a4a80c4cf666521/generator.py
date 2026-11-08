"""Deterministic teaching sampler for ARC task b8078ba8f836.

Selected rule (the unchanged Racket program remains authoritative): for every
non-background color that occurs exactly twice, fill the inclusive straight
segment between the two cells when they share a row or a column.  Other colors,
including diagonal pairs and colors occurring three times, are unchanged.

The sampler deliberately alternates canonical-looking scenes with scenes that
contain both minimal negative controls.  This prevents a lesson from teaching
plausible shortcuts such as connecting any two equal colors or ignoring the
"exactly twice" predicate.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8078ba8f836"
TASK_ID = GENERATOR_ID
RULE_HASH = "48fc6f20bbde"
VERSION = "3.0.0"

SUMMARY = (
    "On a 0 background, each color occurring exactly twice is completed into "
    "an inclusive horizontal or vertical segment when its two cells are "
    "aligned. Every generated input has at least one pair of each orientation. "
    "A scheduled counterexample profile also includes an unaligned two-cell "
    "color and a three-cell color with one aligned subpair; both must remain "
    "unchanged, making the exact-count and alignment predicates learnable."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "counterexample")
MIN_STRICT_FRAC = 0.20
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or deterministic draw",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or deterministic draw",
        "valid": "8..14",
    },
    "n_horizontal_pairs": {"type": "int", "default": "1..2", "valid": "1..2"},
    "n_vertical_pairs": {"type": "int", "default": "1..2", "valid": "1..2"},
    "n_singletons": {"type": "int", "default": "0..2", "valid": "0..2"},
    "distractor_profile": {
        "type": "str",
        "default": "canonical,counterexample,counterexample schedule",
        "valid": "canonical|counterexample",
    },
}

INVARIANTS = [
    "background is 0 and all semantic groups use distinct nonzero colors",
    "at least one horizontal and one vertical exactly-two aligned pair",
    "eligible pair segments are disjoint and contain no distractor cells",
    "counterexample profile has one diagonal pair and one three-cell color",
    "all declared overrides are recoverable from the returned pixels",
]


# ---------------------------------------------------------------------------
# Small structural helpers
# ---------------------------------------------------------------------------


def _copy_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _segment(a: tuple[int, int], b: tuple[int, int]) -> set[tuple[int, int]] | None:
    r1, c1 = a
    r2, c2 = b
    if r1 == r2:
        return {(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
    if c1 == c2:
        return {(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)}
    return None


def _positions(grid: Any) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                result.setdefault(value, []).append((row, col))
    return result


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integers in 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    facts: dict[str, Any] = {
        "errors": errors,
        "grid_h": len(grid) if isinstance(grid, list) else 0,
        "grid_w": len(grid[0]) if isinstance(grid, list) and grid and isinstance(grid[0], list) else 0,
        "horizontal": [],
        "vertical": [],
        "diagonal_pairs": [],
        "triplets": [],
        "singletons": [],
    }
    if errors:
        return facts

    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    eligible: list[dict[str, Any]] = []
    for color, points in sorted(_positions(grid).items()):
        points = sorted(points)
        if len(points) == 1:
            facts["singletons"].append({"color": color, "points": points})
            continue
        if len(points) == 2:
            a, b = points
            cells = _segment(a, b)
            if cells is None:
                facts["diagonal_pairs"].append({"color": color, "points": points})
                continue
            distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if distance < 2:
                errors.append(f"color {color} aligned endpoints must leave at least one gap cell")
                continue
            entry = {"color": color, "points": points, "cells": cells}
            if a[0] == b[0]:
                facts["horizontal"].append(entry)
            else:
                facts["vertical"].append(entry)
            eligible.append(entry)
            continue
        if len(points) == 3:
            aligned: list[dict[str, Any]] = []
            for a, b in combinations(points, 2):
                cells = _segment(a, b)
                if cells is None:
                    continue
                distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
                if distance >= 2:
                    aligned.append({"points": [a, b], "cells": cells})
            if len(aligned) != 1:
                errors.append(
                    f"three-cell color {color} must contain exactly one non-adjacent aligned subpair"
                )
            else:
                entry = {"color": color, "points": points, **aligned[0]}
                facts["triplets"].append(entry)
            continue
        errors.append(f"color {color} occurs {len(points)} times; supported counts are 1, 2, or 3")

    if not facts["horizontal"]:
        errors.append("at least one horizontal exactly-two pair is required")
    if not facts["vertical"]:
        errors.append("at least one vertical exactly-two pair is required")
    if len(facts["horizontal"]) > 2:
        errors.append("at most two horizontal pairs are supported")
    if len(facts["vertical"]) > 2:
        errors.append("at most two vertical pairs are supported")
    if len(facts["singletons"]) > 2:
        errors.append("at most two singleton colors are supported")
    if len(facts["diagonal_pairs"]) > 1:
        errors.append("at most one unaligned two-cell color is supported")
    if len(facts["triplets"]) > 1:
        errors.append("at most one three-cell color is supported")
    if bool(facts["diagonal_pairs"]) != bool(facts["triplets"]):
        errors.append("counterexample profile requires both a diagonal pair and a three-cell color")

    for index, first in enumerate(eligible):
        for second in eligible[index + 1 :]:
            if first["cells"] & second["cells"]:
                errors.append("eligible pair segments must not cross or overlap")
        endpoints = set(first["points"])
        blockers = (first["cells"] & occupied) - endpoints
        if blockers:
            errors.append(
                f"eligible segment for color {first['color']} contains another colored cell"
            )

    for triplet in facts["triplets"]:
        pair_points = set(triplet["points"])
        blockers = (triplet["cells"] & occupied) - pair_points
        if blockers:
            errors.append(
                f"aligned subpair for three-cell color {triplet['color']} contains another colored cell"
            )

    facts["errors"] = errors
    return facts


# ---------------------------------------------------------------------------
# Public validation and observable-axis contract
# ---------------------------------------------------------------------------


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostic grammar errors without mutating or raising on bad grids."""
    errors = list(_analyze(grid)["errors"])
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unsupported difficulty {difficulty!r}")
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict) and not errors:
            observed = observe_overrides(grid)
            for name, value in requested.items():
                if name in AXES and value is not None and observed.get(name) != value:
                    errors.append(
                        f"override {name}={value!r} realized as {observed.get(name)!r}"
                    )
    return errors


def observe_overrides(grid) -> dict[str, object]:
    facts = _analyze(grid)
    diagonal = len(facts["diagonal_pairs"])
    triplets = len(facts["triplets"])
    if diagonal == 0 and triplets == 0:
        profile = "canonical"
    elif diagonal == 1 and triplets == 1:
        profile = "counterexample"
    else:
        profile = "ambiguous"
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_horizontal_pairs": len(facts["horizontal"]),
        "n_vertical_pairs": len(facts["vertical"]),
        "n_singletons": len(facts["singletons"]),
        "distractor_profile": profile,
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the narrow official profile while retaining all five inputs."""
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    strict_errors: list[str] = []
    if observed["grid_h"] not in {6, 7, 8}:
        strict_errors.append("canonical height must be 6, 7, or 8")
    if observed["grid_w"] not in {8, 9, 10, 11}:
        strict_errors.append("canonical width must be 8..11")
    if observed["n_horizontal_pairs"] not in {1, 2}:
        strict_errors.append("canonical profile has one or two horizontal pairs")
    if observed["n_vertical_pairs"] not in {1, 2}:
        strict_errors.append("canonical profile has one or two vertical pairs")
    if observed["n_singletons"] != 0:
        strict_errors.append("canonical profile has no singleton distractors")
    if observed["distractor_profile"] != "canonical":
        strict_errors.append("canonical profile has no count/alignment counterexamples")
    return strict_errors


# ---------------------------------------------------------------------------
# Intended rule mirror and plausible wrong rules
# ---------------------------------------------------------------------------


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains selected authority."""
    if _grid_errors(grid):
        raise ValueError("rule_mirror requires a rectangular 0..9 grid")
    out = _copy_grid(grid)
    for color, points in _positions(grid).items():
        if len(points) != 2:
            continue
        cells = _segment(points[0], points[1])
        if cells is None:
            continue
        for row, col in cells:
            out[row][col] = color
    return out


def _rival_connect_unaligned_l(grid) -> list[list[int]]:
    """Wrong rule: connect every exact-two color, using an L for diagonals."""
    if _grid_errors(grid):
        raise ValueError("rival requires a rectangular 0..9 grid")
    out = _copy_grid(grid)
    for color, points in sorted(_positions(grid).items()):
        if len(points) != 2:
            continue
        a, b = sorted(points)
        cells = _segment(a, b)
        if cells is not None:
            for row, col in cells:
                out[row][col] = color
            continue
        r1, c1 = a
        r2, c2 = b
        for col in range(min(c1, c2), max(c1, c2) + 1):
            out[r1][col] = color
        for row in range(min(r1, r2), max(r1, r2) + 1):
            out[row][c2] = color
    return out


def _rival_ignore_exact_count(grid) -> list[list[int]]:
    """Wrong rule: connect any aligned subpair even when its color occurs >2."""
    if _grid_errors(grid):
        raise ValueError("rival requires a rectangular 0..9 grid")
    out = _copy_grid(grid)
    for color, points in sorted(_positions(grid).items()):
        aligned = []
        for a, b in combinations(sorted(points), 2):
            cells = _segment(a, b)
            if cells is not None:
                aligned.append((a, b, cells))
        if not aligned:
            continue
        _, _, cells = aligned[0]
        for row, col in cells:
            out[row][col] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "connect_unaligned_L": _rival_connect_unaligned_l,
    "ignore_exact_count": _rival_ignore_exact_count,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_unaligned_pair(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and len(facts["diagonal_pairs"]) == 1


def _witness_triplet(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and len(facts["triplets"]) == 1


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "unaligned_pair_ignored": _witness_unaligned_pair,
    "triplet_ignored": _witness_triplet,
}
WITNESS_RIVALS = {
    "unaligned_pair_ignored": ["connect_unaligned_L"],
    "triplet_ignored": ["ignore_exact_count"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and at least one demo that refutes every rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input outside grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with selected rule")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input outside grammar: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected rule")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(item["input"]) == item["output"] for item in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


# ---------------------------------------------------------------------------
# Deterministic schedule and constructive sampler
# ---------------------------------------------------------------------------


def schedule_profile(seed, sample_index, difficulty=None):
    """Every three consecutive samples are canonical, counterexample, counterexample."""
    return "canonical" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "counterexample"


def _default_values(seed: int, sample_index: int, difficulty: str | None, profile: str):
    if profile == "canonical":
        return {
            "grid_h": 8,
            "grid_w": 8,
            "n_horizontal_pairs": 1,
            "n_vertical_pairs": 1,
            "n_singletons": 0,
        }
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|{difficulty}|defaults", VERSION)
    band_shift = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    return {
        "grid_h": 8 + ((sample_index + band_shift + rng.randrange(5)) % 5),
        "grid_w": 8 + ((2 * sample_index + band_shift + rng.randrange(7)) % 7),
        "n_horizontal_pairs": 1 + ((sample_index + band_shift + rng.randrange(2)) % 2),
        "n_vertical_pairs": 1 + ((sample_index // 2 + band_shift + rng.randrange(2)) % 2),
        "n_singletons": (sample_index + band_shift + rng.randrange(3)) % 3,
    }


def _segment_candidates(height: int, width: int, orientation: str):
    candidates = []
    if orientation == "h":
        for row in range(height):
            for left in range(width - 2):
                for right in range(left + 2, width):
                    a, b = (row, left), (row, right)
                    candidates.append((a, b, _segment(a, b)))
    else:
        for col in range(width):
            for top in range(height - 2):
                for bottom in range(top + 2, height):
                    a, b = (top, col), (bottom, col)
                    candidates.append((a, b, _segment(a, b)))
    return candidates


def _choose_segments(height: int, width: int, n_h: int, n_v: int, rng):
    candidates = {
        "h": _segment_candidates(height, width, "h"),
        "v": _segment_candidates(height, width, "v"),
    }
    rng.shuffle(candidates["h"])
    rng.shuffle(candidates["v"])

    def search(h_left, v_left, occupied, chosen):
        if h_left == 0 and v_left == 0:
            return list(chosen)
        orientation = "h" if h_left else "v"
        if h_left and v_left and len(chosen) % 2:
            orientation = "v"
        remaining = h_left if orientation == "h" else v_left
        if remaining == 0:
            orientation = "v" if orientation == "h" else "h"
        checked = 0
        for a, b, cells in candidates[orientation]:
            if cells & occupied:
                continue
            checked += 1
            chosen.append((orientation, a, b, cells))
            result = search(
                h_left - (orientation == "h"),
                v_left - (orientation == "v"),
                occupied | cells,
                chosen,
            )
            if result is not None:
                return result
            chosen.pop()
            if checked >= 160:
                break
        return None

    return search(n_h, n_v, set(), [])


def _free_cells(height: int, width: int, forbidden: set[tuple[int, int]]):
    return [(r, c) for r in range(height) for c in range(width) if (r, c) not in forbidden]


def _choose_diagonal_pair(height: int, width: int, forbidden, rng):
    free = _free_cells(height, width, forbidden)
    rng.shuffle(free)
    for a in free:
        candidates = [b for b in free if b != a and b[0] != a[0] and b[1] != a[1]]
        rng.shuffle(candidates)
        if candidates:
            return a, candidates[0]
    return None


def _choose_triplet(height: int, width: int, forbidden, rng):
    candidates = _segment_candidates(height, width, "h") + _segment_candidates(height, width, "v")
    rng.shuffle(candidates)
    for a, b, cells in candidates:
        if cells & forbidden:
            continue
        thirds = [
            point
            for point in _free_cells(height, width, forbidden | cells)
            if point[0] not in {a[0], b[0]} and point[1] not in {a[1], b[1]}
        ]
        rng.shuffle(thirds)
        if thirds:
            return a, b, thirds[0], cells
    return None


def _construct(
    height: int,
    width: int,
    n_h: int,
    n_v: int,
    n_singletons: int,
    profile: str,
    layout_rng,
    colors: list[int],
):
    for _attempt in range(64):
        selected = _choose_segments(height, width, n_h, n_v, layout_rng)
        if selected is None:
            continue
        grid = full_grid(height, width, 0)
        protected: set[tuple[int, int]] = set()
        used: set[tuple[int, int]] = set()
        color_index = 0
        for _, a, b, cells in selected:
            color = colors[color_index]
            color_index += 1
            grid[a[0]][a[1]] = color
            grid[b[0]][b[1]] = color
            used.update((a, b))
            protected |= cells

        if profile == "counterexample":
            diagonal = _choose_diagonal_pair(height, width, protected | used, layout_rng)
            if diagonal is None:
                continue
            color = colors[color_index]
            color_index += 1
            for row, col in diagonal:
                grid[row][col] = color
                used.add((row, col))

            triplet = _choose_triplet(height, width, protected | used, layout_rng)
            if triplet is None:
                continue
            a, b, third, triplet_cells = triplet
            color = colors[color_index]
            color_index += 1
            for row, col in (a, b, third):
                grid[row][col] = color
                used.add((row, col))
            protected |= triplet_cells

        free = _free_cells(height, width, protected | used)
        layout_rng.shuffle(free)
        if len(free) < n_singletons:
            continue
        for point in free[:n_singletons]:
            color = colors[color_index]
            color_index += 1
            row, col = point
            grid[row][col] = color
            used.add(point)
        return grid
    raise ValueError("could not construct an exact override instance after 64 attempts")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh, override-exact teaching input."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    requested_profile = overrides.get(
        "distractor_profile", schedule_profile(seed, sample_index, difficulty)
    )
    if requested_profile not in SCHEDULE_PROFILES:
        raise ValueError(f"unsupported distractor_profile {requested_profile!r}")
    defaults = _default_values(seed, sample_index, difficulty, requested_profile)
    effective = dict(overrides)
    effective.setdefault("distractor_profile", requested_profile)
    for name, value in defaults.items():
        effective.setdefault(name, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_strict("grid_h", 8, 12)
    width = ctx.draw_int_strict("grid_w", 8, 14)
    n_h = ctx.draw_int_strict("n_horizontal_pairs", 1, 2)
    n_v = ctx.draw_int_strict("n_vertical_pairs", 1, 2)
    n_singletons = ctx.draw_int_strict("n_singletons", 0, 2)
    profile = ctx.draw_choice("distractor_profile", SCHEDULE_PROFILES)

    group_count = n_h + n_v + n_singletons + (2 if profile == "counterexample" else 0)
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(range(1, 10), group_count)
    grid = _construct(
        height,
        width,
        n_h,
        n_v,
        n_singletons,
        profile,
        ctx.draw_rng("layout"),
        colors,
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_horizontal_pairs": n_h,
        "n_vertical_pairs": n_v,
        "n_singletons": n_singletons,
        "distractor_profile": profile,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise ValueError(f"override mismatch: expected {expected}, observed {observed}")
    return _copy_grid(grid)
