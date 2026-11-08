"""Generator for ARC task b28619e32f6f (legacy id 00dbd492).

The input is a 0-background grid containing one or more closed red (2)
boundaries.  Each 4-connected zero region that cannot reach the grid border is
recolored by its own area: at most 8 cells -> azure (8), at most 24 -> yellow
(4), and larger regions -> green (3).  Exterior zero remains unchanged.

The six-slot schedule repeats a split enclosure between single-bucket scenes.
Consequently every three-demo window contains all three area branches, an
outside region, off-boundary sizes, and a counterexample to the tempting
"choose one color per rectangular frame" shortcut.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "b28619e32f6f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1683fe78ae83"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Find every 4-connected zero region. Preserve border-connected exterior "
    "zero. Recolor each enclosed zero region independently by its cell count: "
    "size <=8 with 8, size <=24 with 4, and size >24 with 3; preserve red "
    "boundaries and interior red dividers."
)

INVARIANTS = [
    "input colors are exactly a subset of {0,2}, with background 0",
    "one or more complete red rectangular outer boundaries are present",
    "extra red cells may occur only inside a boundary as dividers or decoys",
    "at least one border-connected zero region and one enclosed zero region exist",
    "every enclosed region is nonempty and the output transformation is non-identity",
]

PROFILES = ("tiny", "medium", "large", "split_all")
SCHEDULE = ("split_all", "tiny", "split_all", "medium", "split_all", "large")
SCHEDULE_PROFILES = PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "six-slot split_all|tiny|split_all|medium|split_all|large schedule",
        "valid": "|".join(PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_PROFILE_DIMS = {
    "tiny": (7, 7),
    "medium": (9, 9),
    "large": (15, 15),
    "split_all": (20, 20),
}
_DIMS_TO_PROFILE = {dims: name for name, dims in _PROFILE_DIMS.items()}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _rectangular_grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "grid must be a nonempty list of rows"
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    return None


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def _box(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _strictly_inside(cell: tuple[int, int], box: tuple[int, int, int, int]) -> bool:
    r, c = cell
    r1, c1, r2, c2 = box
    return r1 < r < r2 and c1 < c < c2


def _zero_regions(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    regions: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        stack = [start]
        touches_border = False
        while stack:
            r, c = stack.pop()
            touches_border |= r in (0, h - 1) or c in (0, w - 1)
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        regions.append({"cells": cells, "size": len(cells), "enclosed": not touches_border})
    return regions


def _frames(grid: list[list[int]]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    red_components = _components(grid, 2)
    frame_components: list[tuple[set[tuple[int, int]], tuple[int, int, int, int]]] = []
    leftovers: list[set[tuple[int, int]]] = []
    for component in red_components:
        box = _box(component)
        r1, c1, r2, c2 = box
        expected = _border(box)
        if r2 - r1 + 1 >= 3 and c2 - c1 + 1 >= 3 and expected <= component:
            frame_components.append((component, box))
        else:
            leftovers.append(component)

    if not frame_components:
        return [], ["no complete red rectangular boundary found"]

    boxes = [box for _, box in frame_components]
    for left in range(len(boxes)):
        for right in range(left + 1, len(boxes)):
            a = boxes[left]
            b = boxes[right]
            if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                errors.append(f"frame boxes {left} and {right} overlap or nest")

    for component in leftovers:
        owners = [index for index, box in enumerate(boxes) if all(_strictly_inside(cell, box) for cell in component)]
        if len(owners) != 1:
            errors.append("red component is neither a frame nor an interior divider/decoy")

    frames: list[dict[str, Any]] = []
    regions = _zero_regions(grid)
    for component, box in frame_components:
        r1, c1, r2, c2 = box
        extras = component - _border(box)
        if any(not _strictly_inside(cell, box) for cell in extras):
            errors.append("frame has red cells outside its rectangular border")
        enclosed = [
            region
            for region in regions
            if region["enclosed"] and all(_strictly_inside(cell, box) for cell in region["cells"])
        ]
        if not enclosed:
            errors.append(f"frame {box} contains no enclosed zero region")
        frames.append({"box": box, "red_cells": component, "regions": enclosed})
    frames.sort(key=lambda frame: frame["box"])
    return frames, errors


def _analyze(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    shape_error = _rectangular_grid_error(grid)
    if shape_error:
        return [shape_error], None
    assert isinstance(grid, list)
    errors: list[str] = []
    invalid = [value for row in grid for value in row if type(value) is not int or value not in (0, 2)]
    if invalid:
        errors.append("input may contain only integer colors 0 and 2")
        return errors, None
    if not any(value == 0 for row in grid for value in row):
        errors.append("grid has no zero background")
    if not any(value == 2 for row in grid for value in row):
        errors.append("grid has no red boundary")
    if errors:
        return errors, None

    regions = _zero_regions(grid)
    enclosed = [region for region in regions if region["enclosed"]]
    exterior = [region for region in regions if not region["enclosed"]]
    if not enclosed:
        errors.append("no enclosed zero region")
    if not exterior:
        errors.append("no border-connected exterior zero region")

    frames, frame_errors = _frames(grid)
    errors.extend(frame_errors)
    enclosed_owned = {
        frozenset(region["cells"])
        for frame in frames
        for region in frame["regions"]
    }
    for region in enclosed:
        if frozenset(region["cells"]) not in enclosed_owned:
            errors.append("enclosed zero region is not contained by exactly one frame")

    analysis = {
        "height": len(grid),
        "width": len(grid[0]),
        "regions": regions,
        "enclosed": enclosed,
        "exterior": exterior,
        "frames": frames,
        "bucket_counts": {
            "tiny": sum(region["size"] <= 8 for region in enclosed),
            "medium": sum(8 < region["size"] <= 24 for region in enclosed),
            "large": sum(region["size"] > 24 for region in enclosed),
        },
    }
    return errors, analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed palettes, broken frames, stray red, and hidden rules."""
    del difficulty, meta
    errors, _analysis = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic census."""
    errors, _analysis = _analyze(grid)
    return errors


def _fill_color(size: int) -> int:
    if size <= 8:
        return 8
    if size <= 24:
        return 4
    return 3


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket oracle, used only for tests."""
    shape_error = _rectangular_grid_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    out = deepcopy(grid)
    for region in _zero_regions(grid):
        if region["enclosed"]:
            color = _fill_color(region["size"])
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the pinned six-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE[sample_index % len(SCHEDULE)]


def _place_single_frame(grid: list[list[int]], outer_h: int, outer_w: int, rng) -> None:
    h, w = len(grid), len(grid[0])
    r0 = rng.randint(0, h - outer_h)
    c0 = rng.randint(0, w - outer_w)
    draw_rect_outline(grid, r0, c0, outer_h, outer_w, 2)


def _place_split_frame(grid: list[list[int]], rng) -> None:
    h, w = len(grid), len(grid[0])
    inner_h = rng.choice((5, 6))
    medium_w = 3
    large_w = 6
    widths = (1, medium_w, large_w)
    outer_h = inner_h + 2
    outer_w = sum(widths) + 4
    r0 = rng.randint(0, h - outer_h)
    c0 = rng.randint(0, w - outer_w)
    draw_rect_outline(grid, r0, c0, outer_h, outer_w, 2)
    divider_1 = c0 + 1 + widths[0]
    divider_2 = divider_1 + 1 + widths[1]
    for r in range(r0, r0 + outer_h):
        grid[r][divider_1] = 2
        grid[r][divider_2] = 2

    # Two isolated interior red decoys reproduce the canonical scene's
    # multi-object complexity without changing the three area branches.
    decoy_row = r0 + 1 + inner_h // 2
    medium_start = divider_1 + 1
    large_start = divider_2 + 1
    grid[decoy_row][medium_start + medium_w // 2] = 2
    grid[decoy_row][large_start + large_w // 2] = 2


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform_square(grid: list[list[int]], turns: int, reflect: bool) -> list[list[int]]:
    out = deepcopy(grid)
    for _ in range(turns % 4):
        out = _rotate_clockwise(out)
    if reflect:
        out = [list(reversed(row)) for row in out]
    return out


def observe_overrides(grid) -> dict[str, str]:
    """Recover the sole exact semantic axis from the returned grid."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    dims = (analysis["height"], analysis["width"])
    profile = _DIMS_TO_PROFILE.get(dims)
    if profile is None:
        raise ValueError(f"unknown generated dimension profile: {dims}")
    required = {
        "tiny": {"tiny"},
        "medium": {"medium"},
        "large": {"large"},
        "split_all": {"tiny", "medium", "large"},
    }[profile]
    present = {name for name, count in analysis["bucket_counts"].items() if count}
    if present != required:
        raise ValueError(f"profile {profile!r} has bucket set {sorted(present)}, expected {sorted(required)}")
    if profile == "split_all" and not any(len(frame["regions"]) >= 3 for frame in analysis["frames"]):
        raise ValueError("split_all profile lacks one frame with three enclosed regions")
    return {"scene_profile": profile}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    choices = PROFILES if overrides.get("scene_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", choices)
    h, w = _PROFILE_DIMS[profile]
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng(f"layout_{profile}_{difficulty or 'medium'}")

    if profile == "tiny":
        _place_single_frame(grid, *rng.choice(((4, 4), (4, 5), (5, 4))), rng)
    elif profile == "medium":
        _place_single_frame(grid, *rng.choice(((5, 6), (6, 6), (6, 7))), rng)
    elif profile == "large":
        _place_single_frame(grid, *rng.choice(((7, 7), (7, 8), (8, 8))), rng)
    else:
        _place_split_frame(grid, rng)

    grid = _transform_square(grid, rng.randrange(4), bool(rng.randrange(2)))
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"observable axis mismatch: requested {profile!r}, observed {observed}")
    return grid


def _valid_analysis(grid):
    errors, analysis = _analyze(grid)
    return None if errors else analysis


def _has_bucket(name: str) -> Callable[[list[list[int]]], bool]:
    def witness(grid):
        analysis = _valid_analysis(grid)
        return analysis is not None and analysis["bucket_counts"][name] > 0
    return witness


def _off_boundary_small_or_medium(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    return any(region["size"] <= 24 and region["size"] not in (8, 24) for region in analysis["enclosed"])


def _split_frame_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(len(frame["regions"]) >= 3 for frame in analysis["frames"])


def _outside_zero_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and bool(analysis["exterior"])


def _nonidentity_witness(grid) -> bool:
    try:
        return rule_mirror(grid) != grid
    except ValueError:
        return False


def _copy(grid):
    return deepcopy(grid)


def _recolor_enclosed(grid, chooser: Callable[[int], int]) -> list[list[int]]:
    out = _copy(grid)
    for region in _zero_regions(grid):
        if region["enclosed"]:
            color = chooser(region["size"])
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def _rival_no_op(grid):
    return _copy(grid)


def _rival_all_8(grid):
    return _recolor_enclosed(grid, lambda _size: 8)


def _rival_all_4(grid):
    return _recolor_enclosed(grid, lambda _size: 4)


def _rival_all_3(grid):
    return _recolor_enclosed(grid, lambda _size: 3)


def _rival_exact_8_24_else_3(grid):
    return _recolor_enclosed(grid, lambda size: 8 if size == 8 else (4 if size == 24 else 3))


def _rival_fill_all_zero(grid):
    out = _copy(grid)
    enclosed_sizes = [region["size"] for region in _zero_regions(grid) if region["enclosed"]]
    color = _fill_color(enclosed_sizes[0]) if enclosed_sizes else 8
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 0:
                out[r][c] = color
    return out


def _rival_one_color_per_frame(grid):
    out = _copy(grid)
    analysis = _valid_analysis(grid)
    if analysis is None:
        return out
    for frame in analysis["frames"]:
        total = sum(region["size"] for region in frame["regions"])
        color = _fill_color(total)
        for region in frame["regions"]:
            for r, c in region["cells"]:
                out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "no_op": _rival_no_op,
    "all_enclosed_to_8": _rival_all_8,
    "all_enclosed_to_4": _rival_all_4,
    "all_enclosed_to_3": _rival_all_3,
    "exact_8_24_else_3": _rival_exact_8_24_else_3,
    "fill_all_zero": _rival_fill_all_zero,
    "one_color_per_frame": _rival_one_color_per_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "exact_8_24_else_3": _rival_exact_8_24_else_3,
    "one_color_per_frame": _rival_one_color_per_frame,
}

SEMANTIC_WITNESSES = {
    "tiny_region_branch": _has_bucket("tiny"),
    "medium_region_branch": _has_bucket("medium"),
    "large_region_branch": _has_bucket("large"),
    "off_boundary_size_refutes_exact_only": _off_boundary_small_or_medium,
    "split_frame_regions_are_independent": _split_frame_witness,
    "exterior_zero_is_preserved": _outside_zero_witness,
    "transformation_is_nonidentity": _nonidentity_witness,
}
WITNESS_RIVALS = {
    "tiny_region_branch": ["all_enclosed_to_4", "all_enclosed_to_3"],
    "medium_region_branch": ["all_enclosed_to_8", "all_enclosed_to_3"],
    "large_region_branch": ["all_enclosed_to_8", "all_enclosed_to_4"],
    "off_boundary_size_refutes_exact_only": "exact_8_24_else_3",
    "split_frame_regions_are_independent": "one_color_per_frame",
    "exterior_zero_is_preserved": "fill_all_zero",
    "transformation_is_nonidentity": "no_op",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which any named plausible rival survives."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} outside rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output disagrees with area-bucket rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query outside rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons
