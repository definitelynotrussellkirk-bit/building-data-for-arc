"""Generator for H125 — pack the object inventory by bounding-box height.

The first row is a three-color palette.  Rows below it contain three isolated,
single-color objects whose source colors are deliberately not a reliable answer.
The oracle crops each body object, sorts by bounding-box height descending (then
width descending for equal heights), recolors the sorted objects from the
palette left-to-right, and packs them horizontally with one zero column between
neighbors.

The scene profiles reproduce the three canonical color-relation lessons
(monochrome/disjoint, height-tie/partial-overlap, and
distinct-height/partial-overlap) and add two controlled anti-shortcut lessons.
The default morphology bank deliberately mixes canonical bbox/size signatures
with adversarial signatures that break cell-count sorting.  Generated placement
also scrambles row-major discovery order.  Those are distribution guarantees,
not structural validity requirements: ``self_check`` still accepts every
canonical input.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79b307b1e4da"
VERSION = "3.1.0"  # canonical-manifold follow-up: structural validation now
# accepts every canonical input, while generation separately enforces scrambled
# scan order and mixes canonical bbox/size signatures with anti-cell-count
# witnesses.  The 3.0.0 checker incorrectly treated curriculum-level shortcut
# prevention as a per-grid validity rule and therefore rejected all canonical
# inputs.
TASK_ID = "79b307b1e4da"
RULE_HASH = "2943fbde1fb4"

SUMMARY = (
    "Read the three nonzero colors in row 0 as an ordered palette. In the body, "
    "crop the three isolated same-color components, sort them by bbox height "
    "descending and then bbox width descending, recolor them with the palette "
    "in that order, and pack them horizontally with one zero column between."
)

INVARIANTS = [
    "row 0 is exactly a contiguous three-color palette followed by zeros",
    "the body has exactly three isolated 4-connected single-color objects",
    "bbox (height, width) sort keys are unique; one profile exercises the "
    "equal-height / wider-first tie branch",
    "body colors are nuisance information: the declared profiles include "
    "disjoint, partial-overlap, monochrome, mixed, and reordered-same-set cases",
    "default draws include canonical morphology signatures and separate "
    "witnesses where cell-count order disagrees with bbox-height order",
    "generated placement makes row-major discovery order disagree with the "
    "required bbox-height ordering, while canonical inputs remain valid",
]

SCENE_PROFILES = (
    "monochrome_disjoint",
    "tie_partial",
    "distinct_partial",
    "mixed_disjoint",
    "same_set_reordered",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped draw over the full 7..12 contract",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped draw over the full 9..14 contract",
        "valid": "9..14",
    },
    "scene_profile": {
        "type": "str",
        "default": "weighted canonical and anti-shortcut profile",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_N_OBJECTS = 3
_VALID_H = (7, 12)
_VALID_W = (9, 14)

# Every recipe is already in the oracle's required order: height descending,
# width descending for equal heights.  The three canonical signatures are
# preserved explicitly; the remaining recipes make cell-count sorting disagree
# with bbox sorting so the distribution does not teach a count-only shortcut.
_CANONICAL_MONO_RECIPE = ((3, 1, 3), (2, 2, 4), (1, 3, 3))
_CANONICAL_TIE_RECIPE = ((3, 2, 6), (3, 1, 3), (1, 2, 2))
_CANONICAL_DISTINCT_RECIPE = ((3, 2, 6), (2, 2, 3), (1, 1, 1))

_ANTI_DISTINCT_RECIPES = (
    ((3, 1, 3), (2, 3, 6), (1, 2, 2)),
    ((4, 1, 4), (2, 3, 6), (1, 2, 2)),
    ((3, 2, 4), (2, 3, 6), (1, 1, 1)),
    ((4, 2, 5), (2, 3, 6), (1, 1, 1)),
)
_ANTI_TIE_RECIPES = (
    ((3, 2, 4), (3, 1, 3), (2, 3, 6)),
    ((4, 2, 5), (4, 1, 4), (2, 3, 6)),
    ((3, 3, 5), (3, 1, 3), (2, 2, 4)),
)

_PROFILE_RECIPES = {
    # Repeating each canonical recipe gives the pooled default distribution a
    # stable canonical-morphology prior rather than a token one-off witness.
    "monochrome_disjoint": (
        _CANONICAL_MONO_RECIPE,
        _CANONICAL_MONO_RECIPE,
        *_ANTI_DISTINCT_RECIPES,
    ),
    "tie_partial": (
        _CANONICAL_TIE_RECIPE,
        _CANONICAL_TIE_RECIPE,
        *_ANTI_TIE_RECIPES,
    ),
    "distinct_partial": (
        _CANONICAL_DISTINCT_RECIPE,
        _CANONICAL_DISTINCT_RECIPE,
        *_ANTI_DISTINCT_RECIPES,
    ),
    "mixed_disjoint": _ANTI_DISTINCT_RECIPES,
    "same_set_reordered": _ANTI_DISTINCT_RECIPES,
}


def _components(body):
    """Same-color 4-connected components, matching the Racket `objects` rule."""
    h, w = len(body), len(body[0]) if body else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for r in range(h):
        for c in range(w):
            if body[r][c] == 0 or (r, c) in seen:
                continue
            color = body[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and body[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            result.append(
                {
                    "id": (r, c),
                    "color": color,
                    "cells": sorted(cells),
                    "size": len(cells),
                    "height": max(rows) - min(rows) + 1,
                    "width": max(cols) - min(cols) + 1,
                }
            )
    return result


def _has_cross_color_touch(body) -> bool:
    h, w = len(body), len(body[0])
    for r in range(h):
        for c in range(w):
            value = body[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = body[nr][nc]
                    if other != 0 and other != value:
                        return True
    return False


def _classify_profile(palette, items):
    if len(palette) != _N_OBJECTS or len(items) != _N_OBJECTS:
        return None
    ordered = sorted(items, key=lambda obj: (-obj["height"], -obj["width"]))
    tie = any(
        left["height"] == right["height"]
        and left["width"] != right["width"]
        for index, left in enumerate(items)
        for right in items[index + 1 :]
    )
    palette_set = set(palette)
    body_set = {obj["color"] for obj in items}
    overlap = palette_set & body_set
    sorted_body_colors = [obj["color"] for obj in ordered]

    if tie:
        if len(overlap) == 1 and palette_set != body_set:
            return "tie_partial"
        return None
    if len(body_set) == 1 and not overlap:
        return "monochrome_disjoint"
    if len(body_set) >= 2 and not overlap:
        return "mixed_disjoint"
    if len(overlap) == 1 and palette_set != body_set:
        return "distinct_partial"
    if (
        body_set == palette_set
        and len(body_set) == _N_OBJECTS
        and sorted_body_colors != list(palette)
    ):
        return "same_set_reordered"
    return None


def _analysis(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-grid input"], "profile": None, "objects": []}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged grid"], "profile": None, "objects": []}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(
            f"dims {h}x{w} outside {_VALID_H[0]}..{_VALID_H[1]} x "
            f"{_VALID_W[0]}..{_VALID_W[1]}"
        )

    palette = grid[0][:_N_OBJECTS]
    if any(value == 0 for value in palette) or any(grid[0][_N_OBJECTS:]):
        errors.append("row 0 must be exactly three nonzero palette cells followed by zeros")
    if len(set(palette)) != _N_OBJECTS:
        errors.append(f"palette colors must be distinct, got {palette}")

    body = grid[1:]
    items = _components(body)
    if len(items) != _N_OBJECTS:
        errors.append(f"expected exactly three body objects, found {len(items)}")
    if _has_cross_color_touch(body):
        errors.append("two differently colored body objects touch orthogonally")

    if len(items) == _N_OBJECTS:
        keys = [(obj["height"], obj["width"]) for obj in items]
        if len(set(keys)) != _N_OBJECTS:
            errors.append(f"ambiguous duplicate bbox sort keys: {keys}")
        if any(not (1 <= obj["height"] <= 4 and 1 <= obj["width"] <= 3) for obj in items):
            errors.append("body object bbox lies outside the calibrated 1..4 x 1..3 envelope")
        ordered = sorted(items, key=lambda obj: (-obj["height"], -obj["width"]))
        mismatches = sum(obj["color"] != color for obj, color in zip(ordered, palette))
        if mismatches < 2:
            errors.append("body colors reveal too much of the palette-to-output assignment")

    profile = _classify_profile(palette, items) if len(items) == _N_OBJECTS else None
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared canonical or anti-shortcut profile")
    return {
        "errors": errors,
        "profile": profile,
        "palette": list(palette),
        "objects": items,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or answer-leaking scenes while accepting canonical inputs.

    Scan-order and cell-count disambiguation are measured over the generated
    distribution, not treated as intrinsic validity requirements for a single
    lawful task instance.
    """
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact scene_profile from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["profile"]}


def _shape_with_size(rng, height: int, width: int, target_size: int):
    """Connected cells with an exact bbox and exact size."""
    if not (1 <= target_size <= height * width):
        raise ValueError("invalid target shape size")
    minimum = height + width - 1
    if target_size < minimum:
        raise ValueError("target shape cannot span the requested bbox")

    vertical = [(1, 0)] * (height - 1)
    horizontal = [(0, 1)] * (width - 1)
    steps = vertical + horizontal
    rng.shuffle(steps)
    row = col = 0
    cells = {(row, col)}
    for dr, dc in steps:
        row += dr
        col += dc
        cells.add((row, col))

    while len(cells) < target_size:
        candidates = {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _DIRS4
            if 0 <= r + dr < height and 0 <= c + dc < width
        } - cells
        if not candidates:
            raise AssertionError("could not grow calibrated connected shape")
        cells.add(rng.choice(sorted(candidates)))

    if rng.random() < 0.5:
        cells = {(height - 1 - r, c) for r, c in cells}
    if rng.random() < 0.5:
        cells = {(r, width - 1 - c) for r, c in cells}
    return sorted(cells)


def _body_colors(profile, palette, rng):
    complement = [color for color in range(1, 10) if color not in palette]
    if profile == "monochrome_disjoint":
        color = rng.choice(complement)
        return [color] * _N_OBJECTS
    if profile == "mixed_disjoint":
        first, second = rng.sample(complement, 2)
        return rng.choice(
            ([first, second, first], [first, second, second], [first, second, rng.choice([c for c in complement if c not in (first, second)])])
        )
    if profile in ("tie_partial", "distinct_partial"):
        shared = rng.choice(palette)
        other = rng.sample(complement, 2)
        colors = [shared, other[0], other[1]]
        rng.shuffle(colors)
        return colors
    if profile == "same_set_reordered":
        # A rotation is a derangement for three distinct palette colors.
        return [palette[1], palette[2], palette[0]]
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _can_place(body, cells, row0, col0):
    h, w = len(body), len(body[0])
    targets = {(row0 + r, col0 + c) for r, c in cells}
    for r, c in targets:
        if not (0 <= r < h and 0 <= c < w) or body[r][c] != 0:
            return False
        for dr, dc in _DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in targets and body[nr][nc] != 0:
                return False
    return True


def _place_objects(body_h, width, records, rng):
    body = full_grid(body_h, width, 0)
    order = list(range(len(records)))
    rng.shuffle(order)
    for index in order:
        record = records[index]
        cells = record["cells"]
        shape_h = max(r for r, _ in cells) + 1
        shape_w = max(c for _, c in cells) + 1
        candidates = [
            (row, col)
            for row in range(body_h - shape_h + 1)
            for col in range(width - shape_w + 1)
        ]
        rng.shuffle(candidates)
        placed = False
        for row0, col0 in candidates:
            if not _can_place(body, cells, row0, col0):
                continue
            for row, col in cells:
                body[row0 + row][col0 + col] = record["color"]
            placed = True
            break
        if not placed:
            return None
    return body


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", *_VALID_H)
    width = ctx.draw_int_diff("grid_w", *_VALID_W)
    profile = ctx.draw_choice(
        "scene_profile",
        [
            "monochrome_disjoint",
            "monochrome_disjoint",
            "tie_partial",
            "tie_partial",
            "distinct_partial",
            "distinct_partial",
            "mixed_disjoint",
            "same_set_reordered",
        ],
    )
    rng = ctx.draw_rng("layout")
    recipes = _PROFILE_RECIPES[profile]

    for _ in range(240):
        recipe = rng.choice(recipes)
        palette = rng.sample(range(1, 10), _N_OBJECTS)
        colors = _body_colors(profile, palette, rng)
        records = []
        for (shape_h, shape_w, size), color in zip(recipe, colors):
            records.append(
                {
                    "cells": _shape_with_size(rng, shape_h, shape_w, size),
                    "color": color,
                }
            )
        body = _place_objects(height - 1, width, records, rng)
        if body is None:
            continue
        grid = [palette + [0] * (width - _N_OBJECTS)] + body
        analysis = _analysis(grid)
        if analysis["errors"] or analysis["profile"] != profile:
            continue
        ordered = sorted(
            analysis["objects"],
            key=lambda item: (-item["height"], -item["width"]),
        )
        if [item["id"] for item in analysis["objects"]] == [
            item["id"] for item in ordered
        ]:
            # Placement is a nuisance factor.  Reject accidental row-major
            # answers so generated lessons force the bbox sort, while leaving
            # self_check broad enough to accept the canonical examples.
            continue
        return grid
    raise ValueError(
        f"could not realize profile={profile!r} on {height}x{width} after 240 attempts"
    )
