"""Input generator for the smallest/largest hollow-frame ranking task.

The selected Racket authority compares frame *interior area*, fills the smallest
interior red (2), fills the largest interior cyan (8), and leaves every middle
frame hollow.  This sampler keeps that ranking unambiguous while deliberately
breaking two shortcuts that fit every public pair: "smallest is the 3x3 frame"
and "largest means widest".
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "e8fb1b5bedfe"
TASK_ID = GENERATOR_ID
RULE_HASH = "583ccfcccab0"
VERSION = "3.0.0"

SUMMARY = (
    "Two to four separated hollow color-4 rectangular frames have distinct "
    "interior areas.  Rank by interior area: fill only the smallest interior "
    "with 2 and only the largest with 8; middle frames stay hollow.  Scheduled "
    "shape profiles refute fixed-3x3 and widest-frame shortcuts."
)

INVARIANTS = [
    "background is 0 and every foreground component is one hollow color-4 rectangle",
    "there are exactly 2..4 frames, separated by at least one background row or column",
    "frame interior areas are all distinct, so smallest and largest are unique",
    "ordinary frame dimensions are 3..6 and interiors begin empty",
]

SCENE_PROFILE_DIMS = {
    "canonical_12": (12, 12),
    "canonical_13": (13, 13),
    "canonical_14": (14, 14),
}
SCENE_PROFILES = tuple(SCENE_PROFILE_DIMS)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted canonical_12|canonical_13|canonical_14",
        "valid": "canonical_12|canonical_13|canonical_14",
    },
    "n_frames": {
        "type": "int",
        "default": "scheduled 2..4; every 3-demo window includes a middle-frame case",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_shape_bias",
    "smallest_not_3x3",
    "widest_not_largest",
)

# Interior areas are distinct within every row.  The third profile has a unique
# width-6 frame whose area is *not* largest, providing an executable counterexample
# to the canonical-compatible "largest = widest" shortcut.
_SIZE_PROFILES = {
    "canonical_shape_bias": {
        2: ((3, 3), (5, 6)),
        3: ((3, 3), (4, 4), (5, 6)),
        4: ((3, 3), (3, 4), (4, 4), (5, 6)),
    },
    "smallest_not_3x3": {
        2: ((3, 4), (5, 5)),
        3: ((3, 4), (4, 4), (5, 5)),
        4: ((3, 4), (3, 5), (4, 4), (5, 5)),
    },
    "widest_not_largest": {
        2: ((3, 6), (6, 5)),
        3: ((3, 4), (3, 6), (6, 5)),
        4: ((3, 4), (3, 6), (4, 5), (6, 5)),
    },
}

_PROFILE_CHOICES = {
    None: ("canonical_12", "canonical_13", "canonical_14"),
    "easy": ("canonical_12", "canonical_12", "canonical_12", "canonical_13", "canonical_14"),
    "medium": ("canonical_12", "canonical_13", "canonical_13", "canonical_13", "canonical_14"),
    "hard": ("canonical_12", "canonical_13", "canonical_14", "canonical_14", "canonical_14"),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic semantic profile used by this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _rects_separated(left, right) -> bool:
    """True iff the two inclusive boxes have at least one blank row/column gap."""
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return (
        lr1 + 1 < rr0
        or rr1 + 1 < lr0
        or lc1 + 1 < rc0
        or rc1 + 1 < lc0
    )


def _oriented_sizes(profile: str, n_frames: int, rng) -> tuple[tuple[int, int], ...]:
    sizes = list(_SIZE_PROFILES[profile][n_frames])
    if profile != "widest_not_largest":
        # Area is invariant under this swap.  The shortcut profile stays in its
        # declared orientation so width 6 remains uniquely non-maximal by area.
        sizes = [
            (width, height) if height != width and rng.randrange(2) else (height, width)
            for height, width in sizes
        ]
    rng.shuffle(sizes)
    return tuple(sizes)


def _place_frames(h: int, w: int, sizes: tuple[tuple[int, int], ...], rng):
    """Finite backtracking placement; never returns a shortened frame set."""
    indexed = list(enumerate(sizes))
    indexed.sort(key=lambda item: (item[1][0] * item[1][1], max(item[1])), reverse=True)
    candidate_lists = []
    for _, (fh, fw) in indexed:
        candidates = [(r, c) for r in range(h - fh + 1) for c in range(w - fw + 1)]
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    placed_by_original: list[tuple[int, int, int, int] | None] = [None] * len(sizes)
    active: list[tuple[int, int, int, int]] = []

    def search(depth: int) -> bool:
        if depth == len(indexed):
            return True
        original_index, (fh, fw) = indexed[depth]
        for r0, c0 in candidate_lists[depth]:
            rect = (r0, c0, r0 + fh - 1, c0 + fw - 1)
            if any(not _rects_separated(rect, other) for other in active):
                continue
            placed_by_original[original_index] = rect
            active.append(rect)
            if search(depth + 1):
                return True
            active.pop()
            placed_by_original[original_index] = None
        return False

    if not search(0):
        raise ValueError(
            f"no separated placement for sizes={sizes!r} in {h}x{w}; "
            "the advertised override combination is not constructive"
        )
    return tuple(rect for rect in placed_by_original if rect is not None)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        if type(overrides["scene_profile"]) is not str:
            raise ValueError("scene_profile must be a string")
    if "n_frames" in overrides and overrides["n_frames"] is not None:
        if type(overrides["n_frames"]) is not int:
            raise ValueError("n_frames must be an integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _PROFILE_CHOICES.get(difficulty, _PROFILE_CHOICES[None]))
    semantic_profile = schedule_profile(seed, sample_index, difficulty)

    if overrides.get("n_frames") is not None:
        n_frames = ctx.draw_choice("n_frames", (2, 3, 4))
    elif semantic_profile == "canonical_shape_bias":
        # Every three consecutive samples includes one 3/4-frame demonstration,
        # so the "fill every non-small frame" rival cannot survive a 3-demo lesson.
        choices = (3, 3, 4) if difficulty == "easy" else ((3, 4) if difficulty == "medium" else (3, 4, 4))
        n_frames = ctx.draw_choice("n_frames", choices)
    else:
        choices = {
            "easy": (2, 2, 3, 4),
            "medium": (2, 3, 3, 4),
            "hard": (2, 3, 4, 4),
        }.get(difficulty, (2, 3, 4))
        n_frames = ctx.draw_choice("n_frames", choices)

    h, w = SCENE_PROFILE_DIMS[profile]
    layout_rng = ctx.draw_rng("layout")
    sizes = _oriented_sizes(semantic_profile, n_frames, ctx.draw_rng("frame_orientations"))
    rects = _place_frames(h, w, sizes, layout_rng)
    grid = full_grid(h, w, 0)
    for r0, c0, r1, c1 in rects:
        draw_frame(grid, r0, c0, r1, c1, 4)
    return grid


def _frame_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    frames = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 4 or (sr, sc) in seen:
                continue
            todo = [(sr, sc)]
            seen.add((sr, sc))
            cells = {(sr, sc)}
            for r, c in todo:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        todo.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            frames.append(
                {
                    "bbox": (r0, c0, r1, c1),
                    "cells": cells,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "area": (r1 - r0 - 1) * (c1 - c0 - 1),
                }
            )
    return sorted(frames, key=lambda frame: frame["bbox"])


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    errors = []
    if any(type(value) is not int or value not in (0, 4) for row in grid for value in row):
        errors.append("input cells must be integer colors 0 or 4")
    frames = _frame_components(grid)
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected exactly 2..4 frames, found {len(frames)}")

    areas = []
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        if frame["height"] < 3 or frame["width"] < 3:
            errors.append("frame bbox is smaller than 3x3")
            continue
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if frame["cells"] != border:
            errors.append("color-4 component is not exactly one hollow rectangular frame")
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
            errors.append("frame interior is not empty")
        areas.append(frame["area"])

    if len(areas) != len(set(areas)):
        errors.append("frame interior areas are not distinct")
    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            if not _rects_separated(left["bbox"], right["bbox"]):
                errors.append("frames are not separated by a background-cell gap")
                break
    return errors


def strict_canonical_like(grid):
    errors = list(self_check(grid))
    if errors:
        return errors
    dims = (len(grid), len(grid[0]))
    if dims not in set(SCENE_PROFILE_DIMS.values()):
        errors.append(f"grid dimensions {dims} are outside the declared canonical profiles")
    for frame in _frame_components(grid):
        if not (3 <= frame["height"] <= 6 and 3 <= frame["width"] <= 6):
            errors.append("frame dimensions must be in 3..6 for this teaching manifold")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    dims = (len(grid), len(grid[0]))
    profiles = [name for name, value in SCENE_PROFILE_DIMS.items() if value == dims]
    if len(profiles) != 1:
        raise ValueError(f"grid dimensions {dims} do not identify one scene_profile")
    return {"scene_profile": profiles[0], "n_frames": len(_frame_components(grid))}


def _fill_interior(out, frame, color):
    r0, c0, r1, c1 = frame["bbox"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = color


def _ranked_frames(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid frame grid: " + "; ".join(errors))
    return sorted(_frame_components(grid), key=lambda frame: frame["area"])


def _intended_output(grid):
    ranked = _ranked_frames(grid)
    out = deepcopy(grid)
    _fill_interior(out, ranked[0], 2)
    _fill_interior(out, ranked[-1], 8)
    return out


def _fixed_3x3_smallest(grid):
    """Wrong shortcut that nevertheless reproduces all public pairs."""
    ranked = _ranked_frames(grid)
    out = deepcopy(grid)
    small = next(
        (frame for frame in ranked if (frame["height"], frame["width"]) == (3, 3)),
        None,
    )
    if small is not None:
        _fill_interior(out, small, 2)
    _fill_interior(out, ranked[-1], 8)
    return out


def _widest_is_largest(grid):
    """Wrong shortcut that ranks the cyan frame by width instead of area."""
    ranked = _ranked_frames(grid)
    widest = max(
        ranked,
        key=lambda frame: (frame["width"], -frame["bbox"][0], -frame["bbox"][1]),
    )
    out = deepcopy(grid)
    _fill_interior(out, ranked[0], 2)
    _fill_interior(out, widest, 8)
    return out


def _fill_all_non_small(grid):
    """Wrong branch rule: colors middle frames cyan instead of leaving them hollow."""
    ranked = _ranked_frames(grid)
    out = deepcopy(grid)
    _fill_interior(out, ranked[0], 2)
    for frame in ranked[1:]:
        _fill_interior(out, frame, 8)
    return out


def _smallest_not_3x3_witness(grid):
    smallest = _ranked_frames(grid)[0]
    return (smallest["height"], smallest["width"]) != (3, 3)


def _widest_not_largest_witness(grid):
    ranked = _ranked_frames(grid)
    widths = [frame["width"] for frame in ranked]
    if widths.count(max(widths)) != 1:
        return False
    return max(ranked, key=lambda frame: frame["width"]) is not ranked[-1]


def _middle_frame_witness(grid):
    return len(_ranked_frames(grid)) >= 3


SEMANTIC_WITNESSES = {
    "smallest_not_3x3": _smallest_not_3x3_witness,
    "widest_not_largest": _widest_not_largest_witness,
    "middle_frame_unchanged": _middle_frame_witness,
}
SEMANTIC_RIVALS = {
    "fixed_3x3_smallest": _fixed_3x3_smallest,
    "widest_is_largest": _widest_is_largest,
    "fill_all_non_small": _fill_all_non_small,
}
WITNESS_RIVALS = {
    "smallest_not_3x3": ["fixed_3x3_smallest"],
    "widest_not_largest": ["widest_is_largest"],
    "middle_frame_unchanged": ["fill_all_non_small"],
}
CANONICAL_SHORTCUTS = {
    "fixed_3x3_smallest": _fixed_3x3_smallest,
    "widest_is_largest": _widest_is_largest,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(deepcopy(demo["input"])) == demo["output"] for demo in demos)
        except Exception as exc:
            reasons.append(f"competitor {name!r} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
