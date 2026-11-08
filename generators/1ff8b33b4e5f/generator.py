"""Generator for ARC task ``1ff8b33b4e5f`` — fill magenta component bboxes.

The input contains a single key cell in one corner and two to four separated
magenta (6) components.  The key cell's color is the output color.  The rule
clears the input and fills the *bounding box of every magenta component* with
the key color.

The generator deliberately mixes irregular components (where bbox filling adds
cells) with already-solid components.  This makes the bbox operation visible
without teaching the false shortcut "just recolor the existing magenta cells".
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ff8b33b4e5f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "040f3dddcc41"

SUMMARY = (
    "A zero-background grid has exactly one non-magenta key cell in a corner "
    "and 2-4 separated magenta(6) components. Clear the input; for every "
    "magenta component, fill its axis-aligned bounding box solid with the key "
    "cell's color."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are magenta(6) plus one singleton key color",
    "the singleton key lies in one of the four grid corners and its color is not 0 or 6",
    "there are 2-4 separated 4-connected magenta components",
    "at least one magenta component is irregular so bbox filling adds at least one output cell",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# The five official input dimensions. Keeping ordinary draws on these sizes
# anchors the teaching distribution to the canonical scale while allowing
# substantial placement and shape diversity inside each canvas.
SCENE_PROFILES = {
    "p10x12": (10, 12),
    "p11x11": (11, 11),
    "p9x13": (9, 13),
    "p10x10": (10, 10),
    "p11x12": (11, 12),
}
_SCENE_NAMES = tuple(SCENE_PROFILES)
_KEY_CORNERS = ("tl", "tr", "bl", "br")
_KEY_COLORS = ("2", "3", "4", "5", "8")
_COMPONENT_MIXES = ("all_irregular", "mixed")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted canonical canvas schedule",
        "valid": "p10x12|p11x11|p9x13|p10x10|p11x12",
    },
    "key_corner": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "tl|tr|bl|br",
    },
    "key_color": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "2|3|4|5|8",
    },
    "n_blobs": {
        "type": "int",
        "default": "sample-index schedule",
        "valid": "2..4",
    },
    "component_mix": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "all_irregular|mixed",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Connected shapes are normalized at (0, 0). Irregular shapes leave at least
# one hole in their bbox; solid shapes exactly equal their bbox.
_IRREGULAR_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
)
_SOLID_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(shape: Sequence[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return unique D4 variants of a small connected shape."""
    current = tuple(shape)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((r, -c) for r, c in current))
        current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


_IRREGULAR_VARIANTS = tuple(
    dict.fromkeys(
        variant for shape in _IRREGULAR_SHAPES for variant in _shape_variants(shape)
    )
)
_SOLID_VARIANTS = tuple(
    dict.fromkeys(
        variant for shape in _SOLID_SHAPES for variant in _shape_variants(shape)
    )
)


def _components_of_color(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            components.append(sorted(cells))
    return components


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells: Sequence[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _key_info(grid) -> tuple[int, int, int] | None:
    non_magenta = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 6)
    ]
    if len(non_magenta) != 1:
        return None
    return non_magenta[0]


def _corner_name(h: int, w: int, r: int, c: int) -> str | None:
    return {
        (0, 0): "tl",
        (0, w - 1): "tr",
        (h - 1, 0): "bl",
        (h - 1, w - 1): "br",
    }.get((r, c))


def _profile_for_shape(h: int, w: int) -> str | None:
    for name, shape in SCENE_PROFILES.items():
        if shape == (h, w):
            return name
    return None


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    h = len(grid)
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return {"errors": ["cells must be literal ARC integers 0..9"]}

    profile = _profile_for_shape(h, w)
    if profile is None:
        errors.append(f"grid shape {h}x{w} is not one of the five canonical canvas profiles")

    key = _key_info(grid)
    if key is None:
        errors.append("expected exactly one nonzero non-magenta key cell")
        key_corner = None
        key_color = None
    else:
        kr, kc, kval = key
        key_corner = _corner_name(h, w, kr, kc)
        key_color = str(kval)
        if key_corner is None:
            errors.append("the singleton key cell must lie in a grid corner")
        if key_color not in _KEY_COLORS:
            errors.append(f"key color {kval} is outside the canonical key-color set {_KEY_COLORS}")

    allowed = {0, 6}
    if key is not None:
        allowed.add(key[2])
    extras = sorted({value for row in grid for value in row if value not in allowed})
    if extras:
        errors.append(f"unexpected foreground colors beyond key and magenta: {extras}")

    components = _components_of_color(grid, 6)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2-4 magenta components, found {len(components)}")
    solid_count = sum(_bbox_area(cells) == len(cells) for cells in components)
    irregular_count = len(components) - solid_count
    if components and irregular_count == 0:
        errors.append("at least one magenta component must be irregular so bbox filling changes support")

    mix = None
    if components:
        if solid_count == 0:
            mix = "all_irregular"
        elif solid_count == 1 and irregular_count >= 1:
            mix = "mixed"
        else:
            mix = "other"

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "scene_profile": profile,
        "key": key,
        "key_corner": key_corner,
        "key_color": key_color,
        "components": components,
        "n_blobs": len(components),
        "solid_count": solid_count,
        "irregular_count": irregular_count,
        "component_mix": mix,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a returned grid."""
    analysis = _analysis(grid)
    if not {"height", "width"}.issubset(analysis):
        return {}
    return {
        "scene_profile": analysis.get("scene_profile"),
        "key_corner": analysis.get("key_corner"),
        "key_color": analysis.get("key_color"),
        "n_blobs": analysis.get("n_blobs"),
        "component_mix": analysis.get("component_mix"),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact structural grammar and any explicit axis contract."""
    errors = list(_analysis(grid).get("errors", []))
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, expected in _meta_overrides(meta).items():
        if name not in AXES or expected is None:
            continue
        if name == "key_color":
            expected = str(expected)
        elif name == "n_blobs":
            expected = int(expected)
        if observed.get(name) != expected:
            errors.append(
                f"override {name}={expected!r} not realized; observed {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict semantic-profile hook used by the generator semantic gate."""
    return self_check(grid)


def _default_profile(band: str, sample_index: int) -> str:
    orders = {
        "easy": ("p10x10", "p9x13", "p11x11", "p10x12", "p11x12"),
        "medium": ("p10x12", "p11x11", "p10x10", "p11x12", "p9x13"),
        "hard": ("p11x12", "p9x13", "p10x12", "p11x11", "p10x10"),
    }
    return orders[band][sample_index % 5]


def _scheduled_overrides(sample_index: int, band: str, overrides: dict[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    scheduled: dict[str, Any] = {
        "scene_profile": _default_profile(band, sample_index),
        "key_corner": _KEY_CORNERS[sample_index % len(_KEY_CORNERS)],
        "key_color": _KEY_COLORS[sample_index % len(_KEY_COLORS)],
        "n_blobs": 2 + (sample_index % 3),
        "component_mix": _COMPONENT_MIXES[sample_index % len(_COMPONENT_MIXES)],
    }
    scheduled.update(overrides)
    if "key_color" in scheduled:
        scheduled["key_color"] = str(scheduled["key_color"])
    return scheduled


def _corner_cell(h: int, w: int, corner: str) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "bl": (h - 1, 0),
        "br": (h - 1, w - 1),
    }[corner]


def _place_shape(
    rng,
    h: int,
    w: int,
    variants: Sequence[Sequence[tuple[int, int]]],
    occupied: set[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    """Place a shape at Chebyshev distance >=2 from existing foreground."""
    ordered_variants = list(variants)
    rng.shuffle(ordered_variants)
    for variant in ordered_variants:
        vh = max(r for r, _ in variant) + 1
        vw = max(c for _, c in variant) + 1
        candidates = [(top, left) for top in range(h - vh + 1) for left in range(w - vw + 1)]
        rng.shuffle(candidates)
        for top, left in candidates:
            cells = tuple((top + r, left + c) for r, c in variant)
            if any(
                abs(r - er) <= 1 and abs(c - ec) <= 1
                for r, c in cells
                for er, ec in occupied
            ):
                continue
            return cells
    raise RuntimeError("could not place a separated component on canonical canvas")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    effective = _scheduled_overrides(int(sample_index), band, dict(overrides))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    scene_profile = ctx.draw_choice("scene_profile", _SCENE_NAMES)
    key_corner = ctx.draw_choice("key_corner", _KEY_CORNERS)
    key_color = int(ctx.draw_choice("key_color", _KEY_COLORS))
    n_blobs = ctx.draw_int("n_blobs", 2, 4)
    component_mix = ctx.draw_choice("component_mix", _COMPONENT_MIXES)

    h, w = SCENE_PROFILES[scene_profile]
    grid = full_grid(h, w, 0)
    kr, kc = _corner_cell(h, w, key_corner)
    grid[kr][kc] = key_color
    occupied = {(kr, kc)}

    kinds = ["irregular"] * n_blobs
    if component_mix == "mixed":
        kinds[-1] = "solid"
    rng = ctx.draw_rng("layout")
    rng.shuffle(kinds)
    for kind in kinds:
        variants = _SOLID_VARIANTS if kind == "solid" else _IRREGULAR_VARIANTS
        cells = _place_shape(rng, h, w, variants, occupied)
        for r, c in cells:
            grid[r][c] = 6
        occupied.update(cells)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": effective})
    if errors:
        raise RuntimeError("generated invalid grid: " + "; ".join(errors))
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Pure-Python semantic mirror used only for tests/rivals, not authority."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("invalid canonical-like input: " + "; ".join(analysis["errors"]))
    key = analysis["key"][2]
    out = full_grid(analysis["height"], analysis["width"], 0)
    for cells in analysis["components"]:
        r0, c0, r1, c1 = _bbox(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = key
    return out


def _rival_recolor_existing_magenta_only(grid):
    info = _analysis(grid)
    key = info["key"][2]
    return [[key if value == 6 else 0 for value in row] for row in grid]


def _rival_fill_only_largest_component_bbox(grid):
    info = _analysis(grid)
    key = info["key"][2]
    out = full_grid(info["height"], info["width"], 0)
    cells = max(info["components"], key=lambda comp: (len(comp), -comp[0][0], -comp[0][1]))
    r0, c0, r1, c1 = _bbox(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = key
    return out


def _rival_fill_one_global_bbox_around_all_magenta(grid):
    info = _analysis(grid)
    key = info["key"][2]
    out = full_grid(info["height"], info["width"], 0)
    cells = [cell for comp in info["components"] for cell in comp]
    r0, c0, r1, c1 = _bbox(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = key
    return out


def _rival_preserve_key_marker_in_output(grid):
    out = rule_mirror(grid)
    r, c, value = _analysis(grid)["key"]
    out[r][c] = value
    return out


def _rival_always_use_color_2(grid):
    info = _analysis(grid)
    out = full_grid(info["height"], info["width"], 0)
    for cells in info["components"]:
        r0, c0, r1, c1 = _bbox(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = 2
    return out


SEMANTIC_RIVALS = {
    "recolor_existing_magenta_only": _rival_recolor_existing_magenta_only,
    "fill_only_largest_component_bbox": _rival_fill_only_largest_component_bbox,
    "fill_one_global_bbox_around_all_magenta": _rival_fill_one_global_bbox_around_all_magenta,
    "preserve_key_marker_in_output": _rival_preserve_key_marker_in_output,
    "always_use_color_2": _rival_always_use_color_2,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_corner(name: str):
    return lambda grid: _analysis(grid).get("key_corner") == name


def _has_key_color(value: str):
    return lambda grid: _analysis(grid).get("key_color") == value


def _has_blob_count(value: int):
    return lambda grid: _analysis(grid).get("n_blobs") == value


SEMANTIC_WITNESSES = {
    "key_corner_tl": _has_corner("tl"),
    "key_corner_tr": _has_corner("tr"),
    "key_corner_bl": _has_corner("bl"),
    "key_corner_br": _has_corner("br"),
    "key_color_2": _has_key_color("2"),
    "key_color_3": _has_key_color("3"),
    "key_color_4": _has_key_color("4"),
    "key_color_5": _has_key_color("5"),
    "key_color_8": _has_key_color("8"),
    "two_components": _has_blob_count(2),
    "three_components": _has_blob_count(3),
    "four_components": _has_blob_count(4),
    "all_irregular": lambda grid: _analysis(grid).get("component_mix") == "all_irregular",
    "mixed_solid_and_irregular": lambda grid: _analysis(grid).get("component_mix") == "mixed",
    "bbox_expands_support": lambda grid: _analysis(grid).get("irregular_count", 0) >= 1,
    "already_solid_component_present": lambda grid: _analysis(grid).get("solid_count", 0) >= 1,
}

WITNESS_RIVALS = {
    "key_corner_tl": ["preserve_key_marker_in_output"],
    "key_corner_tr": ["preserve_key_marker_in_output"],
    "key_corner_bl": ["preserve_key_marker_in_output"],
    "key_corner_br": ["preserve_key_marker_in_output"],
    "key_color_2": ["preserve_key_marker_in_output"],
    "key_color_3": ["always_use_color_2"],
    "key_color_4": ["always_use_color_2"],
    "key_color_5": ["always_use_color_2"],
    "key_color_8": ["always_use_color_2"],
    "two_components": ["fill_only_largest_component_bbox", "fill_one_global_bbox_around_all_magenta"],
    "three_components": ["fill_only_largest_component_bbox", "fill_one_global_bbox_around_all_magenta"],
    "four_components": ["fill_only_largest_component_bbox", "fill_one_global_bbox_around_all_magenta"],
    "all_irregular": ["recolor_existing_magenta_only"],
    "mixed_solid_and_irregular": ["recolor_existing_magenta_only"],
    "bbox_expands_support": ["recolor_existing_magenta_only"],
    "already_solid_component_present": ["recolor_existing_magenta_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson iff a declared plausible rival still fits all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except Exception as exc:
            return [f"demo {index} is outside the canonical-like grammar: {exc}"]
        if expected != demo["output"]:
            reasons.append(f"demo {index} does not match the bbox-fill rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"rival survives all demos: {name}")
        except Exception as exc:
            reasons.append(f"rival {name} errored: {type(exc).__name__}: {exc}")
    return reasons
