"""Generator for ARC task 39fd645f21c6 — match a blue seed's feature triple.

The blue component defines ``(area, enclosed-hole count, reflection-symmetry
class)``.  Every other component with the same triple is recolored cyan (8).

Version 4 makes that full triple identifiable rather than teaching exact shape:
each generated scene contains different-shape feature twins plus three decoys
that differ from the seed in exactly one coordinate of the triple.  One lesson
example contains two matches, so a first-match-only rival is also falsified.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39fd645f21c6"
TASK_ID = "39fd645f21c6"
RULE_HASH = "36a57f0bfc36"
VERSION = "4.0.0"
SUMMARY = (
    "Find the unique blue component and compute its (area, enclosed holes, "
    "reflection-symmetry class). Recolor every non-blue component with the "
    "same triple cyan (8). The v4 curriculum uses different-shape feature "
    "twins, one-coordinate decoys for area/holes/symmetry, a two-match branch, "
    "and exact canonical 11x16, 12x16, and 12x17 five-color profiles."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and exactly one 4-connected component is blue (1)",
    "input dimensions and palette size match one of the three canonical profiles",
    "at least one non-blue component matches the blue seed's full feature triple",
    "at least one non-blue component does not match the seed",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCENE_PROFILES = {
    "canonical_11x16_p5": (11, 16, 5),
    "canonical_12x16_p5": (12, 16, 5),
    "canonical_12x17_p5": (12, 17, 5),
}

TARGET_TRIPLES = {
    "plain_asym": (7, 0, 0),
    "hole_asym": (8, 1, 0),
    "plain_both": (8, 0, 3),
    "plain_col": (9, 0, 2),
    "plain_row": (9, 0, 1),
}
_TRIPLE_TO_FAMILY = {triple: family for family, triple in TARGET_TRIPLES.items()}

_DECOY_TRIPLES: dict[str, dict[str, tuple[int, int, int]]] = {
    "plain_asym": {
        "area": (6, 0, 0),
        "holes": (7, 1, 0),
        "symmetry": (7, 0, 2),
    },
    "hole_asym": {
        "area": (7, 1, 0),
        "holes": (8, 0, 0),
        "symmetry": (8, 1, 3),
    },
    "plain_both": {
        "area": (7, 0, 3),
        "holes": (8, 1, 3),
        "symmetry": (8, 0, 0),
    },
    "plain_col": {
        "area": (8, 0, 2),
        "holes": (9, 1, 2),
        "symmetry": (9, 0, 0),
    },
    "plain_row": {
        "area": (8, 0, 1),
        "holes": (9, 1, 1),
        "symmetry": (9, 0, 0),
    },
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-step deterministic curriculum schedule",
        "valid": "canonical_11x16_p5|canonical_12x16_p5|canonical_12x17_p5",
        "doc": "Exact canonical (height, width, palette-size) profile.",
    },
    "target_family": {
        "type": "str",
        "default": "five-step deterministic curriculum schedule",
        "valid": "plain_asym|hole_asym|plain_both|plain_col|plain_row",
        "doc": "Seed feature-triple family, exactly observable from the grid.",
    },
    "match_count": {
        "type": "int",
        "default": "five-step deterministic curriculum schedule",
        "valid": "1..2",
        "doc": "Number of non-blue components sharing the seed's full triple.",
    },
}

# Every target bank has at least three translation-normalized shapes, allowing
# one seed plus two different-shape matches.  Decoy banks need only one shape.
# The tuples are intentionally static: generation is cheap, deterministic, and
# independent of any rejection sampler's accidental bias.
_SHAPES: dict[
    tuple[int, int, int], tuple[tuple[tuple[int, int], ...], ...]
] = {
    (7, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3)),
    ),
    (6, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2)),
    ),
    (7, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (7, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
    ),
    (8, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1)),
    ),
    (8, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 0)),
    ),
    (8, 1, 3): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (8, 0, 3): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
        ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 3)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2)),
    ),
    (7, 0, 3): (
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ),
    (9, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0), (3, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 0), (3, 1), (3, 2)),
    ),
    (8, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
    ),
    (9, 1, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
    ),
    (9, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
    (9, 0, 1): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
    ),
    (8, 0, 1): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 1, 1): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3)),
    ),
}

_PROFILE_SCHEDULE = tuple(SCENE_PROFILES)
_FAMILY_SCHEDULE = (
    "plain_asym",
    "hole_asym",
    "plain_row",
    "plain_both",
    "plain_col",
)
_MATCH_SCHEDULE = (1, 2)
_NONBLUE_PALETTES = (
    (2, 3, 4),
    (2, 4, 5),
    (3, 6, 7),
    (4, 7, 9),
    (2, 5, 9),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _triple(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int]:
    shape = set(_norm(cells))
    if not shape:
        raise ValueError("feature triple requires a nonempty component")
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1

    seen: set[tuple[int, int]] = set()
    holes = 0
    for row in range(height):
        for col in range(width):
            if (row, col) in shape or (row, col) in seen:
                continue
            region: list[tuple[int, int]] = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current = stack.pop()
                region.append(current)
                for dr, dc in _CARDINAL:
                    nxt = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in shape
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if all(
                0 < r < height - 1 and 0 < c < width - 1
                for r, c in region
            ):
                holes += 1

    row_symmetry = all((height - 1 - row, col) in shape for row, col in shape)
    col_symmetry = all((row, width - 1 - col) in shape for row, col in shape)
    symmetry_class = (
        3 if row_symmetry and col_symmetry
        else 1 if row_symmetry
        else 2 if col_symmetry
        else 0
    )
    return (len(shape), holes, symmetry_class)


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _CARDINAL:
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            shape = _norm(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": shape,
                    "triple": _triple(shape),
                    "top_left": (min(r for r, _ in cells), min(c for _, c in cells)),
                }
            )
    return sorted(components, key=lambda component: component["top_left"])


def _analyze(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"errors": []}
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        errors.append("grid must be a nonempty list of rows")
        return result
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        errors.append("grid must be nonempty and rectangular")
        return result
    if any(
        not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integers in 0..9")
        return result

    height = len(grid)
    palette = {value for row in grid for value in row}
    profile = next(
        (
            name
            for name, (profile_h, profile_w, profile_palette) in SCENE_PROFILES.items()
            if (height, width, len(palette)) == (profile_h, profile_w, profile_palette)
        ),
        None,
    )
    result.update(
        {
            "height": height,
            "width": width,
            "palette": palette,
            "scene_profile": profile,
        }
    )
    if profile is None:
        errors.append(
            "expected canonical profile 11x16/5, 12x16/5, or 12x17/5; "
            f"got {height}x{width} with palette size {len(palette)}"
        )
    if 0 not in palette:
        errors.append("background color 0 is required")

    components = _components(grid)
    blue = [component for component in components if component["color"] == 1]
    candidates = [component for component in components if component["color"] != 1]
    result.update({"components": components, "blue_components": blue, "candidates": candidates})
    if len(blue) != 1:
        errors.append(f"expected exactly one blue component, found {len(blue)}")
        return result
    if len(candidates) < 2:
        errors.append(f"expected at least two non-blue components, found {len(candidates)}")
        return result

    seed = blue[0]
    matches = [component for component in candidates if component["triple"] == seed["triple"]]
    mismatches = [component for component in candidates if component["triple"] != seed["triple"]]
    if not matches:
        errors.append("no non-blue component matches the blue seed's feature triple")
    if not mismatches:
        errors.append("at least one feature-triple mismatch is required")

    output = [row[:] for row in grid]
    for component in matches:
        for row, col in component["cells"]:
            output[row][col] = 8

    target_family = _TRIPLE_TO_FAMILY.get(seed["triple"])
    one_feature_decoys: dict[str, list[dict[str, Any]]] = {
        "area": [],
        "holes": [],
        "symmetry": [],
    }
    coordinate_names = ("area", "holes", "symmetry")
    for component in mismatches:
        differing = [
            index
            for index, (left, right) in enumerate(zip(component["triple"], seed["triple"]))
            if left != right
        ]
        if len(differing) == 1:
            one_feature_decoys[coordinate_names[differing[0]]].append(component)

    result.update(
        {
            "seed": seed,
            "matches": matches,
            "mismatches": mismatches,
            "output": output,
            "target_family": target_family,
            "one_feature_decoys": one_feature_decoys,
        }
    )
    return result


def _paint(grid: list[list[int]], row0: int, col0: int, shape, color: int) -> None:
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def _slot_origins(height: int, width: int, rng) -> list[tuple[int, int]]:
    top = rng.randint(0, 1)
    bottom = height - 4 - rng.randint(0, 1)
    left = rng.randint(0, 1)
    middle = 6 + (rng.randint(0, 1) if width == 17 else 0)
    right = width - 4
    slots = [
        (top, left),
        (top, middle),
        (top, right),
        (bottom, left),
        (bottom, middle),
        (bottom, right),
    ]
    rng.shuffle(slots)
    return slots


def _scheduled_axis(ctx, name: str, options, scheduled):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, tuple(options))
    # Use a singleton keyed draw so the deterministic curriculum schedule is
    # still visible to the exact-axis provenance checker.
    return ctx.draw_choice(name, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    index = int(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _scheduled_axis(
        ctx,
        "scene_profile",
        tuple(SCENE_PROFILES),
        _PROFILE_SCHEDULE[index % len(_PROFILE_SCHEDULE)],
    )
    family = _scheduled_axis(
        ctx,
        "target_family",
        tuple(TARGET_TRIPLES),
        _FAMILY_SCHEDULE[index % len(_FAMILY_SCHEDULE)],
    )
    if "match_count" in overrides and overrides["match_count"] is not None:
        match_count = ctx.draw_int("match_count", 1, 2)
    else:
        scheduled_match_count = _MATCH_SCHEDULE[index % len(_MATCH_SCHEDULE)]
        match_count = ctx.draw_int(
            "match_count", scheduled_match_count, scheduled_match_count
        )

    height, width, _palette_size = SCENE_PROFILES[profile]
    rng = ctx.draw_rng(f"layout_{difficulty or 'none'}")
    target = TARGET_TRIPLES[family]
    target_shapes = list(_SHAPES[target])
    selected = rng.sample(target_shapes, 1 + match_count)
    seed_shape = selected[0]
    match_shapes = selected[1:]

    palette = list(rng.choice(_NONBLUE_PALETTES))
    rng.shuffle(palette)
    decoy_specs = list(_DECOY_TRIPLES[family].items())
    rng.shuffle(decoy_specs)
    decoys = [
        (name, rng.choice(_SHAPES[triple]), color)
        for (name, triple), color in zip(decoy_specs, palette)
    ]
    match_colors = palette

    jobs: list[tuple[str, tuple[tuple[int, int], ...], int]] = [
        ("seed", seed_shape, 1)
    ]
    jobs.extend(
        ("match", shape, rng.choice(match_colors))
        for shape in match_shapes
    )
    jobs.extend((f"decoy_{name}", shape, color) for name, shape, color in decoys)
    rng.shuffle(jobs)

    grid = full_grid(height, width, 0)
    slots = _slot_origins(height, width, rng)
    for (_label, shape, color), (row0, col0) in zip(jobs, slots):
        _paint(grid, row0, col0, shape, color)

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("internal generation error: " + "; ".join(analysis["errors"]))
    if analysis["target_family"] != family:
        raise ValueError("internal generation error: target family drifted")
    if len(analysis["matches"]) != match_count:
        raise ValueError("internal generation error: match count drifted")
    if any(component["shape"] == analysis["seed"]["shape"] for component in analysis["matches"]):
        raise ValueError("internal generation error: exact-shape shortcut survived")
    if any(not analysis["one_feature_decoys"][name] for name in ("area", "holes", "symmetry")):
        raise ValueError("internal generation error: missing one-feature decoy")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and semantic impostors while accepting canon."""
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    """Pure Python mirror of the selected rule; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["target_family"] is None:
        raise ValueError(f"unsupported generated seed triple {analysis['seed']['triple']}")
    return {
        "scene_profile": analysis["scene_profile"],
        "target_family": analysis["target_family"],
        "match_count": len(analysis["matches"]),
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "target_family": analysis["target_family"],
        "grid_shape": [analysis["height"], analysis["width"]],
        "palette": sorted(analysis["palette"]),
        "seed_triple": list(analysis["seed"]["triple"]),
        "seed_shape": [list(cell) for cell in analysis["seed"]["shape"]],
        "candidate_triples": [list(component["triple"]) for component in analysis["candidates"]],
        "matching_count": len(analysis["matches"]),
        "matching_shapes": [
            [list(cell) for cell in component["shape"]]
            for component in analysis["matches"]
        ],
        "all_matching_shapes_differ_from_seed": all(
            component["shape"] != analysis["seed"]["shape"]
            for component in analysis["matches"]
        ),
        "single_feature_decoys": [
            name
            for name in ("area", "holes", "symmetry")
            if analysis["one_feature_decoys"][name]
        ],
        "input_contains_cyan": 8 in analysis["palette"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task manifold shared by canonical inputs and generated curriculum scenes."""
    return self_check(grid)


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _rival_output(grid, mode: str):
    analysis = _lawful(grid)
    if analysis is None:
        return None
    seed = analysis["seed"]
    candidates = analysis["candidates"]
    if mode == "first_equal_triple":
        selected = next(
            (component for component in candidates if component["triple"] == seed["triple"]),
            None,
        )
        chosen = [] if selected is None else [selected]
    else:
        predicates = {
            "exact_shape": lambda component: component["shape"] == seed["shape"],
            "area_only": lambda component: component["triple"][0] == seed["triple"][0],
            "holes_only": lambda component: component["triple"][1] == seed["triple"][1],
            "symmetry_only": lambda component: component["triple"][2] == seed["triple"][2],
            "area_holes": lambda component: component["triple"][:2] == seed["triple"][:2],
            "area_symmetry": lambda component: (
                component["triple"][0], component["triple"][2]
            ) == (seed["triple"][0], seed["triple"][2]),
            "holes_symmetry": lambda component: component["triple"][1:] == seed["triple"][1:],
        }
        predicate = predicates[mode]
        chosen = [component for component in candidates if predicate(component)]
    output = [row[:] for row in grid]
    for component in chosen:
        for row, col in component["cells"]:
            output[row][col] = 8
    return output


def _rival(name: str):
    return lambda grid: _rival_output(grid, name)


SEMANTIC_RIVALS = {
    name: _rival(name)
    for name in (
        "exact_shape",
        "area_only",
        "holes_only",
        "symmetry_only",
        "area_holes",
        "area_symmetry",
        "holes_symmetry",
        "first_equal_triple",
    )
}
CANONICAL_SHORTCUTS = {"exact_shape": SEMANTIC_RIVALS["exact_shape"]}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_single_feature_decoy(grid, name: str) -> bool:
    analysis = _lawful(grid)
    return analysis is not None and bool(analysis["one_feature_decoys"][name])


SEMANTIC_WITNESSES = {
    "different_shape_equal_triple": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and bool(analysis["matches"])
        and all(
            component["shape"] != analysis["seed"]["shape"]
            for component in analysis["matches"]
        )
    ),
    "area_single_feature_decoy": lambda grid: _has_single_feature_decoy(grid, "area"),
    "hole_single_feature_decoy": lambda grid: _has_single_feature_decoy(grid, "holes"),
    "symmetry_single_feature_decoy": lambda grid: _has_single_feature_decoy(grid, "symmetry"),
    "multiple_matches": lambda grid: (
        (analysis := _lawful(grid)) is not None and len(analysis["matches"]) > 1
    ),
    "enclosed_hole_seed": lambda grid: (
        (analysis := _lawful(grid)) is not None and analysis["seed"]["triple"][1] > 0
    ),
}

WITNESS_RIVALS = {
    "different_shape_equal_triple": ["exact_shape"],
    "area_single_feature_decoy": ["holes_only", "symmetry_only", "holes_symmetry"],
    "hole_single_feature_decoy": ["area_only", "symmetry_only", "area_symmetry"],
    "symmetry_single_feature_decoy": ["area_only", "holes_only", "area_holes"],
    "multiple_matches": ["first_equal_triple"],
    "enclosed_hole_seed": ["holes_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if any declared rival survives all demonstrations."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            truth = rule_mirror(demo.get("input"))
        except Exception as exc:
            reasons.append(f"demo {index}: invalid input ({type(exc).__name__}: {exc})")
            continue
        if demo.get("output") != truth:
            reasons.append(f"demo {index}: output disagrees with the feature-triple rule")
    try:
        query_truth = rule_mirror(query.get("input"))
    except Exception as exc:
        reasons.append(f"query: invalid input ({type(exc).__name__}: {exc})")
        query_truth = None
    if query_truth is not None and query.get("output") is not None and query.get("output") != query_truth:
        reasons.append("query: supplied output disagrees with the feature-triple rule")
    if reasons or query_truth is None:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but predicts a different query"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed or semantically incomplete scenes self_check rejects."""
    base = generate(77123, 0, difficulty="medium")
    analysis = _analyze(base)

    missing_seed = [row[:] for row in base]
    for row, col in analysis["seed"]["cells"]:
        missing_seed[row][col] = 0

    no_match = [row[:] for row in base]
    for component in analysis["matches"]:
        for row, col in component["cells"]:
            no_match[row][col] = 0

    extra_blue = [row[:] for row in base]
    occupied = {cell for component in analysis["components"] for cell in component["cells"]}
    isolated = next(
        (row, col)
        for row in range(1, len(base) - 1)
        for col in range(1, len(base[0]) - 1)
        if (row, col) not in occupied
        and all((row + dr, col + dc) not in occupied for dr, dc in _CARDINAL)
    )
    extra_blue[isolated[0]][isolated[1]] = 1

    extra_palette = [row[:] for row in base]
    absent = next(color for color in range(2, 10) if color not in analysis["palette"])
    extra_palette[isolated[0]][isolated[1]] = absent

    wrong_height = [row[:] for row in base[:-1]]
    ragged = [row[:] for row in base]
    ragged[0] = ragged[0][:-1]

    return [
        ("missing_seed", missing_seed),
        ("no_match", no_match),
        ("extra_blue_component", extra_blue),
        ("extra_palette_color", extra_palette),
        ("wrong_height", wrong_height),
        ("ragged", ragged),
    ]
