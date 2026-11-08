"""Generator for ARC task e91a8e375e64: infer a transform and a recolor map.

Each input is five P x P panels separated by color-5 columns::

    A | B | C | D | Q

A -> B teaches one of the eight square dihedral transforms.  C -> D teaches a
cellwise color mapping without moving cells.  The answer is that transform
applied to Q followed by the inferred recoloring.

Version 3 exposes only exact, grid-observable controls (``panel_size`` and
``n_map``).  Former density/texture aliases were not recoverable from a grid and
were silently ignored, so their useful variation is now an internal cyclic
curriculum: canonical, varied, wide-map, and big-panel lessons.  Every generated
query covers every demonstrated source color and is asymmetric, making both the
geometric and recoloring operations visibly necessary in every example.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e91a8e375e64"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "af51be6e4b66"

SUMMARY = (
    "Five square panels A|B|C|D|Q are separated by color-5 columns. B is a "
    "uniquely identifiable dihedral transform of A; D is a consistent recolor "
    "of C; apply both operations to Q. Every query uses every map key and is "
    "asymmetric, so neither operation can be skipped."
)
INVARIANTS = [
    "five P x P panels at columns i*(P+1), with total width 5P+4",
    "the four separator columns are entirely color 5",
    "A and Q have eight distinct dihedral images",
    "B is a non-identity dihedral transform of A",
    "C and D have identical support and define an injective non-identity recolor map",
    "A, C, and Q use exactly every source color in that map",
]

AXES = {
    "panel_size": {"type": "int", "default": "scheduled", "valid": "3..5"},
    "n_map": {"type": "int", "default": "scheduled", "valid": "2..4"},
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "varied", "wide_map", "big_panel")
MIN_STRICT_FRAC = 1.0

_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)  # 0 background; 5 separator
_AXIS_RANGES = {"panel_size": (3, 5), "n_map": (2, 4)}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _identity(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in matrix]


def _rot_cw(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix[::-1])]


def _rot180(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(matrix)]


def _rot_ccw(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix)][::-1]


def _flip_lr(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in matrix]


def _flip_ud(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(matrix)]


def _transpose(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*matrix)]


def _anti(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    return _rot180(_transpose(matrix))


_TRANSFORMS: tuple[Callable[[Sequence[Sequence[int]]], list[list[int]]], ...] = (
    _identity,
    _rot_cw,
    _rot180,
    _rot_ccw,
    _flip_lr,
    _flip_ud,
    _transpose,
    _anti,
)


def _freeze(matrix: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in matrix)


def _all_dihedral_images_distinct(matrix: Sequence[Sequence[int]]) -> bool:
    return len({_freeze(transform(matrix)) for transform in _TRANSFORMS}) == 8


def _validate_call(seed, sample_index, difficulty, overrides: dict) -> dict[str, int]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard or None")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(unknown))

    clean: dict[str, int] = {}
    for name, value in overrides.items():
        lo, hi = _AXIS_RANGES[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
        clean[name] = value
    return clean


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _axis_defaults(ctx, profile: str, band: str) -> tuple[int, int]:
    rng = ctx.draw_rng("axis-defaults")
    if profile == "canonical":
        return 4, 2
    if profile == "wide_map":
        return (4 if band in ("easy", "medium") else 5), 4
    if profile == "big_panel":
        return 5, 3

    # The varied slot carries the remaining difficulty prior.  Every explicit
    # declared value remains legal in every band; only defaults differ.
    panel_choices = {
        "easy": (3, 3, 4),
        "medium": (3, 4, 4, 5),
        "hard": (4, 5, 5),
    }[band]
    map_choices = {
        "easy": (2, 2, 3),
        "medium": (2, 3, 3),
        "hard": (3, 3, 4),
    }[band]
    return rng.choice(panel_choices), rng.choice(map_choices)


def _resolved_axes(ctx, clean: dict[str, int], profile: str, band: str) -> tuple[int, int]:
    default_panel, default_map = _axis_defaults(ctx, profile, band)
    panel_size = clean.get("panel_size", default_panel)
    n_map = clean.get("n_map", default_map)

    # Fixed draws preserve exact overrides while recording provenance through
    # GenCtx for the shared override checker.
    panel_size = ctx.draw_int("panel_size", panel_size, panel_size)
    n_map = ctx.draw_int("n_map", n_map, n_map)
    return panel_size, n_map


def _candidate_positions(side: int, profile: str) -> list[tuple[int, int]]:
    positions = [(row, col) for row in range(side) for col in range(side)]
    if profile == "canonical":
        # Match the sparse public grammar: the bottom row is unused before the
        # geometric transform, while still leaving at least six cells at P=3.
        positions = [(row, col) for row, col in positions if row < side - 1]
    return positions


def _panel_covering(
    rng,
    side: int,
    colors: Sequence[int],
    density: float,
    profile: str,
    *,
    asymmetric: bool,
) -> list[list[int]]:
    colors = tuple(colors)
    positions = _candidate_positions(side, profile)
    minimum = max(3, len(colors))
    if len(positions) < minimum:
        raise ValueError("panel profile has too few usable cells")

    for _ in range(256):
        panel = full_grid(side, side, 0)
        shuffled = positions[:]
        rng.shuffle(shuffled)

        # Cover every requested color first; remaining cells control density.
        for color, (row, col) in zip(colors, shuffled):
            panel[row][col] = color
        for row, col in shuffled[len(colors):]:
            if rng.random() < density:
                panel[row][col] = rng.choice(colors)

        # Distinct profile geometry survives even when public axes are fixed.
        if profile == "canonical":
            panel[0][0] = colors[0]
            panel[0][1] = colors[-1]
            panel[1][0] = colors[0]
        elif profile == "wide_map":
            for index, color in enumerate(colors):
                panel[index % side][(2 * index + 1) % side] = color
        elif profile == "big_panel":
            panel[0][0] = colors[0]
            panel[0][side - 1] = colors[-1]
            panel[side - 1][1] = colors[0]

        present = {value for row in panel for value in row if value != 0}
        occupied = sum(value != 0 for row in panel for value in row)
        if present != set(colors) or occupied < minimum:
            continue
        if asymmetric and not _all_dihedral_images_distinct(panel):
            continue
        return panel
    raise ValueError("could not construct a color-covering asymmetric panel")


def _canonical_panel(colors: Sequence[int], *, query: bool = False) -> list[list[int]]:
    """Public-scale two-color pattern with exactly three 4-connected objects."""
    first, second = colors
    if query:
        return [
            [first, second, 0, 0],
            [first, 0, second, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    return [
        [first, second, 0, 0],
        [first, 0, 0, 0],
        [first, second, second, 0],
        [0, 0, 0, 0],
    ]


def _assemble(panels: Sequence[Sequence[Sequence[int]]], side: int) -> list[list[int]]:
    grid = full_grid(side, 5 * side + 4, 0)
    for index, panel in enumerate(panels):
        left = index * (side + 1)
        for row in range(side):
            for col in range(side):
                grid[row][left + col] = panel[row][col]
        if index < 4:
            separator = left + side
            for row in range(side):
                grid[row][separator] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    clean = _validate_call(seed, sample_index, difficulty, overrides)
    band = difficulty or "medium"
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )
    side, n_map = _resolved_axes(ctx, clean, profile, band)
    rng = ctx.draw_rng("layout")

    density = {
        "canonical": 0.34,
        "varied": rng.choice((0.30, 0.42, 0.56, 0.68)),
        "wide_map": 0.55,
        "big_panel": 0.70,
    }[profile]

    # Disjoint source/target palettes make every map key visibly change while
    # keeping canonical n_map=2 examples at exactly six total colors.
    palette = rng.sample(list(_PALETTE), 2 * n_map)
    sources = tuple(palette[:n_map])
    targets = tuple(palette[n_map:])
    mapping = dict(zip(sources, targets))

    if profile == "canonical" and side == 4 and n_map == 2:
        # The public inputs have three components in each panel (18--19 total
        # once separators are counted).  Keep one scheduled slot on that exact
        # structural manifold rather than merely matching shape and palette.
        a_panel = _canonical_panel(sources)
        c_panel = _canonical_panel(sources)
        q_panel = _canonical_panel(sources, query=True)
    else:
        a_panel = _panel_covering(
            rng, side, sources, density, profile, asymmetric=True
        )
        c_panel = _panel_covering(
            rng, side, sources, density, profile, asymmetric=False
        )
        q_panel = _panel_covering(
            rng, side, sources, density, profile, asymmetric=True
        )

    transform = rng.choice(_TRANSFORMS[1:])
    b_panel = transform(a_panel)
    d_panel = [
        [mapping[value] if value else 0 for value in row]
        for row in c_panel
    ]
    return _assemble((a_panel, b_panel, c_panel, d_panel, q_panel), side)


def _shape_reasons(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]
    return []


def _split_panels(grid) -> tuple[list[list[list[int]]] | None, list[str]]:
    reasons = _shape_reasons(grid)
    if reasons:
        return None, reasons
    side = len(grid)
    width = len(grid[0])
    if not 3 <= side <= 5:
        return None, ["panel side must lie in 3..5"]
    if width != 5 * side + 4:
        return None, ["width must equal 5P+4"]

    panels: list[list[list[int]]] = []
    for index in range(5):
        left = index * (side + 1)
        panels.append([list(row[left:left + side]) for row in grid])
        if index < 4:
            separator = left + side
            if any(grid[row][separator] != 5 for row in range(side)):
                reasons.append(f"separator column {index} is not entirely color 5")
    return panels, reasons


def _infer_transform(a, b) -> tuple[int | None, list[int]]:
    matches = [index for index, transform in enumerate(_TRANSFORMS) if transform(a) == b]
    return (matches[0] if matches else None), matches


def _infer_mapping(c, d) -> tuple[dict[int, int], list[str]]:
    mapping: dict[int, int] = {}
    reasons: list[str] = []
    for row in range(len(c)):
        for col in range(len(c)):
            source, target = c[row][col], d[row][col]
            if (source == 0) != (target == 0):
                reasons.append("C and D supports differ")
                continue
            if source == 0:
                continue
            if source in mapping and mapping[source] != target:
                reasons.append("C-to-D recolor map is inconsistent")
            mapping[source] = target
    return mapping, reasons


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    panels, reasons = _split_panels(grid)
    if panels is None:
        return reasons
    a_panel, b_panel, c_panel, d_panel, q_panel = panels

    transform_index, matches = _infer_transform(a_panel, b_panel)
    if len(matches) != 1:
        reasons.append(f"A-to-B transform must be unique, found {len(matches)} matches")
    elif transform_index == 0:
        reasons.append("A-to-B transform must be non-identity")
    if not _all_dihedral_images_distinct(a_panel):
        reasons.append("A must have eight distinct dihedral images")

    mapping, mapping_reasons = _infer_mapping(c_panel, d_panel)
    reasons.extend(mapping_reasons)
    if not 2 <= len(mapping) <= 4:
        reasons.append(f"recolor map must contain 2..4 source colors, got {len(mapping)}")
    if any(source == target for source, target in mapping.items()):
        reasons.append("recolor map must not contain identity entries")
    if len(set(mapping.values())) != len(mapping):
        reasons.append("recolor map targets must be injective")
    if set(mapping) & set(mapping.values()):
        reasons.append("source and target palettes must be disjoint")

    a_colors = {value for row in a_panel for value in row if value != 0}
    q_colors = {value for row in q_panel for value in row if value != 0}
    if a_colors != set(mapping):
        reasons.append("A must use exactly all C-to-D source colors")
    if q_colors != set(mapping):
        reasons.append("Q must use exactly all C-to-D source colors")
    if not _all_dihedral_images_distinct(q_panel):
        reasons.append("Q must have eight distinct dihedral images")
    return reasons


def strict_canonical_like(grid):
    """Return diagnostics for grids outside the generator's strict task grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    panels, reasons = _split_panels(grid)
    if panels is None or reasons:
        raise ValueError("cannot observe overrides from an invalid panel layout")
    _, _, c_panel, _, _ = panels
    return {
        "panel_size": len(grid),
        "n_map": len({value for row in c_panel for value in row if value != 0}),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the authoritative Racket rule."""
    panels, reasons = _split_panels(grid)
    if panels is None or reasons:
        raise ValueError("invalid five-panel input: " + "; ".join(reasons))
    a_panel, b_panel, c_panel, d_panel, q_panel = panels
    transform_index, matches = _infer_transform(a_panel, b_panel)
    if not matches or transform_index is None:
        raise ValueError("cannot infer A-to-B transform")
    mapping, mapping_reasons = _infer_mapping(c_panel, d_panel)
    if mapping_reasons:
        raise ValueError("cannot infer C-to-D mapping: " + "; ".join(mapping_reasons))
    transformed = _TRANSFORMS[transform_index](q_panel)
    return [
        [mapping.get(value, value) if value else 0 for value in row]
        for row in transformed
    ]


def _recolor_only(grid) -> list[list[int]]:
    panels, reasons = _split_panels(grid)
    if panels is None or reasons:
        raise ValueError("invalid five-panel input")
    _, _, c_panel, d_panel, q_panel = panels
    mapping, mapping_reasons = _infer_mapping(c_panel, d_panel)
    if mapping_reasons:
        raise ValueError("invalid recolor demonstration")
    return [
        [mapping.get(value, value) if value else 0 for value in row]
        for row in q_panel
    ]


def _transform_only(grid) -> list[list[int]]:
    panels, reasons = _split_panels(grid)
    if panels is None or reasons:
        raise ValueError("invalid five-panel input")
    a_panel, b_panel, _, _, q_panel = panels
    transform_index, matches = _infer_transform(a_panel, b_panel)
    if not matches or transform_index is None:
        raise ValueError("invalid transform demonstration")
    return _TRANSFORMS[transform_index](q_panel)


def _unchanged_query(grid) -> list[list[int]]:
    panels, reasons = _split_panels(grid)
    if panels is None or reasons:
        raise ValueError("invalid five-panel input")
    return [row[:] for row in panels[4]]


def _transformation_is_required(grid) -> bool:
    return _recolor_only(grid) != rule_mirror(grid)


def _recolor_is_required(grid) -> bool:
    return _transform_only(grid) != rule_mirror(grid)


def _both_operations_are_required(grid) -> bool:
    return _unchanged_query(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "recolor_only": _recolor_only,
    "transform_only": _transform_only,
    "unchanged_query": _unchanged_query,
}
SEMANTIC_WITNESSES = {
    "transformation_is_required": _transformation_is_required,
    "recolor_is_required": _recolor_is_required,
    "both_operations_are_required": _both_operations_are_required,
}
WITNESS_RIVALS = {
    "transformation_is_required": ["recolor_only"],
    "recolor_is_required": ["transform_only"],
    "both_operations_are_required": ["unchanged_query"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    query_output = query.get("output")
    if query_output is None:
        query_output = rule_mirror(query["input"])
    return [
        f"{name} fits every demo and disagrees on the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query_output
    ]
