"""Generator for the anchor-relative offset stamping family.

A unique color-9 anchor and color-1 cells encode relative offsets.  Every
color-2 seed receives that offset pattern in color 8 on an otherwise blank
output.  The public axes are deliberately small and auditable: dimensions,
exact seed/offset counts, and a semantic texture.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71d5c4ac6ea3"
VERSION = "3.0.0"
TASK_ID = "71d5c4ac6ea3"
RULE_HASH = "ed3afc80127d"

SUMMARY = (
    "A unique 9 anchors an asymmetric constellation of 1s.  Translate the "
    "anchor-relative offsets to every 2 seed and paint those target cells 8 "
    "on a blank output.  wide_offsets increases the constellation span; "
    "edge_seeds makes a lawful stamped copy touch a border.  no_offsets and "
    "no_seeds are explicit empty-output degenerates."
)

INVARIANTS = [
    "exactly one color-9 anchor",
    "normal scenes have exactly 2..5 color-1 offset cells",
    "normal scenes have exactly 1..4 color-2 seed cells",
    "all declared numerical axes are exactly recoverable from the grid",
]

HELPFUL_TEXTURES = ("plain", "wide_offsets", "edge_seeds")
DEGENERATE_TEXTURES = ("no_offsets", "no_seeds")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 8..14", "valid": "8..14"},
    "n_seeds": {"type": "int", "default": "difficulty-skewed 1..4", "valid": "1..4"},
    "n_offsets": {"type": "int", "default": "difficulty-skewed 2..5", "valid": "2..5"},
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": "plain|wide_offsets|edge_seeds|no_offsets|no_seeds",
        "doc": (
            "plain: compact asymmetric constellation; wide_offsets: greater "
            "row/column span; edge_seeds: a complete translated copy touches "
            "the grid border; no_offsets/no_seeds: explicit empty-output cases"
        ),
    },
}

# The two degenerate textures intentionally remove one exact count axis.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "no_offsets", "n_offsets": None},
    {"texture": "no_seeds", "n_seeds": None},
]

# Prefixes are valid at every requested count.  Every prefix is asymmetric and
# contains no zero offset.  The wide families have a four-cell span while still
# fitting an 8x8 board with four seeds.
_COMPACT_PATTERNS = (
    ((0, 1), (1, 0), (1, 1), (-1, 1), (2, -1)),
    ((-1, 0), (0, 1), (1, -1), (1, 1), (-1, 2)),
    ((1, 0), (0, -1), (-1, -1), (1, 2), (-2, 1)),
    ((0, -1), (-1, 0), (1, 1), (-1, -2), (2, 0)),
)
_WIDE_PATTERNS = (
    ((-2, 0), (2, 0), (0, 2), (1, -1), (-1, -2)),
    ((0, -2), (0, 2), (2, 1), (-1, 1), (-2, -1)),
    ((-2, -1), (2, 1), (1, -2), (-1, 2), (0, 1)),
    ((-1, -2), (1, 2), (2, -1), (-2, 1), (1, 0)),
)


def _strict_override_types(overrides: dict) -> None:
    for name in ("grid_h", "grid_w", "n_seeds", "n_offsets"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    if "texture" in overrides and overrides["texture"] is not None and type(overrides["texture"]) is not str:
        raise TypeError("texture override must be a string")


def _points(grid, color: int) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _mirror(grid):
    """Python oracle for the pinned canonical rule (blank output + stamps)."""
    h, w = len(grid), len(grid[0])
    anchors = _points(grid, 9)
    if not anchors:
        raise ValueError("canonical rule requires a color-9 anchor")
    ar, ac = anchors[0]
    offsets = [(r - ar, c - ac) for r, c in _points(grid, 1)]
    out = full_grid(h, w, 0)
    for sr, sc in _points(grid, 2):
        for dr, dc in offsets:
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 8
    return out


def rule_mirror(grid):
    """Public alias used by focused parity probes."""
    return _mirror(grid)


def _pattern(texture: str, n_offsets: int, seed: int, sample_index: int) -> list[tuple[int, int]]:
    library = _WIDE_PATTERNS if texture == "wide_offsets" else _COMPACT_PATTERNS
    chosen = library[(seed * 7 + sample_index) % len(library)]
    return list(chosen[:n_offsets])


def _fits_at(point: tuple[int, int], offsets: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    r, c = point
    return all(0 <= r + dr < h and 0 <= c + dc < w for dr, dc in offsets)


def _touches_border(point: tuple[int, int], offsets: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    r, c = point
    return any(r + dr in (0, h - 1) or c + dc in (0, w - 1) for dr, dc in offsets)


def _spread_pick(candidates: list[tuple[int, int]], count: int, rng) -> list[tuple[int, int]]:
    """Pick distinct points while favoring spatial coverage."""
    if len(candidates) < count:
        raise ValueError(f"only {len(candidates)} lawful seed positions for requested {count}")
    remaining = list(candidates)
    rng.shuffle(remaining)
    selected = [remaining.pop()]
    while len(selected) < count:
        best_score = None
        best = []
        for point in remaining:
            score = min(abs(point[0] - r) + abs(point[1] - c) for r, c in selected)
            if best_score is None or score > best_score:
                best_score, best = score, [point]
            elif score == best_score:
                best.append(point)
        choice = best[rng.randrange(len(best))]
        selected.append(choice)
        remaining.remove(choice)
    return selected


def _normal_scene(h: int, w: int, n_offsets: int, n_seeds: int,
                  texture: str, seed: int, sample_index: int, rng):
    offsets = _pattern(texture, n_offsets, seed, sample_index)
    anchor_candidates = [
        (r, c) for r in range(h) for c in range(w)
        if _fits_at((r, c), offsets, h, w)
    ]
    if not anchor_candidates:
        raise ValueError("no lawful anchor position for selected offset pattern")
    # Consecutive sample indices advance through the lawful set.  This makes
    # anchor movement a generator invariant instead of a probabilistic hope.
    anchor_candidates.sort()
    anchor = anchor_candidates[(seed * 17 + sample_index * 5) % len(anchor_candidates)]
    legend = {anchor, *((anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets)}

    all_seed_candidates = [
        (r, c) for r in range(h) for c in range(w)
        if (r, c) not in legend and _fits_at((r, c), offsets, h, w)
    ]
    if texture == "edge_seeds":
        edge = [p for p in all_seed_candidates if _touches_border(p, offsets, h, w)]
        if not edge:
            raise ValueError("could not realize edge_seeds texture")
        rng.shuffle(edge)
        first = edge[0]
        rest = _spread_pick([p for p in all_seed_candidates if p != first], n_seeds - 1, rng) \
            if n_seeds > 1 else []
        seeds = [first, *rest]
    else:
        seeds = _spread_pick(all_seed_candidates, n_seeds, rng)

    grid = full_grid(h, w, 0)
    grid[anchor[0]][anchor[1]] = 9
    for dr, dc in offsets:
        grid[anchor[0] + dr][anchor[1] + dc] = 1
    for r, c in seeds:
        if grid[r][c] != 0:
            raise AssertionError("seed placement collided with legend")
        grid[r][c] = 2
    return grid


def _degenerate_scene(h: int, w: int, texture: str, n_offsets: int | None,
                      n_seeds: int | None, seed: int, sample_index: int, rng):
    grid = full_grid(h, w, 0)
    if texture == "no_offsets":
        # Anchor movement remains visible even in the empty-pattern case.
        anchor = ((seed + sample_index * 3) % h, (seed * 5 + sample_index) % w)
        grid[anchor[0]][anchor[1]] = 9
        candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) != anchor]
        for r, c in _spread_pick(candidates, int(n_seeds), rng):
            grid[r][c] = 2
        return grid
    if texture == "no_seeds":
        offsets = _pattern("plain", int(n_offsets), seed, sample_index)
        anchors = [(r, c) for r in range(h) for c in range(w)
                   if _fits_at((r, c), offsets, h, w)]
        anchors.sort()
        anchor = anchors[(seed * 17 + sample_index * 5) % len(anchors)]
        grid[anchor[0]][anchor[1]] = 9
        for dr, dc in offsets:
            grid[anchor[0] + dr][anchor[1] + dc] = 1
        return grid
    raise ValueError(f"unknown degenerate texture {texture}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    _strict_override_types(overrides)
    if overrides.get("texture") == "no_offsets" and overrides.get("n_offsets") is not None:
        raise ValueError("n_offsets is incompatible with texture=no_offsets")
    if overrides.get("texture") == "no_seeds" and overrides.get("n_seeds") is not None:
        raise ValueError("n_seeds is incompatible with texture=no_seeds")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    else:
        # Degenerates are opt-in; ordinary corpus draws always exercise the rule.
        texture = ctx.draw_choice("texture", ("plain", "plain", "wide_offsets", "edge_seeds"))
    h = ctx.draw_int_diff("grid_h", 8, 14)
    w = ctx.draw_int_diff("grid_w", 8, 14)
    n_offsets = None if texture == "no_offsets" else ctx.draw_int_diff("n_offsets", 2, 5)
    n_seeds = None if texture == "no_seeds" else ctx.draw_int_diff("n_seeds", 1, 4)
    rng = ctx.draw_rng("layout")

    if texture in DEGENERATE_TEXTURES:
        return _degenerate_scene(h, w, texture, n_offsets, n_seeds, seed, sample_index, rng)
    return _normal_scene(h, w, int(n_offsets), int(n_seeds), texture, seed, sample_index, rng)


def _meta_overrides(meta):
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid):
    """Recover every exact numerical public axis from a lawful grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("cannot observe an empty or ragged grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_offsets": sum(value == 1 for row in grid for value in row),
        "n_seeds": sum(value == 2 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    messages = []
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 14 and 8 <= w <= 14):
        messages.append(f"grid dimensions {h}x{w} outside declared 8..14 bounds")
    illegal = sorted({value for row in grid for value in row if value not in (0, 1, 2, 9)})
    if illegal:
        messages.append(f"unexpected input colors: {illegal}")
    anchors = _points(grid, 9)
    if len(anchors) != 1:
        messages.append(f"expected exactly 1 color-9 anchor, found {len(anchors)}")
    observed = observe_overrides(grid)
    requested = _meta_overrides(meta)
    texture = requested.get("texture")
    if texture == "no_offsets":
        if observed["n_offsets"] != 0:
            messages.append("no_offsets scene contains color-1 offsets")
        if observed["n_seeds"] < 1:
            messages.append("no_offsets scene has no seed")
    elif texture == "no_seeds":
        if observed["n_seeds"] != 0:
            messages.append("no_seeds scene contains color-2 seeds")
        if observed["n_offsets"] < 2:
            messages.append("no_seeds scene has no usable offset pattern")
    else:
        if not 2 <= observed["n_offsets"] <= 5:
            messages.append(f"expected 2..5 offsets, found {observed['n_offsets']}")
        if not 1 <= observed["n_seeds"] <= 4:
            messages.append(f"expected 1..4 seeds, found {observed['n_seeds']}")
    if len(anchors) == 1 and texture not in DEGENERATE_TEXTURES:
        ar, ac = anchors[0]
        offsets = [(r - ar, c - ac) for r, c in _points(grid, 1)]
        if any(not _fits_at(seed, offsets, h, w) for seed in _points(grid, 2)):
            messages.append("a normal seed clips its translated offset pattern")
        if texture == "wide_offsets":
            rows = [dr for dr, _ in offsets]
            cols = [dc for _, dc in offsets]
            if max(max(rows) - min(rows), max(cols) - min(cols)) < 4:
                messages.append("wide_offsets scene lacks a four-cell span")
        if texture == "edge_seeds" and not any(
            _touches_border(seed, offsets, h, w) for seed in _points(grid, 2)
        ):
            messages.append("edge_seeds scene has no border-touching translated copy")
    for name, value in requested.items():
        if name in observed and observed[name] != value:
            messages.append(f"override {name}={value!r} realized as {observed[name]!r}")
    return messages
