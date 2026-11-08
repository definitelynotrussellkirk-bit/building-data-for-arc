"""Generator for the Deepest Seeded Frame ARC task.

Frames are color-1 rectangular outlines.  A color-2 seed makes every frame
that contains it "seeded"; only the deepest seeded frame in each independent
nesting chain has its interior filled with color 3.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "6c40e60caa4a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e82c2d54609b"
SUMMARY = (
    "Fill the interior of the deepest color-1 frame around each color-2 seed."
)

INVARIANTS = [
    "background is color 0",
    "every color-1 component is an exact rectangular outline",
    "nested frames form non-branching containment chains",
    "each independent chain has exactly one color-2 seed inside every frame",
    "only the deepest seeded frame in each chain fills with color 3",
]

SCENE_KINDS = ("single", "nested", "mixed")
SCHEDULE_PROFILES = SCENE_KINDS
LESSON_SCHEDULE = ("single", "mixed", "nested", "mixed")
LESSON_SCHEDULE_PERIOD = len(LESSON_SCHEDULE)
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "11, 12, or 13 from the four-slot lesson schedule",
        "valid": "11..15",
    },
    "grid_w": {
        "type": "int",
        "default": "11, 12, or 13 from the four-slot lesson schedule",
        "valid": "11..15",
    },
    "scene_kind": {
        "type": "str",
        "default": "single, mixed, nested, mixed in a deterministic cycle",
        "valid": "|".join(SCENE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_PROFILE_DIMENSIONS = {
    "single": (11, 11),
    "nested": (12, 12),
    "mixed": (13, 13),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the scheduled semantic branch for an ordinary draw."""
    del seed, difficulty
    return LESSON_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not 11 <= value <= 15:
            raise ValueError(f"{name} must be in 11..15")
    scene_kind = overrides.get("scene_kind")
    if scene_kind is not None:
        if type(scene_kind) is not str:
            raise TypeError("scene_kind must be a string")
        if scene_kind not in SCENE_KINDS:
            raise ValueError(
                f"scene_kind must be one of {', '.join(SCENE_KINDS)}"
            )


def _scheduled_int(ctx, label: str, target: int, overrides: dict) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, 11, 15)
    return ctx.draw_int_strict(label, target, target)


def _scheduled_scene(ctx, target: str, overrides: dict) -> str:
    options = SCENE_KINDS if overrides.get("scene_kind") is not None else (target,)
    return ctx.draw_choice("scene_kind", options)


def _place_seed(grid, box, rng) -> tuple[int, int]:
    r0, c0, r1, c1 = box
    row = rng.randint(r0 + 1, r1 - 1)
    col = rng.randint(c0 + 1, c1 - 1)
    grid[row][col] = 2
    return row, col


def _draw_single(grid, rng) -> None:
    h, w = len(grid), len(grid[0])
    frame_h = 5
    frame_w = 5
    top = rng.randint(0, h - frame_h)
    left = rng.randint(0, w - frame_w)
    box = (top, left, top + frame_h - 1, left + frame_w - 1)
    draw_frame(grid, *box, 1)
    _place_seed(grid, box, rng)


def _draw_nested_at(grid, top: int, left: int, rng) -> tuple[tuple[int, ...], tuple[int, ...]]:
    outer = (top, left, top + 6, left + 6)
    inner = (top + 2, left + 2, top + 4, left + 4)
    draw_frame(grid, *outer, 1)
    draw_frame(grid, *inner, 1)
    _place_seed(grid, inner, rng)
    return outer, inner


def _draw_nested(grid, rng) -> None:
    h, w = len(grid), len(grid[0])
    top = rng.randint(0, h - 7)
    left = rng.randint(0, w - 7)
    _draw_nested_at(grid, top, left, rng)


def _draw_mixed(grid, rng) -> None:
    """Draw one two-frame chain and one disjoint single frame.

    Horizontal and vertical layouts both fit the minimum 11x11 override.  The
    one-cell separator keeps the two color-1 roots disconnected.
    """
    h, w = len(grid), len(grid[0])
    candidates: list[tuple[str, int, int]] = []
    # orientation, single height, single width
    for single_h, single_w in ((3, 3), (4, 3)):
        if 7 + 1 + single_w <= w and max(7, single_h) <= h:
            candidates.append(("horizontal", single_h, single_w))
    for single_h, single_w in ((3, 3), (3, 4)):
        if 7 + 1 + single_h <= h and max(7, single_w) <= w:
            candidates.append(("vertical", single_h, single_w))
    if not candidates:
        raise ValueError(f"mixed scene cannot fit in {h}x{w}")

    orientation, single_h, single_w = rng.choice(candidates)
    if orientation == "horizontal":
        total_w = 7 + 1 + single_w
        left = rng.randint(0, w - total_w)
        nested_top = rng.randint(0, h - 7)
        single_top = rng.randint(0, h - single_h)
        _draw_nested_at(grid, nested_top, left, rng)
        single = (
            single_top,
            left + 8,
            single_top + single_h - 1,
            left + 8 + single_w - 1,
        )
    else:
        total_h = 7 + 1 + single_h
        top = rng.randint(0, h - total_h)
        nested_left = rng.randint(0, w - 7)
        single_left = rng.randint(0, w - single_w)
        _draw_nested_at(grid, top, nested_left, rng)
        single = (
            top + 8,
            single_left,
            top + 8 + single_h - 1,
            single_left + single_w - 1,
        )
    draw_frame(grid, *single, 1)
    _place_seed(grid, single, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    target_h, target_w = _PROFILE_DIMENSIONS[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, "grid_h", target_h, overrides)
    w = _scheduled_int(ctx, "grid_w", target_w, overrides)
    scene_kind = _scheduled_scene(ctx, profile, overrides)

    grid = full_grid(h, w, 0)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "default"
    rng = ctx.draw_rng(f"layout:{band}")
    if scene_kind == "single":
        _draw_single(grid, rng)
    elif scene_kind == "nested":
        _draw_nested(grid, rng)
    elif scene_kind == "mixed":
        _draw_mixed(grid, rng)
    else:  # protected by typed validation and draw_choice
        raise AssertionError(scene_kind)
    return grid


def _shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return None
    return len(grid), width


def _color_components(grid, color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] != color or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            component: set[tuple[int, int]] = set()
            while todo:
                r, c = todo.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(component)
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _strictly_contains(outer, inner) -> bool:
    or0, oc0, or1, oc1 = outer
    ir0, ic0, ir1, ic1 = inner
    return or0 < ir0 and oc0 < ic0 and ir1 < or1 and ic1 < oc1


def _boxes_disjoint(left, right) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return lr1 < rr0 or rr1 < lr0 or lc1 < rc0 or rc1 < lc0


def _inside(box, point) -> bool:
    r0, c0, r1, c1 = box
    r, c = point
    return r0 < r < r1 and c0 < c < c1


def _analyze(grid) -> dict:
    shape = _shape(grid)
    result = {
        "errors": [],
        "shape": shape,
        "frames": [],
        "parents": {},
        "roots": [],
        "groups": {},
        "seeds": [],
        "scene_kind": None,
    }
    errors: list[str] = result["errors"]
    if shape is None:
        errors.append("expected a nonempty rectangular grid")
        return result
    h, w = shape
    if not 11 <= h <= 15 or not 11 <= w <= 15:
        errors.append("grid dimensions must both be in 11..15")
    if any(type(value) is not int for row in grid for value in row):
        errors.append("every cell must be an integer")
        return result
    palette = {value for row in grid for value in row}
    if palette != {0, 1, 2}:
        errors.append(f"input palette must be exactly {{0,1,2}}, found {sorted(palette)}")

    components = _color_components(grid, 1)
    frames: list[tuple[int, int, int, int]] = []
    for component in components:
        box = _bbox(component)
        r0, c0, r1, c1 = box
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            errors.append(f"color-1 component at {box} is smaller than a 3x3 frame")
            continue
        if component != _perimeter(box):
            errors.append(f"color-1 component at {box} is not an exact frame")
            continue
        frames.append(box)
    result["frames"] = frames
    if not frames:
        errors.append("expected at least one exact color-1 frame")

    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            if (
                _strictly_contains(left, right)
                or _strictly_contains(right, left)
                or _boxes_disjoint(left, right)
            ):
                continue
            errors.append(f"frames {left} and {right} overlap without strict nesting")

    parents: dict[int, int | None] = {}
    for index, box in enumerate(frames):
        containers = [
            other
            for other, outer in enumerate(frames)
            if other != index and _strictly_contains(outer, box)
        ]
        parents[index] = (
            min(
                containers,
                key=lambda other: (
                    (frames[other][2] - frames[other][0] + 1)
                    * (frames[other][3] - frames[other][1] + 1)
                ),
            )
            if containers
            else None
        )
    result["parents"] = parents
    children: dict[int, list[int]] = {index: [] for index in range(len(frames))}
    for child, parent in parents.items():
        if parent is not None:
            children[parent].append(child)
    branching = [index for index, items in children.items() if len(items) > 1]
    if branching:
        errors.append(f"nested frames must form chains, not branches: {branching}")

    roots = [index for index, parent in parents.items() if parent is None]
    result["roots"] = roots
    groups: dict[int, list[int]] = {root: [] for root in roots}
    for index in range(len(frames)):
        root = index
        visited: set[int] = set()
        while parents.get(root) is not None:
            if root in visited:
                errors.append("frame containment cycle")
                break
            visited.add(root)
            root = parents[root]  # type: ignore[index]
        if root in groups:
            groups[root].append(index)
    result["groups"] = groups

    seeds = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    ]
    result["seeds"] = seeds
    seeds_by_root: dict[int, list[tuple[int, int]]] = {root: [] for root in roots}
    for seed in seeds:
        containing = [index for index, box in enumerate(frames) if _inside(box, seed)]
        if not containing:
            errors.append(f"seed {seed} is not inside a frame")
            continue
        seed_roots = {
            root for root, indices in groups.items() if any(i in indices for i in containing)
        }
        if len(seed_roots) != 1:
            errors.append(f"seed {seed} belongs to {len(seed_roots)} frame roots")
            continue
        root = next(iter(seed_roots))
        seeds_by_root[root].append(seed)
        if set(containing) != set(groups[root]):
            errors.append(f"seed {seed} is not inside every frame in its chain")

    for root, group in groups.items():
        if len(seeds_by_root.get(root, [])) != 1:
            errors.append(
                f"frame chain rooted at {frames[root]} must contain exactly one seed"
            )
        if not group:
            errors.append(f"empty frame chain at root {root}")

    signature = sorted(len(group) for group in groups.values())
    scene_kind = {
        (1,): "single",
        (2,): "nested",
        (1, 2): "mixed",
    }.get(tuple(signature))
    if scene_kind is None:
        errors.append(
            "frame-chain signature must be one single, one nested pair, or both"
        )
    result["scene_kind"] = scene_kind
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyze(grid)["errors"]


def observe_overrides(grid) -> dict:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    h, w = analysis["shape"]
    return {
        "grid_h": h,
        "grid_w": w,
        "scene_kind": analysis["scene_kind"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    h, w = analysis["shape"]
    scene_kind = analysis["scene_kind"]
    expected = _PROFILE_DIMENSIONS[scene_kind]
    if (h, w) != expected:
        return [
            f"canonical {scene_kind} profile is {expected[0]}x{expected[1]}, got {h}x{w}"
        ]
    return []


def _seeded_frame_indices(analysis: dict) -> list[int]:
    return [
        index
        for index, box in enumerate(analysis["frames"])
        if any(_inside(box, seed) for seed in analysis["seeds"])
    ]


def _fill_frame_interiors(grid, boxes: Sequence[tuple[int, int, int, int]]):
    output = deepcopy(grid)
    for r0, c0, r1, c1 in boxes:
        for row in range(r0 + 1, r1):
            for col in range(c0 + 1, c1):
                output[row][col] = 3
    return output


def expected_output(grid):
    """Independent Python mirror used for tests and semantic competitors."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    seeded = _seeded_frame_indices(analysis)
    deepest = [
        index
        for index in seeded
        if not any(
            other != index
            and _strictly_contains(analysis["frames"][index], analysis["frames"][other])
            for other in seeded
        )
    ]
    return _fill_frame_interiors(
        grid, [analysis["frames"][index] for index in deepest]
    )


def _fill_all_seeded_frames(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input")
    seeded = _seeded_frame_indices(analysis)
    return _fill_frame_interiors(
        grid, [analysis["frames"][index] for index in seeded]
    )


def _global_smallest_seeded_frame(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task input")
    seeded = _seeded_frame_indices(analysis)
    chosen = min(
        seeded,
        key=lambda index: (
            (analysis["frames"][index][2] - analysis["frames"][index][0] + 1)
            * (analysis["frames"][index][3] - analysis["frames"][index][1] + 1),
            analysis["frames"][index],
        ),
    )
    return _fill_frame_interiors(grid, [analysis["frames"][chosen]])


def _has_nested_depth(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["scene_kind"] in {"nested", "mixed"}


def _has_multiple_seeded_chains(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["scene_kind"] == "mixed"


SEMANTIC_WITNESSES = {
    "nested_depth": _has_nested_depth,
    "multiple_seeded_chains": _has_multiple_seeded_chains,
}
SEMANTIC_RIVALS = {
    "fill_all_seeded_frames": _fill_all_seeded_frames,
    "global_smallest_seeded_frame": _global_smallest_seeded_frame,
}
WITNESS_RIVALS = {
    "nested_depth": ["fill_all_seeded_frames"],
    "multiple_seeded_chains": ["global_smallest_seeded_frame"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "global_smallest_seeded_frame": _global_smallest_seeded_frame,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared rival survives and changes query."""
    reasons: list[str] = []
    query_input = query["input"]
    query_output = query.get("output")
    if query_output is None:
        query_output = expected_output(query_input)
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query_input) != query_output
        except Exception as exc:  # fail loud through the contract hook
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives and changes_query:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
