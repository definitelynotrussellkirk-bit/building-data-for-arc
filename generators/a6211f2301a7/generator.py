"""Input sampler for ``Crop And Rotate Right`` (bank task E40).

The unchanged authority tightly crops every nonzero cell and rotates that crop
90 degrees clockwise.  This sampler preserves the canonical zero background,
interior padding, small multicolour motifs, and especially the canonical
multi-component structure.  It also emits tall crops, the missing branch needed
to distinguish an unconditional clockwise turn from a plausible "make it
portrait" shortcut.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a6211f2301a7"
TASK_ID = GENERATOR_ID
RULE_HASH = "aad722fb766b"
VERSION = "2.0.0"
SUMMARY = (
    "A padded 1-3 colour motif with 1-3 components is cropped to its nonzero "
    "bounding box and rotated 90 degrees clockwise."
)

INVARIANTS = [
    "the background is 0 and every motif has at least one zero border cell of padding",
    "the tight motif box is 2..4 by 2..4 with 3..8 nonzero cells",
    "the motif has 1..3 four-connected components and 1..3 nonzero colours",
    "clockwise rotation changes the tight crop; identity lessons are excluded",
]

ORIENTATIONS = ("wide", "tall", "square")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors plus difficulty-weighted 7..13",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus difficulty-weighted 7..13",
        "valid": "7..13",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical anchors plus weighted 1..3",
        "valid": "1..3",
    },
    "bbox_orientation": {
        "type": "str",
        "default": "canonical wide/square anchors plus broad wide|tall|square",
        "valid": "wide|tall|square",
    },
    "component_count": {
        "type": "int",
        "default": "canonical anchors use 2; broad draws cover 1..3",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# (grid_h, grid_w, nonzero colours, bbox orientation, components,
#  preferred bbox_h, preferred bbox_w, preferred cell count)
# These reproduce all five exact canonical (h, w, palette-size) profiles and
# their observed two-component morphology without replaying fixed examples.
_CANONICAL_ANCHORS = (
    (8, 9, 3, "wide", 2, 2, 3, 3),
    (9, 8, 3, "wide", 2, 2, 3, 4),
    (7, 10, 1, "square", 2, 3, 3, 4),
    (8, 8, 2, "square", 2, 3, 3, 6),
    (9, 9, 3, "wide", 2, 3, 4, 6),
)
SCHEDULE_PROFILES = tuple(
    [f"canonical_{index}" for index in range(len(_CANONICAL_ANCHORS))] + ["broad"]
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic 50/50 anchor/broad curriculum schedule."""
    del seed, difficulty
    if sample_index % 2 == 0:
        return f"canonical_{(sample_index // 2) % len(_CANONICAL_ANCHORS)}"
    return "broad"


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    for name, lo, hi in (
        ("grid_h", 7, 13),
        ("grid_w", 7, 13),
        ("n_colors", 1, 3),
        ("component_count", 1, 3),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    if "bbox_orientation" in overrides and overrides["bbox_orientation"] is not None:
        value = overrides["bbox_orientation"]
        if type(value) is not str or value not in ORIENTATIONS:
            raise ValueError(
                "bbox_orientation must be one of " + ", ".join(ORIENTATIONS)
            )


def _axis_choice(ctx, name, *, anchor=None, broad):
    """Draw one exact axis while keeping every advertised override legal."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        options = list(dict.fromkeys(broad))
    elif anchor is not None:
        options = [anchor]
    else:
        options = list(broad)
    return ctx.draw_choice(name, options)


def _weighted_values(values, favored, weight=4):
    values = list(values)
    return values + [value for value in favored for _ in range(weight)]


def _broad_dimension_values(difficulty):
    if difficulty == "easy":
        favored = (7, 8, 9)
    elif difficulty == "hard":
        favored = (10, 11, 12, 13)
    else:
        favored = (8, 9, 10, 11)
    return _weighted_values(range(7, 14), favored)


def _orientation_of(h, w):
    return "wide" if w > h else "tall" if h > w else "square"


def _component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return count


def _turned_mask(cells, h):
    return {(c, h - 1 - r) for r, c in cells}


@lru_cache(maxsize=1)
def _shape_catalog():
    """Finite shape bank keyed by orientation/components/bbox/area.

    Enumerating the at-most-4x4 masks once makes every advertised combination
    constructive without rejection loops or hidden incompatibilities.  Keys are
    selected before masks so combinatorially numerous 4x4 patterns do not drown
    out canonical 2x3 and 3x3 scales.
    """
    catalog = {}
    for h in range(2, 5):
        for w in range(2, 5):
            orientation = _orientation_of(h, w)
            universe = tuple((r, c) for r in range(h) for c in range(w))
            for size in range(3, min(8, len(universe)) + 1):
                key_prefix = (orientation, h, w, size)
                for picked in combinations(universe, size):
                    cells = frozenset(picked)
                    if not (
                        min(r for r, _ in cells) == 0
                        and max(r for r, _ in cells) == h - 1
                        and min(c for _, c in cells) == 0
                        and max(c for _, c in cells) == w - 1
                    ):
                        continue
                    components = _component_count(cells)
                    if components not in (1, 2, 3):
                        continue
                    if h == w and _turned_mask(cells, h) == set(cells):
                        continue
                    key = (key_prefix[0], components, h, w, size)
                    catalog.setdefault(key, []).append(tuple(sorted(cells)))
    frozen = {key: tuple(values) for key, values in catalog.items()}
    for orientation in ORIENTATIONS:
        for components in (1, 2, 3):
            if not any(
                key[0] == orientation and key[1] == components for key in frozen
            ):
                raise RuntimeError(
                    f"shape catalog has no {orientation}/{components}-component masks"
                )
    return frozen


def _select_shape(ctx, orientation, components, preferred=None):
    catalog = _shape_catalog()
    keys = sorted(
        key
        for key in catalog
        if key[0] == orientation and key[1] == components
    )
    if preferred is not None:
        ph, pw, size = preferred
        preferred_key = (orientation, components, ph, pw, size)
        if preferred_key in catalog:
            keys = [preferred_key]
    key = ctx.draw_rng("shape_profile").choice(keys)
    cells = ctx.draw_rng("shape_cells").choice(catalog[key])
    _, _, h, w, _ = key
    return h, w, cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    anchor = None
    if profile != "broad":
        anchor = _CANONICAL_ANCHORS[int(profile.rsplit("_", 1)[1])]

    broad_dims = _broad_dimension_values(difficulty)
    h = _axis_choice(
        ctx,
        "grid_h",
        anchor=anchor[0] if anchor else None,
        broad=broad_dims,
    )
    w = _axis_choice(
        ctx,
        "grid_w",
        anchor=anchor[1] if anchor else None,
        broad=broad_dims,
    )
    n_colors = _axis_choice(
        ctx,
        "n_colors",
        anchor=anchor[2] if anchor else None,
        broad=_weighted_values((1, 2, 3), (2, 3)),
    )
    orientation = _axis_choice(
        ctx,
        "bbox_orientation",
        # Every unforced broad draw is tall.  Since broad draws occupy every
        # odd index, every three consecutive defaults contains a concrete
        # counterexample to the canonical-fitting portrait-normalizer rival.
        anchor=anchor[3] if anchor else "tall",
        broad=("wide", "tall", "square"),
    )
    components = _axis_choice(
        ctx,
        "component_count",
        anchor=anchor[4] if anchor else None,
        broad=(1, 2, 2, 2, 3),
    )

    preferred = anchor[5:8] if anchor else None
    motif_h, motif_w, cells = _select_shape(
        ctx, orientation, components, preferred=preferred
    )
    if motif_h > h - 2 or motif_w > w - 2:
        # This cannot occur for the declared 7..13 canvases and 2..4 motifs.
        raise ValueError("motif does not fit with the required one-cell padding")

    colors = tuple(ctx.draw_distinct_colors("colors", n=n_colors, exclude=[0]))
    ordered_cells = list(cells)
    color_rng = ctx.draw_rng("cell_colors")
    color_rng.shuffle(ordered_cells)
    assignments = {}
    for index, cell in enumerate(ordered_cells):
        assignments[cell] = colors[index] if index < n_colors else color_rng.choice(colors)

    position_rng = ctx.draw_rng("motif_position")
    top = position_rng.randint(1, h - motif_h - 1)
    left = position_rng.randint(1, w - motif_w - 1)
    grid = full_grid(h, w, 0)
    for (r, c), color in assignments.items():
        grid[top + r][left + c] = color
    return grid


def _validated_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cells must be integer ARC colours 0..9"]
    return [list(row) for row in grid], []


def _tight_content(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _turn_right(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _analysis(grid):
    crop = _tight_content(grid)
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len({value for row in grid for value in row if value}),
        "bbox_orientation": _orientation_of(len(crop), len(crop[0])),
        "component_count": _component_count(cells),
        "cell_count": len(cells),
        "bbox_h": len(crop),
        "bbox_w": len(crop[0]),
        "crop": crop,
    }


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    normalized, errors = _validated_grid(grid)
    if errors:
        raise ValueError(errors[0])
    if not any(value for row in normalized for value in row):
        raise ValueError("cannot observe axes from an empty motif")
    stats = _analysis(normalized)
    return {name: stats[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    normalized, errors = _validated_grid(grid)
    if errors:
        return errors
    h, w = len(normalized), len(normalized[0])
    findings = []
    if not (7 <= h <= 13 and 7 <= w <= 13):
        findings.append(f"grid dimensions {h}x{w} outside 7..13")
    if any(normalized[0]) or any(normalized[-1]) or any(
        row[0] or row[-1] for row in normalized
    ):
        findings.append("motif must have at least one zero cell of border padding")
    if not any(value for row in normalized for value in row):
        findings.append("motif is empty")
        return findings

    stats = _analysis(normalized)
    if not (2 <= stats["bbox_h"] <= 4 and 2 <= stats["bbox_w"] <= 4):
        findings.append(
            f"tight bbox {stats['bbox_h']}x{stats['bbox_w']} must be 2..4 by 2..4"
        )
    if not 3 <= stats["cell_count"] <= 8:
        findings.append(f"motif cell count {stats['cell_count']} outside 3..8")
    if not 1 <= stats["n_colors"] <= 3:
        findings.append(f"nonzero colour count {stats['n_colors']} outside 1..3")
    if not 1 <= stats["component_count"] <= 3:
        findings.append(
            f"four-connected component count {stats['component_count']} outside 1..3"
        )
    if _turn_right(stats["crop"]) == stats["crop"]:
        findings.append("clockwise rotation is an identity on the tight crop")
    return findings


def strict_canonical_like(grid):
    """Generated and canonical lessons inside this sampler's declared manifold."""
    return self_check(grid)


def _is_tall_bbox(grid):
    crop = _tight_content(grid)
    return bool(crop) and len(crop) > len(crop[0])


def _portrait_normalizer(grid):
    """RIVAL: rotate wide/square crops, but leave already-tall crops unchanged."""
    crop = _tight_content(grid)
    if not crop:
        return []
    return _turn_right(crop) if len(crop) <= len(crop[0]) else crop


SEMANTIC_WITNESSES = {"tall_bbox": _is_tall_bbox}
SEMANTIC_RIVALS = {"portrait_normalizer": _portrait_normalizer}
WITNESS_RIVALS = {"tall_bbox": ["portrait_normalizer"]}
CANONICAL_SHORTCUTS = {"portrait_normalizer": _portrait_normalizer}
LESSON_COMPETITORS = {"portrait_normalizer": _portrait_normalizer}
MIN_STRICT_FRAC = 0.90
