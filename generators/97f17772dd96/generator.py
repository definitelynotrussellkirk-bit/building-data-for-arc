"""Generate nested rectangular frames for ARC task 97f17772dd96.

The selected Racket rule is the output authority.  Inputs contain two or three
complete blue (1) rectangular outlines on a black (0) background.  Frames are
strictly nested with at least one black cell between adjacent outlines.  The
output keeps every blue outline and fills each black cell strictly inside
``depth`` frames with color ``depth + 1``; cells outside all frames stay black.

Canonical demonstrations happen to use concentric frames.  The ordinary
curriculum also emits offset inner frames so that a plausible "count only
concentric frames" shortcut is observably wrong.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97f17772dd96"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1fab8c098fd0"

SUMMARY = (
    "A 12-15 by 12-15 black grid contains two or three complete blue (1) "
    "rectangular frames, strictly nested with at least one black cell between "
    "adjacent outlines. Frames may be concentric or deliberately offset. Keep "
    "the blue outlines; for every black cell, count how many frames strictly "
    "contain it and paint depth+1 when depth is positive. Cells outside every "
    "frame remain black."
)

INVARIANTS = [
    "the input palette is exactly a subset of {0,1}",
    "there are exactly two or three disconnected complete color-1 rectangular outlines",
    "adjacent frames form one strict nesting chain with at least one 0-cell band",
    "offset and concentric nested layouts are both part of the generated domain",
]

AXES = {
    "grid_h": {"type": "int", "default": "six-profile curriculum", "valid": "12..15"},
    "grid_w": {"type": "int", "default": "six-profile curriculum", "valid": "12..15"},
    "n_frames": {"type": "int", "default": "six-profile curriculum", "valid": "2..3"},
    "asymmetry_force": {
        "type": "bool",
        "default": "six-profile curriculum with offset witnesses",
        "valid": "true|false",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

Grid = list[list[int]]
Box = tuple[int, int, int, int]

# The asymmetry pattern F,T,F,T,T,T has at least two offset scenes in every
# cyclic window of four.  Therefore every three-of-four rotated demo set still
# contains a direct counterexample to the concentric-only shortcut.
_DEFAULT_PROFILES: tuple[tuple[int, int, int, bool], ...] = (
    (12, 12, 2, False),
    (13, 13, 3, True),
    (15, 15, 3, False),
    (14, 14, 2, True),
    (12, 15, 3, True),
    (15, 12, 2, True),
)
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))

    for name in ("grid_h", "grid_w"):
        if name in overrides:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(f"{name} override must be an integer (not bool)")
            if not 12 <= value <= 15:
                raise ValueError(f"{name} override must be in 12..15")
    if "n_frames" in overrides:
        value = overrides["n_frames"]
        if type(value) is not int:
            raise TypeError("n_frames override must be an integer (not bool)")
        if value not in (2, 3):
            raise ValueError("n_frames override must be 2 or 3")
    if "asymmetry_force" in overrides and type(overrides["asymmetry_force"]) is not bool:
        raise TypeError("asymmetry_force override must be bool")


def _draw_axis(ctx, label: str, legal: tuple[Any, ...], scheduled: Any) -> Any:
    """Record an exact axis while preserving a deterministic default schedule."""
    options = legal if label in ctx.overrides else (scheduled,)
    return ctx.draw_choice(label, options)


def _outline(grid: Grid, box: Box) -> None:
    top, left, bottom, right = box
    for col in range(left, right + 1):
        grid[top][col] = 1
        grid[bottom][col] = 1
    for row in range(top, bottom + 1):
        grid[row][left] = 1
        grid[row][right] = 1


def _layout_boxes(height: int, width: int, n_frames: int, offset: bool, rng) -> list[Box]:
    transitions = n_frames - 1
    row_insets = [[2, 2] for _ in range(transitions)]
    col_insets = [[2, 2] for _ in range(transitions)]

    if offset:
        axis = rng.choice(("row", "col"))
        step = rng.randrange(transitions)
        pair = [2, 3]
        if rng.choice((False, True)):
            pair.reverse()
        if axis == "row":
            row_insets[step] = pair
        else:
            col_insets[step] = pair

    min_outer_h = 3 + sum(top + bottom for top, bottom in row_insets)
    min_outer_w = 3 + sum(left + right for left, right in col_insets)
    if min_outer_h > height or min_outer_w > width:
        raise ValueError("requested axes cannot fit the required nested frames")

    # Concentric defaults reproduce the canonical one-cell outer margin whenever
    # possible. Offset scenes stay large but may use a boundary-touching outer
    # frame at the 12-cell minimum needed for three unevenly inset frames.
    lo_h = max(min_outer_h, height - 2)
    lo_w = max(min_outer_w, width - 2)
    outer_h = rng.randint(lo_h, height)
    outer_w = rng.randint(lo_w, width)

    # Placement remains seed-driven even for concentric frames.  Equal per-side
    # insets preserve the common center; varying the outer box prevents one
    # schedule position from collapsing to a single byte-identical grid.
    top = rng.randint(0, height - outer_h)
    left = rng.randint(0, width - outer_w)
    bottom = top + outer_h - 1
    right = left + outer_w - 1

    boxes: list[Box] = [(top, left, bottom, right)]
    for (top_inset, bottom_inset), (left_inset, right_inset) in zip(row_insets, col_insets):
        top += top_inset
        bottom -= bottom_inset
        left += left_inset
        right -= right_inset
        boxes.append((top, left, bottom, right))
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket remains output authority."""
    _validate_call(seed, sample_index, difficulty, overrides)
    profile_index = (sample_index + _DIFFICULTY_OFFSETS[difficulty]) % len(_DEFAULT_PROFILES)
    scheduled_h, scheduled_w, scheduled_frames, scheduled_offset = _DEFAULT_PROFILES[profile_index]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, "grid_h", (12, 13, 14, 15), scheduled_h)
    width = _draw_axis(ctx, "grid_w", (12, 13, 14, 15), scheduled_w)
    n_frames = _draw_axis(ctx, "n_frames", (2, 3), scheduled_frames)
    offset = _draw_axis(ctx, "asymmetry_force", (False, True), scheduled_offset)

    grid = full_grid(height, width, 0)
    for box in _layout_boxes(height, width, n_frames, offset, ctx.draw_rng("layout")):
        _outline(grid, box)

    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_frames": n_frames,
        "asymmetry_force": offset,
    }
    if observed != requested:
        raise AssertionError(f"constructed axes {requested!r} observed as {observed!r}")
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Grid, color: int = 1) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        found.append(component)
    return found


def _bbox(cells: set[tuple[int, int]]) -> Box:
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _outline_cells(box: Box) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        *((top, col) for col in range(left, right + 1)),
        *((bottom, col) for col in range(left, right + 1)),
        *((row, left) for row in range(top, bottom + 1)),
        *((row, right) for row in range(top, bottom + 1)),
    }


def _center2(box: Box) -> tuple[int, int]:
    return box[0] + box[2], box[1] + box[3]


def analyze_grid(grid: Any) -> dict[str, Any]:
    """Return a non-throwing structural analysis used by validators and probes."""
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "frames": []}

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    palette = {value for row in normalized for value in row}
    if not palette <= {0, 1}:
        errors.append(f"input palette must be a subset of {{0,1}}, found {sorted(palette)}")

    frames: list[Box] = []
    for component in _components(normalized, 1):
        box = _bbox(component)
        if component != _outline_cells(box):
            errors.append(f"color-1 component is not one complete rectangular outline: bbox={box}")
            continue
        top, left, bottom, right = box
        if bottom - top < 2 or right - left < 2:
            errors.append(f"frame must enclose at least one cell: bbox={box}")
            continue
        frames.append(box)

    frames.sort(
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    if len(frames) not in (2, 3):
        errors.append(f"expected exactly two or three rectangular frames, found {len(frames)}")

    insets: list[tuple[int, int, int, int]] = []
    for outer, inner in zip(frames, frames[1:]):
        inset = (
            inner[0] - outer[0],
            inner[1] - outer[1],
            outer[2] - inner[2],
            outer[3] - inner[3],
        )
        insets.append(inset)
        if min(inset) < 2:
            errors.append(
                "frames must be strictly nested with at least one black cell "
                f"between outlines, found inset={inset}"
            )

    offset = bool(frames and any(_center2(frame) != _center2(frames[0]) for frame in frames[1:]))
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "frames": frames,
        "insets": insets,
        "asymmetry_force": offset,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = analyze_grid(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_frames": len(analysis["frames"]),
        "asymmetry_force": analysis["asymmetry_force"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = analyze_grid(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def strict_canonical_like(grid) -> list[str]:
    """The task manifold is exactly the validated two/three-frame grammar."""
    return self_check(grid)


def _valid_analysis(grid: Grid) -> dict[str, Any]:
    analysis = analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("invalid nested-frame input: " + "; ".join(analysis["errors"]))
    return analysis


def _paint_depths(grid: Grid, frames: list[Box]) -> Grid:
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 1:
                continue
            depth = sum(top < row < bottom and left < col < right for top, left, bottom, right in frames)
            output[row][col] = depth + 1 if depth else 0
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; selected Racket remains authority."""
    analysis = _valid_analysis(grid)
    return _paint_depths(grid, analysis["frames"])


def _rival_concentric_only(grid: Grid) -> Grid:
    """Wrong but canonical-fitting rule: ignore frames offset from the largest."""
    analysis = _valid_analysis(grid)
    frames: list[Box] = analysis["frames"]
    center = _center2(frames[0])
    return _paint_depths(grid, [frame for frame in frames if _center2(frame) == center])


def _has_offset_frame(grid: Any) -> bool:
    analysis = analyze_grid(grid)
    return not analysis["errors"] and bool(analysis["asymmetry_force"])


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "concentric_only": _rival_concentric_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "offset_inner_frame": _has_offset_frame,
}
WITNESS_RIVALS = {
    "offset_inner_frame": ["concentric_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared rival survives demos but changes query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} is outside the grammar: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Targeted malformed scenes retained for validator regression probes."""
    base = generate(910001, 1, difficulty="medium")
    analysis = analyze_grid(base)
    outer, inner = analysis["frames"][:2]
    fixtures: list[tuple[str, Grid]] = []

    broken = [row[:] for row in base]
    broken[outer[0]][outer[1] + 1] = 0
    fixtures.append(("broken_outer_outline", broken))

    bridge = [row[:] for row in base]
    col = inner[1]
    for row in range(outer[0] + 1, inner[0] + 1):
        bridge[row][col] = 1
    fixtures.append(("merged_frame_components", bridge))

    wrong_color = [row[:] for row in base]
    wrong_color[0][0] = 2
    fixtures.append(("foreign_palette_color", wrong_color))
    return fixtures
