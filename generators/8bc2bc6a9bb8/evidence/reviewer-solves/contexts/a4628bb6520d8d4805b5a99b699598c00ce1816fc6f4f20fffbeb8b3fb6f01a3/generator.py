"""Generator for 8bc2bc6a9bb8 — sort, recolor, and pack shapes.

The first row is a sparse left-to-right palette.  Below a blank separator row,
color-8 components form a shape inventory.  The rule sorts the components by
area from largest to smallest, recolors them in palette order, bottom-aligns
them, and packs them left-to-right with one zero column between neighbors.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8bc2bc6a9bb8"
TASK_ID = "8bc2bc6a9bb8"
VERSION = "2.0.0"
RULE_HASH = "45fdce305a90"

SUMMARY = (
    "A sparse top-row palette recolors distinct-area color-8 components after "
    "sorting them largest-to-smallest; normalized shapes are bottom-aligned "
    "and packed with one blank column between them on the minimal canvas."
)

INVARIANTS = [
    "background is 0 and all cells use ARC colors 0..9",
    "the top row contains 2-4 distinct nonzero palette colors, none equal to 8",
    "palette entries are read left-to-right and separated by at least one zero",
    "row 1 is a blank separator between the palette and the shape inventory",
    "the body contains exactly one separated 4-connected color-8 component per palette entry",
    "component areas are distinct, include a singleton, and lie in 1..5",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled profile", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "scheduled profile", "valid": "10..16"},
    "n": {"type": "int", "default": "scheduled profile", "valid": "2..4"},
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

# Every four consecutive profiles contain canonical-size scenes, a four-shape
# scene, a two-shape scene, a nonnumeric palette, and a body-order conflict.
# That makes the four-demo lesson window falsify every declared competitor.
_PROFILES = (
    {
        "grid_h": 8,
        "grid_w": 12,
        "n": 3,
        "inventory": (4, 3, 1),
        "palette_mode": "ascending",
        "body_order": "conflict",
    },
    {
        "grid_h": 10,
        "grid_w": 16,
        "n": 4,
        "inventory": (5, 4, 2, 1),
        "palette_mode": "nonnumeric",
        "body_order": "conflict",
    },
    {
        "grid_h": 9,
        "grid_w": 14,
        "n": 3,
        "inventory": (4, 3, 1),
        "palette_mode": "nonnumeric",
        "body_order": "aligned",
    },
    {
        "grid_h": 7,
        "grid_w": 10,
        "n": 2,
        "inventory": (3, 1),
        "palette_mode": "ascending",
        "body_order": "conflict",
    },
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))

SHAPE_BANK = {
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    1: (((0, 0),),),
}

_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic semantic-profile id for coverage audits."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + offsets[difficulty]) % len(_PROFILES)


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    r0 = min(r for r, _ in materialized)
    c0 = min(c for _, c in materialized)
    return tuple(sorted((r - r0, c - c0) for r, c in materialized))


def _turn_once(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalized((c, -r) for r, c in cells)


def _orient(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    out = tuple(cells)
    for _ in range(turns % 4):
        out = _turn_once(out)
    return out


def _bbox_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    materialized = tuple(cells)
    return (
        max(r for r, _ in materialized) + 1,
        max(c for _, c in materialized) + 1,
    )


def _inventory_for(profile: dict[str, Any], n: int, h: int, w: int) -> tuple[int, ...]:
    if n == profile["n"]:
        inventory = tuple(profile["inventory"])
    elif n == 2:
        inventory = (4, 1) if profile["palette_mode"] == "nonnumeric" else (3, 1)
    elif n == 3:
        inventory = (5, 3, 1) if h >= 8 and w >= 12 else (4, 3, 1)
    else:
        inventory = (5, 4, 2, 1) if h >= 8 and w >= 12 else (4, 3, 2, 1)
    return inventory


def _sparse_palette_columns(rng, width: int, n: int) -> list[int]:
    candidates = [
        tuple(cols)
        for cols in __import__("itertools").combinations(range(width), n)
        if all(b - a >= 2 for a, b in zip(cols, cols[1:]))
    ]
    if not candidates:
        raise ValueError(f"cannot place {n} separated palette entries in width {width}")
    return list(rng.choice(candidates))


def _palette_colors(ctx, mode: str, n: int) -> list[int]:
    colors = sorted(ctx.draw_distinct_colors("palette", n=n, exclude={0, 8}))
    if mode == "ascending":
        return colors
    shift = 1 + (ctx.draw_rng("palette_order").randrange(max(1, n - 1)))
    rotated = colors[shift:] + colors[:shift]
    if rotated == colors:
        rotated = list(reversed(colors))
    return rotated


def _candidate_positions(
    cells: tuple[tuple[int, int], ...], h: int, w: int
) -> list[tuple[int, int]]:
    ph, pw = _bbox_size(cells)
    return [
        (r0, c0)
        for r0 in range(2, h - ph + 1)
        for c0 in range(0, w - pw + 1)
    ]


def _placement_guard(
    cells: tuple[tuple[int, int], ...], r0: int, c0: int, h: int, w: int
) -> set[tuple[int, int]]:
    occupied = {(r0 + dr, c0 + dc) for dr, dc in cells}
    return {
        (rr, cc)
        for r, c in occupied
        for rr in range(max(2, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _place_pieces(
    rng,
    pieces: list[tuple[int, tuple[tuple[int, int], ...]]],
    h: int,
    w: int,
    desired_order: str,
) -> list[tuple[int, tuple[tuple[int, int], ...], int, int]]:
    for _attempt in range(320):
        candidates: dict[int, list[tuple[int, int]]] = {}
        for index, (_size, cells) in enumerate(pieces):
            options = _candidate_positions(cells, h, w)
            rng.shuffle(options)
            candidates[index] = options

        placed: list[tuple[int, tuple[tuple[int, int], ...], int, int]] = []
        reserved: set[tuple[int, int]] = set()
        order = list(range(len(pieces)))
        rng.shuffle(order)

        def search(depth: int) -> bool:
            if depth == len(order):
                return True
            index = order[depth]
            size, cells = pieces[index]
            for r0, c0 in candidates[index]:
                guard = _placement_guard(cells, r0, c0, h, w)
                occupied = {(r0 + dr, c0 + dc) for dr, dc in cells}
                if not occupied.isdisjoint(reserved):
                    continue
                placed.append((size, cells, r0, c0))
                previous = set(reserved)
                reserved.update(guard)
                if search(depth + 1):
                    return True
                reserved.clear()
                reserved.update(previous)
                placed.pop()
            return False

        if not search(0):
            continue
        reading_sizes = [
            size
            for size, _cells, _r0, _c0 in sorted(
                placed, key=lambda item: (item[2], item[3])
            )
        ]
        target = sorted(reading_sizes, reverse=True)
        if desired_order == "aligned" and reading_sizes != target:
            continue
        if desired_order == "conflict" and reading_sizes == target:
            continue
        heights = [_bbox_size(cells)[0] for _size, cells, _r0, _c0 in placed]
        if len(set(heights)) < 2:
            continue
        return placed
    raise ValueError(
        f"could not place {len(pieces)} separated shapes with {desired_order} body order"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile_id = schedule_profile(seed, sample_index, difficulty)
    profile = _PROFILES[profile_id]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", profile["grid_h"], 7, 12)
    w = _draw_profile_int(ctx, overrides, "grid_w", profile["grid_w"], 10, 16)
    n = _draw_profile_int(ctx, overrides, "n", profile["n"], 2, 4)

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    palette = _palette_colors(ctx, profile["palette_mode"], n)
    for col, color in zip(_sparse_palette_columns(rng, w, n), palette):
        grid[0][col] = color

    inventory = _inventory_for(profile, n, h, w)
    pieces: list[tuple[int, tuple[tuple[int, int], ...]]] | None = None
    for _ in range(64):
        candidate = []
        for size in inventory:
            base = rng.choice(SHAPE_BANK[size])
            candidate.append((size, _orient(base, rng.randrange(4))))
        if len({_bbox_size(cells)[0] for _size, cells in candidate}) >= 2:
            pieces = candidate
            break
    if pieces is None:
        raise ValueError("could not choose shapes with visible bottom alignment")
    placements = _place_pieces(rng, pieces, h, w, profile["body_order"])
    for _size, cells, r0, c0 in placements:
        for dr, dc in cells:
            grid[r0 + dr][c0 + dc] = 8

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid inventory: " + "; ".join(errors))
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(2, h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _ORTHOGONALS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        2 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            r1 = max(rr for rr, _ in cells)
            c1 = max(cc for _, cc in cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "normalized": tuple(sorted((rr - r0, cc - c0) for rr, cc in cells)),
                    "size": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                }
            )
    return sorted(components, key=lambda obj: obj["bbox"])


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if not (7 <= h <= 12):
        errors.append(f"grid height {h} outside 7..12")
    if not (10 <= w <= 16):
        errors.append(f"grid width {w} outside 10..16")
    if any(not isinstance(v, int) or not (0 <= v <= 9) for row in grid for v in row):
        errors.append("all cells must be integer ARC colors 0..9")

    palette_cols = [c for c, value in enumerate(grid[0]) if value != 0]
    palette = [grid[0][c] for c in palette_cols]
    if not (2 <= len(palette) <= 4):
        errors.append(f"palette must contain 2..4 colors, found {len(palette)}")
    if any(color == 8 for color in palette):
        errors.append("palette may not contain placeholder color 8")
    if len(set(palette)) != len(palette):
        errors.append("palette colors must be distinct")
    if any(b - a < 2 for a, b in zip(palette_cols, palette_cols[1:])):
        errors.append("palette entries must be separated by at least one zero")
    if h > 1 and any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be the blank palette/body separator")
    body_bad = sorted({grid[r][c] for r in range(2, h) for c in range(w)} - {0, 8})
    if body_bad:
        errors.append(f"body contains colors other than 0 and 8: {body_bad}")

    components = _components(grid) if not body_bad else []
    if len(components) != len(palette):
        errors.append(
            f"body component count {len(components)} must equal palette count {len(palette)}"
        )
    sizes = [obj["size"] for obj in components]
    if len(set(sizes)) != len(sizes):
        errors.append("component areas must be distinct so size order is identifiable")
    if any(not (1 <= size <= 5) for size in sizes):
        errors.append(f"component areas must lie in 1..5, found {sizes}")
    if components and 1 not in sizes:
        errors.append("inventory must contain a singleton component")

    occupied = [set(obj["cells"]) for obj in components]
    for i, left in enumerate(occupied):
        for right in occupied[i + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left
                for r2, c2 in right
            ):
                errors.append("placeholder components must have a one-cell separation moat")
                break

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n": len(palette),
        "palette": tuple(palette),
        "palette_cols": tuple(palette_cols),
        "components": components,
        "reading_sizes": tuple(sizes),
        "sorted_sizes": tuple(sorted(sizes, reverse=True)),
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n": analysis["n"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _pack_inventory(
    grid,
    *,
    object_order: str = "size",
    palette_order: str = "left",
    alignment: str = "bottom",
    gap: int = 1,
    limit: int | None = None,
    canonical_size_rank: bool = False,
):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    items = list(analysis["components"])
    if object_order == "size":
        items.sort(key=lambda obj: (-obj["size"], obj["bbox"]))
    elif object_order != "reading":
        raise ValueError(f"unknown object order: {object_order}")
    if canonical_size_rank:
        rank = {4: 0, 3: 1, 1: 2}
        items.sort(key=lambda obj: (rank.get(obj["size"], 99), obj["bbox"]))

    palette = list(analysis["palette"])
    if palette_order == "numeric":
        palette.sort()
    elif palette_order != "left":
        raise ValueError(f"unknown palette order: {palette_order}")
    count = min(len(items), len(palette))
    if limit is not None:
        count = min(count, limit)
    items = items[:count]
    palette = palette[:count]
    max_h = max(obj["height"] for obj in items)
    total_w = sum(obj["width"] for obj in items) + gap * max(0, count - 1)
    out = full_grid(max_h, total_w, 0)
    x = 0
    for obj, color in zip(items, palette):
        top = max_h - obj["height"] if alignment == "bottom" else 0
        for dr, dc in obj["normalized"]:
            out[top + dr][x + dc] = color
        x += obj["width"] + gap
    return out


def rule_mirror(grid):
    return _pack_inventory(grid)


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    heights = [obj["height"] for obj in analysis["components"]]
    output = rule_mirror(grid)
    rank = {4: 0, 3: 1, 1: 2}
    canonical_lookup_sizes = tuple(
        obj["size"]
        for obj in sorted(
            analysis["components"],
            key=lambda obj: (rank.get(obj["size"], 99), obj["bbox"]),
        )
    )
    return {
        **observe_overrides(grid),
        "palette_nonnumeric": list(analysis["palette"]) != sorted(analysis["palette"]),
        "body_order_conflict": analysis["reading_sizes"] != analysis["sorted_sizes"],
        "bottom_alignment_visible": len(set(heights)) > 1,
        "canonical_inventory": analysis["sorted_sizes"] == (4, 3, 1),
        "noncanonical_inventory": analysis["sorted_sizes"] not in ((4, 3, 1),),
        "canonical_size_lookup_conflict": canonical_lookup_sizes != analysis["sorted_sizes"],
        "has_four_shapes": analysis["n"] == 4,
        "has_two_shapes": analysis["n"] == 2,
        "has_size_five": 5 in analysis["sorted_sizes"],
        "output_h": len(output),
        "output_w": len(output[0]),
        "palette_cols": analysis["palette_cols"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if (analysis["grid_h"], analysis["grid_w"]) not in ((8, 12), (9, 13), (9, 14)):
        reasons.append("canonical inputs use 8x12, 9x13, or 9x14 canvases")
    if analysis["n"] != 3:
        reasons.append("canonical inputs contain exactly three palette colors and shapes")
    if analysis["sorted_sizes"] != (4, 3, 1):
        reasons.append("canonical shape areas are 4, 3, and 1")
    return reasons


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


def _rival_body_reading_order(grid):
    return _pack_inventory(grid, object_order="reading")


def _rival_numeric_palette(grid):
    return _pack_inventory(grid, palette_order="numeric")


def _rival_top_align(grid):
    return _pack_inventory(grid, alignment="top")


def _rival_no_gap(grid):
    return _pack_inventory(grid, gap=0)


def _rival_always_three_shapes(grid):
    return _pack_inventory(grid, limit=3)


def _rival_canonical_size_lookup(grid):
    return _pack_inventory(grid, canonical_size_rank=True)


SEMANTIC_WITNESSES = {
    "palette_order_nonnumeric": lambda grid: _witness(grid, lambda o: o["palette_nonnumeric"]),
    "body_reading_order_conflict": lambda grid: _witness(grid, lambda o: o["body_order_conflict"]),
    "bottom_alignment_visible": lambda grid: _witness(grid, lambda o: o["bottom_alignment_visible"]),
    "one_column_gaps": lambda grid: _witness(grid, lambda o: o["n"] >= 2),
    "four_shape_inventory": lambda grid: _witness(grid, lambda o: o["has_four_shapes"]),
    "noncanonical_size_inventory": lambda grid: _witness(
        grid, lambda o: o["canonical_size_lookup_conflict"]
    ),
}

SEMANTIC_RIVALS = {
    "body_reading_order": _rival_body_reading_order,
    "numeric_palette": _rival_numeric_palette,
    "top_align": _rival_top_align,
    "no_gap": _rival_no_gap,
    "always_three_shapes": _rival_always_three_shapes,
    "canonical_size_lookup": _rival_canonical_size_lookup,
}

WITNESS_RIVALS = {
    "body_reading_order_conflict": ["body_reading_order"],
    "palette_order_nonnumeric": ["numeric_palette"],
    "bottom_alignment_visible": ["top_align"],
    "one_column_gaps": ["no_gap"],
    "four_shape_inventory": ["always_three_shapes"],
    "noncanonical_size_inventory": ["canonical_size_lookup"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "always_three_shapes": _rival_always_three_shapes,
    "canonical_size_lookup": _rival_canonical_size_lookup,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful shape inventory: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the sort/recolor/pack rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
