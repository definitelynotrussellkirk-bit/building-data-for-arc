"""Generator for puzzle 82e4aea30adc — size-dependent frame fill.

Each non-background object is a monochrome hollow rectangular outline.  Fill
all zero cells strictly inside its bounding box with gray (5) when the interior
has one cell, and orange (7) when it has two or more cells.  The teaching
schedule deliberately cycles single-cell, mixed, and multi-cell scenes so no
three-example lesson can hide either semantic branch.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "82e4aea30adc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3b12f4f95260"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains one to five isolated monochrome hollow "
    "rectangular frames.  For each frame, inspect every zero cell strictly "
    "inside its bounding box.  If that interior consists of exactly one cell, "
    "fill it gray (5); otherwise fill every interior cell orange (7).  Frame "
    "borders and all exterior background cells remain unchanged."
)

INVARIANTS = [
    "background is color 0",
    "every nonzero component is a complete monochrome rectangular outline",
    "each frame is at least 3 by 3 and has an all-zero interior",
    "different frames do not touch orthogonally or overlap",
    "frame colors exclude the output-only fill colors 5 and 7",
    "the one-cell and multi-cell interior branches are both scheduled",
]

# Only exact values recoverable from the returned grid are public axes.  Canvas
# size, frame dimensions, colors, positions, and orientation remain deterministic
# nuisance variation rather than misleading pseudo-overrides.
AXES = {
    "n_frames": {
        "type": "int",
        "default": "difficulty-shaped deterministic choice",
        "valid": "1..5",
    },
    "branch_profile": {
        "type": "str",
        "default": "sample-index cycle",
        "valid": "single_only|mixed|multi_only",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_frames": 1, "branch_profile": "mixed"},
]

_BRANCH_PROFILES = ("single_only", "mixed", "multi_only")
_LEGAL_FRAME_COLORS = (1, 2, 3, 4, 6, 8, 9)
_MULTI_SHAPES = (
    (3, 4),
    (4, 3),
    (3, 5),
    (5, 3),
    (4, 4),
    (4, 5),
    (5, 4),
)
_DIFFICULTY_COUNTS = {
    None: (1, 2, 3, 4, 5),
    "easy": (1, 1, 2, 2, 3),
    "medium": (2, 2, 3, 3, 4),
    "hard": (3, 3, 4, 4, 5),
}
_DIFFICULTY_MIN_CANVAS = {
    None: (8, 9),
    "easy": (6, 6),
    "medium": (9, 10),
    "hard": (13, 13),
}


@dataclass(frozen=True)
class _Frame:
    color: int
    r0: int
    c0: int
    r1: int
    c1: int

    @property
    def height(self) -> int:
        return self.r1 - self.r0 + 1

    @property
    def width(self) -> int:
        return self.c1 - self.c0 + 1

    @property
    def interior_area(self) -> int:
        return (self.height - 2) * (self.width - 2)

    @property
    def interior_cells(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (row, col)
            for row in range(self.r0 + 1, self.r1)
            for col in range(self.c0 + 1, self.c1)
        )


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTY_COUNTS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if "n_frames" in overrides and type(overrides["n_frames"]) is not int:
        raise ValueError("n_frames must be an integer")
    if "branch_profile" in overrides and not isinstance(
        overrides["branch_profile"], str
    ):
        raise ValueError("branch_profile must be a string")


def _scheduled_profile(sample_index: int) -> str:
    return _BRANCH_PROFILES[sample_index % len(_BRANCH_PROFILES)]


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the three-residue curriculum schedule to the semantic gate."""
    del seed, difficulty
    return sample_index % 3


SCHEDULE_PROFILES = (0, 1, 2)


def _default_frame_count(
    ctx, difficulty: str | None, profile_hint: str, sample_index: int
) -> int:
    # One fixed canonical-scale anchor per twelve samples keeps every band tied
    # to the literal 6x6, two-color training profile.
    if sample_index % 12 == 0 and profile_hint != "mixed":
        return 1
    options = list(_DIFFICULTY_COUNTS[difficulty])
    if profile_hint == "mixed":
        options = [value for value in options if value >= 2]
    return int(ctx.draw_rng("n_frames_default").choice(options))


def _frame_sizes(n_frames: int, profile: str, rng) -> list[tuple[int, int]]:
    if profile == "single_only":
        sizes = [(3, 3)] * n_frames
    elif profile == "multi_only":
        offset = rng.randrange(len(_MULTI_SHAPES))
        sizes = [
            _MULTI_SHAPES[(offset + index) % len(_MULTI_SHAPES)]
            for index in range(n_frames)
        ]
    elif profile == "mixed":
        if n_frames < 2:
            raise ValueError("n_frames=1 is incompatible with branch_profile='mixed'")
        offset = rng.randrange(len(_MULTI_SHAPES))
        sizes = [(3, 3), _MULTI_SHAPES[offset]]
        for index in range(2, n_frames):
            if index % 2 == 0:
                sizes.append((3, 3))
            else:
                sizes.append(
                    _MULTI_SHAPES[(offset + index) % len(_MULTI_SHAPES)]
                )
    else:  # guarded by ctx.draw_choice, retained as a loud local invariant
        raise ValueError(f"unknown branch profile: {profile!r}")
    rng.shuffle(sizes)
    return sizes


def _frame_colors(ctx, sizes: list[tuple[int, int]], profile: str) -> list[int]:
    colors = list(
        ctx.draw_distinct_colors(
            "frame_colors", n=len(sizes), exclude={0, 5, 7}
        )
    )
    if profile == "mixed":
        single = next(
            index
            for index, (height, width) in enumerate(sizes)
            if (height - 2) * (width - 2) == 1
        )
        multi = next(
            index
            for index, (height, width) in enumerate(sizes)
            if (height - 2) * (width - 2) > 1
        )
        # Reusing one border color across opposite branches explicitly refutes
        # any lesson that maps border color directly to gray/orange.
        colors[multi] = colors[single]
    return colors


def _packed_layout(
    sizes: list[tuple[int, int]], rng
) -> tuple[list[tuple[int, int]], int, int]:
    n_frames = len(sizes)
    columns = 1 if n_frames == 1 else 2 if n_frames <= 4 else 3
    rows = (n_frames + columns - 1) // columns
    slot_h = max(height for height, _ in sizes) + 1
    slot_w = max(width for _, width in sizes) + 1
    content_h = rows * slot_h - 1
    content_w = columns * slot_w - 1

    slots = [(row, col) for row in range(rows) for col in range(columns)]
    rng.shuffle(slots)
    positions: list[tuple[int, int]] = []
    for (height, width), (slot_row, slot_col) in zip(sizes, slots):
        jitter_r = rng.randint(0, slot_h - 1 - height)
        jitter_c = rng.randint(0, slot_w - 1 - width)
        positions.append(
            (slot_row * slot_h + jitter_r, slot_col * slot_w + jitter_c)
        )
    return positions, content_h, content_w


def _canvas_and_offset(
    content_h: int,
    content_w: int,
    difficulty: str | None,
    sample_index: int,
    n_frames: int,
    profile: str,
    rng,
) -> tuple[int, int, int, int]:
    if sample_index % 12 == 0 and n_frames == 1 and profile == "single_only":
        height = width = 6
    else:
        min_h, min_w = _DIFFICULTY_MIN_CANVAS[difficulty]
        pad_limit = {None: 4, "easy": 3, "medium": 5, "hard": 6}[difficulty]
        height = max(min_h, content_h + rng.randint(0, pad_limit))
        width = max(min_w, content_w + rng.randint(0, pad_limit))
    if content_h > height or content_w > width:
        raise RuntimeError(
            f"internal layout {content_h}x{content_w} exceeds canvas {height}x{width}"
        )
    return (
        height,
        width,
        rng.randint(0, height - content_h),
        rng.randint(0, width - content_w),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid for the canonical Racket rule."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = _scheduled_profile(sample_index)
    profile_hint = overrides.get("branch_profile", scheduled)
    if "n_frames" in overrides:
        n_frames = ctx.draw_int("n_frames", 1, 5)
    else:
        selected = _default_frame_count(
            ctx, difficulty, str(profile_hint), sample_index
        )
        n_frames = int(ctx.draw_choice("n_frames", (selected,)))

    allowed_profiles = (
        ("single_only", "multi_only") if n_frames == 1 else _BRANCH_PROFILES
    )
    if "branch_profile" in overrides:
        profile = str(ctx.draw_choice("branch_profile", allowed_profiles))
    else:
        selected_profile = scheduled
        if selected_profile == "mixed" and n_frames == 1:
            selected_profile = "single_only" if sample_index % 2 == 0 else "multi_only"
        profile = str(ctx.draw_choice("branch_profile", (selected_profile,)))

    rng = ctx.draw_rng(f"layout_{difficulty or 'all'}")
    sizes = _frame_sizes(n_frames, profile, rng)
    colors = _frame_colors(ctx, sizes, profile)
    positions, content_h, content_w = _packed_layout(sizes, rng)
    height, width, offset_r, offset_c = _canvas_and_offset(
        content_h,
        content_w,
        difficulty,
        sample_index,
        n_frames,
        profile,
        rng,
    )

    grid = full_grid(height, width, 0)
    for (frame_h, frame_w), color, (row, col) in zip(
        sizes, colors, positions
    ):
        draw_rect_outline(
            grid,
            offset_r + row,
            offset_c + col,
            frame_h,
            frame_w,
            color,
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid frame scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"n_frames": n_frames, "branch_profile": profile}
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost exact axis values: expected {expected}, got {observed}"
        )
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _components_by_color(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                rr, cc = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _analyze(grid: Any) -> tuple[list[_Frame], list[str]]:
    errors = _shape_errors(grid)
    if errors:
        return [], errors
    height, width = len(grid), len(grid[0])
    if not any(value == 0 for row in grid for value in row):
        errors.append("at least one background cell is required")

    # Different colored borders must not touch orthogonally.  Same-colored
    # touching borders merge in the component pass and fail rectangle shape.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    nr < height
                    and nc < width
                    and grid[nr][nc] != 0
                    and grid[nr][nc] != color
                ):
                    errors.append("different frames touch orthogonally")
                    return [], errors

    frames: list[_Frame] = []
    for color, cells in _components_by_color(grid):
        if color in (5, 7):
            errors.append(f"frame color {color} collides with output fill colors")
            continue
        r0 = min(row for row, _ in cells)
        r1 = max(row for row, _ in cells)
        c0 = min(col for _, col in cells)
        c1 = max(col for _, col in cells)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            errors.append(f"color {color} component is smaller than 3x3")
            continue
        border = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if row in (r0, r1) or col in (c0, c1)
        }
        if cells != border:
            errors.append(
                f"color {color} component is not a complete hollow rectangle outline"
            )
            continue
        interior = [
            grid[row][col]
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
        ]
        if not interior or any(value != 0 for value in interior):
            errors.append(f"color {color} frame interior must be nonempty and all zero")
            continue
        frames.append(_Frame(color, r0, c0, r1, c1))

    if not frames:
        errors.append("at least one hollow frame is required")
    if len(frames) > 5:
        errors.append(f"at most five frames are lawful, got {len(frames)}")
    frames.sort(key=lambda frame: (frame.r0, frame.c0, frame.color))
    return frames, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed inputs while accepting every canonical train/test input."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold: isolated zero-interior rectangle outlines."""
    return self_check(grid)


def _branch_profile(frames: list[_Frame]) -> str:
    single = any(frame.interior_area == 1 for frame in frames)
    multi = any(frame.interior_area > 1 for frame in frames)
    if single and multi:
        return "mixed"
    if single:
        return "single_only"
    return "multi_only"


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every exact declared axis from a returned lawful grid."""
    frames, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
    return {
        "n_frames": len(frames),
        "branch_profile": _branch_profile(frames),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    frames, errors = _analyze(grid)
    if errors:
        return {"valid": False, "errors": errors}
    single_colors = {
        frame.color for frame in frames if frame.interior_area == 1
    }
    multi_colors = {
        frame.color for frame in frames if frame.interior_area > 1
    }
    return {
        "valid": True,
        **observe_overrides(grid),
        "frame_sizes": tuple((frame.height, frame.width) for frame in frames),
        "interior_areas": tuple(frame.interior_area for frame in frames),
        "frame_colors": tuple(frame.color for frame in frames),
        "palette_size": len({value for row in grid for value in row}),
        "same_color_cross_branch": bool(single_colors & multi_colors),
        "changed_cell_count": sum(frame.interior_area for frame in frames),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests; Racket stays authoritative."""
    frames, errors = _analyze(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful frame scene: " + "; ".join(errors))
    output = [row[:] for row in grid]
    for frame in frames:
        fill = 5 if frame.interior_area == 1 else 7
        for row, col in frame.interior_cells:
            output[row][col] = fill
    return output


def _uniform_fill(grid: list[list[int]], fill: int) -> list[list[int]]:
    frames, errors = _analyze(grid)
    if errors:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    for frame in frames:
        for row, col in frame.interior_cells:
            output[row][col] = fill
    return output


def _all_orange(grid):
    return _uniform_fill(grid, 7)


def _all_gray(grid):
    return _uniform_fill(grid, 5)


def _center_only(grid):
    frames, errors = _analyze(grid)
    if errors:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    for frame in frames:
        cells = frame.interior_cells
        row, col = cells[len(cells) // 2]
        output[row][col] = 5 if frame.interior_area == 1 else 7
    return output


def _fill_by_border_color(grid):
    frames, errors = _analyze(grid)
    if errors:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    for frame in frames:
        fill = 5 if frame.color % 2 == 0 else 7
        for row, col in frame.interior_cells:
            output[row][col] = fill
    return output


def _fill_by_frame_count(grid):
    frames, errors = _analyze(grid)
    if errors:
        return [row[:] for row in grid]
    return _uniform_fill(grid, 5 if len(frames) <= 2 else 7)


def _identity(grid):
    return [row[:] for row in grid]


def _single_cell_witness(grid) -> bool:
    frames, errors = _analyze(grid)
    return not errors and any(frame.interior_area == 1 for frame in frames)


def _multi_cell_witness(grid) -> bool:
    frames, errors = _analyze(grid)
    return not errors and any(frame.interior_area > 1 for frame in frames)


def _mixed_witness(grid) -> bool:
    frames, errors = _analyze(grid)
    return not errors and _branch_profile(frames) == "mixed"


def _same_color_cross_branch_witness(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("same_color_cross_branch"))


def _non_square_multi_witness(grid) -> bool:
    frames, errors = _analyze(grid)
    return not errors and any(
        frame.interior_area > 1 and frame.height != frame.width for frame in frames
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "single_cell_gray_branch": _single_cell_witness,
    "multi_cell_orange_branch": _multi_cell_witness,
    "mixed_branches_in_one_scene": _mixed_witness,
    "same_border_color_cross_branch": _same_color_cross_branch_witness,
    "non_square_multi_cell_frame": _non_square_multi_witness,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "fill_every_interior_orange": _all_orange,
    "fill_every_interior_gray": _all_gray,
    "fill_only_one_interior_cell": _center_only,
    "choose_fill_from_border_color": _fill_by_border_color,
    "choose_one_fill_from_frame_count": _fill_by_frame_count,
}

WITNESS_RIVALS = {
    "single_cell_gray_branch": ["fill_every_interior_orange"],
    "multi_cell_orange_branch": [
        "fill_every_interior_gray",
        "fill_only_one_interior_cell",
    ],
    "mixed_branches_in_one_scene": ["choose_one_fill_from_frame_count"],
    "same_border_color_cross_branch": ["choose_fill_from_border_color"],
    "non_square_multi_cell_frame": ["fill_only_one_interior_cell"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut fits every demo but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the frame-fill rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed scenes that structural self_check must reject."""
    broken = full_grid(7, 9, 0)
    draw_rect_outline(broken, 1, 1, 4, 4, 3)
    broken[1][1] = 0

    solid = full_grid(7, 9, 0)
    for row in range(1, 4):
        for col in range(1, 4):
            solid[row][col] = 4

    prefilled = full_grid(7, 9, 0)
    draw_rect_outline(prefilled, 1, 1, 3, 4, 2)
    prefilled[2][2] = 7

    stray_dot = full_grid(7, 9, 0)
    draw_rect_outline(stray_dot, 1, 1, 3, 3, 6)
    stray_dot[5][7] = 8

    touching = full_grid(7, 9, 0)
    draw_rect_outline(touching, 1, 0, 3, 3, 2)
    draw_rect_outline(touching, 1, 3, 3, 3, 4)

    return [
        ("broken_rectangle_border", broken),
        ("solid_rectangle", solid),
        ("prefilled_interior", prefilled),
        ("valid_frame_plus_stray_dot", stray_dot),
        ("orthogonally_touching_frames", touching),
    ]
