"""Generator for ARC task ded97339 / content hash 7515881f2786.

Rule: cyan (8) anchors that share a row or column are joined through the
background.  For a line containing three or more anchors, only consecutive
anchors are direct pairs (the canonical Racket rule rejects an outer pair when
another cyan anchor lies strictly between it), but the union still fills each
consecutive gap.

The ordinary distribution uses four recoverable scene profiles. Every scene
contains both a horizontal and a vertical positive-length bridge. A seed-keyed
five-slot schedule contains every profile plus a second chain witness, so every
four-demo lesson (and every leave-one-out rotation of its five pairs) refutes
the canonical-fitting "exactly two anchors per line" shortcut without leaking a
fixed profile at any sample-index residue across seeds.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
from itertools import combinations, permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7515881f2786"
VERSION = "3.1.0"
TASK_ID = "7515881f2786"
RULE_HASH = "7327f2eb0272"

SUMMARY = (
    "A sparse 0-background grid contains 4-8 cyan (8) anchors. For every row "
    "and column, fill the zero cells between consecutive cyan anchors. Every "
    "ordinary draw includes at least one horizontal and one vertical bridge. "
    "Profiles distinguish a shared L-junction, disjoint row/column pairs, a "
    "multi-bridge rectangle, and a three-anchor chain whose outer pair is "
    "blocked by the middle anchor. A seed-keyed five-slot lesson schedule "
    "contains two chain witnesses; extra anchors are isolated distractors."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "rectangular 8..14 by 8..14 grid using only colors 0 and 8",
    "4..8 sparse cyan anchors",
    "at least one horizontal and one vertical anchor pair with a nonempty gap",
    "ordinary draws realize one recoverable profile: shared_l, disjoint, multi, or chain",
    "every five consecutive ordinary draws contain all profiles and two chain witnesses",
    "the Racket transformation changes at least one zero cell to cyan",
]

PROFILES = ("shared_l", "disjoint", "multi", "chain")
SCHEDULE_PROFILES = PROFILES
_SCHEDULE_TEMPLATE = ("shared_l", "disjoint", "multi", "chain", "chain")
_PROFILE_CYCLES = tuple(sorted(set(permutations(_SCHEDULE_TEMPLATE))))
# Keep the entire 8..14 support while making the canonical 10x10 profile common
# enough to be represented in every small per-band census.
_DIMENSION_CHOICES = tuple(range(8, 15)) + (10,) * 20

AXES = {
    "grid_h": {"type": "int", "default": "10-weighted full-domain", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "10-weighted full-domain", "valid": "8..14"},
    "n_dots": {"type": "int", "default": "difficulty-aware", "valid": "4..8"},
    "profile": {
        "type": "str",
        "default": "seed-keyed five-slot schedule",
        "valid": "shared_l|disjoint|multi|chain",
    },
}


def _separated_pairs(size: int) -> list[tuple[int, int]]:
    return [(a, b) for a, b in combinations(range(size), 2) if b - a >= 2]


def _separated_triples(size: int) -> list[tuple[int, int, int]]:
    return [
        (a, b, c)
        for a, b, c in combinations(range(size), 3)
        if b - a >= 2 and c - b >= 2
    ]


def _pick_pair(rng, size: int) -> tuple[int, int]:
    choices = _separated_pairs(size)
    if not choices:
        raise ValueError(f"dimension {size} cannot hold a positive-gap pair")
    return rng.choice(choices)


def _pick_triple(rng, size: int) -> tuple[int, int, int]:
    choices = _separated_triples(size)
    if not choices:
        raise ValueError(f"dimension {size} cannot hold a three-anchor chain")
    return rng.choice(choices)


def _pick_unused(rng, size: int, used: set[int], count: int) -> list[int]:
    available = [value for value in range(size) if value not in used]
    if len(available) < count:
        raise ValueError(
            f"dimension {size} has only {len(available)} unused coordinates; need {count}"
        )
    rng.shuffle(available)
    return available[:count]


def _validate_controls(seed, sample_index, difficulty, overrides: dict) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for axis in ("grid_h", "grid_w", "n_dots"):
        value = overrides.get(axis)
        if value is not None and type(value) is not int:
            raise TypeError(f"{axis} override must be an integer (not bool)")
    profile = overrides.get("profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("profile override must be a string")


def _profile_cycle(seed: int) -> tuple[str, ...]:
    digest = hashlib.sha256(
        f"{TASK_ID}|profile-schedule-v1|{seed}".encode()
    ).digest()
    index = int.from_bytes(digest[:8], "big") % len(_PROFILE_CYCLES)
    return _PROFILE_CYCLES[index]


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic ordinary-path profile for one draw."""
    _validate_controls(seed, sample_index, difficulty, {})
    cycle = _profile_cycle(seed)
    return cycle[sample_index % len(cycle)]


def _scheduled_profile(ctx, seed: int, sample_index: int, overrides: dict) -> str:
    if overrides.get("profile") is not None:
        return ctx.draw_choice("profile", PROFILES)
    scheduled = schedule_profile(seed, sample_index, ctx.difficulty)
    # A singleton keyed draw records the exact ordinary-path semantic request.
    return ctx.draw_choice("profile", (scheduled,))


def _base_points(profile: str, h: int, w: int, rng) -> set[tuple[int, int]]:
    if profile == "shared_l":
        r0, r1 = _pick_pair(rng, h)
        c0, c1 = _pick_pair(rng, w)
        return {(r0, c0), (r0, c1), (r1, c0)}

    if profile == "disjoint":
        vr0, vr1 = _pick_pair(rng, h)
        hr = rng.choice([r for r in range(h) if r not in {vr0, vr1}])
        hc0, hc1 = _pick_pair(rng, w)
        vc = rng.choice([c for c in range(w) if c not in {hc0, hc1}])
        return {(hr, hc0), (hr, hc1), (vr0, vc), (vr1, vc)}

    if profile == "multi":
        r0, r1 = _pick_pair(rng, h)
        c0, c1 = _pick_pair(rng, w)
        return {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}

    if profile == "chain":
        r0, r1 = _pick_pair(rng, h)
        c0, c1, c2 = _pick_triple(rng, w)
        return {(r0, c0), (r0, c1), (r0, c2), (r1, c1)}

    raise ValueError(f"unknown profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", _DIMENSION_CHOICES)
    w = ctx.draw_choice("grid_w", _DIMENSION_CHOICES)
    n_dots = ctx.draw_int_diff("n_dots", 4, 8)
    profile = _scheduled_profile(ctx, seed, sample_index, overrides)
    rng = ctx.draw_rng("layout")

    points = _base_points(profile, h, w, rng)
    if len(points) > n_dots:
        # All declared n_dots values are compatible with all profiles, so this
        # should remain unreachable unless a profile definition changes.
        raise ValueError(f"profile {profile!r} requires {len(points)} anchors")

    extra = n_dots - len(points)
    used_rows = {r for r, _ in points}
    used_cols = {c for _, c in points}
    extra_rows = _pick_unused(rng, h, used_rows, extra)
    extra_cols = _pick_unused(rng, w, used_cols, extra)
    rng.shuffle(extra_cols)
    points.update(zip(extra_rows, extra_cols))

    grid = full_grid(h, w, 0)
    for row, col in points:
        grid[row][col] = 8

    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_dots": n_dots,
        "profile": profile,
    }
    if {key: observed.get(key) for key in expected} != expected:
        raise RuntimeError(
            f"constructed scene does not realize keyed axes: expected {expected}, "
            f"observed {observed}"
        )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid scene: {errors}")
    return grid


def _anchor_groups(grid):
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    dots = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 8:
                dots.append((row, col))
                rows[row].append(col)
                cols[col].append(row)
    for values in rows.values():
        values.sort()
    for values in cols.values():
        values.sort()
    return dots, rows, cols


def _profile_from_groups(dots, rows, cols) -> str:
    row_lines = [row for row, values in rows.items() if len(values) >= 2]
    col_lines = [col for col, values in cols.items() if len(values) >= 2]
    if any(len(values) >= 3 for values in rows.values()) or any(
        len(values) >= 3 for values in cols.values()
    ):
        return "chain"
    if len(row_lines) >= 2 and len(col_lines) >= 2:
        return "multi"
    if len(row_lines) == 1 and len(col_lines) == 1:
        intersection = (row_lines[0], col_lines[0])
        return "shared_l" if intersection in set(dots) else "disjoint"
    return "other"


def rule_mirror(grid):
    """Diagnostic Python mirror; Racket remains the sole output authority."""
    output = [row[:] for row in grid]
    _, rows, cols = _anchor_groups(grid)
    for row, anchors in rows.items():
        for left, right in zip(anchors, anchors[1:]):
            for col in range(left + 1, right):
                if output[row][col] == 0:
                    output[row][col] = 8
    for col, anchors in cols.items():
        for top, bottom in zip(anchors, anchors[1:]):
            for row in range(top + 1, bottom):
                if output[row][col] == 0:
                    output[row][col] = 8
    return output


def semantic_observables(grid) -> dict[str, int | str]:
    dots, rows, cols = _anchor_groups(grid)
    row_lines = [values for values in rows.values() if len(values) >= 2]
    col_lines = [values for values in cols.values() if len(values) >= 2]
    participating = {
        point
        for point in dots
        if len(rows[point[0]]) >= 2 or len(cols[point[1]]) >= 2
    }
    output = rule_mirror(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_dots": len(dots),
        "profile": _profile_from_groups(dots, rows, cols),
        "row_lines": len(row_lines),
        "col_lines": len(col_lines),
        "row_segments": sum(len(values) - 1 for values in row_lines),
        "col_segments": sum(len(values) - 1 for values in col_lines),
        "chain_lines": sum(len(values) >= 3 for values in rows.values())
        + sum(len(values) >= 3 for values in cols.values()),
        "isolated_dots": len(dots) - len(participating),
        "changed_cells": sum(
            before != after
            for in_row, out_row in zip(grid, output)
            for before, after in zip(in_row, out_row)
        ),
    }


def observe_overrides(grid) -> dict[str, int | str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value not in (0, 8)
        for row in grid
        for value in row
    ):
        return {}
    dots, rows, cols = _anchor_groups(grid)
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_dots": len(dots),
        "profile": _profile_from_groups(dots, rows, cols),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    h = len(grid)
    if not (8 <= h <= 14 and 8 <= width <= 14):
        errors.append(f"expected dimensions in 8..14; got {h}x{width}")

    bad = Counter(
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or value not in (0, 8)
    )
    if bad:
        errors.append(f"expected only colors 0 and 8; found {dict(bad)}")
        return errors

    dots, rows, cols = _anchor_groups(grid)
    if not (4 <= len(dots) <= 8):
        errors.append(f"expected 4..8 cyan anchors; got {len(dots)}")

    row_positive = [
        (row, left, right)
        for row, anchors in rows.items()
        for left, right in zip(anchors, anchors[1:])
        if right - left >= 2
    ]
    col_positive = [
        (col, top, bottom)
        for col, anchors in cols.items()
        for top, bottom in zip(anchors, anchors[1:])
        if bottom - top >= 2
    ]
    if not row_positive:
        errors.append("expected a horizontal cyan pair with a nonempty zero gap")
    if not col_positive:
        errors.append("expected a vertical cyan pair with a nonempty zero gap")

    if not errors and rule_mirror(grid) == grid:
        errors.append("bridge rule is an identity on this scene")
    return errors


def strict_canonical_like(grid):
    """Return [] exactly for lawful instances in this generator's task manifold."""
    return self_check(grid)


def _rival_exactly_two_anchors_per_line(grid):
    """Plausible shortcut: ignore every row/column containing 3+ anchors."""
    output = [row[:] for row in grid]
    _, rows, cols = _anchor_groups(grid)
    for row, anchors in rows.items():
        if len(anchors) == 2:
            left, right = anchors
            for col in range(left + 1, right):
                if output[row][col] == 0:
                    output[row][col] = 8
    for col, anchors in cols.items():
        if len(anchors) == 2:
            top, bottom = anchors
            for row in range(top + 1, bottom):
                if output[row][col] == 0:
                    output[row][col] = 8
    return output


def _has_three_anchor_line(grid) -> bool:
    _, rows, cols = _anchor_groups(grid)
    return any(len(values) >= 3 for values in rows.values()) or any(
        len(values) >= 3 for values in cols.values()
    )


SEMANTIC_WITNESSES = {"three_anchor_line": _has_three_anchor_line}
SEMANTIC_RIVALS = {
    "exactly_two_anchors_per_line": _rival_exactly_two_anchors_per_line,
}
WITNESS_RIVALS = {
    "three_anchor_line": ["exactly_two_anchors_per_line"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labeled lesson when a declared plausible rival remains viable."""
    reasons: list[str] = []

    def expected_pair(pair, label: str):
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"{label} is not a labeled input/output pair")
            return None
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{label} is outside the task grammar: {errors}")
            return None
        expected = rule_mirror(pair["input"])
        if pair.get("output") is not None and pair.get("output") != expected:
            reasons.append(f"{label} output disagrees with the bridge rule")
        return expected

    demo_answers = [
        expected_pair(pair, f"demo {index}") for index, pair in enumerate(demos)
    ]
    query_answer = expected_pair(query, "query")
    if reasons or query_answer is None or any(answer is None for answer in demo_answers):
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == answer
            for pair, answer in zip(demos, demo_answers)
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
