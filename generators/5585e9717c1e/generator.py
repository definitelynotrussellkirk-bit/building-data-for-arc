"""Generator for 9cb3cc0a41e6:S24_H4 — keyed onion-histogram lookup.

The input is a horizontal strip of equal 9x9 panels separated by full color-9
columns.  Every prototype panel has a key color at (0, 0) and one connected
main shape.  The final query panel has a shape but no key.  Remove each prototype's
key, onion-peel its shape by 4-neighbor boundary layers, and compare the full
per-layer cell-count histogram with the query.  Return the unique matching
prototype key as a 1x1 grid.

The teaching distribution deliberately uses non-congruent shape pairs with the
same onion histogram.  It also places a same-area, same-maximum-depth distractor
next to the target.  Consequently exact-mask, area-only, and max-depth-only
shortcuts disagree with the true rule on ordinary generated instances.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5585e9717c1e"
VERSION = "3.0.2"
TASK_ID = "5585e9717c1e"
RULE_HASH = "fc44e914eb1c"
EXPECTED_OUTPUT_CODOMAIN = 8  # one scalar key color from 1..8
SUMMARY = (
    "Equal 9x9 panels separated by full color-9 columns. Prototype panels "
    "carry distinct key colors at (0,0); the last panel is an unkeyed query. "
    "Match the query to the unique prototype with the same complete 4-neighbor "
    "onion-layer cell-count histogram and output that prototype's key (1x1). "
    "Generated matches are normally non-congruent histogram collisions, with "
    "same-area and same-depth distractors to refute shortcut rules."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.90
CANONICAL_PROFILE_OPT_OUT = (
    "canonical source grids are 9x39, but generated ARC grids must remain at most "
    "30 columns; the 11x29 compression preserves 9-column panels, palette size 6, "
    "canonical-scale area, and the complete keyed onion-histogram rule"
)

INVARIANTS = [
    "all panels are equal-width 9-column panels separated by one full color-9 column",
    "generated scenes have two keyed prototypes followed by one unkeyed query panel",
    "every shape has one monochrome main component and at most one accent-colored isolated cell",
    "prototype keys are distinct colors in 1..8 and occur only at panel (0,0)",
    "exactly one prototype has the query's full onion-depth histogram",
    "generated shapes include one accent-colored isolated cell whose depth-1 contribution is explicit",
    "ordinary generated matches are non-congruent and include a same-area distractor",
]

AXES = {
    "match_index": {
        "type": "int",
        "default": "weighted toward the second prototype",
        "valid": "0..1",
    },
    "target_family": {
        "type": "enum",
        "default": "difficulty-aware histogram family",
        "valid": (
            "a11_h83|a11_h92|a17_h125|a17_h134|a22_h1471|"
            "a22_h148|a27_h1683|a27_h1692|a36_h181161|a36_h191151"
        ),
    },
    "shape_color": {
        "type": "color",
        "default": "rng",
        "valid": "1..8",
    },
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_GENERATED_PANEL_H = 11
_PANEL_W = 9


def _mask(*rows: str) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r, row in enumerate(rows)
        for c, char in enumerate(row)
        if char == "#"
    )


# Each family has two connected, non-dihedrally-equivalent masks with exactly
# the same onion histogram.  Families come in same-area pairs whose histograms
# differ, furnishing a count-only distractor without changing object area.
_SHAPE_FAMILIES: dict[str, tuple[frozenset[tuple[int, int]], ...]] = {
    "a11_h83": (
        _mask("..#.", ".###", "####", ".###"),
        _mask(".#.", "###", "###", "###", ".#."),
    ),
    "a11_h92": (
        _mask(".#..", "####", ".###", ".###"),
        _mask("#..", "###", "###", "###", ".#."),
    ),
    "a17_h125": (
        _mask(".#...", "#####", "#####", "#####", ".#..."),
        _mask(".#####.", "#######", ".#####."),
    ),
    "a17_h134": (
        _mask("#....", "#####", "#####", "#####", ".#..."),
        _mask("######.", ".######", ".#####."),
    ),
    "a22_h1471": (
        _mask(".##..", "#####", "#####", "#####", "#####"),
        _mask("...#..", ".#####", "######", ".#####", ".#####"),
    ),
    "a22_h148": (
        _mask(".#...", "#####", "#####", "#####", "#####", ".#..."),
        _mask(".#####.", "#######", ".#####.", ".#####."),
    ),
    "a27_h1683": (
        _mask("...#..", ".#####", ".#####", "######", ".#####", ".#####"),
        _mask("..#..", "#####", "#####", "#####", "#####", "#####", "..#.."),
    ),
    "a27_h1692": (
        _mask("..#...", ".#####", "######", ".#####", ".#####", ".#####"),
        _mask(".#...", "#####", "#####", "#####", "#####", "#####", "..#.."),
    ),
    "a36_h181161": (
        _mask("####...", ".#####.", "######.", "#######", "######.", ".#####.", "..###.."),
        _mask("...###.", "..#####", "#######", "#######", "#######", ".####..", "..###.."),
    ),
    "a36_h191151": (
        _mask("...##..", ".####..", ".######", "#######", ".######", "#######", ".####.."),
        _mask(".#####.", ".######", ".######", "#######", "#######", "..###.#", "...#..."),
    ),
}

_AREA_SIBLING = {
    "a11_h83": "a11_h92",
    "a11_h92": "a11_h83",
    "a17_h125": "a17_h134",
    "a17_h134": "a17_h125",
    "a22_h1471": "a22_h148",
    "a22_h148": "a22_h1471",
    "a27_h1683": "a27_h1692",
    "a27_h1692": "a27_h1683",
    "a36_h181161": "a36_h191151",
    "a36_h191151": "a36_h181161",
}

_EASY_FAMILIES = (
    "a11_h83", "a11_h92", "a17_h125", "a17_h134", "a22_h148"
)
_MEDIUM_FAMILIES = tuple(_SHAPE_FAMILIES)
_HARD_FAMILIES = (
    "a22_h1471", "a22_h148", "a27_h1683", "a27_h1692",
    "a36_h181161", "a36_h191151",
)


def _normalize(cells) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        return cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _transform(cells, turns: int, reflected: bool) -> frozenset[tuple[int, int]]:
    out = set(cells)
    if reflected:
        out = {(r, -c) for r, c in out}
    for _ in range(turns % 4):
        out = {(c, -r) for r, c in out}
    return _normalize(out)


def _dims(cells) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _components(cells) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        found.append(component)
    return found


def _onion_hist(cells) -> tuple[int, ...]:
    counts: Counter[int] = Counter()
    for component in _components(cells):
        current = set(component)
        depth = 1
        while current:
            boundary = {
                cell
                for cell in current
                if any(
                    (cell[0] + dr, cell[1] + dc) not in current
                    for dr, dc in _CARD
                )
            }
            counts[depth] += len(boundary)
            current -= boundary
            depth += 1
    return tuple(counts[d] for d in range(1, max(counts, default=0) + 1))


_FAMILY_HIST = {
    name: _onion_hist(variants[0]) for name, variants in _SHAPE_FAMILIES.items()
}
_HIST_TO_FAMILY = {}
for _family_name, _base_hist in _FAMILY_HIST.items():
    _HIST_TO_FAMILY[_base_hist] = _family_name
    _satellite_hist = (_base_hist[0] + 1, *_base_hist[1:])
    _HIST_TO_FAMILY[_satellite_hist] = _family_name
assert len(_HIST_TO_FAMILY) == 2 * len(_FAMILY_HIST)
for _name, _variants in _SHAPE_FAMILIES.items():
    assert len(_variants) >= 2
    assert len({_onion_hist(mask) for mask in _variants}) == 1
    assert len({_normalize(mask) for mask in _variants}) == len(_variants)
    assert all(_dims(mask)[0] <= 7 and _dims(mask)[1] <= 7 for mask in _variants)


def _assemble(panels: list[list[list[int]]]) -> list[list[int]]:
    panel_h = len(panels[0])
    panel_w = len(panels[0][0])
    total_w = len(panels) * panel_w + (len(panels) - 1)
    grid = full_grid(panel_h, total_w, 0)
    col = 0
    for index, panel in enumerate(panels):
        for r in range(panel_h):
            grid[r][col : col + panel_w] = list(panel[r])
        col += panel_w
        if index + 1 < len(panels):
            for r in range(panel_h):
                grid[r][col] = 9
            col += 1
    return grid


def _place_shape(panel, cells, color: int, rng) -> set[tuple[int, int]]:
    shape_h, shape_w = _dims(cells)
    panel_h = len(panel)
    panel_w = len(panel[0])
    top = rng.randint(1, panel_h - shape_h - 1)
    left = rng.randint(1, panel_w - shape_w - 1)
    placed = {(top + r, left + c) for r, c in cells}
    for r, c in placed:
        panel[r][c] = color
    return placed


def _add_satellite(panel, occupied: set[tuple[int, int]], accent_color: int, rng) -> None:
    """Add one accent-colored depth-1 cell without changing the main component."""
    panel_h = len(panel)
    panel_w = len(panel[0])
    candidates = [
        (r, c)
        for r in range(1, panel_h - 1)
        for c in range(1, panel_w - 1)
        if (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in _CARD)
    ]
    if not candidates:
        raise ValueError("no legal isolated satellite position")
    r, c = rng.choice(candidates)
    panel[r][c] = accent_color


def _incompatible(*axes: str, detail: str) -> None:
    exc = ValueError(detail)
    exc.incompatible_axes = tuple(axes)
    raise exc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    n_protos = 2
    match_index = ctx.draw_choice("match_index", (0, 1, 1, 1))

    family_pool = (
        _EASY_FAMILIES if difficulty == "easy"
        else _HARD_FAMILIES if difficulty == "hard"
        else _MEDIUM_FAMILIES
    )
    # The full catalog is passed whenever the caller supplies an override, so
    # every declared target_family remains exactly realizable in every band.
    family_options = tuple(_SHAPE_FAMILIES) if "target_family" in overrides else family_pool
    target_family = ctx.draw_choice("target_family", family_options)
    shape_color = ctx.draw_color("shape_color", exclude={0, 9})

    rng = ctx.draw_rng("layout")
    sibling_family = _AREA_SIBLING[target_family]
    sibling_index = match_index - 1 if match_index > 0 else 1

    assigned: list[str | None] = [None] * n_protos
    assigned[match_index] = target_family
    assigned[sibling_index] = sibling_family

    used_hists = {_FAMILY_HIST[target_family], _FAMILY_HIST[sibling_family]}
    remaining_families = [
        name for name in _SHAPE_FAMILIES
        if _FAMILY_HIST[name] not in used_hists
    ]
    rng.shuffle(remaining_families)
    for index in range(n_protos):
        if assigned[index] is None:
            chosen = remaining_families.pop()
            assigned[index] = chosen
            used_hists.add(_FAMILY_HIST[chosen])
            remaining_families = [
                name for name in remaining_families
                if _FAMILY_HIST[name] not in used_hists
            ]

    keys = rng.sample([color for color in range(1, 9) if color != shape_color], n_protos)
    accent_color = rng.choice(
        [color for color in range(1, 9) if color not in {shape_color, *keys}]
    )
    panels: list[list[list[int]]] = []
    target_variant = None
    target_transform = None
    for index, family in enumerate(assigned):
        assert family is not None
        panel = full_grid(_GENERATED_PANEL_H, _PANEL_W, 0)
        panel[0][0] = keys[index]
        variants = _SHAPE_FAMILIES[family]
        variant_index = rng.randrange(len(variants))
        turns = rng.randrange(4)
        reflected = bool(rng.randrange(2))
        cells = _transform(variants[variant_index], turns, reflected)
        if index == match_index:
            target_variant = variant_index
            target_transform = (turns, reflected)
        placed = _place_shape(panel, cells, shape_color, rng)
        _add_satellite(panel, placed, accent_color, rng)
        panels.append(panel)

    # The query uses the other non-dihedrally-equivalent member of the same
    # histogram family.  Independent transform/translation keep position and
    # orientation from becoming accidental answer keys.
    assert target_variant is not None and target_transform is not None
    target_variants = _SHAPE_FAMILIES[target_family]
    query_variant = (target_variant + 1) % len(target_variants)
    query_cells = _transform(
        target_variants[query_variant], rng.randrange(4), bool(rng.randrange(2))
    )
    query_panel = full_grid(_GENERATED_PANEL_H, _PANEL_W, 0)
    query_placed = _place_shape(query_panel, query_cells, shape_color, rng)
    _add_satellite(query_panel, query_placed, accent_color, rng)
    panels.append(query_panel)

    grid = _assemble(panels)
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError(f"internal generator error: {errors}")
    return grid


def _is_arc_grid(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _extract_panels(grid) -> tuple[list[list[list[int]]], list[int]]:
    if not _is_arc_grid(grid):
        return [], []
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    panels = []
    start = 0
    for divider in dividers + [w]:
        if divider > start:
            panels.append([row[start:divider] for row in grid])
        start = divider + 1
    return panels, dividers


def _panel_shape(panel, *, keyed: bool) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9) and not (keyed and (r, c) == (0, 0))
    )


def _parsed(grid):
    panels, dividers = _extract_panels(grid)
    if len(panels) < 2:
        return None
    prototypes = panels[:-1]
    query = panels[-1]
    proto_shapes = [_panel_shape(panel, keyed=True) for panel in prototypes]
    query_shape = _panel_shape(query, keyed=False)
    keys = [panel[0][0] if panel and panel[0] else 0 for panel in prototypes]
    proto_hists = [_onion_hist(shape) for shape in proto_shapes]
    query_hist = _onion_hist(query_shape)
    matches = [i for i, hist in enumerate(proto_hists) if hist == query_hist]
    return {
        "panels": panels,
        "dividers": dividers,
        "prototypes": prototypes,
        "query": query,
        "proto_shapes": proto_shapes,
        "query_shape": query_shape,
        "keys": keys,
        "proto_hists": proto_hists,
        "query_hist": query_hist,
        "matches": matches,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed strips and every scene that hides the histogram rule."""
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]

    h, w = len(grid), len(grid[0])
    errors = []
    if not (9 <= h <= 14):
        errors.append(f"grid height must be in 9..14, got {h}")

    parsed = _parsed(grid)
    if parsed is None:
        return errors + ["could not extract prototype/query panels"]
    panels = parsed["panels"]
    dividers = parsed["dividers"]
    prototypes = parsed["prototypes"]
    query = parsed["query"]

    if not (3 <= len(panels) <= 5):
        errors.append(f"expected 2..4 prototypes plus query, found {len(panels)} panels")
    if len(dividers) != len(panels) - 1:
        errors.append("panel separators must be exactly the full-height color-9 columns")
    if any(b - a == 1 for a, b in zip(dividers, dividers[1:])):
        errors.append("adjacent divider columns are not allowed")
    widths = [len(panel[0]) if panel and panel[0] else 0 for panel in panels]
    if any(width != _PANEL_W for width in widths):
        errors.append(f"all panels must be {_PANEL_W} columns wide, got {widths}")
    expected_w = len(panels) * _PANEL_W + len(panels) - 1
    if w != expected_w:
        errors.append(f"grid width {w} inconsistent with {len(panels)} 9x9 panels")
    if any(value == 9 for panel in panels for row in panel for value in row):
        errors.append("color 9 may occur only in separator columns")

    keys = parsed["keys"]
    if any(key not in range(1, 9) for key in keys):
        errors.append(f"prototype keys must be colors 1..8 at (0,0), got {keys}")
    if len(set(keys)) != len(keys):
        errors.append("prototype keys must be distinct")
    if query and query[0][0] != 0:
        errors.append("query panel must not carry a key at (0,0)")

    all_shapes = parsed["proto_shapes"] + [parsed["query_shape"]]
    shape_colors = []
    satellite_colors = []
    component_counts = []
    for index, (panel, shape) in enumerate(zip(panels, all_shapes)):
        label = f"prototype {index}" if index < len(prototypes) else "query"
        if not shape:
            errors.append(f"{label} shape is empty")
            continue
        components = sorted(_components(shape), key=lambda component: (-len(component), min(component)))
        component_counts.append(len(components))
        component_sizes = sorted(len(component) for component in components)
        if len(components) not in (1, 2):
            errors.append(f"{label} must have one main component and at most one satellite")
        elif len(components) == 2 and component_sizes[0] != 1:
            errors.append(f"{label} second component must be one isolated cell, got {component_sizes}")
        outside = sorted(
            (r, c) for r, c in shape
            if not (1 <= r <= h - 2 and 1 <= c <= _PANEL_W - 2)
        )
        if outside:
            errors.append(f"{label} shape leaves the one-cell panel margin: {outside[:4]}")
        if not (8 <= len(shape) <= 49):
            errors.append(f"{label} shape area {len(shape)} outside 8..49")
        main = components[0] if components else set()
        main_colors = {panel[r][c] for r, c in main}
        if len(main_colors) != 1 or next(iter(main_colors), 0) not in range(1, 9):
            errors.append(
                f"{label} main component must be monochrome in colors 1..8, "
                f"got {sorted(main_colors)}"
            )
        else:
            shape_colors.append(next(iter(main_colors)))
        if len(components) == 2:
            satellite = next(iter(components[1]))
            satellite_color = panel[satellite[0]][satellite[1]]
            if satellite_color not in range(1, 9):
                errors.append(f"{label} satellite color must be in 1..8, got {satellite_color}")
            elif main_colors and satellite_color == next(iter(main_colors)):
                errors.append(f"{label} satellite must use an accent color distinct from the main shape")
            else:
                satellite_colors.append(satellite_color)
        stray_top = [
            (r, c, panel[r][c])
            for r, row in enumerate(panel)
            for c, value in enumerate(row)
            if value not in (0, 9)
            and (r, c) not in shape
            and not (index < len(prototypes) and (r, c) == (0, 0))
        ]
        if stray_top:
            errors.append(f"{label} has non-shape marker cells: {stray_top[:4]}")

    if component_counts and len(set(component_counts)) != 1:
        errors.append(f"all panels must use the same component profile, got {component_counts}")
    if shape_colors and len(set(shape_colors)) != 1:
        errors.append(f"all main shapes must share one color, got {sorted(set(shape_colors))}")
    if satellite_colors and len(set(satellite_colors)) != 1:
        errors.append(f"all satellites must share one accent color, got {sorted(set(satellite_colors))}")

    proto_hists = parsed["proto_hists"]
    query_hist = parsed["query_hist"]
    if any(not hist for hist in proto_hists) or not query_hist:
        errors.append("every panel must have a nonempty onion histogram")
    if len(set(proto_hists)) != len(proto_hists):
        errors.append(f"prototype onion histograms must be distinct, got {proto_hists}")
    if len(parsed["matches"]) != 1:
        errors.append(
            f"query histogram {query_hist} must match exactly one prototype; "
            f"matched indices {parsed['matches']}"
        )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared semantic axis from the returned grid."""
    if self_check(grid):
        return {}
    parsed = _parsed(grid)
    assert parsed is not None and len(parsed["matches"]) == 1
    query_panel = parsed["query"]
    color_counts = Counter(
        query_panel[r][c] for r, c in parsed["query_shape"]
    )
    shape_color = color_counts.most_common(1)[0][0]
    observed: dict[str, int | str] = {
        "match_index": parsed["matches"][0],
        "shape_color": shape_color,
    }
    family = _HIST_TO_FAMILY.get(parsed["query_hist"])
    if family is not None:
        observed["target_family"] = family
    return observed


def strict_canonical_like(grid) -> list[str]:
    """Accept canonical-scale keyed panel strips, including the 9x39 source."""
    errors = self_check(grid)
    if errors:
        return errors
    parsed = _parsed(grid)
    assert parsed is not None
    reasons = []
    area = len(grid) * len(grid[0])
    if not (300 <= area <= 420):
        reasons.append(f"canonical-scale canvas area is 300..420, got {area}")
    if len(parsed["prototypes"]) not in (2, 3):
        reasons.append(f"canonical-scale profile uses 2 or 3 prototypes, got {len(parsed['prototypes'])}")
    return reasons


def canonical_like(grid) -> bool:
    """Boolean alias used by the standalone linked-census tool."""
    return strict_canonical_like(grid) == []


def _solve_histogram(grid) -> list[list[int]]:
    parsed = _parsed(grid)
    if parsed is None or len(parsed["matches"]) != 1:
        return [[0]]
    return [[parsed["keys"][parsed["matches"][0]]]]


def _solve_exact_mask(grid) -> list[list[int]]:
    parsed = _parsed(grid)
    if parsed is None:
        return [[0]]
    query = _normalize(parsed["query_shape"])
    for key, shape in zip(parsed["keys"], parsed["proto_shapes"]):
        if _normalize(shape) == query:
            return [[key]]
    return [[0]]


def _solve_area_only(grid) -> list[list[int]]:
    parsed = _parsed(grid)
    if parsed is None:
        return [[0]]
    area = len(parsed["query_shape"])
    for key, shape in zip(parsed["keys"], parsed["proto_shapes"]):
        if len(shape) == area:
            return [[key]]
    return [[0]]


def _solve_max_depth_only(grid) -> list[list[int]]:
    parsed = _parsed(grid)
    if parsed is None:
        return [[0]]
    depth = len(parsed["query_hist"])
    for key, hist in zip(parsed["keys"], parsed["proto_hists"]):
        if len(hist) == depth:
            return [[key]]
    return [[0]]


def _solve_first_proto(grid) -> list[list[int]]:
    parsed = _parsed(grid)
    if parsed is None or not parsed["keys"]:
        return [[0]]
    return [[parsed["keys"][0]]]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "exact_mask": _solve_exact_mask,
    "area_only": _solve_area_only,
    "max_depth_only": _solve_max_depth_only,
    "first_proto_key": _solve_first_proto,
}
CANONICAL_SHORTCUTS = {
    "exact_mask": _solve_exact_mask,
    "area_only": _solve_area_only,
}
LESSON_COMPETITORS = {
    "exact_mask": _solve_exact_mask,
    "area_only": _solve_area_only,
    "first_proto_key": _solve_first_proto,
}


def _witness_histogram_not_exact(grid) -> bool:
    parsed = _parsed(grid)
    if parsed is None or len(parsed["matches"]) != 1:
        return False
    target = parsed["proto_shapes"][parsed["matches"][0]]
    return (
        parsed["query_hist"] == _onion_hist(target)
        and _normalize(parsed["query_shape"]) != _normalize(target)
        and _solve_exact_mask(grid) != _solve_histogram(grid)
    )


def _witness_area_collision(grid) -> bool:
    return _solve_area_only(grid) != _solve_histogram(grid)


def _witness_depth_collision(grid) -> bool:
    return _solve_max_depth_only(grid) != _solve_histogram(grid)


def _witness_match_not_first(grid) -> bool:
    return _solve_first_proto(grid) != _solve_histogram(grid)


def _witness_four_layers(grid) -> bool:
    parsed = _parsed(grid)
    return bool(parsed and len(parsed["query_hist"]) >= 4)


SEMANTIC_WITNESSES = {
    "histogram_match_not_exact_mask": _witness_histogram_not_exact,
    "same_area_wrong_histogram_precedes_target": _witness_area_collision,
    "same_depth_wrong_histogram_precedes_target": _witness_depth_collision,
    "matching_key_not_first": _witness_match_not_first,
}
WITNESS_RIVALS = {
    "histogram_match_not_exact_mask": ["exact_mask"],
    "same_area_wrong_histogram_precedes_target": ["area_only"],
    "same_depth_wrong_histogram_precedes_target": ["max_depth_only"],
    "matching_key_not_first": ["first_proto_key"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every rival that changes the query."""
    reasons = []
    if not isinstance(query, dict) or self_check(query.get("input")):
        return ["query input is not a lawful keyed histogram scene"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or self_check(demo.get("input")):
            reasons.append(f"demo {index} input is not a lawful keyed histogram scene")
    if reasons:
        return reasons

    true_query = query.get("output", _solve_histogram(query["input"]))
    for name, competitor in LESSON_COMPETITORS.items():
        if competitor(query["input"]) == true_query:
            continue
        refuted = any(
            competitor(demo["input"]) != demo.get("output", _solve_histogram(demo["input"]))
            for demo in demos
        )
        if not refuted:
            reasons.append(
                f"query distinguishes {name!r}, but no demonstration refutes that rival"
            )
    return reasons
