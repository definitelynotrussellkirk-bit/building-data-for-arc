"""Generator for the smallest exact enclosing-frame recoloring task.

A color-1 marker is recolored by the smallest *intact same-color connected
rectangular outline* that strictly encloses it.  An apparent frame whose edge
has been overwritten is not a frame, so a marker enclosed only by that broken
outline remains color 1.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "72a261e69372"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d763a0664108"
SUMMARY = (
    "Generate two or three distinct-color rectangular outlines with one color-1 "
    "marker assigned to every color role. Nested scenes require choosing the "
    "smallest intact enclosing outline. Overlap scenes draw a later intact frame "
    "across an earlier outline, so the earlier color is only an occluded frame "
    "fragment and its marker must remain 1."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0 and markers are color 1",
    "every non-marker color denotes one intact or visibly occluded rectangular outline",
    "an occluded outline is missing only cells overwritten by an intact frame",
    "every intact frame is the smallest enclosing frame for at least one marker",
    "every occluded frame has an orphan marker that no intact frame encloses",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor or rng", "valid": "11..18"},
    "grid_w": {"type": "int", "default": "canonical anchor or rng", "valid": "13..20"},
    "n_frames": {"type": "int", "default": "canonical anchor or rng", "valid": "2..3"},
    "layout_kind": {"type": "str", "default": "alternating", "valid": "nested|overlap"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "low|high|mixed"},
}

_INT_DOMAINS = {
    "grid_h": range(11, 19),
    "grid_w": range(13, 21),
    "n_frames": range(2, 4),
}
_CHOICE_DOMAINS = {
    "layout_kind": ("nested", "overlap"),
    "palette_kind": ("low", "high", "mixed"),
}
_PALETTES = {
    "low": (2, 3, 4),
    "high": (7, 8, 9),
    "mixed": (2, 6, 9),
}
_CANONICAL_ANCHORS = {
    "p11": (11, 13, 2),
    "p12": (12, 14, 3),
    "p13": (13, 15, 3),
}


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
    for name, domain in _CHOICE_DOMAINS.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not str or value not in domain:
            raise ValueError(f"{name} must be one of {'|'.join(domain)}")


def _profile_anchor(sample_index: int, difficulty) -> str:
    """Deterministic 80% canonical-scale schedule, with one broad slot."""
    schedules = {
        "easy": ("p11", "p11", "p12", "p13", "broad"),
        "medium": ("p12", "p12", "p13", "p11", "broad"),
        "hard": ("p13", "p13", "p12", "p11", "broad"),
    }
    schedule = schedules.get(difficulty, ("p11", "p12", "p13", "p11", "broad"))
    return schedule[sample_index % len(schedule)]


def _axis_options(name: str, *, anchor: str, overrides: dict):
    if name in overrides or anchor == "broad":
        if name in _INT_DOMAINS:
            return tuple(_INT_DOMAINS[name])
        return _CHOICE_DOMAINS[name]
    index = {"grid_h": 0, "grid_w": 1, "n_frames": 2}[name]
    return (_CANONICAL_ANCHORS[anchor][index],)


def _inside(box: tuple[int, int, int, int], point: tuple[int, int]) -> bool:
    r1, c1, r2, c2 = box
    r, c = point
    return r1 < r < r2 and c1 < c < c2


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    comp.add(point)
                    stack.append(point)
        result.append(comp)
    return result


def _is_exact_outline(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    box = _bbox(cells)
    return box[2] - box[0] >= 2 and box[3] - box[1] >= 2 and cells == _outline(box)


def _exact_frames(grid: list[list[int]]) -> list[tuple[int, tuple[int, int, int, int]]]:
    colors = sorted({value for row in grid for value in row if value not in (0, 1)})
    result = []
    for color in colors:
        for comp in _components(grid, color):
            if _is_exact_outline(comp):
                result.append((color, _bbox(comp)))
    return result


def _color_boxes(grid: list[list[int]]) -> list[tuple[int, tuple[int, int, int, int]]]:
    colors = sorted({value for row in grid for value in row if value not in (0, 1)})
    return [
        (
            color,
            _bbox(
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value == color
            ),
        )
        for color in colors
    ]


def _smallest_frame_output(
    grid: list[list[int]], *, use_color_bboxes: bool = False, outermost: bool = False
) -> list[list[int]]:
    """Task rule mirror used only for executable rivals and witnesses."""
    out = deepcopy(grid)
    candidates = _color_boxes(grid) if use_color_bboxes else _exact_frames(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            enclosing = [(color, box) for color, box in candidates if _inside(box, (r, c))]
            if not enclosing:
                continue
            enclosing.sort(
                key=lambda item: (item[1][2] - item[1][0] + 1)
                * (item[1][3] - item[1][1] + 1),
                reverse=outermost,
            )
            out[r][c] = enclosing[0][0]
    return out


def _pick(candidates: list[tuple[int, int]], rng, label: str) -> tuple[int, int]:
    if not candidates:
        raise ValueError(f"no legal marker cell for {label}")
    return candidates[rng.randrange(len(candidates))]


def _draw_nested(grid: list[list[int]], colors: list[int], ctx) -> None:
    h, w = len(grid), len(grid[0])
    if len(colors) == 2:
        boxes = [(1, 1, h - 2, w - 2), (3, 3, h - 4, w - 4)]
    else:
        boxes = [(0, 0, h - 1, w - 1), (2, 2, h - 3, w - 3), (4, 4, h - 5, w - 5)]
    for color, box in zip(colors, boxes):
        draw_frame(grid, *box, color)

    for index, box in enumerate(boxes):
        candidates = []
        for r in range(h):
            for c in range(w):
                if grid[r][c] != 0 or not _inside(box, (r, c)):
                    continue
                enclosing = [j for j, candidate in enumerate(boxes) if _inside(candidate, (r, c))]
                if enclosing and max(enclosing) == index:
                    candidates.append((r, c))
        r, c = _pick(candidates, ctx.draw_rng(f"marker_nested_{index}"), f"nested frame {index}")
        grid[r][c] = 1


def _draw_overlap(grid: list[list[int]], colors: list[int], ctx) -> None:
    h, w = len(grid), len(grid[0])
    mid = w // 2 + 1
    broken = (1, 1, h - 2, mid)
    occluder = (2, mid - 1, h - 3, w - 1)
    intact_inner = (3, 3, h - 4, mid - 2) if len(colors) == 3 else None

    draw_frame(grid, *broken, colors[0])
    if intact_inner is not None:
        draw_frame(grid, *intact_inner, colors[1])
    draw_frame(grid, *occluder, colors[-1])

    exact_boxes = [box for box in (intact_inner, occluder) if box is not None]
    orphan_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0
        and _inside(broken, (r, c))
        and not any(_inside(box, (r, c)) for box in exact_boxes)
    ]
    r, c = _pick(orphan_candidates, ctx.draw_rng("marker_overlap_broken"), "occluded frame")
    grid[r][c] = 1

    if intact_inner is not None:
        inner_candidates = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == 0 and _inside(intact_inner, (r, c))
        ]
        r, c = _pick(inner_candidates, ctx.draw_rng("marker_overlap_inner"), "inner intact frame")
        grid[r][c] = 1

    occluder_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0
        and _inside(occluder, (r, c))
        and not _inside(broken, (r, c))
    ]
    r, c = _pick(occluder_candidates, ctx.draw_rng("marker_overlap_occluder"), "occluding frame")
    grid[r][c] = 1


def _reflect(grid: list[list[int]], orientation: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    if orientation & 1:
        result = [row[::-1] for row in result]
    if orientation & 2:
        result = result[::-1]
    return result


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
    anchor = _profile_anchor(sample_index, difficulty)
    # Record the internal curriculum branch without advertising it as an exact
    # caller control.
    ctx.draw_choice("profile_anchor", (anchor,))

    h = ctx.draw_choice("grid_h", _axis_options("grid_h", anchor=anchor, overrides=overrides))
    w = ctx.draw_choice("grid_w", _axis_options("grid_w", anchor=anchor, overrides=overrides))
    n_frames = ctx.draw_choice(
        "n_frames", _axis_options("n_frames", anchor=anchor, overrides=overrides)
    )
    layout_options = (
        _CHOICE_DOMAINS["layout_kind"]
        if "layout_kind" in overrides
        else (("nested",) if sample_index % 2 == 0 else ("overlap",))
    )
    layout_kind = ctx.draw_choice("layout_kind", layout_options)
    palette_kind = ctx.draw_choice("palette_kind", _CHOICE_DOMAINS["palette_kind"])

    colors = list(_PALETTES[palette_kind])
    ctx.draw_rng("palette_order").shuffle(colors)
    colors = colors[:n_frames]

    grid = full_grid(h, w, 0)
    if layout_kind == "nested":
        _draw_nested(grid, colors, ctx)
    else:
        _draw_overlap(grid, colors, ctx)
    orientation = ctx.draw_int("orientation", 0, 3)
    return _reflect(grid, orientation)


def _shape_analysis(grid: list[list[int]]):
    """Return exact frames, lawful occluded frames, and structural errors."""
    colors = sorted({value for row in grid for value in row if value not in (0, 1)})
    exact: list[tuple[int, tuple[int, int, int, int]]] = []
    occluded: list[tuple[int, tuple[int, int, int, int]]] = []
    missing_by_color: dict[int, set[tuple[int, int]]] = {}
    errors: list[str] = []

    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        box = _bbox(cells)
        expected = _outline(box)
        comps = _components(grid, color)
        exact_components = [comp for comp in comps if _is_exact_outline(comp)]
        if len(comps) == 1 and len(exact_components) == 1 and cells == expected:
            exact.append((color, box))
            continue
        missing = expected - cells
        if (
            box[2] - box[0] >= 2
            and box[3] - box[1] >= 2
            and cells < expected
            and bool(missing)
            and all(grid[r][c] not in (0, 1, color) for r, c in missing)
        ):
            occluded.append((color, box))
            missing_by_color[color] = missing
            continue
        errors.append(f"color {color} is neither one exact frame nor one overwritten frame outline")

    exact_colors = {color for color, _ in exact}
    for color, missing in missing_by_color.items():
        overwriters = {grid[r][c] for r, c in missing}
        if not overwriters <= exact_colors:
            errors.append(
                f"occluded color {color} has missing edge cells not overwritten by an intact frame"
            )
    return exact, occluded, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged or has a non-list row"]
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not (0 <= value <= 9)
    ]
    if bad_cells:
        return [f"grid has invalid ARC cell at {bad_cells[0]}"]
    h, w = len(grid), width
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")

    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    colors = sorted({value for row in grid for value in row if value not in (0, 1)})
    if len(colors) not in (2, 3):
        errors.append(f"expected 2 or 3 frame colors, found {len(colors)}")
    if len(markers) != len(colors):
        errors.append(f"expected one marker per frame color, found {len(markers)} markers")
    if errors:
        return errors

    exact, occluded, shape_errors = _shape_analysis(grid)
    errors.extend(shape_errors)
    if not exact:
        errors.append("no intact rectangular frame")
    if errors:
        return errors

    used_exact: set[int] = set()
    used_occluded: set[int] = set()
    for point in markers:
        enclosing = [(color, box) for color, box in exact if _inside(box, point)]
        if enclosing:
            chosen = min(
                enclosing,
                key=lambda item: (item[1][2] - item[1][0] + 1)
                * (item[1][3] - item[1][1] + 1),
            )
            used_exact.add(chosen[0])
            continue
        broken = [(color, box) for color, box in occluded if _inside(box, point)]
        if len(broken) != 1:
            errors.append(
                f"marker at {point} is enclosed by neither one intact frame nor exactly one occluded frame"
            )
        else:
            used_occluded.add(broken[0][0])

    unused_exact = sorted({color for color, _ in exact} - used_exact)
    unused_occluded = sorted({color for color, _ in occluded} - used_occluded)
    if unused_exact:
        errors.append(f"intact frame colors never selected by a marker: {unused_exact}")
    if unused_occluded:
        errors.append(f"occluded frame colors lack an orphan marker: {unused_occluded}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe axes on invalid grid: {errors}")
    colors = {value for row in grid for value in row if value not in (0, 1)}
    if colors <= set(_PALETTES["low"]):
        palette_kind = "low"
    elif colors <= set(_PALETTES["high"]):
        palette_kind = "high"
    elif colors <= set(_PALETTES["mixed"]):
        palette_kind = "mixed"
    else:
        raise ValueError(f"unrecognized palette family: {sorted(colors)}")
    _, occluded, _ = _shape_analysis(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(colors),
        "layout_kind": "overlap" if occluded else "nested",
        "palette_kind": palette_kind,
    }


def _has_occluded_frame(grid) -> bool:
    if self_check(grid):
        return False
    exact = _exact_frames(grid)
    exact_colors = {color for color, _ in exact}
    boxes = _color_boxes(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            if any(_inside(box, (r, c)) for _, box in exact):
                continue
            if any(color not in exact_colors and _inside(box, (r, c)) for color, box in boxes):
                return True
    return False


def _has_smallest_choice(grid) -> bool:
    if self_check(grid):
        return False
    frames = _exact_frames(grid)
    return any(
        sum(_inside(box, (r, c)) for _, box in frames) >= 2
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )


def _bbox_is_frame(grid):
    return _smallest_frame_output(grid, use_color_bboxes=True)


def _outermost_frame(grid):
    return _smallest_frame_output(grid, outermost=True)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a four-demo lesson if either named wrong rule survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar = self_check(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the task grammar: {grammar[0]}")
            continue
        if _smallest_frame_output(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the selected frame rule")
    if reasons:
        return sorted(set(reasons))

    layouts = {observe_overrides(pair["input"])["layout_kind"] for pair in demos}
    if layouts != {"nested", "overlap"}:
        reasons.append("demonstrations must include both nested and occluded-frame scenes")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival survives every demonstration: {name}")
    return sorted(set(reasons))


SEMANTIC_WITNESSES = {
    "occluded_frame": _has_occluded_frame,
    "smallest_not_outermost": _has_smallest_choice,
}
SEMANTIC_RIVALS = {
    "bbox_is_frame": _bbox_is_frame,
    "outermost_frame": _outermost_frame,
}
WITNESS_RIVALS = {
    "occluded_frame": ["bbox_is_frame"],
    "smallest_not_outermost": ["outermost_frame"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
