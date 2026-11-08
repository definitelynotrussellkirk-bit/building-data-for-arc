"""Generator for arc_additional_puzzle_bank_volume16:E108.

Every solid green (3) rectangle is converted to a cyan (8) perimeter while
strict interior cells stay green.  Other colored objects are distractors and
must be preserved exactly.

The canonical task contains both ordinary rectangles with green interiors and
a 2x3 rectangle whose entire body is perimeter.  Ordinary generation keeps
both branches visible and includes a non-green rectangle with the same shape
as a green target.  Color, rather than rectangle size, identifies what changes.
Every four consecutive draws contain two thin-target witnesses, so three
demonstrations retain one after any one of those four pairs becomes the query.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "34f8510e39d0"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
# Re-pinned to the selected commented authority by the task-scoped Racket sync.
RULE_HASH = "f97715331ac1"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a background-0 grid, find every solid green (3) axis-aligned rectangle. "
    "Recolor exactly its bounding-box perimeter cyan (8), leave strict green "
    "interior cells green, and preserve all non-green distractor objects."
)

INVARIANTS = [
    "background is 0 and remains visible",
    "every green component is one solid axis-aligned rectangle at least 2 cells in each dimension and area at least 6",
    "ordinary draws contain at least one interior-bearing green rectangle",
    "ordinary draws contain at least one non-green distractor that the rule leaves unchanged",
    "one non-green distractor matches the shape of a green target, refuting size-only selection",
    "a scheduled thin 2-cell-wide/high green rectangle exposes the all-perimeter branch",
]


@dataclass(frozen=True)
class SceneProfile:
    h: int
    w: int
    green_shapes: tuple[tuple[int, int], ...]
    distractor_count: int


SCENE_PROFILES: dict[str, SceneProfile] = {
    # Each (h, w, palette-size) tuple is one observed canonical profile.
    "canonical_8x10_two": SceneProfile(8, 10, ((3, 4), (3, 3)), 1),
    "canonical_9x9_single": SceneProfile(9, 9, ((4, 3),), 2),
    "canonical_7x12_thin_two": SceneProfile(7, 12, ((2, 3), (4, 4)), 1),
    "canonical_10x10_single": SceneProfile(10, 10, ((4, 5),), 1),
    "canonical_9x11_two": SceneProfile(9, 11, ((3, 5), (3, 3)), 1),
}
PROFILE_NAMES = tuple(SCENE_PROFILES)
_PROFILE_BY_DIMS = {(p.h, p.w): name for name, p in SCENE_PROFILES.items()}
DISTRACTOR_COLORS = (1, 2, 4, 5, 6, 7, 9)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot canonical-profile schedule",
        "valid": "canonical_8x10_two|canonical_9x9_single|canonical_7x12_thin_two|canonical_10x10_single|canonical_9x11_two",
        "doc": "Linked canonical-scale scene profile; exactly recoverable from grid dimensions.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)

_DEFAULT_PROFILE_BY_BAND = {
    "easy": (
        "canonical_7x12_thin_two",
        "canonical_8x10_two",
        "canonical_7x12_thin_two",
        "canonical_9x9_single",
    ),
    "medium": (
        "canonical_7x12_thin_two",
        "canonical_10x10_single",
        "canonical_7x12_thin_two",
        "canonical_8x10_two",
    ),
    "hard": (
        "canonical_7x12_thin_two",
        "canonical_9x11_two",
        "canonical_7x12_thin_two",
        "canonical_9x9_single",
    ),
    "all": (
        "canonical_7x12_thin_two",
        "canonical_8x10_two",
        "canonical_7x12_thin_two",
        "canonical_9x11_two",
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Four consecutive pairs contain two thin slots, surviving any holdout."""
    del seed, difficulty
    return int(sample_index) % LESSON_SCHEDULE_PERIOD


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}"
        )


def _draw_profile(ctx, sample_index: int, difficulty) -> str:
    if ctx.overrides.get("scene_profile") is not None:
        return ctx.draw_choice("scene_profile", PROFILE_NAMES)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "all"
    scheduled = _DEFAULT_PROFILE_BY_BAND[band][sample_index % LESSON_SCHEDULE_PERIOD]
    return ctx.draw_choice("scene_profile", (scheduled,))


def _separated_from(box, other, margin: int = 1) -> bool:
    r, c, h, w = box
    rr, cc, hh, ww = other
    return (
        r + h - 1 + margin < rr
        or rr + hh - 1 + margin < r
        or c + w - 1 + margin < cc
        or cc + ww - 1 + margin < c
    )


def _try_place_scene(profile_name: str, rng) -> list[list[int]] | None:
    profile = SCENE_PROFILES[profile_name]
    distractor_colors = rng.sample(
        list(DISTRACTOR_COLORS), profile.distractor_count
    )

    green_shapes = list(profile.green_shapes)
    # Vary orientation where it stays within the canonical task grammar.
    for index, (rh, rw) in enumerate(green_shapes):
        if rh != rw and rng.randrange(2):
            green_shapes[index] = (rw, rh)

    # The old distractors had area <= 4 while every target had area >= 6.
    # Matching a target's geometry makes that size-based shortcut observably wrong.
    matched_shape = max(green_shapes, key=lambda shape: shape[0] * shape[1])
    distractor_shapes = [matched_shape] + [
        rng.choice(((2, 1), (1, 2), (3, 1), (1, 3), (2, 2)))
        for _ in distractor_colors[1:]
    ]
    scene_items = [
        (3, rh, rw) for rh, rw in green_shapes
    ] + [
        (color, rh, rw)
        for color, (rh, rw) in zip(distractor_colors, distractor_shapes)
    ]
    # Place larger objects first to keep rejection inexpensive on the 7x12 case.
    scene_items.sort(key=lambda item: item[1] * item[2], reverse=True)

    grid = full_grid(profile.h, profile.w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for color, rh, rw in scene_items:
        legal: list[tuple[int, int]] = []
        for r in range(profile.h - rh + 1):
            for c in range(profile.w - rw + 1):
                box = (r, c, rh, rw)
                if all(_separated_from(box, other) for other in boxes):
                    legal.append((r, c))
        if not legal:
            return None
        r, c = rng.choice(legal)
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                grid[rr][cc] = color
        boxes.append((r, c, rh, rw))
    return grid


def _fallback_scene(profile_name: str) -> list[list[int]]:
    """Deterministic safe layout; used only if randomized placement exhausts."""
    profile = SCENE_PROFILES[profile_name]
    grid = full_grid(profile.h, profile.w, 0)
    layouts = {
        "canonical_8x10_two": [
            (3, 0, 0, 3, 4), (3, 4, 0, 3, 3), (5, 0, 5, 3, 4),
        ],
        "canonical_9x9_single": [
            (3, 0, 0, 4, 3), (5, 0, 4, 4, 3), (6, 6, 0, 1, 2),
        ],
        "canonical_7x12_thin_two": [
            (3, 5, 0, 2, 3), (3, 0, 0, 4, 4), (5, 0, 5, 4, 4),
        ],
        "canonical_10x10_single": [
            (3, 0, 0, 4, 5), (5, 5, 0, 4, 5),
        ],
        "canonical_9x11_two": [
            (3, 0, 0, 3, 5), (3, 4, 0, 3, 3), (5, 0, 6, 3, 5),
        ],
    }
    for color, r, c, rh, rw in layouts[profile_name]:
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                grid[rr][cc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    if isinstance(difficulty, str) and difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"invalid difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = _draw_profile(ctx, sample_index, difficulty)
    rng = ctx.draw_rng(f"scene:{profile_name}")

    grid = None
    for _ in range(48):
        grid = _try_place_scene(profile_name, rng)
        if grid is not None:
            break
    if grid is None:
        grid = _fallback_scene(profile_name)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(
            f"constructed invalid profile {profile_name!r}: {errors}"
        )
    if strict_canonical_like(grid):
        raise RuntimeError(
            f"constructed non-canonical-like profile {profile_name!r}: "
            f"{strict_canonical_like(grid)}"
        )
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile_name}:
        raise RuntimeError(
            f"profile round-trip failed: expected {profile_name!r}, observed {observed!r}"
        )
    return grid


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    errors: list[str] = []
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            return ["grid rows must be rectangular"]
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors


def _components_of_color(grid, color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    out: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        stack = [start]
        remaining.remove(start)
        comp = {start}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    comp.add((rr, cc))
                    stack.append((rr, cc))
        out.append(comp)
    return out


def _bbox(comp: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def _solid_rect(comp: set[tuple[int, int]]) -> tuple[bool, tuple[int, int, int, int]]:
    r0, c0, r1, c1 = _bbox(comp)
    return len(comp) == (r1 - r0 + 1) * (c1 - c0 + 1), (r0, c0, r1, c1)


def _green_boxes(grid) -> list[tuple[int, int, int, int]]:
    boxes = []
    for comp in _components_of_color(grid, 3):
        solid, box = _solid_rect(comp)
        if solid:
            boxes.append(box)
    return boxes


def observe_overrides(grid) -> dict[str, str]:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    dims = (len(grid), len(grid[0]))
    try:
        profile_name = _PROFILE_BY_DIMS[dims]
    except KeyError as exc:
        raise ValueError(f"grid dimensions {dims} do not identify a declared scene_profile") from exc
    return {"scene_profile": profile_name}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible solid-green-rectangle input grammar."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must remain visible")

    green_components = _components_of_color(grid, 3)
    if not green_components:
        errors.append("expected at least one green rectangle")
        return errors

    for index, comp in enumerate(green_components):
        solid, (r0, c0, r1, c1) = _solid_rect(comp)
        hh, ww = r1 - r0 + 1, c1 - c0 + 1
        if not solid:
            errors.append(f"green component {index} is not a filled rectangle")
        if hh < 2 or ww < 2 or hh * ww < 6:
            errors.append(
                f"green component {index} must be at least 2 cells thick with area >= 6, got {hh}x{ww}"
            )
        # A green target must remain a distinct object for the canonical Racket
        # object's bounding box; mixed-color orthogonal contact merges objects.
        for r, c in comp:
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in {0, 3}:
                    errors.append(
                        f"green component {index} touches non-green color at ({rr},{cc})"
                    )
                    break
            else:
                continue
            break
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in _PROFILE_BY_DIMS:
        errors.append(f"dimensions {h}x{w} are outside the canonical profile set")

    colors = {value for row in grid for value in row}
    if len(colors) not in {3, 4}:
        errors.append(f"canonical palette size is 3 or 4, got {len(colors)}")
    distractors = colors - {0, 3}
    if not (1 <= len(distractors) <= 2):
        errors.append(f"expected 1 or 2 non-green distractor colors, got {len(distractors)}")

    boxes = _green_boxes(grid)
    if not (1 <= len(boxes) <= 2):
        errors.append(f"canonical scenes have 1 or 2 green rectangles, got {len(boxes)}")
    if boxes and not any((r1 - r0 + 1) >= 3 and (c1 - c0 + 1) >= 3 for r0, c0, r1, c1 in boxes):
        errors.append("scene lacks an interior-bearing green rectangle")
    return errors


def _outline_boxes(grid, boxes: list[tuple[int, int, int, int]]) -> list[list[int]]:
    out = [list(row) for row in grid]
    for r0, c0, r1, c1 in boxes:
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] == 3 and (r in {r0, r1} or c in {c0, c1}):
                    out[r][c] = 8
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Testing/semantic mirror only; the canonical Racket rule remains authority."""
    return _outline_boxes(grid, _green_boxes(grid))


def _fill_all_green_rival(grid) -> list[list[int]]:
    return [[8 if value == 3 else value for value in row] for row in grid]


def _outline_all_nonzero_rectangles_rival(grid) -> list[list[int]]:
    out = [list(row) for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        for comp in _components_of_color(grid, color):
            solid, (r0, c0, r1, c1) = _solid_rect(comp)
            if not solid:
                continue
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if grid[r][c] == color and (r in {r0, r1} or c in {c0, c1}):
                        out[r][c] = 8
    return out


def _largest_green_only_rival(grid) -> list[list[int]]:
    boxes = _green_boxes(grid)
    if not boxes:
        return [list(row) for row in grid]
    largest = max(boxes, key=lambda b: ((b[2] - b[0] + 1) * (b[3] - b[1] + 1), -b[0], -b[1]))
    return _outline_boxes(grid, [largest])


def _outline_rectangles_by_size_rival(grid) -> list[list[int]]:
    """Canonical-fitting shortcut: target geometry, with no green-color test."""
    out = [list(row) for row in grid]
    for color in sorted({value for row in grid for value in row} - {0}):
        for comp in _components_of_color(grid, color):
            solid, (r0, c0, r1, c1) = _solid_rect(comp)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if not solid or min(h, w) < 2 or h * w < 6:
                continue
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if r in {r0, r1} or c in {c0, c1}:
                        out[r][c] = 8
    return out


def _ignore_thin_green_rival(grid) -> list[list[int]]:
    boxes = [
        box
        for box in _green_boxes(grid)
        if (box[2] - box[0] + 1) >= 3 and (box[3] - box[1] + 1) >= 3
    ]
    return _outline_boxes(grid, boxes)


def _has_green_interior(grid) -> bool:
    return any(
        (r1 - r0 + 1) >= 3 and (c1 - c0 + 1) >= 3
        for r0, c0, r1, c1 in _green_boxes(grid)
    )


def _has_non_green_distractor(grid) -> bool:
    return any(value not in {0, 3} for row in grid for value in row)


def _has_size_matched_distractor(grid) -> bool:
    target_shapes = {
        tuple(sorted((r1 - r0 + 1, c1 - c0 + 1)))
        for r0, c0, r1, c1 in _green_boxes(grid)
    }
    for color in sorted({value for row in grid for value in row} - {0, 3, 8}):
        for comp in _components_of_color(grid, color):
            solid, (r0, c0, r1, c1) = _solid_rect(comp)
            if solid and tuple(sorted((r1 - r0 + 1, c1 - c0 + 1))) in target_shapes:
                return True
    return False


def _has_multiple_green_rectangles(grid) -> bool:
    return len(_green_boxes(grid)) >= 2


def _has_thin_green_rectangle(grid) -> bool:
    return any(
        min(r1 - r0 + 1, c1 - c0 + 1) == 2
        for r0, c0, r1, c1 in _green_boxes(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "green_interior_refutes_fill": _has_green_interior,
    "distractor_refutes_color_blind_outline": _has_non_green_distractor,
    "matched_distractor_refutes_size_selection": _has_size_matched_distractor,
    "multiple_targets_refute_largest_only": _has_multiple_green_rectangles,
    "thin_target_exposes_all_perimeter_branch": _has_thin_green_rectangle,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_all_green": _fill_all_green_rival,
    "outline_all_nonzero_rectangles": _outline_all_nonzero_rectangles_rival,
    "outline_rectangles_by_size": _outline_rectangles_by_size_rival,
    "largest_green_only": _largest_green_only_rival,
    "ignore_thin_green": _ignore_thin_green_rival,
}

WITNESS_RIVALS = {
    "green_interior_refutes_fill": ["fill_all_green"],
    "distractor_refutes_color_blind_outline": ["outline_all_nonzero_rectangles"],
    "matched_distractor_refutes_size_selection": ["outline_rectangles_by_size"],
    "multiple_targets_refute_largest_only": ["largest_green_only"],
    "thin_target_exposes_all_perimeter_branch": ["ignore_thin_green"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Other rivals already fail canonical demonstrations. Only this one actually
# fits every canonical pair and needs newly generated teaching evidence.
CANONICAL_SHORTCUTS = {
    "outline_rectangles_by_size": _outline_rectangles_by_size_rival,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible rival to be falsified by the demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    errors: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} is missing input/output")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            errors.append(f"pair {index} output disagrees with green-perimeter rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                errors.append(f"demonstrations do not refute rival: {name}")
        except Exception as exc:
            errors.append(f"rival {name} raised {type(exc).__name__}: {exc}")
    return errors
