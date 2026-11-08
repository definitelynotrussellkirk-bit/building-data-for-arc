"""Generator for completing one-hole 3x3 rings.

The authoritative rule is local: in any 3x3 window, ignore the center.  When
seven perimeter cells share one non-background color and the eighth perimeter
cell is zero, fill that one missing perimeter cell.  Centers may be empty or
occupied, colors may repeat across rings, and unrelated near-ring distractors
must remain unchanged.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8d4c7f482c25"
VERSION = "2.0.0"
TASK_ID = "8d4c7f482c25"
RULE_HASH = "4f529a98ea53"

SUMMARY = (
    "Complete every 3x3 perimeter that has seven equal nonzero cells and one "
    "missing perimeter cell; ignore the center and leave mixed-color near-rings "
    "unchanged."
)

INVARIANTS = [
    "zero is the modal background",
    "every generated scene contains two or three unambiguous one-hole 3x3 rings",
    "the ring center is irrelevant and may be zero or a foreign nonzero color",
    "ring colors may be distinct or deliberately reused across multiple rings",
    "at least one pair of true rings is spatially nearby without overlapping",
    "distractor scenes contain a mixed-color almost-ring that the oracle leaves unchanged",
    "the only authoritative output is produced by the task's pinned Racket rule",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical",
    "filled_centers",
    "shared_colors",
    "distractors",
)
HOLE_CLASSES = ("corner", "edge", "mixed")
_HOLE_SCHEDULE = ("corner", "edge", "mixed", "mixed")
SCHEDULE_PROFILES = tuple(zip(SCENE_PROFILES, _HOLE_SCHEDULE))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware, with canonical-profile anchors",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware, with canonical-profile anchors",
        "valid": "8..12",
    },
    "ring_count": {
        "type": "int",
        "default": "difficulty-aware two or three",
        "valid": "2..3",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-step teaching schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "hole_class": {
        "type": "str",
        "default": "corner/edge/mixed teaching schedule",
        "valid": "|".join(HOLE_CLASSES),
    },
}

RING = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)
CORNER_RING_INDEXES = (0, 2, 5, 7)
EDGE_RING_INDEXES = (1, 3, 4, 6)

Grid = list[list[int]]
RingFact = dict[str, Any]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _shape(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    return len(grid), width


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _qualifying_rings(grid: Grid) -> list[RingFact]:
    """Return every exact one-hole monochrome perimeter window.

    The center is intentionally ignored, matching the Racket authority.
    """
    h, w = _shape(grid)
    rings: list[RingFact] = []
    for r in range(h - 2):
        for c in range(w - 2):
            values = [grid[r + dr][c + dc] for dr, dc in RING]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) != 7 or len(set(nonzero)) != 1:
                continue
            hole_index = values.index(0)
            dr, dc = RING[hole_index]
            rings.append({
                "r": r,
                "c": c,
                "color": nonzero[0],
                "hole_index": hole_index,
                "hole": (r + dr, c + dc),
                "center": grid[r + 1][c + 1],
            })
    return rings


def _mixed_almost_rings(grid: Grid) -> list[RingFact]:
    """Return one-hole perimeters with a 6+1 nonzero color split.

    These are deliberate negative examples: a modal-color completion shortcut
    changes them, while the authoritative rule leaves them untouched.
    """
    h, w = _shape(grid)
    candidates: list[RingFact] = []
    for r in range(h - 2):
        for c in range(w - 2):
            values = [grid[r + dr][c + dc] for dr, dc in RING]
            if values.count(0) != 1:
                continue
            nonzero = [value for value in values if value != 0]
            counts = Counter(nonzero)
            if len(nonzero) != 7 or len(counts) < 2:
                continue
            color, count = counts.most_common(1)[0]
            if count < 6:
                continue
            hole_index = values.index(0)
            dr, dc = RING[hole_index]
            candidates.append({
                "r": r,
                "c": c,
                "color": color,
                "hole_index": hole_index,
                "hole": (r + dr, c + dc),
                "center": grid[r + 1][c + 1],
            })
    return candidates


def _zones_overlap(a: RingFact, b: RingFact) -> bool:
    return not (
        a["r"] + 3 < b["r"] - 1
        or b["r"] + 3 < a["r"] - 1
        or a["c"] + 3 < b["c"] - 1
        or b["c"] + 3 < a["c"] - 1
    )


def _has_nearby_pair(rings: list[RingFact]) -> bool:
    return any(
        _zones_overlap(first, second)
        for index, first in enumerate(rings)
        for second in rings[index + 1:]
    )


def _ring_hole_class(ring: RingFact) -> str:
    return "corner" if ring["hole_index"] in CORNER_RING_INDEXES else "edge"


def _scene_profile(grid: Grid, rings: list[RingFact] | None = None) -> str:
    rings = _qualifying_rings(grid) if rings is None else rings
    if _mixed_almost_rings(grid):
        return "distractors"
    if rings and all(ring["center"] != 0 for ring in rings):
        return "filled_centers"
    colors = [ring["color"] for ring in rings]
    if len(colors) >= 2 and len(set(colors)) == 1:
        return "shared_colors"
    return "canonical"


def observe_overrides(grid: Grid) -> dict[str, int | str]:
    h, w = _shape(grid)
    rings = _qualifying_rings(grid)
    hole_types = {_ring_hole_class(ring) for ring in rings}
    if hole_types == {"corner"}:
        hole_class = "corner"
    elif hole_types == {"edge"}:
        hole_class = "edge"
    else:
        hole_class = "mixed"
    return {
        "grid_h": h,
        "grid_w": w,
        "ring_count": len(rings),
        "scene_profile": _scene_profile(grid, rings),
        "hole_class": hole_class,
    }


def _dimension_options(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (8, 8, 8, 9, 9, 10, 11, 12)
    if difficulty == "hard":
        return (8, 9, 10, 10, 11, 11, 12, 12)
    return (8, 8, 9, 9, 10, 10, 11, 12)


def _ring_count_options(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (2, 2, 2, 3)
    if difficulty == "hard":
        return (2, 3, 3, 3)
    return (2, 2, 3, 3)


def _canonical_anchor(difficulty: Any) -> tuple[int, int, int, tuple[int, ...]]:
    if difficulty == "easy":
        return 8, 8, 2, (3, 6)
    if difficulty == "hard":
        return 10, 10, 3, (4, 8, 9)
    return 9, 9, 2, (2, 7)


def _boxes_overlap(first: tuple[int, int], second: tuple[int, int]) -> bool:
    r1, c1 = first
    r2, c2 = second
    return not (r1 + 2 < r2 or r2 + 2 < r1 or c1 + 2 < c2 or c2 + 2 < c1)


def _near_pair_candidates(h: int, w: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(h - 2):
        for c in range(w - 6):
            pairs.append(((r, c), (r, c + 4)))
    for r in range(h - 6):
        for c in range(w - 2):
            pairs.append(((r, c), (r + 4, c)))
    for r in range(h - 6):
        for c in range(w - 6):
            pairs.append(((r, c), (r + 4, c + 4)))
            pairs.append(((r, c + 4), (r + 4, c)))
    return pairs


def _choose_positions(h: int, w: int, count: int, rng) -> list[tuple[int, int]]:
    candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    near_pairs = _near_pair_candidates(h, w)
    if not near_pairs:
        raise ValueError(f"grid {h}x{w} cannot hold a nearby ring pair")
    for _ in range(300):
        first, second = rng.choice(near_pairs)
        chosen = [first, second]
        if count == 2:
            rng.shuffle(chosen)
            return chosen
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        for candidate in shuffled:
            if all(not _boxes_overlap(candidate, prior) for prior in chosen):
                chosen.append(candidate)
                if len(chosen) == count:
                    rng.shuffle(chosen)
                    return chosen
    raise ValueError(f"could not place {count} disjoint 3x3 motifs in {h}x{w}")


def _hole_indexes(count: int, hole_class: str, rng) -> list[int]:
    corners = list(CORNER_RING_INDEXES)
    edges = list(EDGE_RING_INDEXES)
    rng.shuffle(corners)
    rng.shuffle(edges)
    if hole_class == "corner":
        return corners[:count]
    if hole_class == "edge":
        return edges[:count]
    indexes = [corners[0], edges[0]]
    pool = corners[1:] + edges[1:]
    rng.shuffle(pool)
    return indexes + pool[:count - 2]


def _draw_true_ring(
    grid: Grid,
    top_left: tuple[int, int],
    color: int,
    hole_index: int,
    center: int,
) -> None:
    r, c = top_left
    for index, (dr, dc) in enumerate(RING):
        if index != hole_index:
            grid[r + dr][c + dc] = color
    grid[r + 1][c + 1] = center


def _draw_mixed_distractor(
    grid: Grid,
    top_left: tuple[int, int],
    base_color: int,
    intruder_color: int,
    hole_index: int,
    rng,
) -> None:
    r, c = top_left
    filled = [index for index in range(len(RING)) if index != hole_index]
    intruder_index = rng.choice(filled)
    for index, (dr, dc) in enumerate(RING):
        if index == hole_index:
            continue
        grid[r + dr][c + dc] = (
            intruder_color if index == intruder_index else base_color
        )
    grid[r + 1][c + 1] = 0


def _expected_ring_key(
    top_left: tuple[int, int], color: int, hole_index: int
) -> tuple[int, int, int, int]:
    return top_left[0], top_left[1], color, hole_index


def _actual_ring_keys(rings: list[RingFact]) -> set[tuple[int, int, int, int]]:
    return {
        (ring["r"], ring["c"], ring["color"], ring["hole_index"])
        for ring in rings
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    residue = int(sample_index) % len(SCENE_PROFILES)
    effective = dict(overrides)
    effective.setdefault("scene_profile", SCENE_PROFILES[residue])
    effective.setdefault("hole_class", _HOLE_SCHEDULE[residue])

    anchor_h, anchor_w, anchor_count, anchor_colors = _canonical_anchor(difficulty)
    if residue == 0:
        effective.setdefault("grid_h", anchor_h)
        effective.setdefault("grid_w", anchor_w)
        effective.setdefault("ring_count", anchor_count)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_choice("grid_h", _dimension_options(difficulty))
    w = ctx.draw_choice("grid_w", _dimension_options(difficulty))
    ring_count = ctx.draw_choice("ring_count", _ring_count_options(difficulty))
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    hole_class = ctx.draw_choice("hole_class", HOLE_CLASSES)

    if scene_profile == "shared_colors":
        shared = ctx.draw_color("shared_ring_color", exclude={0})
        ring_colors = (shared,) * ring_count
    elif (
        h == anchor_h
        and w == anchor_w
        and ring_count == anchor_count
        and scene_profile == "canonical"
    ):
        ring_colors = anchor_colors
    else:
        ring_colors = ctx.draw_distinct_colors(
            "ring_colors", n=ring_count, exclude={0}
        )

    if scene_profile == "filled_centers":
        center_color = ctx.draw_color("center_color", exclude={0, *ring_colors})
        centers = (center_color,) * ring_count
    else:
        centers = (0,) * ring_count

    hole_rng = ctx.draw_rng("hole_layout")
    holes = _hole_indexes(ring_count, hole_class, hole_rng)
    layout_rng = ctx.draw_rng("motif_layout")
    total_motifs = ring_count + (1 if scene_profile == "distractors" else 0)

    available_colors = [color for color in range(1, 10) if color not in ring_colors]
    if len(available_colors) < 2:
        available_colors = list(range(1, 10))
    distractor_rng = ctx.draw_rng("distractor")

    for _ in range(400):
        positions = _choose_positions(h, w, total_motifs, layout_rng)
        grid = full_grid(h, w, 0)
        intended: set[tuple[int, int, int, int]] = set()
        for position, color, hole_index, center in zip(
            positions[:ring_count], ring_colors, holes, centers
        ):
            _draw_true_ring(grid, position, color, hole_index, center)
            intended.add(_expected_ring_key(position, color, hole_index))

        if scene_profile == "distractors":
            base_color, intruder_color = distractor_rng.sample(available_colors, 2)
            distractor_hole = distractor_rng.randrange(len(RING))
            _draw_mixed_distractor(
                grid,
                positions[-1],
                base_color,
                intruder_color,
                distractor_hole,
                distractor_rng,
            )

        rings = _qualifying_rings(grid)
        if _actual_ring_keys(rings) != intended:
            continue
        if not _has_nearby_pair(rings):
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": h,
            "grid_w": w,
            "ring_count": ring_count,
            "scene_profile": scene_profile,
            "hole_class": hole_class,
        }
        if observed != expected:
            continue
        findings = self_check(grid, difficulty=difficulty)
        if findings:
            continue
        return _copy_grid(grid)

    raise ValueError(
        "could not build a collision-free, semantically exact one-hole-ring scene"
    )


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    messages: list[str] = []
    try:
        h, w = _shape(grid)
    except ValueError as exc:
        return [str(exc)]
    if not (8 <= h <= 12 and 8 <= w <= 12):
        messages.append(f"grid shape {h}x{w} is outside the supported 8..12 range")
    values = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        messages.append("all cells must be integer colors")
        return messages
    if any(value < 0 or value > 9 for value in values):
        messages.append("cell colors must lie in 0..9")
    if Counter(values).most_common(1)[0][0] != 0:
        messages.append("zero is not the modal background")

    rings = _qualifying_rings(grid)
    if not (2 <= len(rings) <= 3):
        messages.append(f"expected 2..3 one-hole rings, found {len(rings)}")

    proposals: dict[tuple[int, int], set[int]] = {}
    for ring in rings:
        proposals.setdefault(ring["hole"], set()).add(ring["color"])
    conflicts = {
        position: colors for position, colors in proposals.items() if len(colors) > 1
    }
    if conflicts:
        messages.append(f"conflicting ring completions at {sorted(conflicts)}")

    return messages


def strict_canonical_like(grid: Grid) -> list[str]:
    return self_check(grid)


def _official_python(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for ring in _qualifying_rings(grid):
        r, c = ring["hole"]
        output[r][c] = ring["color"]
    return output


def _rival_zero_center_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for ring in _qualifying_rings(grid):
        if ring["center"] == 0:
            r, c = ring["hole"]
            output[r][c] = ring["color"]
    return output


def _rival_distinct_color_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    rings = _qualifying_rings(grid)
    frequencies = Counter(ring["color"] for ring in rings)
    for ring in rings:
        if frequencies[ring["color"]] == 1:
            r, c = ring["hole"]
            output[r][c] = ring["color"]
    return output


def _rival_isolated_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    rings = _qualifying_rings(grid)
    for index, ring in enumerate(rings):
        if any(
            _zones_overlap(ring, other)
            for j, other in enumerate(rings)
            if j != index
        ):
            continue
        r, c = ring["hole"]
        output[r][c] = ring["color"]
    return output


def _rival_majority_ring_fill(grid: Grid) -> Grid:
    output = _official_python(grid)
    for ring in _mixed_almost_rings(grid):
        r, c = ring["hole"]
        output[r][c] = ring["color"]
    return output


def _rival_edge_holes_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for ring in _qualifying_rings(grid):
        if _ring_hole_class(ring) == "edge":
            r, c = ring["hole"]
            output[r][c] = ring["color"]
    return output


def _rival_corner_holes_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for ring in _qualifying_rings(grid):
        if _ring_hole_class(ring) == "corner":
            r, c = ring["hole"]
            output[r][c] = ring["color"]
    return output


def _rival_fill_centers_too(grid: Grid) -> Grid:
    output = _official_python(grid)
    for ring in _qualifying_rings(grid):
        if ring["center"] == 0:
            output[ring["r"] + 1][ring["c"] + 1] = ring["color"]
    return output


def _rival_single_target_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    rings = sorted(
        _qualifying_rings(grid),
        key=lambda ring: (ring["r"], ring["c"], ring["hole_index"]),
    )
    if rings:
        ring = rings[0]
        r, c = ring["hole"]
        output[r][c] = ring["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "zero_center_only": _rival_zero_center_only,
    "distinct_color_only": _rival_distinct_color_only,
    "isolated_rings_only": _rival_isolated_only,
    "modal_or_majority_ring_fill": _rival_majority_ring_fill,
    "edge_holes_only": _rival_edge_holes_only,
    "corner_holes_only": _rival_corner_holes_only,
    "fill_centers_too": _rival_fill_centers_too,
    "single_target_only": _rival_single_target_only,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "zero_center_only": _rival_zero_center_only,
    "distinct_color_only": _rival_distinct_color_only,
    "modal_or_majority_ring_fill": _rival_majority_ring_fill,
}


def _witness_zero_center(grid: Grid) -> bool:
    return any(ring["center"] == 0 for ring in _qualifying_rings(grid))


def _witness_filled_center(grid: Grid) -> bool:
    return any(ring["center"] != 0 for ring in _qualifying_rings(grid))


def _witness_shared_color(grid: Grid) -> bool:
    colors = [ring["color"] for ring in _qualifying_rings(grid)]
    return len(colors) >= 2 and len(set(colors)) < len(colors)


def _witness_nearby(grid: Grid) -> bool:
    return _has_nearby_pair(_qualifying_rings(grid))


def _witness_mixed_distractor(grid: Grid) -> bool:
    return bool(_mixed_almost_rings(grid))


def _witness_corner_hole(grid: Grid) -> bool:
    return any(
        _ring_hole_class(ring) == "corner" for ring in _qualifying_rings(grid)
    )


def _witness_edge_hole(grid: Grid) -> bool:
    return any(
        _ring_hole_class(ring) == "edge" for ring in _qualifying_rings(grid)
    )


def _witness_multiple_targets(grid: Grid) -> bool:
    return len(_qualifying_rings(grid)) >= 2


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "zero_center_ring": _witness_zero_center,
    "filled_center_ring": _witness_filled_center,
    "shared_ring_color": _witness_shared_color,
    "nearby_rings": _witness_nearby,
    "mixed_almost_ring_distractor": _witness_mixed_distractor,
    "corner_hole": _witness_corner_hole,
    "edge_hole": _witness_edge_hole,
    "multiple_targets": _witness_multiple_targets,
}

WITNESS_RIVALS = {
    "zero_center_ring": ["fill_centers_too"],
    "filled_center_ring": ["zero_center_only"],
    "shared_ring_color": ["distinct_color_only"],
    "nearby_rings": ["isolated_rings_only"],
    "mixed_almost_ring_distractor": ["modal_or_majority_ring_fill"],
    "corner_hole": ["edge_holes_only"],
    "edge_hole": ["corner_holes_only"],
    "multiple_targets": ["single_target_only"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    residue = int(sample_index) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[residue]


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    try:
        for index, demo in enumerate(demos):
            if self_check(demo["input"]):
                reasons.append(f"demonstration {index} is outside the teaching grammar")
            if _official_python(demo["input"]) != demo["output"]:
                reasons.append(f"demonstration {index} output disagrees with the local rule")
        if self_check(query["input"]):
            reasons.append("query input is outside the teaching grammar")

        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"competitor {name!r} fits every demonstration")

        required = {
            "filled-center branch": _witness_filled_center,
            "shared-color branch": _witness_shared_color,
            "negative mixed-ring distractor": _witness_mixed_distractor,
            "corner-hole branch": _witness_corner_hole,
            "edge-hole branch": _witness_edge_hole,
        }
        for label, predicate in required.items():
            if not any(predicate(demo["input"]) for demo in demos):
                reasons.append(f"lesson omits {label}")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reasons.append(f"lesson analysis failed: {type(exc).__name__}: {exc}")
    return sorted(set(reasons))


def mutation_impostors(grid: Grid) -> list[tuple[str, Grid]]:
    """Four focused malformed scenes for mutation-sensitive review tests."""
    rings = _qualifying_rings(grid)
    impostors: list[tuple[str, Grid]] = []

    complete = _official_python(grid)
    impostors.append(("already_complete_identity", complete))

    two_holes = _copy_grid(grid)
    for ring in rings:
        for index, (dr, dc) in enumerate(RING):
            if index != ring["hole_index"]:
                two_holes[ring["r"] + dr][ring["c"] + dc] = 0
                break
    impostors.append(("two_holes_per_true_ring", two_holes))

    one_ring = full_grid(8, 8, 0)
    _draw_true_ring(one_ring, (2, 2), 4, 0, 0)
    impostors.append(("only_one_true_ring", one_ring))

    non_rectangular = _copy_grid(grid)
    non_rectangular[-1] = non_rectangular[-1][:-1]
    impostors.append(("non_rectangular", non_rectangular))
    return impostors
