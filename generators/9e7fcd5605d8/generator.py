"""Topology-rich input sampler for enclosed-hole component recoloring.

The unchanged Racket authority finds each same-colour 4-connected nonzero
component.  A component with at least one enclosed background region inside
its bounding box is recoloured 8; a component with no enclosed hole is
recoloured 4.  Open concavities are therefore hole-free even though they do
not fill their bounding boxes.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e7fcd5605d8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "02bf16fb38e9"

SUMMARY = (
    "A 0-background grid contains separated same-colour connected components. "
    "Recolour each component 8 exactly when it encloses one or more 4-connected "
    "background regions inside its bounding box; otherwise recolour it 4. Open "
    "U/C/L-shaped concavities have no enclosed hole and therefore become 4."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0 and input component colours exclude output labels 4 and 8",
    "2..4 separated same-colour 4-connected components are present",
    "at least one component encloses a hole and at least one component is hole-free",
    "every generated grid includes a hole-free open concavity that refutes bbox-nonfull shortcuts",
    "0 or 1 generated components contain two enclosed holes",
    "one or two distinct input colours are used and every requested colour appears",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-prior 10..11 or difficulty-aware 10..16",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-prior 10..11 or difficulty-aware 10..18",
        "valid": "10..18",
    },
    "n_hollow": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Number of components with at least one enclosed hole.",
    },
    "n_hole_free": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Number of components with no enclosed holes; one is an open concavity.",
    },
    "n_multi_hole": {
        "type": "int",
        "default": "scheduled 0 or 1",
        "valid": "0..1",
        "doc": "Number of hole-containing components with two enclosed regions.",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_one_hole",
    "canonical_two_holes",
    "broad_multicolour",
    "broad_multihole",
)

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = {(10, 10, 2), (10, 11, 2), (11, 11, 2)}
_LEGAL_INPUT_COLOURS = (1, 2, 3, 5, 6, 7, 9)

# Binary templates.  Dihedral transforms are applied after selection.
_ONE_HOLE_SHAPES = (
    ("111", "101", "111"),
    ("1111", "1001", "1001", "1111"),
    ("1110", "1010", "1111", "0010"),
)
_MULTI_HOLE_SHAPES = (
    ("1111", "1011", "1101", "1111"),
)
_OPEN_CONCAVE_SHAPES = (
    ("101", "101", "111"),  # U: the missing cells reach the bbox boundary.
    ("111", "100", "111"),  # C.
    ("100", "100", "111"),  # L.
    ("111", "010", "010"),  # T.
    ("110", "011", "001"),  # bent chain.
)
_FILLED_SHAPES = (
    ("11", "11"),
    ("111", "111"),
    ("11", "11", "11"),
    ("111", "111", "111"),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Four consecutive examples cover both canonical anchors and broad cases."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _has_override(ctx: Any, name: str) -> bool:
    return name in ctx.overrides and ctx.overrides[name] is not None


def _draw_axis_int(
    ctx: Any,
    name: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    bounds = valid_bounds if _has_override(ctx, name) else default_bounds
    return ctx.draw_int(name, *bounds)


def _rotate_cw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*shape[::-1])]


def _transform_template(template: tuple[str, ...], rng: Any) -> list[list[int]]:
    shape = [[int(value) for value in row] for row in template]
    if rng.choice((False, True)):
        shape = [row[::-1] for row in shape]
    for _ in range(rng.randrange(4)):
        shape = _rotate_cw(shape)
    return shape


def _slot_bounds(h: int, w: int) -> tuple[tuple[int, int, int, int], ...]:
    """Four disjoint slots with a full background row and column between them."""
    middle_r, middle_c = h // 2, w // 2
    return (
        (0, middle_r - 1, 0, middle_c - 1),
        (0, middle_r - 1, middle_c + 1, w - 1),
        (middle_r + 1, h - 1, 0, middle_c - 1),
        (middle_r + 1, h - 1, middle_c + 1, w - 1),
    )


def _paint_shape(
    grid: list[list[int]],
    shape: list[list[int]],
    colour: int,
    slot: tuple[int, int, int, int],
    rng: Any,
) -> None:
    r_lo, r_hi, c_lo, c_hi = slot
    sh, sw = len(shape), len(shape[0])
    if sh > r_hi - r_lo + 1 or sw > c_hi - c_lo + 1:
        raise ValueError("shape does not fit its constructive slot")
    r0 = rng.randint(r_lo, r_hi - sh + 1)
    c0 = rng.randint(c_lo, c_hi - sw + 1)
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if value:
                grid[r0 + r][c0 + c] = colour


def _profile_defaults(
    ctx: Any,
    profile: str,
    difficulty: Any,
) -> dict[str, tuple[int, int]]:
    if profile.startswith("canonical_"):
        h, w = ctx.draw_choice(
            "canonical_dimensions", ((10, 10), (10, 11), (11, 11))
        )
        if profile == "canonical_one_hole":
            counts = (1, 2, 0, 1)
        else:
            counts = (2, 1, 0, 1)
        return {
            "grid_h": (h, h),
            "grid_w": (w, w),
            "n_hollow": (counts[0], counts[0]),
            "n_hole_free": (counts[1], counts[1]),
            "n_multi_hole": (counts[2], counts[2]),
            "n_distinct_colors": (counts[3], counts[3]),
        }

    if difficulty == "easy":
        h_bounds, w_bounds = (10, 12), (10, 13)
    elif difficulty == "hard":
        h_bounds, w_bounds = (11, 16), (11, 18)
    else:
        h_bounds, w_bounds = (10, 14), (10, 16)

    counts = (1, 2, 0, 2) if profile == "broad_multicolour" else (2, 2, 1, 2)
    return {
        "grid_h": h_bounds,
        "grid_w": w_bounds,
        "n_hollow": (counts[0], counts[0]),
        "n_hole_free": (counts[1], counts[1]),
        "n_multi_hole": (counts[2], counts[2]),
        "n_distinct_colors": (counts[3], counts[3]),
    }


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(ctx, profile, difficulty)

    h = _draw_axis_int(ctx, "grid_h", defaults["grid_h"], (10, 16))
    w = _draw_axis_int(ctx, "grid_w", defaults["grid_w"], (10, 18))
    n_hollow = _draw_axis_int(ctx, "n_hollow", defaults["n_hollow"], (1, 2))
    n_hole_free = _draw_axis_int(
        ctx, "n_hole_free", defaults["n_hole_free"], (1, 2)
    )
    n_multi_hole = _draw_axis_int(
        ctx, "n_multi_hole", defaults["n_multi_hole"], (0, 1)
    )
    n_colours = _draw_axis_int(
        ctx, "n_distinct_colors", defaults["n_distinct_colors"], (1, 2)
    )

    total = n_hollow + n_hole_free
    if total > 4:
        raise ValueError("constructive layout supports at most four components")
    if n_multi_hole > n_hollow:
        raise ValueError("n_multi_hole cannot exceed n_hollow")
    if n_colours > total:
        raise ValueError("n_distinct_colors cannot exceed component count")

    shape_rng = ctx.draw_rng("shape_selection")
    specs: list[tuple[str, list[list[int]]]] = []
    for index in range(n_hollow):
        bank = _MULTI_HOLE_SHAPES if index < n_multi_hole else _ONE_HOLE_SHAPES
        specs.append(("hole", _transform_template(shape_rng.choice(bank), shape_rng)))

    # Every generated input has at least one topology counterexample: a
    # bbox-nonfull component whose missing cells remain connected to the rim.
    specs.append(
        ("open", _transform_template(shape_rng.choice(_OPEN_CONCAVE_SHAPES), shape_rng))
    )
    for _ in range(n_hole_free - 1):
        specs.append(
            ("filled", _transform_template(shape_rng.choice(_FILLED_SHAPES), shape_rng))
        )
    shape_rng.shuffle(specs)

    palette_rng = ctx.draw_rng("input_palette")
    palette = palette_rng.sample(list(_LEGAL_INPUT_COLOURS), n_colours)
    colours = [palette[index % n_colours] for index in range(total)]
    palette_rng.shuffle(colours)

    layout_rng = ctx.draw_rng("layout")
    slots = list(_slot_bounds(h, w))
    chosen_slots = layout_rng.sample(slots, total)
    grid = full_grid(h, w, 0)
    for (_, shape), colour, slot in zip(specs, colours, chosen_slots):
        _paint_shape(grid, shape, colour, slot, layout_rng)

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"constructive generator emitted invalid grid: {findings}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_hollow": n_hollow,
        "n_hole_free": n_hole_free,
        "n_multi_hole": n_multi_hole,
        "n_distinct_colors": n_colours,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes disagree: expected {expected}, observed {observed}")
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _same_colour_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            colour = grid[r0][c0]
            if colour == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _DIRS4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            cell_set = frozenset(cells)
            components.append(
                {
                    "colour": colour,
                    "cells": tuple(sorted(cells)),
                    "cell_set": cell_set,
                    "bbox": (r1, c1, r2, c2),
                    "holes": _hole_count(cell_set, (r1, c1, r2, c2)),
                }
            )
    return components


def _hole_count(
    cells: frozenset[tuple[int, int]],
    bbox: tuple[int, int, int, int],
) -> int:
    r1, c1, r2, c2 = bbox
    unseen = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if (r, c) not in cells
    }
    holes = 0
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        touches_rim = start[0] in (r1, r2) or start[1] in (c1, c2)
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRS4:
                point = (r + dr, c + dc)
                if point not in unseen:
                    continue
                unseen.remove(point)
                queue.append(point)
                if point[0] in (r1, r2) or point[1] in (c1, c2):
                    touches_rim = True
        holes += not touches_rim
    return holes


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    shape = _grid_shape(grid)
    if shape is None:
        return {}, ["grid must be a non-empty rectangular list of non-empty rows"]
    h, w = shape
    errors: list[str] = []
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"grid_h": h, "grid_w": w}, ["grid values must be integer ARC colours 0..9"]
    colours = {value for row in grid for value in row if value != 0}
    components = _same_colour_components(grid)
    holey = [component for component in components if component["holes"] > 0]
    hole_free = [component for component in components if component["holes"] == 0]
    open_concave = []
    for component in hole_free:
        r1, c1, r2, c2 = component["bbox"]
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if len(component["cells"]) < area:
            open_concave.append(component)
    info = {
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "colours": colours,
        "n_hollow": len(holey),
        "n_hole_free": len(hole_free),
        "n_multi_hole": sum(component["holes"] >= 2 for component in holey),
        "n_distinct_colors": len(colours),
        "open_concavities": open_concave,
    }
    return info, errors


def _component_hole_counts(grid: Any) -> list[int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [component["holes"] for component in info["components"]]


def observe_overrides(grid: Any) -> dict[str, int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n_hollow": info["n_hollow"],
        "n_hole_free": info["n_hole_free"],
        "n_multi_hole": info["n_multi_hole"],
        "n_distinct_colors": info["n_distinct_colors"],
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    info, errors = _analyse(grid)
    if errors:
        return errors
    if not 10 <= info["grid_h"] <= 16:
        errors.append(f"grid height must be 10..16, found {info['grid_h']}")
    if not 10 <= info["grid_w"] <= 18:
        errors.append(f"grid width must be 10..18, found {info['grid_w']}")
    if info["colours"] & {4, 8}:
        errors.append("input component colours must exclude output labels 4 and 8")
    if not 2 <= len(info["components"]) <= 4:
        errors.append(f"expected 2..4 components, found {len(info['components'])}")
    if not 1 <= info["n_hollow"] <= 2:
        errors.append(f"expected 1..2 hole-containing components, found {info['n_hollow']}")
    if not 1 <= info["n_hole_free"] <= 2:
        errors.append(f"expected 1..2 hole-free components, found {info['n_hole_free']}")
    if info["n_multi_hole"] > 1:
        errors.append(f"expected at most one multi-hole component, found {info['n_multi_hole']}")
    if not 1 <= info["n_distinct_colors"] <= 2:
        errors.append(
            f"expected one or two distinct input colours, found {info['n_distinct_colors']}"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    errors = self_check(grid)
    profile = (
        info["grid_h"],
        info["grid_w"],
        len({value for row in grid for value in row}),
    )
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}")
    if len(info["components"]) != 3:
        errors.append(f"canonical-like inputs have three components, found {len(info['components'])}")
    if info["n_distinct_colors"] != 1:
        errors.append("canonical-like inputs use one shared component colour")
    if info["n_multi_hole"] != 0:
        errors.append("canonical-like inputs do not contain a multi-hole component")
    return errors


def _paint_classified(
    grid: list[list[int]],
    classifier: Callable[[dict[str, Any]], bool],
) -> list[list[int]]:
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("grid must be a non-empty rectangle")
    h, w = shape
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer ARC colours 0..9")
    out = full_grid(h, w, 0)
    for component in _same_colour_components(grid):
        label = 8 if classifier(component) else 4
        for r, c in component["cells"]:
            out[r][c] = label
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected enclosed-region authority."""
    return _paint_classified(grid, lambda component: component["holes"] > 0)


def _bbox_nonfull_rule(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: every non-full bounding box is called a hole."""
    def nonfull(component: dict[str, Any]) -> bool:
        r1, c1, r2, c2 = component["bbox"]
        return len(component["cells"]) < (r2 - r1 + 1) * (c2 - c1 + 1)

    return _paint_classified(grid, nonfull)


def _open_concavity_witness(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["open_concavities"])


SEMANTIC_RIVALS = {
    "bbox_nonfull_is_hole": _bbox_nonfull_rule,
}
SEMANTIC_WITNESSES = {
    "open_concavity_not_hole": _open_concavity_witness,
}
WITNESS_RIVALS = {
    "open_concavity_not_hole": ["bbox_nonfull_is_hole"],
}
LESSON_COMPETITORS = {
    "bbox_nonfull_is_hole": _bbox_nonfull_rule,
}
CANONICAL_SHORTCUTS = {
    "bbox_nonfull_is_hole": _bbox_nonfull_rule,
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    del query
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for pair in demos:
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                return ["lesson demonstrations must contain input and output grids"]
            if rival(pair["input"]) != pair["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"declared competitor {name} fits every demonstration")
    return reasons
