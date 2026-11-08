"""Generate sparse green wall networks containing sealed black regions.

The authoritative transformation is global and topological: black cells that
cannot reach a grid edge by 4-connectivity become yellow, while green walls and
edge-reachable black cells are preserved.  Generated scenes deliberately use
thin, often diagonally-connected wall fragments rather than rectangle icons.
They also contain open wall decoys whose bounding boxes contain exterior black
cells, so a learner must reason about reachability instead of visual boxes.
"""
from __future__ import annotations

from collections import deque
import hashlib
from typing import Any, Callable, NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ad5998ad11d6"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "2658bcc9cd0f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 250_000

SUMMARY = (
    "A sparse green (3) wall network partitions black (0) cells into one or "
    "more sealed 4-connected regions plus border-reachable exterior. Fill "
    "every sealed black region yellow (4), preserving all green walls and "
    "every exterior black cell. Open wall fragments and irregular holes make "
    "bounding-box, rectangle-only, and largest-hole shortcuts visibly wrong."
)

INVARIANTS = [
    "inputs use exactly black 0 and green 3; yellow 4 is output-only",
    "at least one black component is sealed from every grid edge",
    "at least one black component remains connected to a grid edge",
    "all sealed components are filled, including singleton and irregular ones",
    "open green fragments may surround exterior cells without sealing them",
]


class SceneSpec(NamedTuple):
    height: int
    width: int
    enclosed_regions: int


SCENE_SPECS = {
    "single_10x10": SceneSpec(10, 10, 1),
    "double_10x10": SceneSpec(10, 10, 2),
    "triple_10x10": SceneSpec(10, 10, 3),
    "five_20x20": SceneSpec(20, 20, 5),
    "eight_20x20": SceneSpec(20, 20, 8),
    "tiny_two_6x6": SceneSpec(6, 6, 2),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
# Interleave the two canonical 20x20 profiles so every cyclic window of three
# demonstrations contains a large-room example.  A seed-keyed rotation below
# prevents any fixed demo/query role from owning one profile forever.
SCHEDULE_PROFILES = (
    "single_10x10",
    "five_20x20",
    "double_10x10",
    "triple_10x10",
    "eight_20x20",
    "tiny_two_6x6",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index schedule over six canonical-scale profiles",
        "valid": (
            "single_10x10|double_10x10|triple_10x10|five_20x20|"
            "eight_20x20|tiny_two_6x6"
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]

# Connected black-region shapes.  The boundary painter converts their
# orthogonal neighbourhoods to green, reproducing the sparse diagonal wall
# geometry seen in the canonical examples.
_DOT: Shape = ((0, 0),)
_DOMINO: Shape = ((0, 0), (0, 1))
_L3: Shape = ((0, 0), (1, 0), (1, 1))
_Z4: Shape = ((0, 0), (0, 1), (1, 1), (1, 2))
_STAIR6: Shape = (
    (0, 0), (0, 1),
    (1, 1), (1, 2),
    (2, 2), (2, 3),
)
_BENT8: Shape = (
    (0, 0), (0, 1), (0, 2),
    (1, 0), (1, 1),
    (2, 0), (2, 1),
    (3, 0),
)
_STAIR12: Shape = (
    (0, 0), (0, 1), (0, 2),
    (1, 1), (1, 2), (1, 3),
    (2, 2), (2, 3), (2, 4),
    (3, 3), (3, 4), (3, 5),
)
_RECT_3X5: Shape = tuple((row, col) for row in range(3) for col in range(5))
_RECT_4X6: Shape = tuple((row, col) for row in range(4) for col in range(6))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Seed-rotate an interleaved profile cycle for every lesson.

    Every three consecutive examples contain a canonical-scale 20x20 case, but
    the seed rotation prevents a fixed demonstration/query role from revealing
    one profile across the whole corpus. Difficulty adds a reproducible band
    offset while retaining exact canonical (height, width, palette) profiles.
    """
    offset = {"easy": 0, "medium": 2, "hard": 4}.get(difficulty, 0)
    payload = f"{TASK_ID}|{VERSION}|profile-cycle|{int(seed)}".encode()
    seed_offset = int.from_bytes(hashlib.blake2s(payload, digest_size=2).digest(), "big")
    return SCHEDULE_PROFILES[
        (int(sample_index) + offset + seed_offset) % len(SCHEDULE_PROFILES)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task input with exact override provenance."""
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
    if "scene_profile" in overrides:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    spec = SCENE_SPECS[profile]
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "all"
    rng = ctx.draw_rng(f"geometry_{profile}_{band}")

    for _ in range(96):
        grid = _construct_scene(profile, rng)
        # A square-grid dihedral transform adds broad visual diversity without
        # changing any semantic signature.
        grid = _apply_square_transform(grid, rng.randrange(8))
        analysis = _analyze(grid)
        if (
            analysis["enclosed_regions"] == spec.enclosed_regions
            and not self_check(grid)
            and observe_overrides(grid).get("scene_profile") == profile
        ):
            return grid
    raise RuntimeError(f"unable to construct lawful scene profile {profile!r}")


def _construct_scene(profile: str, rng) -> Grid:
    spec = SCENE_SPECS[profile]
    grid = full_grid(spec.height, spec.width, 0)

    if profile == "tiny_two_6x6":
        # Two diagonal singleton holes share two wall pixels, exactly the
        # topology that makes diagonal-looking walls seal 4-connected regions.
        interiors = [{(2, 2)}, {(3, 3)}]
    elif profile == "single_10x10":
        interiors = [
            _fit_shape(rng.choice((_Z4, _STAIR6, _BENT8)), (2, 2, 7, 7), rng)
        ]
    elif profile == "double_10x10":
        interiors = [
            _fit_shape(rng.choice((_L3, _Z4)), (2, 2, 4, 4), rng),
            _fit_shape(_DOT, (7, 7, 7, 7), rng),
        ]
    elif profile == "triple_10x10":
        interiors = [
            _fit_shape(rng.choice((_L3, _Z4)), (2, 2, 4, 4), rng),
            _fit_shape(_DOT, (2, 7, 3, 8), rng),
            _fit_shape(rng.choice((_DOT, _DOMINO)), (7, 4, 8, 5), rng),
        ]
    else:
        # Canonical 20x20 examples include 15- and 24-cell rooms.  The earlier
        # distribution capped every generated room at eight cells, permitting
        # a size-cutoff shortcut and underrepresenting the canonical scale.
        large = _fit_shape(
            rng.choice((_STAIR12, _RECT_3X5, _RECT_4X6)),
            (2, 2, 6, 7),
            rng,
        )
        small_boxes = [
            (2, 11, 3, 12), (2, 16, 3, 17),
            (9, 2, 10, 3), (9, 8, 10, 9), (9, 14, 10, 15),
            (15, 2, 16, 3), (15, 8, 16, 9), (15, 14, 16, 15),
        ]
        rng.shuffle(small_boxes)
        count = 4 if profile == "five_20x20" else 7
        interiors = [large]
        for index, box in enumerate(small_boxes[:count]):
            # At least two singleton regions remain visible in every large
            # scene, while other rooms vary between dot, domino and L-shape.
            choices = (_DOT,) if index < 2 else (_DOT, _DOMINO, _L3)
            interiors.append(_fit_shape(rng.choice(choices), box, rng))

    _paint_boundaries(grid, interiors)
    _paint_open_bbox_decoy(grid, rng)
    _paint_border_texture(grid, rng)
    return grid


def _shape_variants(shape: Shape) -> tuple[Shape, ...]:
    points = list(shape)
    variants: set[Shape] = set()
    for reflect in (False, True):
        for turns in range(4):
            transformed: list[Cell] = []
            for row, col in points:
                x, y = row, -col if reflect else col
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            min_r = min(r for r, _ in transformed)
            min_c = min(c for _, c in transformed)
            variants.add(tuple(sorted((r - min_r, c - min_c) for r, c in transformed)))
    return tuple(sorted(variants))


def _fit_shape(shape: Shape, box: tuple[int, int, int, int], rng) -> set[Cell]:
    r1, c1, r2, c2 = box
    options = []
    for variant in _shape_variants(shape):
        vh = max(r for r, _ in variant) + 1
        vw = max(c for _, c in variant) + 1
        if vh <= r2 - r1 + 1 and vw <= c2 - c1 + 1:
            options.append((variant, vh, vw))
    if not options:
        raise ValueError(f"shape does not fit box {box}")
    variant, vh, vw = rng.choice(options)
    top = rng.randint(r1, r2 - vh + 1)
    left = rng.randint(c1, c2 - vw + 1)
    return {(top + r, left + c) for r, c in variant}


def _paint_boundaries(grid: Grid, interiors: list[set[Cell]]) -> None:
    all_interior = set().union(*interiors)
    boundary: set[Cell] = set()
    h, w = len(grid), len(grid[0])
    for row, col in all_interior:
        for nr, nc in _neighbors4((row, col)):
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in all_interior:
                boundary.add((nr, nc))
    for row, col in boundary:
        grid[row][col] = 3


def _paint_open_bbox_decoy(grid: Grid, rng) -> None:
    """Paint an open corner whose bbox contains edge-reachable black cells."""
    h, w = len(grid), len(grid[0])
    corners = (
        ((0, 0), (1, 0), (1, 1)),
        ((0, w - 1), (1, w - 1), (1, w - 2)),
        ((h - 1, 0), (h - 2, 0), (h - 2, 1)),
        ((h - 1, w - 1), (h - 2, w - 1), (h - 2, w - 2)),
    )
    for row, col in rng.choice(corners):
        grid[row][col] = 3


def _paint_border_texture(grid: Grid, rng) -> None:
    """Add sparse border-attached branches; they cannot create sealed rooms."""
    h, w = len(grid), len(grid[0])
    border = (
        [(0, c) for c in range(w)]
        + [(h - 1, c) for c in range(w)]
        + [(r, 0) for r in range(1, h - 1)]
        + [(r, w - 1) for r in range(1, h - 1)]
    )
    rng.shuffle(border)
    for row, col in border[: rng.randint(0, max(1, min(4, h // 4)))]:
        grid[row][col] = 3


def _apply_square_transform(grid: Grid, code: int) -> Grid:
    out = [row[:] for row in grid]
    if code >= 4:
        out = [list(reversed(row)) for row in out]
    for _ in range(code % 4):
        out = [list(row) for row in zip(*reversed(out))]
    return out


def solve_python(grid: Grid) -> Grid:
    """Independent Python mirror of ``fill-all-enclosed g 4``."""
    analysis = _analyze(grid)
    enclosed = set().union(*analysis["enclosed_components"])
    return [
        [4 if value == 0 and (row, col) in enclosed else value
         for col, value in enumerate(source_row)]
        for row, source_row in enumerate(grid)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical sparse enclosure grammar from the final grid."""
    del difficulty, meta
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    h, w = analysis["height"], analysis["width"]
    if h != w or h not in {6, 10, 20}:
        errors.append(f"expected square canonical scale 6, 10, or 20; got {h}x{w}")
    if analysis["palette"] != (0, 3):
        errors.append(f"expected exact input palette (0, 3), got {analysis['palette']}")

    allowed_regions = {6: {2}, 10: {1, 2, 3}, 20: {5, 8}}
    if h in allowed_regions and analysis["enclosed_regions"] not in allowed_regions[h]:
        errors.append(
            f"enclosed-region count {analysis['enclosed_regions']} is not canonical "
            f"for {h}x{w}"
        )
    if not analysis["exterior_cells"]:
        errors.append("no border-reachable black exterior")
    if analysis["foreground_components"] < 2:
        errors.append("green structure collapsed to fewer than two components")
    if not (0.08 <= analysis["foreground_density"] <= 0.38):
        errors.append(
            "green density outside sparse canonical envelope: "
            f"{analysis['foreground_density']:.4f}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted draw lies on the same topological task manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Infer the exact declared profile from dimensions and region count."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    profile = _SIGNATURE_TO_PROFILE.get(
        (analysis["height"], analysis["width"], analysis["enclosed_regions"])
    )
    return {"scene_profile": profile} if profile is not None else {}


def canonical_profile_index(grid) -> int | None:
    profile = observe_overrides(grid).get("scene_profile")
    return SCENE_PROFILES.index(profile) if profile in SCENE_PROFILES else None


def _rival_fill_all_zeros(grid: Grid) -> Grid:
    return [[4 if value == 0 else value for value in row] for row in grid]


def _rival_largest_enclosure_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    components = analysis["enclosed_components"]
    chosen = max(components, key=len, default=set())
    return [
        [4 if value == 0 and (r, c) in chosen else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _rival_component_bboxes(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    fill: set[Cell] = set()
    for component in analysis["foreground_component_cells"]:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                if grid[r][c] == 0:
                    fill.add((r, c))
    return [
        [4 if value == 0 and (r, c) in fill else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _rival_ignore_singletons(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    fill = set().union(*(component for component in analysis["enclosed_components"] if len(component) > 1))
    return [
        [4 if value == 0 and (r, c) in fill else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _rival_rectangular_rooms_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    fill: set[Cell] = set()
    for component in analysis["enclosed_components"]:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        if len(component) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1):
            fill |= component
    return [
        [4 if value == 0 and (r, c) in fill else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _rival_rooms_at_most_eight(grid: Grid) -> Grid:
    """Distribution shortcut exposed by the former eight-cell room ceiling."""
    analysis = _analyze(grid)
    fill = set().union(*(
        component
        for component in analysis["enclosed_components"]
        if len(component) <= 8
    ))
    return [
        [4 if value == 0 and (r, c) in fill else value
         for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "fill_all_zeros": _rival_fill_all_zeros,
    "largest_enclosure_only": _rival_largest_enclosure_only,
    "foreground_component_bboxes": _rival_component_bboxes,
    "ignore_singleton_rooms": _rival_ignore_singletons,
    "rectangular_rooms_only": _rival_rectangular_rooms_only,
    "rooms_at_most_eight": _rival_rooms_at_most_eight,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid: Grid, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != solve_python(grid)


SEMANTIC_WITNESSES = {
    "exterior_zero_must_survive": lambda grid: _rival_differs(grid, "fill_all_zeros"),
    "all_enclosures_not_only_largest": lambda grid: (
        _analyze(grid)["enclosed_regions"] > 1
        and _rival_differs(grid, "largest_enclosure_only")
    ),
    "open_bbox_is_not_enclosed": lambda grid: _rival_differs(
        grid, "foreground_component_bboxes"
    ),
    "singleton_enclosures_count": lambda grid: (
        _analyze(grid)["singleton_enclosed_regions"] > 0
        and _rival_differs(grid, "ignore_singleton_rooms")
    ),
    "irregular_enclosures_count": lambda grid: (
        _analyze(grid)["nonrectangular_enclosed_regions"] > 0
        and _rival_differs(grid, "rectangular_rooms_only")
    ),
    "canonical_scale_large_rooms": lambda grid: (
        max(_analyze(grid)["enclosed_sizes"], default=0) > 8
        and _rival_differs(grid, "rooms_at_most_eight")
    ),
}

WITNESS_RIVALS = {
    "exterior_zero_must_survive": ["fill_all_zeros"],
    "all_enclosures_not_only_largest": ["largest_enclosure_only"],
    "open_bbox_is_not_enclosed": ["foreground_component_bboxes"],
    "singleton_enclosures_count": ["ignore_singleton_rooms"],
    "irregular_enclosures_count": ["rectangular_rooms_only"],
    "canonical_scale_large_rooms": ["rooms_at_most_eight"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons still compatible with a named wrong transformation."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors}")
        elif demo["output"] != solve_python(demo["input"]):
            reasons.append(f"demo {index} output disagrees with fill-all-enclosed")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors}")
    if reasons:
        return reasons

    truth = solve_python(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which "
                    "changes the query answer"
                )
            else:
                reasons.append(f"competitor {name!r} survives all demos and query")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Focused negative fixtures for the task-local recognizer."""
    all_zero = full_grid(10, 10, 0)
    wrong_color = full_grid(10, 10, 0)
    wrong_color[4][4] = 8
    open_line = full_grid(10, 10, 0)
    for col in range(2, 8):
        open_line[5][col] = 3
    rectangle_icon = full_grid(10, 10, 0)
    for col in range(2, 8):
        rectangle_icon[2][col] = rectangle_icon[7][col] = 3
    for row in range(2, 8):
        rectangle_icon[row][2] = rectangle_icon[row][7] = 3
    # A single connected rectangle icon is deliberately outside this sparse
    # line-network grammar even though the broad transformation is defined.
    return [
        ("all_zero", all_zero),
        ("wrong_foreground_color", wrong_color),
        ("open_line_without_enclosure", open_line),
        ("single_rectangle_icon", rectangle_icon),
    ]


def _neighbors4(cell: Cell) -> tuple[Cell, Cell, Cell, Cell]:
    row, col = cell
    return ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))


def _validate_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        raise ValueError("grid values must be integer ARC colors 0..9")
    return grid


def _components(grid: Grid, value: int) -> list[set[Cell]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == value
    }
    result: list[set[Cell]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            cell = stack.pop()
            for neighbor in _neighbors4(cell):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    grid = _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    zero_components = _components(grid, 0)
    exterior_components: list[set[Cell]] = []
    enclosed_components: list[set[Cell]] = []
    for component in zero_components:
        if any(r in {0, h - 1} or c in {0, w - 1} for r, c in component):
            exterior_components.append(component)
        else:
            enclosed_components.append(component)

    foreground_components = _components(grid, 3)
    nonrectangular = 0
    for component in enclosed_components:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        nonrectangular += int(area != len(component))

    foreground_cells = sum(value == 3 for row in grid for value in row)
    return {
        "height": h,
        "width": w,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "zero_components": zero_components,
        "exterior_components": exterior_components,
        "exterior_cells": set().union(*exterior_components) if exterior_components else set(),
        "enclosed_components": enclosed_components,
        "enclosed_regions": len(enclosed_components),
        "enclosed_sizes": sorted((len(component) for component in enclosed_components), reverse=True),
        "singleton_enclosed_regions": sum(len(component) == 1 for component in enclosed_components),
        "nonrectangular_enclosed_regions": nonrectangular,
        "foreground_component_cells": foreground_components,
        "foreground_components": len(foreground_components),
        "foreground_density": foreground_cells / (h * w),
    }


_SIGNATURE_TO_PROFILE = {
    (spec.height, spec.width, spec.enclosed_regions): profile
    for profile, spec in SCENE_SPECS.items()
}
