"""Generator for cc4d8d3dc442 — fill wall-bounded regions by key parity.

Color 5 is an impassable wall.  Every four-connected non-wall region is
repainted from its number of color-2 keys: zero stays 0, an odd positive
count becomes 8, and an even positive count becomes 7.  Generated instances
include local wall segments inside a regular outer lattice, matching the
canonical task's essential irregular-region decomposition.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc4d8d3dc442"
VERSION = "3.0.0"
TASK_ID = "cc4d8d3dc442"
RULE_HASH = "cdefe31a4be3"

SUMMARY = (
    "Color-5 walls bound four-connected regions. A regular 2-3 by 2-3 "
    "lattice is refined by 1-3 local wall segments, so some nominal cells "
    "split into smaller regions as in the canonical examples. Each region "
    "contains 0-4 color-2 keys. The whole non-wall region, including its "
    "keys, becomes 0 for zero keys, 8 for an odd count, or 7 for a positive "
    "even count. Profiles deliberately include 3- and 4-key regions to "
    "separate parity from the canonical-compatible one-versus-many shortcut."
)

INVARIANTS = [
    "inputs use only colors 0, 2, and 5",
    "full color-5 rows and columns form an outer regular chamber lattice",
    "one to three lattice cells contain one local straight color-5 separator",
    "each open four-connected region contains zero to four color-2 keys",
    "at least one region has zero keys and at least one has a positive count",
]

COUNT_PROFILES = ("mixed", "zero_even", "zero_odd", "high_parity")
PROFILE_COUNTS = {
    "mixed": (0, 1, 2),
    "zero_even": (0, 2, 4),
    "zero_odd": (0, 1, 3),
    "high_parity": (0, 3, 4),
}

AXES = {
    "ch_h": {
        "type": "int",
        "default": "difficulty-aware 3..6 with canonical-scale prior",
        "valid": "3..6",
    },
    "ch_w": {
        "type": "int",
        "default": "difficulty-aware 3..6 with canonical-scale prior",
        "valid": "3..6",
    },
    "n_rows": {
        "type": "int",
        "default": "difficulty-aware 2..3 with canonical-scale prior",
        "valid": "2..3",
    },
    "n_cols": {
        "type": "int",
        "default": "difficulty-aware 2..3 with canonical-scale prior",
        "valid": "2..3",
    },
    "split_count": {
        "type": "int",
        "default": "difficulty-aware 1..3 with canonical-scale prior",
        "valid": "1..3",
    },
    "count_profile": {
        "type": "str",
        "default": "rng mixed|zero_even|zero_odd|high_parity",
        "valid": "|".join(COUNT_PROFILES),
    },
}

# Every accepted generated grid is intended to lie on the strict task manifold.
MIN_STRICT_FRAC = 1.0


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if all(isinstance(row, str) for row in grid):
        if any(not row or any(ch not in "0123456789" for ch in row) for row in grid):
            return None, ["string rows must contain ARC color digits"]
        normalized = [[int(ch) for ch in row] for row in grid]
    elif all(isinstance(row, list) and row for row in grid):
        normalized = [list(row) for row in grid]
    else:
        return None, ["rows must be nonempty lists or digit strings"]
    width = len(normalized[0])
    if any(len(row) != width for row in normalized):
        return None, ["grid must be rectangular"]
    return normalized, []


def _open_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return all four-connected components whose cells are not color 5."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    regions: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            queue: deque[tuple[int, int]] = deque([(r, c)])
            seen.add((r, c))
            region: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                region.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            regions.append(region)
    return regions


def _wall_connected(grid: list[list[int]]) -> bool:
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    if not walls:
        return False
    start = next(iter(walls))
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nbr = (r + dr, c + dc)
            if nbr in walls and nbr not in seen:
                seen.add(nbr)
                queue.append(nbr)
    return seen == walls


def _uniform_cell_size(dividers: list[int]) -> int | None:
    if len(dividers) < 3:
        return None
    gaps = [b - a for a, b in zip(dividers, dividers[1:])]
    if len(set(gaps)) != 1:
        return None
    size = gaps[0] - 1
    return size if 3 <= size <= 6 else None


def _structure(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None:
        return None, errors
    g = normalized
    h, w = len(g), len(g[0])

    bad_values = sorted(
        {
            value
            for row in g
            for value in row
            if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 2, 5)
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"input colors must be only 0, 2, and 5; got {bad_values}")

    full_rows = [r for r in range(h) if all(value == 5 for value in g[r])]
    full_cols = [c for c in range(w) if all(g[r][c] == 5 for r in range(h))]
    if not full_rows or full_rows[0] != 0 or full_rows[-1] != h - 1:
        errors.append("top and bottom borders must be full color-5 walls")
    if not full_cols or full_cols[0] != 0 or full_cols[-1] != w - 1:
        errors.append("left and right borders must be full color-5 walls")

    ch_h = _uniform_cell_size(full_rows)
    ch_w = _uniform_cell_size(full_cols)
    if ch_h is None:
        errors.append("full wall rows must define 2-3 equal cells of height 3-6")
    if ch_w is None:
        errors.append("full wall columns must define 2-3 equal cells of width 3-6")

    n_rows = len(full_rows) - 1
    n_cols = len(full_cols) - 1
    if n_rows not in (2, 3):
        errors.append(f"expected 2-3 lattice rows, got {n_rows}")
    if n_cols not in (2, 3):
        errors.append(f"expected 2-3 lattice columns, got {n_cols}")

    split_count = 0
    if ch_h is not None and ch_w is not None and n_rows in (2, 3) and n_cols in (2, 3):
        for i in range(n_rows):
            r0, r1 = full_rows[i], full_rows[i + 1]
            for j in range(n_cols):
                c0, c1 = full_cols[j], full_cols[j + 1]
                interior = {
                    (r, c)
                    for r in range(r0 + 1, r1)
                    for c in range(c0 + 1, c1)
                }
                wall_cells = {(r, c) for r, c in interior if g[r][c] == 5}
                if not wall_cells:
                    continue
                horizontal = [
                    r
                    for r in range(r0 + 1, r1)
                    if all(g[r][c] == 5 for c in range(c0 + 1, c1))
                ]
                vertical = [
                    c
                    for c in range(c0 + 1, c1)
                    if all(g[r][c] == 5 for r in range(r0 + 1, r1))
                ]
                expected: set[tuple[int, int]] | None = None
                if len(horizontal) == 1 and not vertical:
                    expected = {(horizontal[0], c) for c in range(c0 + 1, c1)}
                elif len(vertical) == 1 and not horizontal:
                    expected = {(r, vertical[0]) for r in range(r0 + 1, r1)}
                if expected is None or wall_cells != expected:
                    errors.append(
                        f"lattice cell ({i},{j}) walls must be one complete local straight separator"
                    )
                else:
                    split_count += 1

    if not 1 <= split_count <= 3:
        errors.append(f"expected 1-3 local separators, got {split_count}")
    if not _wall_connected(g):
        errors.append("all color-5 wall cells must be four-connected")

    regions = _open_regions(g)
    if n_rows in (2, 3) and n_cols in (2, 3):
        expected_regions = n_rows * n_cols + split_count
        if len(regions) != expected_regions:
            errors.append(
                f"expected {expected_regions} open regions from the lattice and separators, got {len(regions)}"
            )
    counts = [sum(g[r][c] == 2 for r, c in region) for region in regions]
    if counts:
        if max(counts) > 4:
            errors.append(f"regions may contain at most four keys, got {counts}")
        if 0 not in counts:
            errors.append("at least one open region must have zero keys")
        if not any(count > 0 for count in counts):
            errors.append("at least one open region must contain a key")
    else:
        errors.append("grid has no open regions")

    info = {
        "grid": g,
        "ch_h": ch_h,
        "ch_w": ch_w,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "split_count": split_count,
        "regions": regions,
        "counts": counts,
    }
    return info, sorted(set(errors))


def _draw_lattice(
    ch_h: int,
    ch_w: int,
    n_rows: int,
    n_cols: int,
    split_count: int,
    rng: Any,
) -> list[list[int]]:
    h = n_rows * ch_h + n_rows + 1
    w = n_cols * ch_w + n_cols + 1
    grid = full_grid(h, w, 0)
    for i in range(n_rows + 1):
        r = i * (ch_h + 1)
        for c in range(w):
            grid[r][c] = 5
    for j in range(n_cols + 1):
        c = j * (ch_w + 1)
        for r in range(h):
            grid[r][c] = 5

    chambers = [(i, j) for i in range(n_rows) for j in range(n_cols)]
    chosen = rng.sample(chambers, split_count)
    candidate_sets: list[list[list[tuple[int, int]]]] = []
    for i, j in chosen:
        r0 = i * (ch_h + 1)
        r1 = r0 + ch_h + 1
        c0 = j * (ch_w + 1)
        c1 = c0 + ch_w + 1
        # A separator on the first/last interior line would merely thicken
        # an existing boundary and create no new open region. Keep at least
        # one open row/column on both sides.
        candidates = [
            [(r0 + offset, c) for c in range(c0, c1 + 1)]
            for offset in range(2, ch_h)
        ] + [
            [(r, c0 + offset) for r in range(r0, r1 + 1)]
            for offset in range(2, ch_w)
        ]
        rng.shuffle(candidates)
        candidate_sets.append(candidates)

    def place(index: int) -> bool:
        if index == len(candidate_sets):
            return True
        for cells in candidate_sets[index]:
            changed = [(r, c) for r, c in cells if grid[r][c] != 5]
            for r, c in changed:
                grid[r][c] = 5
            creates_full_row = any(
                all(value == 5 for value in grid[r]) for r, _ in changed
            )
            creates_full_col = any(
                all(grid[r][c] == 5 for r in range(h)) for _, c in changed
            )
            if not creates_full_row and not creates_full_col and place(index + 1):
                return True
            for r, c in changed:
                grid[r][c] = 0
        return False

    if not place(0):  # pragma: no cover - declared bounds are exhaustively tested
        raise ValueError(
            "could not place local separators without extending the base lattice"
        )
    return grid


def _profile_for_counts(counts: list[int]) -> str | None:
    values = set(counts)
    if {0, 3, 4} <= values and values <= {0, 3, 4}:
        return "high_parity"
    if {0, 2, 4} <= values and values <= {0, 2, 4}:
        return "zero_even"
    if {0, 1, 3} <= values and values <= {0, 1, 3}:
        return "zero_odd"
    if {0, 1, 2} <= values and values <= {0, 1, 2}:
        return "mixed"
    return None


def _place_profile_keys(
    grid: list[list[int]], profile: str, rng: Any
) -> None:
    regions = _open_regions(grid)
    allowed = PROFILE_COUNTS[profile]
    by_capacity = sorted(range(len(regions)), key=lambda index: len(regions[index]), reverse=True)
    counts: list[int | None] = [None] * len(regions)

    positives = sorted((value for value in allowed if value), reverse=True)
    for index, count in zip(by_capacity, positives):
        if len(regions[index]) < count:
            raise ValueError(f"region of size {len(regions[index])} cannot hold {count} keys")
        counts[index] = count

    zero_candidates = [index for index in reversed(by_capacity) if counts[index] is None]
    if not zero_candidates:  # pragma: no cover - minimum region count is five
        raise ValueError("count profile needs a zero-key region")
    counts[zero_candidates[0]] = 0

    for index, region in enumerate(regions):
        if counts[index] is None:
            feasible = [value for value in allowed if value <= len(region)]
            counts[index] = rng.choice(feasible)
        count = int(counts[index])
        for r, c in rng.sample(region, count):
            grid[r][c] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # The exact 11x11 canonical scale remains common in every band, while any
    # explicit override bypasses this prior and is honored against the full
    # declared domain.
    canonical_prior = (
        not overrides
        and ctx.draw_rng("canonical_profile_prior").random() < 0.45
    )
    if canonical_prior:
        ch_h = ctx.draw_int("ch_h", 4, 4)
        ch_w = ctx.draw_int("ch_w", 4, 4)
        n_rows = ctx.draw_int("n_rows", 2, 2)
        n_cols = ctx.draw_int("n_cols", 2, 2)
        split_count = ctx.draw_int("split_count", 1, 1)
    else:
        ch_h = ctx.draw_int_diff("ch_h", 3, 6)
        ch_w = ctx.draw_int_diff("ch_w", 3, 6)
        n_rows = ctx.draw_int_diff("n_rows", 2, 3)
        n_cols = ctx.draw_int_diff("n_cols", 2, 3)
        split_count = ctx.draw_int_diff("split_count", 1, 3)
    count_profile = str(ctx.draw_choice("count_profile", COUNT_PROFILES))

    layout_rng = ctx.draw_rng("local_separator_layout")
    grid = _draw_lattice(ch_h, ch_w, n_rows, n_cols, split_count, layout_rng)
    _place_profile_keys(grid, count_profile, ctx.draw_rng("key_layout"))
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a returned grid."""
    info, errors = _structure(grid)
    if info is None or errors:
        raise ValueError("cannot observe overrides from invalid grid: " + "; ".join(errors))
    profile = _profile_for_counts(info["counts"])
    if profile is None:
        raise ValueError(f"key counts do not identify a declared profile: {info['counts']}")
    return {
        "ch_h": int(info["ch_h"]),
        "ch_w": int(info["ch_w"]),
        "n_rows": int(info["n_rows"]),
        "n_cols": int(info["n_cols"]),
        "split_count": int(info["split_count"]),
        "count_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated/canonical input grammar."""
    _, errors = _structure(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Semantic-gate hook: [] exactly for lawful task-manifold inputs."""
    return self_check(grid)


def _fill_by_count(grid: Any, fill_for_count) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    out = [row[:] for row in normalized]
    for region in _open_regions(normalized):
        count = sum(normalized[r][c] == 2 for r, c in region)
        fill = int(fill_for_count(count))
        for r, c in region:
            out[r][c] = fill
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected Racket rule for tests and witnesses."""
    return _fill_by_count(
        grid,
        lambda count: 0 if count == 0 else (8 if count % 2 else 7),
    )


def _one_vs_many(grid) -> list[list[int]]:
    """Canonical-compatible rival: one key is cyan, two-or-more orange."""
    return _fill_by_count(
        grid,
        lambda count: 0 if count == 0 else (8 if count == 1 else 7),
    )


def _has_three_key_region(grid) -> bool:
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        return False
    return any(
        sum(normalized[r][c] == 2 for r, c in region) == 3
        for region in _open_regions(normalized)
    )


SEMANTIC_WITNESSES = {
    "three_key_region": _has_three_key_region,
}
SEMANTIC_RIVALS = {
    "one_vs_many": _one_vs_many,
}
WITNESS_RIVALS = {
    "three_key_region": ["one_vs_many"],
}
CANONICAL_SHORTCUTS = {
    "one_vs_many": _one_vs_many,
}
