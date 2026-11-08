"""Input sampler for the nested-frame ownership-fill task.

The unchanged Racket authority keeps every exact monochrome rectangular border
and fills each zero cell with the color of the *smallest* enclosing operative
border.  Two-by-N terminal outlines are legal colored objects but have no
interior and are not operative under the authority's >=3-by-3 frame predicate.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94d475bf67ba"
TASK_ID = GENERATOR_ID
RULE_HASH = "beb1b900ffc7"
VERSION = "2.0.0"
SUMMARY = (
    "Two or three distinct-color exact rectangular outlines are strictly nested. "
    "Every operative outline owns a visible zero region, and four scheduled "
    "profiles teach smallest-enclosing-frame ownership independently of color rank."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid contains exactly two or three distinct nonzero colors",
    "each nonzero color is one connected exact rectangle outline",
    "outlines are strictly nested with at least one zero-cell ring between levels",
    "at least the two outermost outlines are operative (height and width >= 3)",
    "every operative outline owns at least one visible zero input cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "four-profile canonical-scale schedule", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "four-profile canonical-scale schedule", "valid": "10..18"},
    "n_frames": {"type": "int", "default": "alternating 2|3", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_INT_DOMAINS = {
    "grid_h": range(10, 19),
    "grid_w": range(10, 19),
    "n_frames": range(2, 4),
}

# Every four consecutive sample indices contain two ordinary two-level scenes
# and two deep three-operative-frame scenes.  The profiles also overlap the
# canonical grid/palette profiles exactly in every difficulty band.
_PROFILE_SPECS = {
    "two_11x11": (11, 11, 2),
    "three_12x12": (12, 12, 3),
    "two_10x13": (10, 13, 2),
    "three_12x14": (12, 14, 3),
}
SCHEDULE_PROFILES = tuple(_PROFILE_SPECS)
_PROFILE_ORDER = SCHEDULE_PROFILES


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum branch; seed/band only vary its pixels."""
    del seed, difficulty
    return _PROFILE_ORDER[sample_index % len(_PROFILE_ORDER)]


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int or value not in domain:
            raise ValueError(f"{name} must be an integer in {domain.start}..{domain.stop - 1}")


def _axis_options(name: str, profile: str, overrides: dict) -> tuple[int, ...]:
    if name in overrides:
        return tuple(_INT_DOMAINS[name])
    index = {"grid_h": 0, "grid_w": 1, "n_frames": 2}[name]
    return (_PROFILE_SPECS[profile][index],)


def _candidate_margin_pairs(limit: int, *, difficulty) -> list[tuple[int, int]]:
    pairs = [(a, b) for a in range(limit + 1) for b in range(limit + 1 - a)]
    if difficulty == "easy":
        balanced = [pair for pair in pairs if abs(pair[0] - pair[1]) <= 1]
        return balanced or pairs
    if difficulty == "medium":
        moderate = [pair for pair in pairs if max(pair) <= 2]
        return moderate or pairs
    return pairs


def _nested_intervals(size: int, n_frames: int, rng, *, difficulty) -> list[tuple[int, int]]:
    """Construct one dimension of nested boxes without rejection sampling."""
    # A three-level 10-cell override can only end in a 2-cell terminal outline.
    # At size >= 11 all levels are operative, which is true for both scheduled
    # three-frame profiles and supplies the decisive depth counterexample.
    terminal_min = 3 if size >= 4 * (n_frames - 1) + 3 else 2
    minimum_outer_span = terminal_min + 4 * (n_frames - 1)
    margin_budget = size - minimum_outer_span
    if margin_budget < 0:
        raise ValueError(f"size {size} cannot fit {n_frames} nested outlines")

    before, after = rng.choice(_candidate_margin_pairs(margin_budget, difficulty=difficulty))
    intervals = [(before, size - 1 - after)]
    for depth in range(1, n_frames):
        parent_start, parent_end = intervals[-1]
        parent_span = parent_end - parent_start + 1
        remaining_levels = n_frames - depth
        minimum_child_span = terminal_min + 4 * (remaining_levels - 1)
        extra_budget = parent_span - 4 - minimum_child_span
        if extra_budget < 0:
            raise RuntimeError("constructive nesting arithmetic became infeasible")
        extra_before, extra_after = rng.choice(
            _candidate_margin_pairs(extra_budget, difficulty=difficulty)
        )
        child_start = parent_start + 2 + extra_before
        child_end = parent_end - 2 - extra_after
        intervals.append((child_start, child_end))
    return intervals


def _boxes(h: int, w: int, n_frames: int, ctx, difficulty) -> list[tuple[int, int, int, int]]:
    rows = _nested_intervals(
        h, n_frames, ctx.draw_rng("row_geometry"), difficulty=difficulty
    )
    cols = _nested_intervals(
        w, n_frames, ctx.draw_rng("column_geometry"), difficulty=difficulty
    )
    return [(top, left, bottom, right) for (top, bottom), (left, right) in zip(rows, cols)]


def _ordered_colors(ctx, n_frames: int, sample_index: int) -> list[int]:
    colors = sorted(ctx.draw_rng("frame_colors").sample(range(1, 10), n_frames))
    phase = sample_index % 4
    if phase in (0, 3):
        colors.reverse()
    elif n_frames == 3 and phase == 2:
        colors = [colors[1], colors[2], colors[0]]
    return colors


def _draw_outline(grid: list[list[int]], box: tuple[int, int, int, int], color: int) -> None:
    top, left, bottom, right = box
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


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
    # Retain the branch in draw provenance without exposing a fake exact axis.
    ctx.draw_choice("curriculum_profile", (profile,))
    h = ctx.draw_choice("grid_h", _axis_options("grid_h", profile, overrides))
    w = ctx.draw_choice("grid_w", _axis_options("grid_w", profile, overrides))
    n_frames = ctx.draw_choice("n_frames", _axis_options("n_frames", profile, overrides))

    grid = full_grid(h, w, 0)
    boxes = _boxes(h, w, n_frames, ctx, difficulty)
    colors = _ordered_colors(ctx, n_frames, sample_index)
    for box, color in zip(boxes, colors):
        _draw_outline(grid, box, color)
    return grid


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty component")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def _inside(box: tuple[int, int, int, int], r: int, c: int) -> bool:
    top, left, bottom, right = box
    return top < r < bottom and left < c < right


def _analysis(grid) -> tuple[list[dict], list[str]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return [], ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return [], ["grid is ragged or contains a non-list row"]
    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        return [], [f"grid has invalid ARC cell at {invalid[0]}"]

    height = len(grid)
    errors: list[str] = []
    if not (10 <= height <= 18 and 10 <= width <= 18):
        errors.append(f"grid dimensions must be within 10..18, got {height}x{width}")
    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) not in (2, 3):
        errors.append(f"expected exactly 2 or 3 nonzero colors, found {len(colors)}")
    if errors:
        return [], errors

    frames: list[dict] = []
    for color in colors:
        components = _components(grid, color)
        if len(components) != 1:
            errors.append(f"color {color} has {len(components)} connected components, expected 1")
            continue
        cells = components[0]
        box = _bbox(cells)
        frame_h = box[2] - box[0] + 1
        frame_w = box[3] - box[1] + 1
        if frame_h < 2 or frame_w < 2 or cells != _outline(box):
            errors.append(f"color {color} is not one exact rectangle outline")
            continue
        frames.append(
            {
                "color": color,
                "box": box,
                "height": frame_h,
                "width": frame_w,
                "area": frame_h * frame_w,
                "operative": frame_h >= 3 and frame_w >= 3,
            }
        )
    if errors:
        return frames, errors

    frames.sort(key=lambda frame: frame["area"], reverse=True)
    for outer, inner in zip(frames, frames[1:]):
        ot, ol, ob, oright = outer["box"]
        it, il, ib, iright = inner["box"]
        gaps = (it - ot, il - ol, ob - ib, oright - iright)
        if min(gaps) < 2:
            errors.append(
                f"frame color {inner['color']} is not nested with a one-cell zero ring "
                f"inside color {outer['color']}: side gaps={gaps}"
            )
    operative = [frame for frame in frames if frame["operative"]]
    if len(operative) < 2:
        errors.append(f"expected at least two operative frames, found {len(operative)}")

    # Every operative frame must own at least one zero input cell not enclosed
    # by a smaller operative frame. This prevents decorative, unteachable roles.
    for frame in operative:
        smaller = [candidate for candidate in operative if candidate["area"] < frame["area"]]
        owned = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0
            and _inside(frame["box"], r, c)
            and not any(_inside(candidate["box"], r, c) for candidate in smaller)
        ]
        if not owned:
            errors.append(f"operative frame color {frame['color']} owns no visible zero cell")
    return frames, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _analysis(grid)
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    frames, errors = _analysis(grid)
    if errors:
        raise ValueError(f"cannot observe axes on invalid grid: {errors}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(frames)}


def _fill(grid, selector, *, frames=None) -> list[list[int]]:
    if frames is None:
        frames, errors = _analysis(grid)
        if errors:
            raise ValueError(f"invalid task grid: {errors}")
        frames = [frame for frame in frames if frame["operative"]]
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            enclosing = [frame for frame in frames if _inside(frame["box"], r, c)]
            if enclosing:
                output[r][c] = selector(enclosing)["color"]
    return output


def _innermost_owner(grid):
    return _fill(grid, lambda frames: min(frames, key=lambda frame: frame["area"]))


def _outermost_owner(grid):
    return _fill(grid, lambda frames: max(frames, key=lambda frame: frame["area"]))


def _maximum_color_owner(grid):
    return _fill(grid, lambda frames: max(frames, key=lambda frame: frame["color"]))


def _two_levels_only(grid):
    frames, errors = _analysis(grid)
    if errors:
        raise ValueError(f"invalid task grid: {errors}")
    operative = [frame for frame in frames if frame["operative"]][:2]
    return _fill(
        grid,
        lambda enclosing: min(enclosing, key=lambda frame: frame["area"]),
        frames=operative,
    )


def _third_operative_frame(grid) -> bool:
    frames, errors = _analysis(grid)
    return not errors and sum(frame["operative"] for frame in frames) >= 3 and _two_levels_only(grid) != _innermost_owner(grid)


def _innermost_not_outermost(grid) -> bool:
    return not self_check(grid) and _innermost_owner(grid) != _outermost_owner(grid)


def _numeric_color_not_role(grid) -> bool:
    return not self_check(grid) and _innermost_owner(grid) != _maximum_color_owner(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require four lawful demonstrations that refute every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = self_check(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the task grammar: {grammar[0]}")
            continue
        if _innermost_owner(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with innermost-frame ownership")
    if reasons:
        return sorted(set(reasons))

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival survives every demonstration: {name}")
    return sorted(reasons)


SEMANTIC_WITNESSES = {
    "third_operative_frame": _third_operative_frame,
    "innermost_not_outermost": _innermost_not_outermost,
    "numeric_color_not_role": _numeric_color_not_role,
}
SEMANTIC_RIVALS = {
    "two_levels_only": _two_levels_only,
    "outermost_owner": _outermost_owner,
    "maximum_color_owner": _maximum_color_owner,
}
WITNESS_RIVALS = {
    "third_operative_frame": ["two_levels_only"],
    "innermost_not_outermost": ["outermost_owner"],
    "numeric_color_not_role": ["maximum_color_owner"],
}
CANONICAL_SHORTCUTS = {"two_levels_only": _two_levels_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
