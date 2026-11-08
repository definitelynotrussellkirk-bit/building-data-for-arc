"""Generator for ARC task 077fc80653c6 — feature-triple lookup.

A full-height gray (5) divider splits the input into two panels.  The left
panel contains one red (2) reference object.  Right-panel objects are scanned
in top-left order; the first object whose

    (area, enclosed-hole count, reflection-symmetry class)

matches the red reference is cropped and recolored cyan (8).

The generated curriculum makes every coordinate of that triple load-bearing:
it includes different-shape feature twins, single-feature distractors, and a
decisive two-match branch.  Dimensions and palette sizes remain anchored to
the two canonical profiles.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "077fc80653c6"
TASK_ID = "077fc80653c6"
RULE_HASH = "5e186b36b85c"
VERSION = "4.0.0"
SUMMARY = (
    "Split at the full gray divider.  Compute (area, enclosed holes, "
    "reflection-symmetry class) for the red reference and each right-panel "
    "object; crop/recolor the first top-left candidate with the equal triple. "
    "The v4 curriculum uses feature twins, one-feature distractors, decisive "
    "ties, canonical 10x16/8-color and 11x16/7-color profiles, and exact "
    "observable override axes."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "10x16 or 11x16 input with exactly one full-height color-5 divider",
    "exactly one red reference component left of the divider",
    "at least three candidate components right of the divider",
    "at least one right candidate exactly matches the reference feature triple",
    "the first matching candidate in top-left order determines the output",
]

DEGENERATE_TEXTURES = ()
# No legacy ``texture=...`` axis: the curriculum branches are represented by
# the exact, observable target_family axis instead.
HELPFUL_TEXTURES = ()

SCENE_PROFILES = {
    "canonical_10x16_p8": (10, 16, 8),
    "canonical_11x16_p7": (11, 16, 7),
}
TARGET_TRIPLES = {
    "plain_asym": (7, 0, 0),
    "hole_asym": (8, 1, 0),
    "canonical_small": (5, 0, 0),
    "canonical_u": (7, 0, 2),
    "canonical_hole": (9, 1, 1),
}
_TRIPLE_TO_FAMILY = {value: key for key, value in TARGET_TRIPLES.items()}
_CANONICAL_TARGET_TRIPLES = {
    TARGET_TRIPLES["canonical_small"],
    TARGET_TRIPLES["canonical_u"],
    TARGET_TRIPLES["canonical_hole"],
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng canonical profile",
        "valid": "canonical_10x16_p8|canonical_11x16_p7",
        "doc": "Exact canonical (height, width, palette-size) profile.",
    },
    "target_family": {
        "type": "str",
        "default": "rng curriculum family",
        "valid": (
            "plain_asym|hole_asym|canonical_small|canonical_u|canonical_hole"
        ),
        "doc": "Exact reference feature-triple family, observable from the grid.",
    },
    "divider_col": {
        "type": "int",
        "default": "rng 6..8",
        "valid": "6..8",
        "doc": "Zero-based full-height gray divider column.",
    },
}

# Candidate colors include 8 intentionally: cyan in the input is a distractor,
# not an answer marker.  Together with {0,2,5}, the prefixes realize the exact
# canonical palette sizes 7 and 8.
_EXTRA_COLORS = {
    7: (1, 3, 4, 8),
    8: (1, 3, 4, 6, 8),
}

# Compact deterministic banks for rare triples.  Common asymmetric no-hole
# families are sampled by rejection from _grow(), which preserves high output
# geometry diversity.
_SHAPES: dict[tuple[int, int, int], tuple[tuple[tuple[int, int], ...], ...]] = {
    (7, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0), (3, 2)),
    ),
    (9, 1, 1): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3)),
    ),
    (8, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2), (3, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 1), (0, 2), (1, 1), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (3, 1)),
    ),
    (7, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (8, 1, 3): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 0, 1): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
    ),
    (9, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (5, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ),
    (6, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
}

# Per-family single-feature decoys.  A decoy triple differs from the target in
# exactly the named coordinate.
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
    "canonical_small": {
        "area": (6, 0, 0),
        "symmetry": (5, 0, 2),
    },
    "canonical_u": {
        "area": (6, 0, 2),
        "symmetry": (7, 0, 0),
    },
    "canonical_hole": {
        "holes": (9, 0, 1),
        "symmetry": (9, 1, 0),
    },
}

_LEFT_DISTRACTOR_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
)


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _grow(rng, size: int) -> tuple[tuple[int, int], ...]:
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _triple(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int]:
    cells = _norm(cells)
    shape = set(cells)
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1

    holes = 0
    seen: set[tuple[int, int]] = set()
    for row in range(height):
        for col in range(width):
            if (row, col) in shape or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            region: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                region.append(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
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

    row_sym = all((height - 1 - r, c) in shape for r, c in shape)
    col_sym = all((r, width - 1 - c) in shape for r, c in shape)
    symmetry_class = 3 if row_sym and col_sym else 1 if row_sym else 2 if col_sym else 0
    return (len(cells), holes, symmetry_class)


def _shape_with_triple(
    rng,
    want: tuple[int, int, int],
    *,
    avoid: set[tuple[tuple[int, int], ...]] | None = None,
    tries: int = 2000,
) -> tuple[tuple[int, int], ...] | None:
    avoid = avoid or set()
    bank = _SHAPES.get(want)
    if bank:
        choices = [shape for shape in bank if shape not in avoid]
        if choices:
            return rng.choice(choices)
    for _ in range(tries):
        shape = _grow(rng, want[0])
        if shape not in avoid and _triple(shape) == want:
            return shape
    return None


def _components(panel: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(panel), len(panel[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = panel[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and panel[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            normalized = _norm(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": normalized,
                    "triple": _triple(normalized),
                    "top_left": (min(r for r, _ in cells), min(c for _, c in cells)),
                }
            )
    return components


def _render_shape(shape: Iterable[tuple[int, int]], color: int = 8) -> list[list[int]]:
    shape = _norm(shape)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    out = full_grid(height, width, 0)
    for row, col in shape:
        out[row][col] = color
    return out


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
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid colors must be integers in 0..9")
        return result

    height = len(grid)
    palette = {value for row in grid for value in row}
    result.update({"height": height, "width": width, "palette": palette})
    if (height, width) not in {(10, 16), (11, 16)}:
        errors.append(f"expected canonical dimensions 10x16 or 11x16, got {height}x{width}")
    if len(palette) not in (7, 8):
        errors.append(f"expected canonical palette size 7 or 8, got {len(palette)}")

    divider_cols = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_cols) != 1:
        errors.append(f"expected exactly one full-height color-5 divider, found {len(divider_cols)}")
        return result
    divider = divider_cols[0]
    result["divider_col"] = divider
    if not 6 <= divider <= 8:
        errors.append(f"divider column must be in 6..8, got {divider}")
    if any(
        grid[row][col] == 5
        for row in range(height)
        for col in range(width)
        if col != divider
    ):
        errors.append("color 5 may appear only in the divider column")

    left = [row[:divider] for row in grid]
    right = [row[divider + 1 :] for row in grid]
    if not left or not left[0] or not right or not right[0]:
        errors.append("divider must leave two nonempty panels")
        return result

    left_components = _components(left)
    right_components = _components(right)
    red_components = [component for component in left_components if component["color"] == 2]
    if len(red_components) != 1:
        errors.append(f"expected exactly one red reference component on the left, found {len(red_components)}")
    if any(component["color"] == 2 for component in right_components):
        errors.append("red reference color 2 may not appear in the right panel")
    if not any(component["color"] != 2 for component in left_components):
        errors.append("left panel must contain at least one non-red distractor component")
    if len(right_components) < 3:
        errors.append(f"expected at least three right-panel candidates, found {len(right_components)}")
    if errors or len(red_components) != 1:
        result.update({"left_components": left_components, "candidates": right_components})
        return result

    reference = red_components[0]
    candidates = sorted(right_components, key=lambda component: component["top_left"])
    matches = [index for index, component in enumerate(candidates) if component["triple"] == reference["triple"]]
    if not matches:
        errors.append("no right-panel candidate matches the red reference feature triple")
        result.update({"reference": reference, "candidates": candidates, "matches": matches})
        return result

    selected_index = matches[0]
    selected = candidates[selected_index]
    output = _render_shape(selected["shape"])
    profile = next(
        (
            name
            for name, (profile_h, profile_w, profile_palette) in SCENE_PROFILES.items()
            if (height, width, len(palette)) == (profile_h, profile_w, profile_palette)
        ),
        None,
    )
    if profile is None:
        errors.append("grid does not realize a declared canonical scene profile")
    target_family = _TRIPLE_TO_FAMILY.get(reference["triple"])
    if target_family is None:
        errors.append(f"unsupported reference feature triple {reference['triple']}")

    result.update(
        {
            "left_components": left_components,
            "reference": reference,
            "candidates": candidates,
            "matches": matches,
            "selected_index": selected_index,
            "selected": selected,
            "output": output,
            "scene_profile": profile,
            "target_family": target_family,
        }
    )
    return result


def _can_place(
    panel: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    row0: int,
    col0: int,
) -> bool:
    cells = {(row0 + row, col0 + col) for row, col in shape}
    if any(panel[row][col] != 0 for row, col in cells):
        return False
    # Reused colors must remain separate 4-connected components.  Different
    # colors may touch, exactly as the canonical component parser permits.
    for row, col in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < len(panel)
                and 0 <= nc < len(panel[0])
                and (nr, nc) not in cells
                and panel[nr][nc] == color
            ):
                return False
    return True


def _place_one(panel, rng, shape, color) -> tuple[tuple[int, int], ...] | None:
    shape = _norm(shape)
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    height, width = len(panel), len(panel[0])
    if shape_h > height or shape_w > width:
        return None
    positions = [
        (row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]
    rng.shuffle(positions)
    for row0, col0 in positions:
        if not _can_place(panel, shape, color, row0, col0):
            continue
        cells = tuple(sorted((row0 + row, col0 + col) for row, col in shape))
        for row, col in cells:
            panel[row][col] = color
        return cells
    return None


def _choose_family_shapes(rng, family: str) -> tuple[tuple[tuple[int, int], ...], list[dict[str, Any]]] | None:
    want = TARGET_TRIPLES[family]
    reference = _shape_with_triple(rng, want)
    if reference is None:
        return None
    selected = _shape_with_triple(rng, want, avoid={reference})
    if selected is None:
        return None

    specs: list[dict[str, Any]] = []
    for role, decoy_triple in _DECOY_TRIPLES[family].items():
        shape = _shape_with_triple(rng, decoy_triple)
        if shape is None:
            return None
        specs.append({"role": role, "shape": shape, "triple": decoy_triple})
    specs.append({"role": "selected", "shape": selected, "triple": want})

    # hole_asym is the decisive first-vs-last match branch.  Its selected and
    # late candidates have different crops, so top-left order is load-bearing.
    if family == "hole_asym":
        late = _shape_with_triple(rng, want, avoid={reference, selected})
        if late is None:
            return None
        specs.append({"role": "late_match", "shape": late, "triple": want})
    return reference, specs


def _place_right(
    rng,
    height: int,
    width: int,
    specs: list[dict[str, Any]],
    extra_colors: tuple[int, ...],
) -> tuple[list[list[int]], list[dict[str, Any]]] | None:
    # Cyan is always assigned to a decoy, making input-color shortcutting wrong.
    decoys = [spec for spec in specs if spec["role"] not in {"selected", "late_match"}]
    role_colors: dict[str, int] = {}
    if decoys:
        role_colors[decoys[0]["role"]] = 8
    remaining = [color for color in extra_colors if color != 8]
    for spec in specs:
        role = spec["role"]
        if role in role_colors:
            continue
        role_colors[role] = remaining[len(role_colors) % len(remaining)]

    # Whole-board retries are cheap and make semantic order constraints exact.
    for _ in range(500):
        panel = full_grid(height, width, 0)
        placements: list[dict[str, Any]] = []
        order = list(specs)
        rng.shuffle(order)
        failed = False
        for spec in order:
            color = role_colors[spec["role"]]
            cells = _place_one(panel, rng, spec["shape"], color)
            if cells is None:
                failed = True
                break
            placements.append({**spec, "color": color, "cells": cells, "top_left": min(cells)})
        if failed:
            continue
        placements.sort(key=lambda item: item["top_left"])
        role_index = {item["role"]: index for index, item in enumerate(placements)}
        selected_index = role_index["selected"]
        decoy_roles = [spec["role"] for spec in specs if spec["role"] not in {"selected", "late_match"}]
        if any(role_index[role] >= selected_index for role in decoy_roles):
            continue
        if "late_match" in role_index and role_index["late_match"] <= selected_index:
            continue
        return panel, placements
    return None


def _place_left(
    rng,
    height: int,
    width: int,
    reference: tuple[tuple[int, int], ...],
    extra_colors: tuple[int, ...],
    colors_used_right: set[int],
) -> list[list[int]] | None:
    # Missing palette colors are materialized as proper small objects, not
    # isolated marker pixels.  At least one non-red object is always present.
    missing = [color for color in extra_colors if color not in colors_used_right]
    distractor_colors = missing or [extra_colors[-1]]
    for _ in range(200):
        panel = full_grid(height, width, 0)
        if _place_one(panel, rng, reference, 2) is None:
            continue
        ok = True
        for index, color in enumerate(distractor_colors):
            shape = _LEFT_DISTRACTOR_SHAPES[(index + rng.randrange(len(_LEFT_DISTRACTOR_SHAPES))) % len(_LEFT_DISTRACTOR_SHAPES)]
            if _place_one(panel, rng, shape, color) is None:
                ok = False
                break
        if ok:
            return panel
    return None


def _default_profile_choices(difficulty: str | None) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("canonical_10x16_p8", "canonical_10x16_p8", "canonical_11x16_p7")
    if difficulty == "hard":
        return ("canonical_11x16_p7", "canonical_11x16_p7", "canonical_10x16_p8")
    return tuple(SCENE_PROFILES)


def _default_family_choices(difficulty: str | None) -> tuple[str, ...]:
    if difficulty == "easy":
        return (
            "plain_asym", "plain_asym", "plain_asym",
            "canonical_small", "canonical_small", "canonical_u",
            "hole_asym", "canonical_hole",
        )
    if difficulty == "hard":
        return (
            "plain_asym", "plain_asym",
            "hole_asym", "hole_asym", "hole_asym", "hole_asym",
            "canonical_hole", "canonical_hole", "canonical_u",
        )
    return (
        "plain_asym", "plain_asym", "plain_asym", "plain_asym",
        "hole_asym", "hole_asym", "hole_asym",
        "canonical_small", "canonical_u", "canonical_hole",
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", tuple(SCENE_PROFILES))
    else:
        profile = ctx.draw_choice("scene_profile", _default_profile_choices(difficulty))

    # The first three standard lesson slots are deliberately complementary.
    lesson_families = ("plain_asym", "hole_asym", "canonical_hole")
    if overrides.get("target_family") is not None:
        family = ctx.draw_choice("target_family", tuple(TARGET_TRIPLES))
    elif 0 <= int(sample_index) < EXAMPLES_NEEDED:
        family = ctx.draw_choice("target_family", (lesson_families[int(sample_index)],))
    else:
        family = ctx.draw_choice("target_family", _default_family_choices(difficulty))

    if overrides.get("divider_col") is not None:
        divider = ctx.draw_int("divider_col", 6, 8)
    elif 0 <= int(sample_index) < EXAMPLES_NEEDED:
        divider = ctx.draw_int("divider_col", 7, 7)
    else:
        divider = ctx.draw_int("divider_col", 6, 8)

    height, width, palette_size = SCENE_PROFILES[profile]
    extra_colors = _EXTRA_COLORS[palette_size]
    rng = ctx.draw_rng("layout")

    for _ in range(160):
        chosen = _choose_family_shapes(rng, family)
        if chosen is None:
            continue
        reference, specs = chosen
        right_result = _place_right(rng, height, width - divider - 1, specs, extra_colors)
        if right_result is None:
            continue
        right, placements = right_result
        left = _place_left(
            rng,
            height,
            divider,
            reference,
            extra_colors,
            {item["color"] for item in placements},
        )
        if left is None:
            continue

        grid = full_grid(height, width, 0)
        for row in range(height):
            grid[row][:divider] = left[row]
            grid[row][divider] = 5
            grid[row][divider + 1 :] = right[row]

        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        if analysis["scene_profile"] != profile or analysis["target_family"] != family:
            continue
        if analysis["divider_col"] != divider:
            continue
        if analysis["selected"]["shape"] == analysis["reference"]["shape"]:
            continue
        if any(
            component["color"] == 8 and index != analysis["selected_index"]
            for index, component in enumerate(analysis["candidates"])
        ) is False:
            continue
        if family == "hole_asym":
            if len(analysis["matches"]) < 2:
                continue
            first_shape = analysis["candidates"][analysis["matches"][0]]["shape"]
            last_shape = analysis["candidates"][analysis["matches"][-1]]["shape"]
            if first_shape == last_shape:
                continue
        return grid
    raise ValueError("could not realize a lawful feature-triple lookup scene")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and semantic impostors, including no-match boards."""
    return list(_analyze(grid)["errors"])


def _mirror(grid):
    """Exact pure Python mirror of the canonical rule; Racket stays authority."""
    analysis = _analyze(grid)
    return None if analysis["errors"] else [row[:] for row in analysis["output"]]


def rule_mirror(grid):
    output = _mirror(grid)
    if output is None:
        raise ValueError("; ".join(self_check(grid)))
    return output


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "target_family": analysis["target_family"],
        "divider_col": analysis["divider_col"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "scene_profile": analysis["scene_profile"],
        "target_family": analysis["target_family"],
        "grid_shape": [analysis["height"], analysis["width"]],
        "palette_size": len(analysis["palette"]),
        "divider_col": analysis["divider_col"],
        "reference_triple": list(analysis["reference"]["triple"]),
        "reference_shape": [list(cell) for cell in analysis["reference"]["shape"]],
        "candidate_count": len(analysis["candidates"]),
        "candidate_triples": [list(component["triple"]) for component in analysis["candidates"]],
        "matching_indices": list(analysis["matches"]),
        "selected_index": analysis["selected_index"],
        "selected_differs_from_reference": analysis["selected"]["shape"] != analysis["reference"]["shape"],
        "input_contains_cyan": 8 in analysis["palette"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold: the canonical parser plus exact profiles."""
    return self_check(grid)


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _feature_decoy_precedes(grid, coordinate: int) -> bool:
    analysis = _lawful(grid)
    if analysis is None:
        return False
    want = analysis["reference"]["triple"]
    selected_index = analysis["selected_index"]
    return any(
        index < selected_index
        and component["triple"][coordinate] == want[coordinate]
        and component["triple"] != want
        for index, component in enumerate(analysis["candidates"])
    )


def _tie_decisive(grid) -> bool:
    analysis = _lawful(grid)
    if analysis is None or len(analysis["matches"]) < 2:
        return False
    first = analysis["candidates"][analysis["matches"][0]]["shape"]
    last = analysis["candidates"][analysis["matches"][-1]]["shape"]
    return first != last


SEMANTIC_WITNESSES = {
    "different_shape_equal_triple": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and analysis["selected"]["shape"] != analysis["reference"]["shape"]
    ),
    "area_only_decoy_precedes_match": lambda grid: _feature_decoy_precedes(grid, 0),
    "hole_only_decoy_precedes_match": lambda grid: _feature_decoy_precedes(grid, 1),
    "symmetry_only_decoy_precedes_match": lambda grid: _feature_decoy_precedes(grid, 2),
    "top_left_tie_decisive": _tie_decisive,
    "enclosed_hole_target": lambda grid: (
        (analysis := _lawful(grid)) is not None and analysis["reference"]["triple"][1] > 0
    ),
    "cyan_input_is_nonselected": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and any(
            component["color"] == 8 and index != analysis["selected_index"]
            for index, component in enumerate(analysis["candidates"])
        )
    ),
    "canonical_target_triple": lambda grid: (
        (analysis := _lawful(grid)) is not None
        and analysis["reference"]["triple"] in _CANONICAL_TARGET_TRIPLES
    ),
}


def _competitor_output(grid, mode: str):
    analysis = _lawful(grid)
    if analysis is None:
        return None
    reference = analysis["reference"]
    candidates = analysis["candidates"]
    if mode == "last_equal_triple":
        indices = [
            index for index, component in enumerate(candidates)
            if component["triple"] == reference["triple"]
        ]
        index = indices[-1] if indices else None
    elif mode == "first_object":
        index = 0 if candidates else None
    else:
        predicate = {
            "shape_identity": lambda component: component["shape"] == reference["shape"],
            "area_only": lambda component: component["triple"][0] == reference["triple"][0],
            "holes_only": lambda component: component["triple"][1] == reference["triple"][1],
            "symmetry_only": lambda component: component["triple"][2] == reference["triple"][2],
        }[mode]
        index = next((i for i, component in enumerate(candidates) if predicate(component)), None)
    return None if index is None else _render_shape(candidates[index]["shape"])


_COMPETING_RULES = (
    "shape_identity",
    "area_only",
    "holes_only",
    "symmetry_only",
    "first_object",
    "last_equal_triple",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a documented shortcut survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        truth = _mirror(demo.get("input"))
        if truth is None:
            reasons.append(f"demo {index}: input is not a lawful scene")
        elif demo.get("output") != truth:
            reasons.append(f"demo {index}: output disagrees with the feature-triple rule")
    query_truth = _mirror(query.get("input"))
    if query_truth is None:
        reasons.append("query: input is not a lawful scene")
    elif query.get("output") is not None and query.get("output") != query_truth:
        reasons.append("query: output disagrees with the feature-triple rule")
    if reasons or query_truth is None:
        return reasons

    for name in _COMPETING_RULES:
        survives = all(
            _competitor_output(demo["input"], name) == demo["output"]
            for demo in demos
        )
        if survives and _competitor_output(query["input"], name) != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo but predicts a different query"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted semantic impostors that self_check must reject."""
    base = generate(77123, 0, difficulty="medium")
    analysis = _analyze(base)

    broken_divider = [row[:] for row in base]
    broken_divider[0][analysis["divider_col"]] = 0

    missing_reference = [row[:] for row in base]
    for row, col in analysis["reference"]["cells"]:
        missing_reference[row][col] = 0

    no_match = [row[:] for row in base]
    selected = analysis["selected"]
    selected_row, selected_col = selected["cells"][0]
    no_match[selected_row][analysis["divider_col"] + 1 + selected_col] = 0

    red_on_right = [row[:] for row in base]
    candidate = analysis["candidates"][0]
    row, col = candidate["cells"][0]
    red_on_right[row][analysis["divider_col"] + 1 + col] = 2

    second_divider = [row[:] for row in base]
    other_col = 0 if analysis["divider_col"] != 0 else 1
    for row in range(len(second_divider)):
        second_divider[row][other_col] = 5

    return [
        ("broken_divider", broken_divider),
        ("missing_reference", missing_reference),
        ("no_match", no_match),
        ("red_on_right", red_on_right),
        ("second_divider", second_divider),
    ]
