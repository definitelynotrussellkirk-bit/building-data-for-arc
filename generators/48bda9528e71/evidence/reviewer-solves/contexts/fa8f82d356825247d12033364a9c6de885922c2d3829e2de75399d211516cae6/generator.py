"""Generator for ARC task aa62e3f4 / 48bda9528e71.

The input is one orthogonally-convex, connected, multicolor shape on
background 8.  Exactly one non-background color is least frequent, and its
cells are nested inside the occupied shape.  The oracle erases the shape and
uses that rare color to mark one cell beyond every occupied row and column
extent, clipping markers that fall outside the canvas.

Default four-pair windows contain a complete official archetype, a general
lattice-convex shape, and two oppositely oriented notched shapes.  The notches
teach that Euclidean convexification is incorrect, while preserving the
connected, orthogonally-convex grammar.  Every single-query holdout of such a
window retains a separating demonstration.  Palettes remain freely renamed.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "48bda9528e71"
TASK_ID = "48bda9528e71"
VERSION = "2.1.0"
RULE_HASH = "b9f9e9bda3f3"

SUMMARY = (
    "Erase one connected nested shape, then use its unique least-frequent "
    "color to mark one cell beyond each occupied row and column extent."
)

INVARIANTS = [
    "background is the modal color 8",
    "the non-background cells form one 4-connected orthogonally-convex shape",
    "two or three non-background colors are present",
    "the least-frequent non-background color is unique",
    "every rare-color cell is cardinally enclosed by the occupied shape",
    "the shape may touch canvas edges, so out-of-bounds extent markers clip",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware rng 5..16",
        "valid": "5..16",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-phase canonical/general teaching schedule",
        "valid": "canonical|general",
    },
}

_BACKGROUND = 8
_CANONICAL_SIZES = (5, 7, 16)
_BANDS = {"easy", "medium", "hard"}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "notch_top", "general", "notch_bottom")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_size": size, "scene_profile": "canonical"}
    for size in range(5, 17) if size not in _CANONICAL_SIZES
]


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic branch schedule; geometry and palettes use keyed random draws."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]

# Complete official inputs, not independently recombined feature banks.
# Dots are background 8; digits are the original non-background colors.
_CANONICAL_TEMPLATE_ROWS = {
    "official_5": (
        "..4..",
        "..44.",
        ".444.",
        ".434.",
        ".444.",
    ),
    "official_7": (
        ".3.....",
        ".33....",
        ".313...",
        ".3313..",
        ".313...",
        ".33....",
        ".3.....",
    ),
    "official_16": (
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        ".33.............",
        "3223............",
        "32423...........",
        "32423...........",
        "32223...........",
        "3333............",
    ),
}


def _parse_template(rows: Iterable[str]) -> list[list[int]]:
    parsed = [
        [_BACKGROUND if char == "." else int(char) for char in row]
        for row in rows
    ]
    if not parsed or any(len(row) != len(parsed) for row in parsed):
        raise ValueError("canonical templates must be non-empty square grids")
    return parsed


_CANONICAL_TEMPLATES = {
    name: _parse_template(rows)
    for name, rows in _CANONICAL_TEMPLATE_ROWS.items()
}


def _rotate90(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _reflect(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _d4_variants(grid: list[list[int]]) -> list[list[list[int]]]:
    variants: list[list[list[int]]] = []
    current = [row[:] for row in grid]
    for _ in range(4):
        variants.append([row[:] for row in current])
        variants.append(_reflect(current))
        current = _rotate90(current)
    return variants


def _frequency_role_grid(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    counts = Counter(value for row in grid for value in row if value != _BACKGROUND)
    first_seen: dict[int, tuple[int, int]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != _BACKGROUND and value not in first_seen:
                first_seen[value] = (row_index, col_index)
    ordered = sorted(counts, key=lambda color: (counts[color], first_seen[color], color))
    roles = {color: index + 1 for index, color in enumerate(ordered)}
    return tuple(
        tuple(0 if value == _BACKGROUND else roles[value] for value in row)
        for row in grid
    )


def _full_profile_signature(grid: list[list[int]]) -> tuple[int, tuple[tuple[int, ...], ...]]:
    """Return the linked full-grid signature, quotienting only color names and D4."""
    role_grid = [list(row) for row in _frequency_role_grid(grid)]
    canonical = min(tuple(tuple(row) for row in variant) for variant in _d4_variants(role_grid))
    return len(grid), canonical


CANONICAL_PROFILE_SIGNATURES = frozenset(
    _full_profile_signature(grid) for grid in _CANONICAL_TEMPLATES.values()
)


def profile_signature(grid: Any):
    """Executable linked signature used for both official and generated grids."""
    basic_errors = _basic_grid_errors(grid)
    if basic_errors:
        return None
    return _full_profile_signature(grid)


def canonical_profile_signature(grid: Any):
    """Return the complete official-profile signature, or ``None``."""
    signature = profile_signature(grid)
    return signature if signature in CANONICAL_PROFILE_SIGNATURES else None


def _band(difficulty: Any) -> str:
    return difficulty if difficulty in _BANDS else "medium"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic task input while honoring every declared axis."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override axes: " + ", ".join(sorted(unknown)))
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    requested_size = overrides.get("grid_size")
    if requested_size is not None and type(requested_size) is not int:
        raise TypeError("grid_size must be an integer (not bool, float or string)")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = _band(difficulty)
    rng = ctx.draw_rng(f"layout|{band}")

    requested_profile = overrides.get("scene_profile")
    if requested_profile is not None:
        profile_options = ["canonical", "general"]
    elif (scheduled_profile == "canonical"
          and (requested_size is None or requested_size in _CANONICAL_SIZES)):
        profile_options = ["canonical"]
    else:
        profile_options = ["general"]
    scene_profile = ctx.draw_choice("scene_profile", profile_options)

    if scene_profile == "canonical":
        if requested_size is None:
            template_name = rng.choice(sorted(_CANONICAL_TEMPLATES))
            size = len(_CANONICAL_TEMPLATES[template_name])
            size = ctx.draw_int_strict("grid_size", size, size)
        else:
            size = ctx.draw_int_strict("grid_size", 5, 16)
            candidates = [
                name
                for name, template in _CANONICAL_TEMPLATES.items()
                if len(template) == size
            ]
            if not candidates:
                raise ValueError(
                    "scene_profile='canonical' requires grid_size 5, 7, or 16"
                )
            template_name = rng.choice(sorted(candidates))
        return _render_canonical(template_name, rng)

    size = ctx.draw_int_diff("grid_size", 5, 16)
    if scheduled_profile in ("notch_top", "notch_bottom"):
        mask, row0, col0 = _notched_mask(size, band, rng, scheduled_profile)
        grid = _color_mask(size, mask, row0, col0, band, rng)
        errors = self_check(grid)
        if errors:
            raise RuntimeError("invalid constructed notched scene: " + "; ".join(errors))
        return grid
    return _render_general(size, band, rng)


def _render_canonical(template_name: str, rng) -> list[list[int]]:
    grid = [row[:] for row in _CANONICAL_TEMPLATES[template_name]]
    grid = _d4_variants(grid)[rng.randrange(8)]
    source_colors = sorted({value for row in grid for value in row if value != _BACKGROUND})
    target_colors = rng.sample([color for color in range(10) if color != _BACKGROUND], len(source_colors))
    remap = dict(zip(source_colors, target_colors))
    return [
        [_BACKGROUND if value == _BACKGROUND else remap[value] for value in row]
        for row in grid
    ]


def _render_general(size: int, band: str, rng) -> list[list[int]]:
    for _attempt in range(256):
        mask, row0, col0 = _general_mask(size, band, rng)
        grid = _color_mask(size, mask, row0, col0, band, rng)
        if canonical_profile_signature(grid) is not None:
            continue
        if not self_check(grid):
            return grid
    raise RuntimeError("failed to construct a valid general nested-shape scene")


def _general_mask(size: int, band: str, rng):
    span_cap = min(size, {"easy": 5, "medium": 7, "hard": 9}[band])
    max_cells = (size * size - 1) // 2

    for _attempt in range(256):
        box_h = rng.randint(3, span_cap)
        box_w = rng.randint(3, span_cap)
        cut_cap = min({"easy": 1, "medium": 2, "hard": 3}[band], box_h - 2, box_w - 2)
        cuts = [rng.randint(0, cut_cap) for _ in range(4)]
        top_left, top_right, bottom_left, bottom_right = cuts
        mask = {
            (row, col)
            for row in range(box_h)
            for col in range(box_w)
            if row + col >= top_left
            and row + (box_w - 1 - col) >= top_right
            and (box_h - 1 - row) + col >= bottom_left
            and (box_h - 1 - row) + (box_w - 1 - col) >= bottom_right
        }
        if not 7 <= len(mask) <= max_cells:
            continue
        if not _is_connected(mask) or not _is_orthogonally_convex(mask):
            continue
        if not _interior_cells(mask):
            continue

        max_row0 = size - box_h
        max_col0 = size - box_w
        edge_probability = {"easy": 0.25, "medium": 0.55, "hard": 0.80}[band]
        row0 = _biased_offset(max_row0, edge_probability, rng)
        col0 = _biased_offset(max_col0, edge_probability, rng)
        return mask, row0, col0
    raise RuntimeError("failed to construct a feasible orthogonally-convex mask")


def _notched_mask(size: int, band: str, rng, profile: str):
    """Construct an L with a guaranteed in-bounds convexification witness.

    For arms a,b and notch dimensions >=2, the missing elbow (a,b) is
    the midpoint of occupied cells (a-1,b+1) and (a+1,b-1).  The reference
    marks that elbow, whereas the convexified rival erases it.  Arms >=2
    also leave an enclosed cell at (a-1,b-1).  A 4x4 minus 2x2 member fits
    even size=5 under the unchanged area cap.
    """
    span_cap = min(size, {"easy": 5, "medium": 7, "hard": 9}[band])
    max_cells = (size * size - 1) // 2
    choices = [
        (height, width, arm_h, arm_w)
        for height in range(4, span_cap + 1)
        for width in range(4, span_cap + 1)
        for arm_h in range(2, height - 1)
        for arm_w in range(2, width - 1)
        if height * width - (height - arm_h) * (width - arm_w) <= max_cells
    ]
    height, width, arm_h, arm_w = rng.choice(choices)
    bitmap = [[int(row < arm_h or col < arm_w) for col in range(width)]
              for row in range(height)]
    # These disjoint D4 halves guarantee that the two notched inputs in
    # any four-index window cannot be discarded as duplicate inputs.
    transform = rng.randrange(4) + (4 if profile == "notch_top" else 0)
    bitmap = _d4_variants(bitmap)[transform]
    height, width = len(bitmap), len(bitmap[0])
    mask = {(row, col) for row in range(height) for col in range(width)
            if bitmap[row][col]}
    edge_probability = {"easy": 0.25, "medium": 0.55, "hard": 0.80}[band]
    row0 = _biased_offset(size - height, edge_probability, rng)
    col0 = _biased_offset(size - width, edge_probability, rng)
    return mask, row0, col0


def _biased_offset(limit: int, edge_probability: float, rng) -> int:
    if limit <= 0:
        return 0
    roll = rng.random()
    if roll < edge_probability / 2:
        return 0
    if roll < edge_probability:
        return limit
    return rng.randint(0, limit)


def _color_mask(size: int, mask: set[tuple[int, int]], row0: int, col0: int, band: str, rng):
    interior = sorted(_interior_cells(mask))
    max_rare = min(3, len(interior), max(1, (len(mask) - 2) // 3))
    rare_count = 1 if band == "easy" else rng.randint(1, max_rare)
    rare = set(rng.sample(interior, rare_count))
    boundary = {
        cell
        for cell in mask
        if any((cell[0] + dr, cell[1] + dc) not in mask for dr, dc in _CARDINAL)
    }
    inner_common = mask - boundary - rare
    use_inner_layer = (
        band != "easy"
        and len(boundary) > rare_count
        and len(inner_common) > rare_count
        and rng.random() < (0.55 if band == "medium" else 0.80)
    )

    palette_count = 3 if use_inner_layer else 2
    palette = rng.sample([color for color in range(10) if color != _BACKGROUND], palette_count)
    rare_color = palette[0]
    outer_color = palette[1]
    inner_color = palette[2] if use_inner_layer else outer_color

    grid = [[_BACKGROUND for _ in range(size)] for _ in range(size)]
    for row, col in mask:
        if (row, col) in rare:
            color = rare_color
        elif use_inner_layer and (row, col) in inner_common:
            color = inner_color
        else:
            color = outer_color
        grid[row0 + row][col0 + col] = color
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular with non-empty rows"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid colors must be integers in 0..9"]
    return []


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(cells)


def _is_orthogonally_convex(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    for row in rows:
        occupied = sorted(col for r, col in cells if r == row)
        if occupied != list(range(occupied[0], occupied[-1] + 1)):
            return False
    for col in cols:
        occupied = sorted(row for row, c in cells if c == col)
        if occupied != list(range(occupied[0], occupied[-1] + 1)):
            return False
    return True


def _interior_cells(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, col in cells
        if all((row + dr, col + dc) in cells for dr, dc in _CARDINAL)
    }


def _extent_positions(cells: set[tuple[int, int]], height: int, width: int) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for row in {row for row, _ in cells}:
        cols = [col for r, col in cells if r == row]
        left, right = min(cols), max(cols)
        if left > 0:
            positions.add((row, left - 1))
        if right + 1 < width:
            positions.add((row, right + 1))
    for col in {col for _, col in cells}:
        rows = [row for row, c in cells if c == col]
        top, bottom = min(rows), max(rows)
        if top > 0:
            positions.add((top - 1, col))
        if bottom + 1 < height:
            positions.add((bottom + 1, col))
    return positions


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any]]:
    errors = _basic_grid_errors(grid)
    if errors:
        return errors, {}

    height, width = len(grid), len(grid[0])
    if height != width:
        errors.append(f"generated curriculum grids must be square, got {height}x{width}")
    if not 5 <= height <= 16 or not 5 <= width <= 16:
        errors.append(f"grid dimensions must lie in 5..16, got {height}x{width}")

    counts = Counter(value for row in grid for value in row)
    background_count = counts.get(_BACKGROUND, 0)
    non_background_colors = sorted(color for color in counts if color != _BACKGROUND)
    if not 2 <= len(non_background_colors) <= 3:
        errors.append(
            "scene must contain exactly two or three non-background colors, "
            f"got {len(non_background_colors)}"
        )
    if non_background_colors and background_count <= max(counts[color] for color in non_background_colors):
        errors.append("background 8 must be strictly modal")

    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != _BACKGROUND
    }
    max_cells = (height * width - 1) // 2
    if not 7 <= len(cells) <= max_cells:
        errors.append(
            f"occupied shape must contain 7..{max_cells} cells, got {len(cells)}"
        )
    if cells and not _is_connected(cells):
        errors.append("non-background cells must form one 4-connected shape")
    if cells and not _is_orthogonally_convex(cells):
        errors.append("occupied cells must be contiguous in every active row and column")

    if cells:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        if max(rows) - min(rows) + 1 < 3 or max(cols) - min(cols) + 1 < 3:
            errors.append("occupied shape must span at least three rows and three columns")

    rare_color = None
    rare_count = None
    if non_background_colors:
        ordered_counts = sorted((counts[color], color) for color in non_background_colors)
        rare_count, rare_color = ordered_counts[0]
        if len(ordered_counts) > 1 and ordered_counts[1][0] == rare_count:
            errors.append("least-frequent non-background color must be unique")
        rare_cells = {
            (row, col)
            for row, col in cells
            if grid[row][col] == rare_color
        }
        if rare_cells and not rare_cells <= _interior_cells(cells):
            errors.append("every rare-color cell must have four occupied cardinal neighbors")

    extent_positions = _extent_positions(cells, height, width) if cells else set()
    if len(extent_positions) < 4:
        errors.append("shape must expose at least four in-bounds row/column extent markers")

    facts = {
        "grid_size": height if height == width else (height, width),
        "scene_profile": "canonical" if canonical_profile_signature(grid) is not None else "general",
        "occupied_cells": len(cells),
        "non_background_colors": tuple(non_background_colors),
        "rare_color": rare_color,
        "rare_count": rare_count,
        "extent_marker_count": len(extent_positions),
        "edge_contacts": {
            "top": any(row == 0 for row, _ in cells),
            "bottom": any(row == height - 1 for row, _ in cells),
            "left": any(col == 0 for _, col in cells),
            "right": any(col == width - 1 for _, col in cells),
        },
    }
    return errors, facts


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid itself."""
    errors, facts = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {
        "grid_size": facts["grid_size"],
        "scene_profile": facts["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-specific input grammar without mutating the input."""
    del difficulty, meta
    errors, _facts = _analyze_grid(grid)
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket oracle for focused tests."""
    errors, facts = _analyze_grid(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != _BACKGROUND
    }
    output = [[_BACKGROUND for _ in range(width)] for _ in range(height)]
    for row, col in _extent_positions(cells, height, width):
        output[row][col] = facts["rare_color"]
    return output


def strict_canonical_like(grid):
    """Keep the complete linked official profiles, including color roles."""
    return [] if canonical_profile_signature(grid) is not None else [
        "not one of the three complete official profiles up to D4/color renaming"
    ]


def _occupied_cells(grid):
    return {(row, col) for row, values in enumerate(grid)
            for col, value in enumerate(values) if value != _BACKGROUND}


def _cross(origin, first, second):
    return ((first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0]))


def _lattice_convex_hull(cells):
    """Integer lattice points inside the Euclidean hull; no floating point."""
    points = sorted(cells)
    if len(points) < 3:
        return set(points)
    lower = []
    for point in points:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return set(points)
    edges = list(zip(hull, hull[1:] + hull[:1]))
    return {(row, col)
            for row in range(min(r for r, _ in points), max(r for r, _ in points) + 1)
            for col in range(min(c for _, c in points), max(c for _, c in points) + 1)
            if all(_cross(first, second, (row, col)) >= 0 for first, second in edges)}


def _convexify_then_shell(grid):
    """Wrong rival: fill the Euclidean hull before drawing the cardinal shell."""
    errors, facts = _analyze_grid(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    cells = _lattice_convex_hull(_occupied_cells(grid))
    height, width = len(grid), len(grid[0])
    output = [[_BACKGROUND] * width for _ in range(height)]
    for row, col in cells:
        for dr, dc in _CARDINAL:
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cells:
                output[nr][nc] = facts["rare_color"]
    return output


def _has_lattice_concavity(grid):
    cells = _occupied_cells(grid)
    return bool(_lattice_convex_hull(cells) - cells)


SEMANTIC_RIVALS = {"convexify_then_shell": _convexify_then_shell}
CANONICAL_SHORTCUTS = {"convexify_then_shell": _convexify_then_shell}
LESSON_COMPETITORS = {"convexify_then_shell": _convexify_then_shell}
SEMANTIC_WITNESSES = {"lattice_concavity": _has_lattice_concavity}
WITNESS_RIVALS = {"lattice_concavity": ["convexify_then_shell"]}
