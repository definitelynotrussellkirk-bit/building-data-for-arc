"""Generator for 1b39c0e8ebc7 — vector-projected source/target overlap.

The unique color-8 and color-9 markers define an input-dependent vector.  The
canonical rule starts with an empty output grid, translates every color-3 source
by that 8→9 vector, and paints color 7 only where the translated source lands on
an input color-4 target.  Nothing from the input is copied to the output.

Ordinary generated scenes deliberately include reverse-direction pairs,
unmatched sources, and unmatched targets.  These are answer-bearing negative
examples: recoloring every 4, ignoring the 3s, or using the marker vector in the
wrong direction must fail.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b39c0e8ebc7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2327556798a0"

SUMMARY = (
    "The unique 8 and 9 markers define a displacement vector. Translate every "
    "color-3 source by the 8→9 vector; in an otherwise empty output grid, paint "
    "color 7 exactly at translated cells that contain color 4 in the input. "
    "Ordinary scenes contain reverse-direction traps and unmatched 3/4 decoys."
)

INVARIANTS = [
    "one color-8 marker and one color-9 marker define a nonzero supported vector",
    "at least two color-3 sources hit color-4 targets in the forward 8-to-9 direction",
    "at least one reverse-only 3-to-4 pair prevents direction-free shortcuts",
    "at least one unmatched color-3 source and one unmatched color-4 target are present",
    "the canonical output is empty except for color-7 forward hit locations",
]

# Includes every canonical vector, all sign quadrants, and unequal row/column
# magnitudes that expose sign/swap/axis-only shortcut rules.
VECTORS = (
    (1, 2), (2, 1), (-1, 2), (1, -2), (-2, 1), (2, -1), (-1, -2), (-2, -1),
    (2, 3), (3, 2), (3, 1), (-2, 3), (-3, 2), (-3, 1),
    (2, -3), (3, -2), (3, -1), (-2, -3), (-3, -2), (-3, -1),
    (1, 3), (-1, 3), (1, -3), (-1, -3),
)
VECTOR_NAMES = tuple(f"({dr},{dc})" for dr, dc in VECTORS)
_VECTOR_BY_NAME = dict(zip(VECTOR_NAMES, VECTORS))

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-linked 8..30", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "difficulty-linked 8..30", "valid": "8..30"},
    "vector": {"type": "str", "default": "keyed choice", "valid": "|".join(VECTOR_NAMES)},
    "matched_pairs": {"type": "int", "default": "difficulty-linked", "valid": "2..16"},
    "reverse_pairs": {"type": "int", "default": "difficulty-linked", "valid": "1..16"},
    "source_decoys": {"type": "int", "default": "difficulty-linked", "valid": "1..8"},
    "target_decoys": {"type": "int", "default": "difficulty-linked", "valid": "1..8"},
}

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

Point = tuple[int, int]


def _unknown_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _draw_axis_int(ctx, label: str, low: int, high: int, default_low: int, default_high: int) -> int:
    """Strict exact-int override with a narrower deterministic default band."""
    ctx.draw_bounds_store[label] = (low, high)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
        if type(value) is not int:
            raise TypeError(f"{label} override must be an exact integer; bool is forbidden")
        if not low <= value <= high:
            raise ValueError(f"{label} override {value} outside [{low}, {high}]")
        return int(ctx._record(label, value, from_override=True))
    value = ctx.draw_rng(label).randint(default_low, default_high)
    return int(ctx._record(label, value, from_override=False))


def _shift(point: Point, vector: Point, factor: int = 1) -> Point:
    return point[0] + factor * vector[0], point[1] + factor * vector[1]


def _in_bounds(point: Point, height: int, width: int) -> bool:
    return 0 <= point[0] < height and 0 <= point[1] < width


def _all_cells(height: int, width: int) -> list[Point]:
    return [(r, c) for r in range(height) for c in range(width)]


def _match_sets(sources: set[Point], targets: set[Point], vector: Point) -> tuple[set[Point], set[Point]]:
    forward = {target for target in targets if _shift(target, vector, -1) in sources}
    reverse = {target for target in targets if _shift(target, vector, 1) in sources}
    return forward, reverse


def _edges(point: Point, height: int, width: int) -> set[str]:
    r, c = point
    result = set()
    if r == 0:
        result.add("top")
    if r == height - 1:
        result.add("bottom")
    if c == 0:
        result.add("left")
    if c == width - 1:
        result.add("right")
    return result


def _quadrant(point: Point, height: int, width: int) -> int:
    r, c = point
    return (2 if r >= height // 2 else 0) + (1 if c >= width // 2 else 0)


def _coverage_score(cells: Iterable[Point], occupied: set[Point], height: int, width: int, rng) -> float:
    existing_edges = set().union(*(_edges(p, height, width) for p in occupied)) if occupied else set()
    counts = [0, 0, 0, 0]
    for point in occupied:
        counts[_quadrant(point, height, width)] += 1
    new_edges = set().union(*(_edges(p, height, width) for p in cells)) if cells else set()
    score = 1000 * len(new_edges - existing_edges)
    for point in cells:
        score += max(0, 12 - counts[_quadrant(point, height, width)]) * 10
        # Prefer broad canvas use once edge/quadrant deficits are tied.
        score += abs(point[0] - (height - 1) / 2) + abs(point[1] - (width - 1) / 2)
    return score + rng.random()


def _strict_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be within 1..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return len(grid), width


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the exact vector and forward/reverse/decoy roles from an input."""
    try:
        height, width = _strict_grid(grid)
    except (TypeError, ValueError) as error:
        return {"errors": [str(error)]}
    by_color: dict[int, set[Point]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, set()).add((r, c))
    errors = []
    eights = by_color.get(8, set())
    nines = by_color.get(9, set())
    if len(eights) != 1 or len(nines) != 1:
        return {
            "height": height,
            "width": width,
            "errors": ["need exactly one color-8 marker and one color-9 marker"],
        }
    p8 = next(iter(eights))
    p9 = next(iter(nines))
    vector = (p9[0] - p8[0], p9[1] - p8[1])
    if vector not in VECTORS:
        errors.append(f"unsupported 8-to-9 vector {vector}")
    illegal = sorted(set(by_color) - {3, 4, 8, 9})
    if illegal:
        errors.append(f"unexpected input colors {illegal}")
    sources = set(by_color.get(3, set()))
    targets = set(by_color.get(4, set()))
    forward, reverse = _match_sets(sources, targets, vector)
    ambiguous = forward & reverse
    unmatched_sources = {
        source
        for source in sources
        if _shift(source, vector, 1) not in targets and _shift(source, vector, -1) not in targets
    }
    unmatched_targets = targets - forward - reverse
    return {
        "height": height,
        "width": width,
        "marker_8": p8,
        "marker_9": p9,
        "vector": vector,
        "sources": sorted(sources),
        "targets": sorted(targets),
        "forward_targets": sorted(forward),
        "reverse_targets": sorted(reverse),
        "ambiguous_targets": sorted(ambiguous),
        "unmatched_sources": sorted(unmatched_sources),
        "unmatched_targets": sorted(unmatched_targets),
        "errors": errors,
    }


def apply_direction(grid: list[list[int]], direction: str = "forward") -> list[list[int]]:
    """Independent Python mirror for diagnostics; protected Racket remains authority."""
    info = analyze_scene(grid)
    if info.get("errors"):
        raise ValueError(f"invalid vector scene: {info['errors']}")
    if type(direction) is not str or direction not in {"forward", "reverse"}:
        raise ValueError("direction must be 'forward' or 'reverse'")
    targets = info["forward_targets"] if direction == "forward" else info["reverse_targets"]
    output = full_grid(info["height"], info["width"], 0)
    for r, c in targets:
        output[r][c] = 7
    return output


def _candidate_pairs(height: int, width: int, vector: Point, direction: str, blocked: set[Point]) -> list[tuple[Point, Point]]:
    factor = 1 if direction == "forward" else -1
    result = []
    for source in _all_cells(height, width):
        target = _shift(source, vector, factor)
        if _in_bounds(target, height, width) and source not in blocked and target not in blocked and source != target:
            result.append((source, target))
    return result


def _choose_marker(height: int, width: int, vector: Point, rng) -> tuple[Point, Point]:
    candidates = [
        point
        for point in _all_cells(height, width)
        if _in_bounds(_shift(point, vector), height, width)
    ]
    if not candidates:
        raise ValueError(f"vector {vector} does not fit {height}x{width}")
    rng.shuffle(candidates)
    # Prefer a marker pair away from the exact center so absolute-position
    # shortcuts cannot rely on a fixed central anchor.
    candidates.sort(
        key=lambda point: (
            abs(point[0] - (height - 1) / 2) + abs(point[1] - (width - 1) / 2),
            rng.random(),
        ),
        reverse=True,
    )
    p8 = candidates[0]
    return p8, _shift(p8, vector)


def construct_scene(
    *,
    height: int,
    width: int,
    vector: Point,
    matched_pairs: int,
    reverse_pairs: int,
    source_decoys: int,
    target_decoys: int,
    rng,
    spread: bool = False,
) -> list[list[int]]:
    """Construct one scene with exact semantic role counts.

    Pair candidates are accepted only when the complete source/target relation
    still has exactly the intended forward and reverse target sets.  Decoys are
    then added under the same relation constraint.  Bounded restarts avoid the
    old greedy-overwrite and accidental-shortcut failures.
    """
    for name, value, low, high in (
        ("height", height, 8, 30),
        ("width", width, 8, 30),
        ("matched_pairs", matched_pairs, 2, 16),
        ("reverse_pairs", reverse_pairs, 1, 16),
        ("source_decoys", source_decoys, 1, 8),
        ("target_decoys", target_decoys, 1, 8),
    ):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer")
        if not low <= value <= high:
            raise ValueError(f"{name} must be in [{low}, {high}]")
    if type(vector) is not tuple or len(vector) != 2 or any(type(v) is not int for v in vector):
        raise TypeError("vector must be a pair of exact integers")
    if vector not in VECTORS:
        raise ValueError(f"unsupported vector {vector}")
    requested_cells = 2 + 2 * (matched_pairs + reverse_pairs) + source_decoys + target_decoys
    if requested_cells > height * width:
        raise ValueError("requested semantic roles exceed canvas capacity")

    directions = []
    for index in range(max(matched_pairs, reverse_pairs)):
        if index < matched_pairs:
            directions.append("forward")
        if index < reverse_pairs:
            directions.append("reverse")

    for _attempt in range(512):
        p8, p9 = _choose_marker(height, width, vector, rng)
        blocked = {p8, p9}
        candidates = {
            direction: _candidate_pairs(height, width, vector, direction, blocked)
            for direction in ("forward", "reverse")
        }
        for values in candidates.values():
            rng.shuffle(values)

        sources: set[Point] = set()
        targets: set[Point] = set()
        expected_forward: set[Point] = set()
        expected_reverse: set[Point] = set()
        occupied = set(blocked)
        ok = True

        for direction in directions:
            valid = []
            for source, target in candidates[direction]:
                if source in occupied or target in occupied:
                    continue
                trial_sources = sources | {source}
                trial_targets = targets | {target}
                trial_forward, trial_reverse = _match_sets(trial_sources, trial_targets, vector)
                want_forward = expected_forward | ({target} if direction == "forward" else set())
                want_reverse = expected_reverse | ({target} if direction == "reverse" else set())
                if trial_forward == want_forward and trial_reverse == want_reverse:
                    valid.append((source, target))
            if not valid:
                ok = False
                break
            if spread:
                source, target = max(
                    valid,
                    key=lambda pair: _coverage_score(pair, occupied, height, width, rng),
                )
            else:
                source, target = valid[rng.randrange(len(valid))]
            sources.add(source)
            targets.add(target)
            occupied.update((source, target))
            if direction == "forward":
                expected_forward.add(target)
            else:
                expected_reverse.add(target)
        if not ok:
            continue

        def add_source_decoy() -> bool:
            valid = [
                point
                for point in _all_cells(height, width)
                if point not in occupied
                and _shift(point, vector, 1) not in targets
                and _shift(point, vector, -1) not in targets
            ]
            if not valid:
                return False
            point = (
                max(valid, key=lambda p: _coverage_score((p,), occupied, height, width, rng))
                if spread
                else valid[rng.randrange(len(valid))]
            )
            sources.add(point)
            occupied.add(point)
            return True

        def add_target_decoy() -> bool:
            valid = [
                point
                for point in _all_cells(height, width)
                if point not in occupied
                and _shift(point, vector, -1) not in sources
                and _shift(point, vector, 1) not in sources
            ]
            if not valid:
                return False
            point = (
                max(valid, key=lambda p: _coverage_score((p,), occupied, height, width, rng))
                if spread
                else valid[rng.randrange(len(valid))]
            )
            targets.add(point)
            occupied.add(point)
            return True

        if not all(add_source_decoy() for _ in range(source_decoys)):
            continue
        if not all(add_target_decoy() for _ in range(target_decoys)):
            continue

        actual_forward, actual_reverse = _match_sets(sources, targets, vector)
        if actual_forward != expected_forward or actual_reverse != expected_reverse:
            continue
        unmatched_sources = {
            source
            for source in sources
            if _shift(source, vector, 1) not in targets and _shift(source, vector, -1) not in targets
        }
        unmatched_targets = targets - actual_forward - actual_reverse
        if len(unmatched_sources) != source_decoys or len(unmatched_targets) != target_decoys:
            continue

        if spread:
            rows = {r for r, _ in occupied}
            cols = {c for _, c in occupied}
            quadrants = [sum(_quadrant(point, height, width) == q for point in occupied) for q in range(4)]
            if not ({0, height - 1} <= rows and {0, width - 1} <= cols):
                continue
            if min(quadrants) < 6:
                continue

        grid = full_grid(height, width, 0)
        grid[p8[0]][p8[1]] = 8
        grid[p9[0]][p9[1]] = 9
        for r, c in sources:
            grid[r][c] = 3
        for r, c in targets:
            grid[r][c] = 4
        info = analyze_scene(grid)
        if info["errors"]:
            continue
        if (
            len(info["forward_targets"]) == matched_pairs
            and len(info["reverse_targets"]) == reverse_pairs
            and len(info["unmatched_sources"]) == source_decoys
            and len(info["unmatched_targets"]) == target_decoys
            and not info["ambiguous_targets"]
        ):
            return grid
    raise ValueError(
        "could not construct exact vector scene after bounded restarts; "
        "reduce counts or enlarge the canvas"
    )


def _difficulty_defaults(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 11), (8, 12), (2, 3), (1, 2), (1, 2), (1, 2)
    if difficulty == "medium":
        return (12, 18), (12, 19), (3, 5), (2, 4), (1, 3), (1, 3)
    if difficulty == "hard":
        return (19, 30), (19, 30), (5, 9), (4, 8), (2, 4), (2, 4)
    return (8, 20), (8, 21), (2, 5), (1, 4), (1, 3), (1, 3)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _unknown_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_band, w_band, matched_band, reverse_band, source_band, target_band = _difficulty_defaults(difficulty)
    height = _draw_axis_int(ctx, "grid_h", 8, 30, *h_band)
    width = _draw_axis_int(ctx, "grid_w", 8, 30, *w_band)
    vector_name = ctx.draw_choice("vector", VECTOR_NAMES)
    vector = _VECTOR_BY_NAME[vector_name]
    matched_pairs = _draw_axis_int(ctx, "matched_pairs", 2, 16, *matched_band)
    reverse_pairs = _draw_axis_int(ctx, "reverse_pairs", 1, 16, *reverse_band)
    source_decoys = _draw_axis_int(ctx, "source_decoys", 1, 8, *source_band)
    target_decoys = _draw_axis_int(ctx, "target_decoys", 1, 8, *target_band)
    return construct_scene(
        height=height,
        width=width,
        vector=vector,
        matched_pairs=matched_pairs,
        reverse_pairs=reverse_pairs,
        source_decoys=source_decoys,
        target_decoys=target_decoys,
        rng=ctx.draw_rng("layout"),
        spread=height >= 24 and width >= 24 and matched_pairs + reverse_pairs >= 16,
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    info = analyze_scene(grid)
    errors = list(info.get("errors", []))
    if errors:
        return sorted(set(errors))
    if not 8 <= info["height"] <= 30 or not 8 <= info["width"] <= 30:
        errors.append("generated dimensions must be within 8..30")
    if len(info["forward_targets"]) < 2:
        errors.append("need at least two forward vector hits")
    if len(info["reverse_targets"]) < 1:
        errors.append("need at least one reverse-only target")
    if len(info["unmatched_sources"]) < 1:
        errors.append("need at least one unmatched color-3 source")
    if len(info["unmatched_targets"]) < 1:
        errors.append("need at least one unmatched color-4 target")
    if info["ambiguous_targets"]:
        errors.append("a target must not match both vector directions")
    return sorted(set(errors))
