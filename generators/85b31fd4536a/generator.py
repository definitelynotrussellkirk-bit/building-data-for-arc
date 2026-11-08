"""High-integrity generator for ARC task ``85b31fd4536a``.

A full maroon (9) column separates two equal panels.  The left panel is a
binary blue (1) stencil over black (0); the right panel is a dense color field
using colors 2..8.  The output copies the right-panel value at every blue
stencil position and writes black elsewhere.

The old generator taught a materially different visual prior: large 7..16 by
5..14 panels and one connected mask blob.  Every canonical mask is instead a
small 4-row panel with three or four disconnected components.  This version
anchors the canonical scale and palette, preserves disconnected-mask evidence,
and makes every ordinary lesson refute the main count-, color-, and
connectivity-based shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85b31fd4536a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "02edca4e3e1c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "A full color-9 column separates equal panels. The left panel is a "
    "three- or four-component binary color-1 mask; the right panel is a dense "
    "2..8 color field. Copy right-panel colors through color-1 positions and "
    "write 0 everywhere else."
)

INVARIANTS = [
    "exactly one full color-9 column separates two equal nonempty panels",
    "the left panel contains only 0 and 1 and has exactly three or four 4-connected color-1 components",
    "every left-panel row and column contains both mask and background cells",
    "the right panel contains only colors 2..8 and uses exactly the declared source-palette size",
    "masked and unmasked source positions each contain multiple colors and share at least one source color",
    "the mask is not a row-major prefix or suffix, so cell count cannot reveal its positions",
    "ordinary grids stay near the canonical 4-row, 3..4-column panel scale while retaining bounded size variation",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted keyed draw, canonical height 4 most often",
        "valid": "4..6",
    },
    "panel_w": {
        "type": "int",
        "default": "weighted keyed draw, canonical widths 3 and 4 most often",
        "valid": "3..5",
    },
    "mask_components": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "3..4",
    },
    "src_colors": {
        "type": "int",
        "default": "weighted keyed draw, full canonical 2..8 palette often",
        "valid": "2..7",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SOURCE_COLORS = tuple(range(2, 9))


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name, value in overrides.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name!r} must be an integer")


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                raise ValueError("row strings must be non-empty decimal colors")
            values = [int(ch) for ch in row]
        elif isinstance(row, list):
            values = list(row)
        else:
            raise ValueError("grid rows must be lists or digit strings")
        if not values:
            raise ValueError("grid rows must be non-empty")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid values must be integer colors in 0..9")
        out.append(values)
    width = len(out[0])
    if any(len(row) != width for row in out):
        raise ValueError("grid must be rectangular")
    return out


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        found.append(component)
    return found


def _is_fixed_traversal_mask(
    cells: set[tuple[int, int]], h: int, w: int
) -> bool:
    indices = sorted(r * w + c for r, c in cells)
    count = len(indices)
    return indices == list(range(count)) or indices == list(
        range(h * w - count, h * w)
    )


def _rows_and_columns_are_mixed(
    cells: set[tuple[int, int]], h: int, w: int
) -> bool:
    for r in range(h):
        occupied = [(r, c) in cells for c in range(w)]
        if all(occupied) or not any(occupied):
            return False
    for c in range(w):
        occupied = [(r, c) in cells for r in range(h)]
        if all(occupied) or not any(occupied):
            return False
    return True


def _scene_facts(grid: Any) -> dict[str, Any]:
    g = _coerce_grid(grid)
    h, width = len(g), len(g[0])
    dividers = [
        c for c in range(width) if all(g[r][c] == 9 for r in range(h))
    ]
    if len(dividers) != 1:
        raise ValueError(
            f"expected exactly one full color-9 divider column; found {len(dividers)}"
        )
    divider = dividers[0]
    if divider == 0 or divider == width - 1:
        raise ValueError("divider must have nonempty panels on both sides")
    left = [row[:divider] for row in g]
    right = [row[divider + 1 :] for row in g]
    if any(len(row) != divider for row in right):
        raise ValueError("divider must split the grid into equal-width panels")

    mask = {
        (r, c)
        for r in range(h)
        for c in range(divider)
        if left[r][c] == 1
    }
    background = {
        (r, c)
        for r in range(h)
        for c in range(divider)
        if left[r][c] == 0
    }
    components = _components(mask) if mask else []
    source_palette = {value for row in right for value in row}
    masked_source_palette = {right[r][c] for r, c in mask}
    unmasked_source_palette = {right[r][c] for r, c in background}
    return {
        "grid": g,
        "height": h,
        "panel_w": divider,
        "left": left,
        "right": right,
        "mask": mask,
        "background": background,
        "components": components,
        "source_palette": source_palette,
        "masked_source_palette": masked_source_palette,
        "unmasked_source_palette": unmasked_source_palette,
        "mask_fraction": len(mask) / (h * divider),
    }


def self_check(
    grid: Any, *, difficulty: str | None = None, meta: dict[str, Any] | None = None
) -> list[str]:
    """Reject malformed and shortcut-teaching mask/source scenes."""
    del difficulty
    try:
        facts = _scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []
    h = facts["height"]
    panel_w = facts["panel_w"]
    left = facts["left"]
    right = facts["right"]
    mask = facts["mask"]
    background = facts["background"]
    components = facts["components"]

    if not 4 <= h <= 6:
        errors.append(f"grid height must be in 4..6; got {h}")
    if not 3 <= panel_w <= 5:
        errors.append(f"panel width must be in 3..5; got {panel_w}")
    if any(value not in (0, 1) for row in left for value in row):
        errors.append("left panel must contain only colors 0 and 1")
    if any(value not in _SOURCE_COLORS for row in right for value in row):
        errors.append("right panel must contain only source colors 2..8")
    if not 3 <= len(components) <= 4:
        errors.append(
            "mask must contain exactly three or four 4-connected components; "
            f"found {len(components)}"
        )
    if len(mask) < 4:
        errors.append("mask must contain at least four color-1 cells")
    if len(background) < 3:
        errors.append("mask must leave at least three background cells")
    if mask and not _rows_and_columns_are_mixed(mask, h, panel_w):
        errors.append("every mask row and column must contain both 0 and 1")
    if mask and _is_fixed_traversal_mask(mask, h, panel_w):
        errors.append("mask must not be a row-major prefix or suffix")
    if not 2 <= len(facts["source_palette"]) <= 7:
        errors.append("right source panel must use two to seven colors")
    if len(facts["masked_source_palette"]) < 2:
        errors.append("masked source positions must contain at least two colors")
    if len(facts["unmasked_source_palette"]) < 2:
        errors.append("unmasked source positions must contain at least two colors")
    if not (
        facts["masked_source_palette"] & facts["unmasked_source_palette"]
    ):
        errors.append(
            "at least one source color must occur both inside and outside the mask"
        )

    requested = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested = dict(meta["overrides"])
        else:
            requested = {name: meta[name] for name in AXES if name in meta}
    if requested:
        observed = observe_overrides(facts["grid"])
        for name, value in requested.items():
            if name in observed and observed[name] != value:
                errors.append(
                    f"override {name!r} requested {value!r}, observed "
                    f"{observed[name]!r}"
                )
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Return every exact public axis as recovered from the emitted grid."""
    facts = _scene_facts(grid)
    return {
        "grid_h": facts["height"],
        "panel_w": facts["panel_w"],
        "mask_components": len(facts["components"]),
        "src_colors": len(facts["source_palette"]),
    }


def _rule_unchecked(grid: Any) -> list[list[int]]:
    """Mirror the fixed Racket transform without applying teaching checks."""
    facts = _scene_facts(grid)
    return [
        [
            facts["right"][r][c] if facts["left"][r][c] == 1 else 0
            for c in range(facts["panel_w"])
        ]
        for r in range(facts["height"])
    ]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Input-pure audit mirror; canonical Racket remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid mask/source scene: " + "; ".join(errors))
    return _rule_unchecked(grid)


def _target_mask_cells(rng, h: int, w: int, difficulty: str | None) -> int:
    ranges = {
        "easy": (45, 52),
        "medium": (48, 56),
        "hard": (52, 60),
        None: (46, 58),
    }
    lo, hi = ranges[difficulty]
    target = round(h * w * rng.randint(lo, hi) / 100)
    return max(4, min(target, h * w - 3))


def _draw_mask(
    rng, h: int, w: int, component_count: int, target: int
) -> set[tuple[int, int]]:
    positions = [(r, c) for r in range(h) for c in range(w)]
    candidate_targets = sorted(
        range(max(4, component_count), h * w - 2),
        key=lambda value: (abs(value - target), value),
    )
    for candidate_target in candidate_targets:
        for _ in range(800):
            cells = set(rng.sample(positions, candidate_target))
            if len(_components(cells)) != component_count:
                continue
            if not _rows_and_columns_are_mixed(cells, h, w):
                continue
            if _is_fixed_traversal_mask(cells, h, w):
                continue
            return cells
    raise ValueError(
        f"could not construct a {component_count}-component mixed mask in {h}x{w}"
    )


def _cyclic_source(
    rng, h: int, w: int, palette: list[int]
) -> list[list[int]]:
    ordered = list(palette)
    rng.shuffle(ordered)
    offset = rng.randrange(len(ordered))
    return [
        [ordered[(offset + r * w + c) % len(ordered)] for c in range(w)]
        for r in range(h)
    ]


def _random_source(
    rng, h: int, w: int, palette: list[int]
) -> list[list[int]]:
    return [[rng.choice(palette) for _ in range(w)] for _ in range(h)]


def _repair_source_palette(
    rng,
    source: list[list[int]],
    palette: list[int],
    protected: set[tuple[int, int]],
) -> None:
    positions = [
        (r, c)
        for r in range(len(source))
        for c in range(len(source[0]))
        if (r, c) not in protected
    ]
    rng.shuffle(positions)
    counts = Counter(value for row in source for value in row)
    for color in palette:
        if counts[color] > 0:
            continue
        donor_index = next(
            (
                index
                for index, (r, c) in enumerate(positions)
                if counts[source[r][c]] > 1
            ),
            None,
        )
        if donor_index is None:
            raise ValueError("could not preserve exact source palette")
        r, c = positions.pop(donor_index)
        counts[source[r][c]] -= 1
        source[r][c] = color
        counts[color] += 1


def _build_source(
    rng,
    h: int,
    w: int,
    palette: list[int],
    mask: set[tuple[int, int]],
    difficulty: str | None,
    sample_index: int,
) -> list[list[int]]:
    background = [
        (r, c) for r in range(h) for c in range(w) if (r, c) not in mask
    ]
    mask_positions = sorted(mask)
    for _ in range(300):
        if difficulty == "hard" or (
            difficulty == "medium" and sample_index % 2 == 1
        ):
            source = _random_source(rng, h, w, palette)
        else:
            source = _cyclic_source(rng, h, w, palette)

        inside = list(mask_positions)
        outside = list(background)
        rng.shuffle(inside)
        rng.shuffle(outside)
        protected: set[tuple[int, int]] = set()
        for cells in (inside, outside):
            source[cells[0][0]][cells[0][1]] = palette[0]
            source[cells[1][0]][cells[1][1]] = palette[1]
            protected.update(cells[:2])
        _repair_source_palette(rng, source, palette, protected)

        masked = {source[r][c] for r, c in mask}
        unmasked = {source[r][c] for r, c in background}
        actual = {value for row in source for value in row}
        if actual != set(palette):
            continue
        if len(masked) < 2 or len(unmasked) < 2:
            continue
        if not masked & unmasked:
            continue
        return source
    raise ValueError("could not build a branch-discriminating source field")


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Duplicate draw-choice entries are deliberate canonical anchoring while
    # retaining exact support for every declared boundary value.
    h = ctx.draw_choice("grid_h", (4, 4, 4, 5, 6))
    panel_w = ctx.draw_choice("panel_w", (3, 3, 4, 4, 5))
    component_count = ctx.draw_int_diff("mask_components", 3, 4)
    source_color_count = ctx.draw_choice(
        "src_colors", (2, 3, 4, 5, 6, 7, 7, 7, 7, 7)
    )

    density_rng = ctx.draw_rng("mask-density")
    mask_rng = ctx.draw_rng("mask-layout")
    source_rng = ctx.draw_rng("source")
    target = _target_mask_cells(density_rng, h, panel_w, difficulty)
    mask = _draw_mask(mask_rng, h, panel_w, component_count, target)

    palette = source_rng.sample(list(_SOURCE_COLORS), source_color_count)
    source = _build_source(
        source_rng,
        h,
        panel_w,
        palette,
        mask,
        difficulty,
        sample_index,
    )

    grid = full_grid(h, panel_w * 2 + 1, 0)
    for r in range(h):
        for c in range(panel_w):
            grid[r][c] = 1 if (r, c) in mask else 0
        grid[r][panel_w] = 9
        grid[r][panel_w + 1 :] = source[r]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid grid: " + "; ".join(errors))
    return grid


def strict_canonical_like(grid: Any) -> list[str]:
    """Characterize the canonical small, full-palette task manifold."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _scene_facts(grid)
    if facts["height"] != 4:
        reasons.append(f"canonical height is 4, got {facts['height']}")
    if facts["panel_w"] not in (3, 4):
        reasons.append(
            f"canonical panel width is 3 or 4, got {facts['panel_w']}"
        )
    if facts["source_palette"] != set(_SOURCE_COLORS):
        reasons.append("canonical right panel uses every source color 2..8")
    if len(facts["components"]) not in (3, 4):
        reasons.append("canonical mask has three or four components")
    if not 0.45 <= facts["mask_fraction"] <= 0.60:
        reasons.append(
            "canonical mask occupies about half the panel; got "
            f"{facts['mask_fraction']:.3f}"
        )
    return reasons


def _rival_copy_right(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    return [list(row) for row in facts["right"]]


def _rival_copy_mask(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    return [
        [1 if facts["left"][r][c] == 1 else 0 for c in range(facts["panel_w"])]
        for r in range(facts["height"])
    ]


def _rival_modal_fill(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    counts = Counter(value for row in facts["right"] for value in row)
    modal = min(counts, key=lambda color: (-counts[color], color))
    return [
        [
            modal if facts["left"][r][c] == 1 else 0
            for c in range(facts["panel_w"])
        ]
        for r in range(facts["height"])
    ]


def _rival_largest_component(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    largest = min(
        facts["components"],
        key=lambda component: (-len(component), min(component)),
    )
    return [
        [
            facts["right"][r][c] if (r, c) in largest else 0
            for c in range(facts["panel_w"])
        ]
        for r in range(facts["height"])
    ]


def _rival_row_major_count(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    count = len(facts["mask"])
    chosen = {
        (index // facts["panel_w"], index % facts["panel_w"])
        for index in range(count)
    }
    return [
        [
            facts["right"][r][c] if (r, c) in chosen else 0
            for c in range(facts["panel_w"])
        ]
        for r in range(facts["height"])
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "copy_right_ignore_mask": _rival_copy_right,
    "copy_mask_marker_as_answer": _rival_copy_mask,
    "fill_mask_with_modal_source_color": _rival_modal_fill,
    "copy_only_largest_mask_component": _rival_largest_component,
    "copy_row_major_prefix_with_same_count": _rival_row_major_count,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_multiple_components(grid: Any) -> bool:
    try:
        return len(_scene_facts(grid)["components"]) >= 2
    except ValueError:
        return False


def _witness_irregular_positions(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    return not _is_fixed_traversal_mask(
        facts["mask"], facts["height"], facts["panel_w"]
    )


def _witness_multicolor_mask(grid: Any) -> bool:
    try:
        return len(_scene_facts(grid)["masked_source_palette"]) >= 2
    except ValueError:
        return False


def _witness_unmasked_source(grid: Any) -> bool:
    try:
        return bool(_scene_facts(grid)["background"])
    except ValueError:
        return False


def _witness_source_not_marker(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    return bool(facts["mask"]) and all(
        facts["right"][r][c] != 1 for r, c in facts["mask"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "multiple_components_refute_largest_only": _witness_multiple_components,
    "irregular_positions_refute_count_prefix": _witness_irregular_positions,
    "multicolor_mask_refutes_modal_fill": _witness_multicolor_mask,
    "background_cells_refute_copy_right": _witness_unmasked_source,
    "source_colors_refute_mask_echo": _witness_source_not_marker,
}

WITNESS_RIVALS = {
    "multiple_components_refute_largest_only": [
        "copy_only_largest_mask_component"
    ],
    "irregular_positions_refute_count_prefix": [
        "copy_row_major_prefix_with_same_count"
    ],
    "multicolor_mask_refutes_modal_fill": [
        "fill_mask_with_modal_source_color"
    ],
    "background_cells_refute_copy_right": ["copy_right_ignore_mask"],
    "source_colors_refute_mask_echo": ["copy_mask_marker_as_answer"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require the demonstrations to eliminate every named plausible rival."""
    if not isinstance(demos, list) or not demos:
        return ["lesson must contain at least one demonstration"]
    if not isinstance(query, dict):
        return ["query must be a materialized pair"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:  # fail loud through a diagnostic reason
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            query_differs = rival(query["input"]) != query["output"]
            suffix = " and answers the query differently" if query_differs else ""
            reasons.append(f"competitor {name} survives every demo{suffix}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes used by focused regression tests."""
    valid = generate(
        74_001,
        7,
        difficulty="medium",
        grid_h=4,
        panel_w=4,
        mask_components=4,
        src_colors=4,
    )
    facts = _scene_facts(valid)
    divider = facts["panel_w"]
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_divider = [list(row) for row in valid]
    missing_divider[0][divider] = 0
    fixtures.append(("broken_separator", missing_divider))

    unequal = [list(row) + [row[-1]] for row in valid]
    fixtures.append(("unequal_panel_widths", unequal))

    illegal_left = [list(row) for row in valid]
    r0, c0 = min(facts["background"])
    illegal_left[r0][c0] = 8
    fixtures.append(("illegal_left_color", illegal_left))

    full_mask = [list(row) for row in valid]
    for r in range(facts["height"]):
        for c in range(divider):
            full_mask[r][c] = 1
    fixtures.append(("single_component_full_mask", full_mask))

    illegal_source = [list(row) for row in valid]
    illegal_source[0][divider + 1] = 0
    fixtures.append(("source_contains_background", illegal_source))

    second_separator = [list(row) for row in valid]
    for r in range(facts["height"]):
        second_separator[r][divider + 1] = 9
    fixtures.append(("second_full_separator", second_separator))
    return fixtures


def negative_recombination_fixture() -> tuple[list[list[int]], int]:
    """Malformed input whose new left color is absent everywhere else.

    The Racket rule can execute it because only color 1 activates the mask, but
    the teaching grammar must reject the unseen role/color recombination.
    """
    grid = generate(
        91_337,
        5,
        difficulty="medium",
        grid_h=4,
        panel_w=4,
        mask_components=4,
        src_colors=3,
    )
    facts = _scene_facts(grid)
    present = {value for row in grid for value in row}
    replacement = next(color for color in _SOURCE_COLORS if color not in present)
    r, c = min(facts["background"])
    out = [list(row) for row in grid]
    out[r][c] = replacement
    return out, replacement
