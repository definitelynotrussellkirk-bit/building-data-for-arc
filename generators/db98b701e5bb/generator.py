"""Generator for ARC task db98b701e5bb: recolor the largest red object.

The input contains two to four separated 4-connected color-2 components and one
connected distractor object in another color.  The unique largest red component
is recolored to 8; every other cell is preserved.

The sampler intentionally includes the canonical smaller-size tie (3, 3, 5).
Only the maximum must be unique.  A three-example sample-index schedule rotates
the largest component through first/middle/last scan order and places two
bounding-box counterexamples per three indices, so positional and maximum-bbox
rules cannot survive a normal lesson or any one-query rotation of four
consecutive pairs.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db98b701e5bb"
TASK_ID = GENERATOR_ID
RULE_HASH = "da19a5612a17"
VERSION = "3.1.0"

SUMMARY = (
    "A canonical-sized 0-background grid contains 2-4 mutually separated "
    "4-connected red (color-2) components. Their largest cell-count is unique, "
    "but smaller components may tie. One connected non-red distractor is "
    "preserved. Recolor exactly the unique largest red component to color 8."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid dimensions and three-color palette match a canonical profile by default",
    "2-4 color-2 components are pairwise separated even diagonally",
    "the largest color-2 component is unique; smaller component sizes may tie",
    "one connected distractor object uses one color outside {0,2,8}",
    "color 8 is absent from the input and is introduced only by the rule",
]

COMPONENT_PROFILES = (
    "tie_small",
    "three_distinct",
    "two_large",
    "four_varied",
)
PROFILE_SIZES = {
    "tie_small": (3, 3, 5),
    "three_distinct": (3, 4, 5),
    "two_large": (3, 9),
    "four_varied": (1, 2, 3, 5),
}
PROFILE_BY_SIZES = {tuple(sorted(sizes)): name for name, sizes in PROFILE_SIZES.items()}
DISTRACTOR_SIZE = {
    "tie_small": 3,
    "three_distinct": 1,
    "two_large": 3,
    "four_varied": 1,
}
CANONICAL_COMPONENT_PROFILES = frozenset({"tie_small", "three_distinct", "two_large"})
CANONICAL_GRID_PROFILES = frozenset({(8, 10, 3), (8, 11, 3), (9, 12, 3), (10, 13, 3)})
DISTRACTOR_COLORS = (1, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile curriculum", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "canonical-profile curriculum", "valid": "10..13"},
    "component_profile": {
        "type": "str",
        "default": "tie_small|three_distinct",
        "valid": "|".join(COMPONENT_PROFILES),
    },
    "distractor_color": {
        "type": "color",
        "default": "rng !{0,2,8}",
        "valid": "1|3|4|5|6|7|9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# Connected templates whose bounding boxes fit a 3x3 placement zone.
_BASE_SHAPES = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ),
    9: (tuple((r, c) for r in range(3) for c in range(3)),),
}


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


@lru_cache(maxsize=None)
def _shape_variants(size):
    variants = set()
    for base in _BASE_SHAPES[size]:
        current = tuple(base)
        for reflected in (False, True):
            cells = tuple((r, -c if reflected else c) for r, c in current)
            for _ in range(4):
                variants.add(_normalize(cells))
                cells = tuple((c, -r) for r, c in cells)
    return tuple(sorted(variants))


def _components_4(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def _touches_other_component(components):
    owner = {cell: index for index, cells in enumerate(components) for cell in cells}
    for index, cells in enumerate(components):
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    other = owner.get((r + dr, c + dc))
                    if other is not None and other != index:
                        return True
    return False


def _draw_axis(ctx, label, full_values, default_values, overrides):
    options = full_values if overrides.get(label) is not None else default_values
    return ctx.draw_choice(label, options)


def _canvas_profile(ctx, difficulty):
    if difficulty == "easy":
        options = ((8, 10), (8, 10), (8, 11), (8, 11), (9, 12))
    elif difficulty == "hard":
        options = ((8, 11), (9, 12), (9, 12), (10, 13), (10, 13))
    else:
        options = ((8, 10), (8, 11), (9, 12), (10, 13))
    return ctx.draw_choice("curriculum_canvas", options)


def _default_profile(sample_index):
    # Residue 0 preserves the canonical smaller-size tie. Residues 1 and 2
    # construct explicit counterexamples to the maximum-bounding-box shortcut.
    return "tie_small" if sample_index % 3 == 0 else "three_distinct"


def _bbox_area(cells):
    rows = [r for r, _ in cells]
    columns = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)


def _placed_shape(rng, size, zone_top, zone_left, *, required_bbox_area=None):
    variants = _shape_variants(size)
    if required_bbox_area is not None:
        variants = tuple(shape for shape in variants if _bbox_area(shape) == required_bbox_area)
        if not variants:
            raise RuntimeError(
                f"no size-{size} shape has required bbox area {required_bbox_area}"
            )
    shape = rng.choice(variants)
    sw = max(c for _, c in shape) + 1
    # Pin each shape's first occupied row to its zone's first row.  The two
    # horizontal zones then share the same minimum row, so scan order is set by
    # their separated columns and cannot be changed by shape-specific jitter.
    top = zone_top
    left = zone_left + rng.randint(0, 3 - sw)
    return tuple(sorted((top + r, left + c) for r, c in shape))


def _red_components(ctx, h, w, profile, sample_index):
    sizes = PROFILE_SIZES[profile]
    rng = ctx.draw_rng("red_layout")
    top = rng.randint(0, h - 8)
    # Anchor the 8-wide zone block to one side, reserving two columns on the
    # opposite side even at 8x10.  This makes distractor placement constructive.
    left = rng.choice((0, w - 8))
    zones = (
        (top, left),
        (top, left + 5),
        (top + 5, left),
        (top + 5, left + 5),
    )
    selected = sorted(rng.sample(zones, len(sizes)))

    largest = max(sizes)
    largest_rank = sample_index % len(sizes)
    bbox_counterexample = profile == "three_distinct" and sample_index % 3 in (1, 2)
    if bbox_counterexample:
        # Size 4 and size 5 both get bbox area 6, while size 4 is earlier in scan
        # order. A max-bbox rule therefore recolors size 4, not the true size 5.
        ordered_sizes = [4, 5, 3] if largest_rank == 1 else [4, 3, 5]
    else:
        remaining = list(sizes)
        remaining.remove(largest)
        rng.shuffle(remaining)
        ordered_sizes = list(remaining)
        ordered_sizes.insert(largest_rank, largest)

    components = []
    for (zone_top, zone_left), size in zip(selected, ordered_sizes):
        required_area = 6 if bbox_counterexample and size in (4, 5) else None
        components.append(
            _placed_shape(
                rng,
                size,
                zone_top,
                zone_left,
                required_bbox_area=required_area,
            )
        )
    return components


def _distractor_candidates(h, w, red_cells, size):
    blocked = {
        (r + dr, c + dc)
        for r, c in red_cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    }
    candidates = set()
    for shape in _shape_variants(size):
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for top in range(h - sh + 1):
            for left in range(w - sw + 1):
                cells = tuple(sorted((top + r, left + c) for r, c in shape))
                if all(cell not in blocked for cell in cells):
                    candidates.add(cells)
    return tuple(sorted(candidates))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    for label in ("grid_h", "grid_w", "distractor_color"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer, not {type(value).__name__}")
    profile_override = overrides.get("component_profile")
    if profile_override is not None and not isinstance(profile_override, str):
        raise TypeError("component_profile must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _canvas_profile(ctx, difficulty)
    h = _draw_axis(ctx, "grid_h", (8, 9, 10), (default_h,), overrides)
    w = _draw_axis(ctx, "grid_w", (10, 11, 12, 13), (default_w,), overrides)
    profile = _draw_axis(
        ctx,
        "component_profile",
        COMPONENT_PROFILES,
        (_default_profile(sample_index),),
        overrides,
    )
    distractor_color = _draw_axis(
        ctx,
        "distractor_color",
        DISTRACTOR_COLORS,
        DISTRACTOR_COLORS,
        overrides,
    )

    red_components = _red_components(ctx, h, w, profile, sample_index)
    grid = full_grid(h, w, 0)
    for component in red_components:
        for r, c in component:
            grid[r][c] = 2

    red_cells = set().union(*map(set, red_components))
    candidates = _distractor_candidates(h, w, red_cells, DISTRACTOR_SIZE[profile])
    if not candidates:
        raise RuntimeError(
            f"constructive distractor placement failed for {h}x{w}, profile={profile}"
        )
    distractor = ctx.draw_rng("distractor_layout").choice(candidates)
    for r, c in distractor:
        grid[r][c] = distractor_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"generator produced an invalid grid: {errors}")
    return grid


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty list or tuple of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None, ["every row must be a list or tuple"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return None, ["grid must be rectangular and nonempty"]
    h, w = len(grid), next(iter(widths))
    if not (8 <= h <= 10):
        errors.append(f"height {h} outside declared 8..10 range")
    if not (10 <= w <= 13):
        errors.append(f"width {w} outside declared 10..13 range")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (bool is not accepted)")
        return None, errors

    colors = {value for row in grid for value in row}
    if 8 in colors:
        errors.append("input contains color 8, reserved for the output recolor")
    other_colors = sorted(colors - {0, 2, 8})
    if colors and 0 not in colors:
        errors.append("background color 0 is missing")
    if 2 not in colors:
        errors.append("input contains no color-2 component")
    if len(other_colors) != 1:
        errors.append(f"expected exactly one distractor color, found {other_colors}")

    red = _components_4(grid, 2)
    red_sizes = tuple(sorted(len(component) for component in red))
    profile = PROFILE_BY_SIZES.get(red_sizes)
    if not (2 <= len(red) <= 4):
        errors.append(f"expected 2-4 color-2 components, found {len(red)}")
    if profile is None:
        errors.append(f"unsupported red component-size profile {red_sizes}")
    if red:
        largest_size = max(map(len, red))
        if sum(len(component) == largest_size for component in red) != 1:
            errors.append(f"largest color-2 component is not unique: {red_sizes}")
    if _touches_other_component(red):
        errors.append("distinct color-2 components touch diagonally or orthogonally")

    distractor = []
    if len(other_colors) == 1:
        distractor = _components_4(grid, other_colors[0])
        if len(distractor) != 1:
            errors.append(f"distractor must be one 4-connected component, found {len(distractor)}")
        elif profile is not None and len(distractor[0]) != DISTRACTOR_SIZE[profile]:
            errors.append(
                f"distractor size {len(distractor[0])} does not match profile {profile!r} "
                f"size {DISTRACTOR_SIZE[profile]}"
            )
        red_cells = {cell for component in red for cell in component}
        if any(
            (r + dr, c + dc) in red_cells
            for component in distractor
            for r, c in component
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        ):
            errors.append("distractor touches a red component diagonally or orthogonally")

    facts = {
        "height": h,
        "width": w,
        "colors": colors,
        "red": red,
        "red_sizes": red_sizes,
        "profile": profile,
        "other_colors": other_colors,
        "distractor": distractor,
    }
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared generator grammar; canonical smaller ties are lawful."""
    return list(_analysis(grid)[1])


def strict_canonical_like(grid):
    facts, errors = _analysis(grid)
    if errors:
        return list(errors)
    strict_errors = []
    profile = (facts["height"], facts["width"], len(facts["colors"]))
    if profile not in CANONICAL_GRID_PROFILES:
        strict_errors.append(f"grid/palette profile {profile} is not canonical-sized")
    if facts["profile"] not in CANONICAL_COMPONENT_PROFILES:
        strict_errors.append(f"component profile {facts['profile']!r} is outside canonical support")
    return strict_errors


def observe_overrides(grid):
    facts, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "component_profile": facts["profile"],
        "distractor_color": facts["other_colors"][0],
    }


def _recolor_component(grid, component):
    out = deepcopy(grid)
    for r, c in component:
        out[r][c] = 8
    return out


def _ranked_red(grid):
    return sorted(_components_4(grid, 2), key=lambda cells: min(cells))


def _reference_output(grid):
    red = _ranked_red(grid)
    largest_size = max(map(len, red))
    largest = [component for component in red if len(component) == largest_size]
    if len(largest) != 1:
        raise ValueError("reference requires a unique largest red component")
    return _recolor_component(grid, largest[0])


def _first_red(grid):
    return _recolor_component(grid, _ranked_red(grid)[0])


def _last_red(grid):
    return _recolor_component(grid, _ranked_red(grid)[-1])


def _smallest_red(grid):
    component = min(_ranked_red(grid), key=lambda cells: (len(cells), min(cells)))
    return _recolor_component(grid, component)


def _largest_bbox_area(grid):
    """Rival: maximize red bounding-box area, breaking ties by scan order."""
    component = max(_ranked_red(grid), key=_bbox_area)
    return _recolor_component(grid, component)


def _largest_not_first(grid):
    red = _ranked_red(grid)
    return len(red[0]) != max(map(len, red))


def _largest_not_last(grid):
    red = _ranked_red(grid)
    return len(red[-1]) != max(map(len, red))


def _smaller_size_tie(grid):
    sizes = sorted(map(len, _ranked_red(grid)))
    return len(sizes) >= 3 and len(set(sizes[:-1])) < len(sizes[:-1])


def _bbox_area_shortcut_fails(grid):
    return _largest_bbox_area(grid) != _reference_output(grid)


SEMANTIC_WITNESSES = {
    "largest_not_first": _largest_not_first,
    "largest_not_last": _largest_not_last,
    "smaller_size_tie": _smaller_size_tie,
    "bbox_area_tie_selects_smaller": _bbox_area_shortcut_fails,
}
SEMANTIC_RIVALS = {
    "first_red": _first_red,
    "last_red": _last_red,
    "smallest_red": _smallest_red,
    "largest_bbox_area": _largest_bbox_area,
}
WITNESS_RIVALS = {
    "largest_not_first": ["first_red"],
    "largest_not_last": ["last_red"],
    "smaller_size_tie": ["smallest_red"],
    "bbox_area_tie_selects_smaller": ["largest_bbox_area"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"largest_bbox_area": _largest_bbox_area}


def lesson_identifiable(demos, query):
    """Return named competitors that fit every demo but alter the query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} input is outside the declared grammar")
        elif _reference_output(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not follow the largest-red rule")
    if self_check(query["input"]):
        reasons.append("query input is outside the declared grammar")
    elif _reference_output(query["input"]) != query["output"]:
        reasons.append("query output does not follow the largest-red rule")

    if reasons:
        return reasons
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        differs = rival(query["input"]) != query["output"]
        if survives and differs:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
