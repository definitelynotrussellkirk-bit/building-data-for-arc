"""Generate rectilinear line networks with enclosed and exterior regions.

The input contains one connected, single-color network made from long
horizontal and vertical strokes on a black background.  Some black regions are
sealed by the network and others reach a grid edge.  The rule fills sealed
regions red (2), fills edge-reachable background green (3), and preserves the
network.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Callable, NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "33275a4aae3e"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "a7f4d11b444d"
SUMMARY = (
    "One connected orthogonal stroke network partitions black cells into "
    "sealed regions and edge-reachable exterior regions."
)
INVARIANTS = [
    "the input has exactly black plus one network color other than 2 or 3",
    "the foreground is one connected union of straight horizontal/vertical strokes",
    "the network has two or three enclosed black regions and an exterior",
    "network turns are crossings or at most one T-junction, never elbow pixels",
]
EXPECTED_OUTPUT_CODOMAIN = 100_000


class SceneSpec(NamedTuple):
    height: int
    width: int
    orientation: str
    rooms: int
    horizontal_runs: int
    vertical_runs: int
    boundary_sides: tuple[str, ...]
    t_junction: bool
    density_lo: float
    density_hi: float
    enclosed_lo: int
    enclosed_hi: int


SCENE_SPECS = {
    # Four parameterized public-form profiles.  They preserve the answer-bearing
    # topology and canvas extrema without replaying a literal public bitmap.
    "two_room_lr_22x25": SceneSpec(
        22, 25, "horizontal", 2, 4, 3, ("left", "right"), True,
        0.17, 0.205, 40, 70,
    ),
    "three_room_tl_23x23": SceneSpec(
        23, 23, "vertical", 3, 4, 5, ("top", "left"), True,
        0.18, 0.225, 50, 85,
    ),
    "three_room_r_24x21": SceneSpec(
        24, 21, "vertical", 3, 5, 4, ("right",), True,
        0.195, 0.24, 60, 100,
    ),
    "three_room_b_22x25": SceneSpec(
        22, 25, "vertical", 3, 5, 4, ("bottom",), False,
        0.19, 0.235, 75, 115,
    ),
    # Additional linked networks vary branch count and boundary attachment while
    # staying inside the demonstrated dimensional and topological envelope.
    "two_room_tr_21x24": SceneSpec(
        21, 24, "horizontal", 2, 5, 4, ("top", "right"), False,
        0.18, 0.24, 35, 75,
    ),
    "two_room_bl_23x21": SceneSpec(
        23, 21, "vertical", 2, 4, 5, ("bottom", "left"), True,
        0.18, 0.24, 35, 80,
    ),
    "three_room_lr_24x25": SceneSpec(
        24, 25, "vertical", 3, 5, 5, ("left", "right"), False,
        0.18, 0.24, 55, 110,
    ),
    "three_room_tb_22x23": SceneSpec(
        22, 23, "horizontal", 3, 4, 4, ("top", "bottom"), True,
        0.18, 0.24, 50, 100,
    ),
}
SCENE_PROFILES = tuple(SCENE_SPECS)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng over linked line-network profiles",
        "valid": (
            "two_room_lr_22x25|three_room_tl_23x23|three_room_r_24x21|"
            "three_room_b_22x25|two_room_tr_21x24|two_room_bl_23x21|"
            "three_room_lr_24x25|three_room_tb_22x23"
        ),
    },
}

Grid = list[list[int]]
Cell = tuple[int, int]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic line-network input grid."""
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
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    spec = SCENE_SPECS[scene_profile]
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "all"
    rng = ctx.draw_rng(f"network_geometry_{band}")
    color_rng = ctx.draw_rng(f"network_color_{band}")
    color = color_rng.choice((1, 4, 5, 6, 7, 8, 9))

    for _ in range(512):
        grid = _construct_candidate(spec, color, rng)
        analysis = _analyze(grid)
        if _matches_spec(analysis, spec):
            return grid
    raise RuntimeError(
        f"unable to construct {scene_profile!r} after 512 deterministic attempts"
    )


def solve_python(grid: Grid) -> Grid:
    """Independent Python mirror of fill-all-enclosed followed by recolor."""
    _validate_rectangular_grid(grid)
    height = len(grid)
    width = len(grid[0])
    exterior: set[Cell] = set()
    queue: deque[Cell] = deque()

    for row in range(height):
        for col in (0, width - 1):
            if grid[row][col] == 0 and (row, col) not in exterior:
                exterior.add((row, col))
                queue.append((row, col))
    for col in range(width):
        for row in (0, height - 1):
            if grid[row][col] == 0 and (row, col) not in exterior:
                exterior.add((row, col))
                queue.append((row, col))

    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] == 0
                and (nr, nc) not in exterior
            ):
                exterior.add((nr, nc))
                queue.append((nr, nc))

    return [
        [
            value
            if value != 0
            else (3 if (row, col) in exterior else 2)
            for col, value in enumerate(source_row)
        ]
        for row, source_row in enumerate(grid)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the returned task grammar from the final grid only."""
    errors: list[str] = []
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    if not (21 <= analysis["height"] <= 24):
        errors.append(f"height outside 21..24: {analysis['height']}")
    if not (21 <= analysis["width"] <= 25):
        errors.append(f"width outside 21..25: {analysis['width']}")
    if len(analysis["nonzero_colors"]) != 1:
        errors.append(
            f"expected one network color, got {analysis['nonzero_colors']}"
        )
    elif analysis["nonzero_colors"][0] in {2, 3}:
        errors.append("network uses output-only color 2 or 3")
    if analysis["foreground_components"] != 1:
        errors.append(
            "foreground must be one connected network, got "
            f"{analysis['foreground_components']} components"
        )
    if analysis["enclosed_regions"] not in {2, 3}:
        errors.append(
            f"expected two or three enclosed regions, got "
            f"{analysis['enclosed_regions']}"
        )
    if not (4 <= analysis["horizontal_runs"] <= 5):
        errors.append(
            f"expected four or five horizontal strokes, got "
            f"{analysis['horizontal_runs']}"
        )
    if not (3 <= analysis["vertical_runs"] <= 5):
        errors.append(
            f"expected three to five vertical strokes, got "
            f"{analysis['vertical_runs']}"
        )
    if analysis["turns"] != 0:
        errors.append(f"network contains {analysis['turns']} elbow pixels")
    if analysis["degree3"] not in {0, 1}:
        errors.append(
            f"expected zero or one T-junction, got {analysis['degree3']}"
        )
    if not (7 <= analysis["degree4"] <= 12):
        errors.append(
            f"expected 7..12 crossing pixels, got {analysis['degree4']}"
        )
    if analysis["unsupported_foreground_cells"]:
        errors.append("network contains isolated foreground cells")
    if not (0.17 <= analysis["foreground_density"] <= 0.24):
        errors.append(
            "foreground density outside canonical envelope: "
            f"{analysis['foreground_density']:.4f}"
        )
    touched = analysis["boundary_sides"]
    if not (1 <= len(touched) <= 2):
        errors.append(f"expected one or two touched grid sides, got {touched}")
    if not analysis["boundary_zero_regions"]:
        errors.append("no edge-reachable background region")
    return errors


def observe_overrides(grid):
    """Infer the exact declared scene profile from returned-grid semantics."""
    if self_check(grid):
        return {}
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    signature = _signature(analysis)
    profile = _SIGNATURE_TO_PROFILE.get(signature)
    return {"scene_profile": profile} if profile is not None else {}


def canonical_profile_index(grid):
    """Return a public-form profile index, or ``None`` for extrapolation."""
    observed = observe_overrides(grid).get("scene_profile")
    public_profiles = SCENE_PROFILES[:4]
    return public_profiles.index(observed) if observed in public_profiles else None


def _construct_candidate(spec: SceneSpec, color: int, rng) -> Grid:
    if spec.orientation == "horizontal":
        return _construct_horizontal_candidate(spec, color, rng)
    side_map = {
        "top": "left",
        "bottom": "right",
        "left": "top",
        "right": "bottom",
    }
    side_order = ("top", "bottom", "left", "right")
    mapped_sides = tuple(
        side
        for side in side_order
        if side in {side_map[value] for value in spec.boundary_sides}
    )
    virtual = SceneSpec(
        height=spec.width,
        width=spec.height,
        orientation="horizontal",
        rooms=spec.rooms,
        horizontal_runs=spec.vertical_runs,
        vertical_runs=spec.horizontal_runs,
        boundary_sides=mapped_sides,
        t_junction=spec.t_junction,
        density_lo=spec.density_lo,
        density_hi=spec.density_hi,
        enclosed_lo=spec.enclosed_lo,
        enclosed_hi=spec.enclosed_hi,
    )
    grid = _construct_horizontal_candidate(virtual, color, rng)
    return [list(row) for row in zip(*grid)]


def _construct_horizontal_candidate(spec: SceneSpec, color: int, rng) -> Grid:
    height = spec.height
    width = spec.width
    row_count = spec.rooms + 1

    row_start = rng.randint(3, 5)
    row_gaps = [rng.randint(4, 6) for _ in range(spec.rooms)]
    rows = [row_start]
    for gap in row_gaps:
        rows.append(rows[-1] + gap)
    if rows[-1] > height - 4:
        return full_grid(height, width, 0)

    left_rail = rng.randint(3, min(7, width - 13))
    rail_gap = rng.randint(9, min(11, width - left_rail - 4))
    right_rail = left_rail + rail_gap
    if right_rail > width - 4:
        return full_grid(height, width, 0)

    horizontal: list[list[int]] = []
    for row in rows:
        left_room = rng.randint(1, left_rail - 1)
        right_room = rng.randint(right_rail + 1, width - 2)
        horizontal.append([row, left_room, right_room])

    vertical: list[list[int]] = []
    for col in (left_rail, right_rail):
        top = rng.randint(1, min(2, rows[0] - 1))
        bottom = rng.randint(max(rows[-1] + 1, height - 3), height - 2)
        vertical.append([col, top, bottom])

    boundary_bar = 0
    boundary_rail = 0
    if "left" in spec.boundary_sides:
        horizontal[boundary_bar][1] = 0
    if "right" in spec.boundary_sides:
        horizontal[boundary_bar][2] = width - 1
    if "top" in spec.boundary_sides:
        vertical[boundary_rail][1] = 0
    if "bottom" in spec.boundary_sides:
        vertical[boundary_rail][2] = height - 1

    if spec.t_junction:
        t_bar = 1 if row_count > 1 else 0
        horizontal[t_bar][1] = left_rail

    extra_horizontal = spec.horizontal_runs - row_count
    horizontal_rows = _branch_rows(rows, extra_horizontal, rng)
    for index, row in enumerate(horizontal_rows):
        if index % 2 == 0:
            extension_hi = max(2, min(6, left_rail - 1))
            extension = rng.randint(2, extension_hi)
            horizontal.append([row, left_rail - extension, left_rail + 1])
        else:
            extension_hi = max(2, min(6, width - 2 - right_rail))
            extension = rng.randint(2, extension_hi)
            horizontal.append([row, right_rail - 1, right_rail + extension])

    extra_vertical = spec.vertical_runs - 2
    available_cols = list(range(left_rail + 3, right_rail - 2))
    rng.shuffle(available_cols)
    chosen_cols: list[int] = []
    for col in available_cols:
        if all(abs(col - prior) > 1 for prior in chosen_cols):
            chosen_cols.append(col)
            if len(chosen_cols) == extra_vertical:
                break
    if len(chosen_cols) < extra_vertical:
        return full_grid(height, width, 0)
    for index, col in enumerate(chosen_cols):
        bar_index = index % row_count
        row = rows[bar_index]
        top_limit = 1 if bar_index == 0 else rows[bar_index - 1] + 2
        bottom_limit = (
            height - 2
            if bar_index == row_count - 1
            else rows[bar_index + 1] - 2
        )
        if top_limit >= row or bottom_limit <= row:
            return full_grid(height, width, 0)
        top = rng.randint(top_limit, row - 1)
        bottom = rng.randint(row + 1, bottom_limit)
        vertical.append([col, top, bottom])

    grid = full_grid(height, width, 0)
    for row, col1, col2 in horizontal:
        for col in range(col1, col2 + 1):
            grid[row][col] = color
    for col, row1, row2 in vertical:
        for row in range(row1, row2 + 1):
            grid[row][col] = color
    return grid


def _branch_rows(rows: list[int], count: int, rng) -> list[int]:
    if count <= 0:
        return []
    candidates: list[int] = []
    for upper, lower in zip(rows, rows[1:]):
        candidates.extend(range(upper + 2, lower - 1))
    rng.shuffle(candidates)
    chosen: list[int] = []
    for row in candidates:
        if (
            all(abs(row - core_row) > 1 for core_row in rows)
            and all(abs(row - prior) > 1 for prior in chosen)
        ):
            chosen.append(row)
            if len(chosen) == count:
                break
    return chosen


def _matches_spec(analysis: dict, spec: SceneSpec) -> bool:
    if analysis["height"] != spec.height or analysis["width"] != spec.width:
        return False
    if analysis["foreground_components"] != 1:
        return False
    if analysis["enclosed_regions"] != spec.rooms:
        return False
    if analysis["horizontal_runs"] != spec.horizontal_runs:
        return False
    if analysis["vertical_runs"] != spec.vertical_runs:
        return False
    if analysis["boundary_sides"] != spec.boundary_sides:
        return False
    if analysis["degree3"] != int(spec.t_junction):
        return False
    expected_crossings = (
        2 * (spec.rooms + 1)
        + (spec.horizontal_runs - (spec.rooms + 1))
        + (spec.vertical_runs - 2)
        - int(spec.t_junction)
    )
    if analysis["degree4"] != expected_crossings:
        return False
    if analysis["turns"] or analysis["unsupported_foreground_cells"]:
        return False
    if not (
        spec.density_lo
        <= analysis["foreground_density"]
        <= spec.density_hi
    ):
        return False
    enclosed_total = sum(analysis["enclosed_sizes"])
    return spec.enclosed_lo <= enclosed_total <= spec.enclosed_hi


def _signature(analysis: dict) -> tuple:
    return (
        analysis["height"],
        analysis["width"],
        analysis["enclosed_regions"],
        analysis["horizontal_runs"],
        analysis["vertical_runs"],
        analysis["boundary_sides"],
        analysis["degree3"],
        analysis["degree4"],
    )


def _expected_signature(spec: SceneSpec) -> tuple:
    crossings = (
        2 * (spec.rooms + 1)
        + (spec.horizontal_runs - (spec.rooms + 1))
        + (spec.vertical_runs - 2)
        - int(spec.t_junction)
    )
    return (
        spec.height,
        spec.width,
        spec.rooms,
        spec.horizontal_runs,
        spec.vertical_runs,
        spec.boundary_sides,
        int(spec.t_junction),
        crossings,
    )


_SIGNATURE_TO_PROFILE = {
    _expected_signature(spec): profile
    for profile, spec in SCENE_SPECS.items()
}


def _validate_rectangular_grid(grid: Grid) -> None:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid values must be ARC colors 0..9")


def _components(grid: Grid, accept: Callable[[int], bool]) -> list[set[Cell]]:
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if accept(grid[row][col])
    }
    result: list[set[Cell]] = []
    while unseen:
        start = unseen.pop()
        unseen_component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    unseen_component.add(neighbor)
                    stack.append(neighbor)
        result.append(unseen_component)
    return result


def _maximal_runs(grid: Grid, *, horizontal: bool) -> list[tuple[int, int, int]]:
    height = len(grid)
    width = len(grid[0])
    runs: list[tuple[int, int, int]] = []
    outer = height if horizontal else width
    inner = width if horizontal else height
    for primary in range(outer):
        start = None
        for secondary in range(inner + 1):
            if secondary < inner:
                row, col = (
                    (primary, secondary)
                    if horizontal
                    else (secondary, primary)
                )
                occupied = grid[row][col] != 0
            else:
                occupied = False
            if occupied and start is None:
                start = secondary
            elif not occupied and start is not None:
                length = secondary - start
                if length >= 2:
                    runs.append((primary, start, length))
                start = None
    return runs


def _analyze(grid: Grid) -> dict:
    _validate_rectangular_grid(grid)
    height = len(grid)
    width = len(grid[0])
    color_counts = Counter(value for row in grid for value in row)
    nonzero_colors = tuple(sorted(color for color in color_counts if color != 0))
    foreground = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    foreground_components = _components(grid, lambda value: value != 0)
    zero_components = _components(grid, lambda value: value == 0)
    boundary_zero = [
        component
        for component in zero_components
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in component
        )
    ]
    enclosed = [
        component for component in zero_components if component not in boundary_zero
    ]
    horizontal_runs = _maximal_runs(grid, horizontal=True)
    vertical_runs = _maximal_runs(grid, horizontal=False)

    degree_counts: Counter[int] = Counter()
    turns = 0
    unsupported = 0
    for row, col in foreground:
        neighbors = {
            (dr, dc)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if (row + dr, col + dc) in foreground
        }
        degree_counts[len(neighbors)] += 1
        if len(neighbors) == 2:
            first, second = tuple(neighbors)
            if first != (-second[0], -second[1]):
                turns += 1
        if not neighbors:
            unsupported += 1

    boundary_sides: list[str] = []
    if any(row == 0 for row, _ in foreground):
        boundary_sides.append("top")
    if any(row == height - 1 for row, _ in foreground):
        boundary_sides.append("bottom")
    if any(col == 0 for _, col in foreground):
        boundary_sides.append("left")
    if any(col == width - 1 for _, col in foreground):
        boundary_sides.append("right")
    canonical_side_order = ("top", "bottom", "left", "right")
    ordered_sides = tuple(
        side for side in canonical_side_order if side in boundary_sides
    )

    return {
        "height": height,
        "width": width,
        "nonzero_colors": nonzero_colors,
        "foreground_count": len(foreground),
        "foreground_density": len(foreground) / (height * width),
        "foreground_components": len(foreground_components),
        "zero_regions": len(zero_components),
        "boundary_zero_regions": len(boundary_zero),
        "enclosed_regions": len(enclosed),
        "enclosed_sizes": tuple(
            sorted((len(component) for component in enclosed), reverse=True)
        ),
        "horizontal_runs": len(horizontal_runs),
        "vertical_runs": len(vertical_runs),
        "degree1": degree_counts[1],
        "degree3": degree_counts[3],
        "degree4": degree_counts[4],
        "turns": turns,
        "unsupported_foreground_cells": unsupported,
        "boundary_sides": ordered_sides,
    }
