"""Curriculum generator for moving color-coded markers toward matching sides.

The border has four distinct side colors and background-colored corners.  Each
interior marker whose color matches a side moves exactly one cell toward that
side.  A matching marker already adjacent to its side stays put, and interior
colors that match no side are stationary distractors.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2b749aefc65"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "d151397a0cab"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Use the four uniform non-corner border sides as a color-to-direction key. "
    "Clear the interior to its modal background, then move every interior cell "
    "matching the top, bottom, left, or right side exactly one cell toward that "
    "side. A matching cell already adjacent to its side remains in place, and "
    "interior colors matching no side are stationary distractors."
)

INVARIANTS = [
    "the interior has a unique modal background color and all four corners use it",
    "each non-corner border side is uniform and the four side colors are distinct",
    "side-colored interior markers move one cell toward their matching side",
    "side-colored markers adjacent to their matching side remain in place",
    "interior colors absent from the four side colors remain stationary",
    "all final marker and distractor destinations are distinct",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# A single joint observable axis preserves the canonical dependency between
# grid size, palette size, marker count, blocked-marker count, and distractor
# multiplicities. Advertising these as independent controls would create many
# impossible or non-canonical cross-products.
PROFILE_SPECS: dict[str, tuple[int, int, int, int, tuple[int, ...]]] = {
    # name: (square size, palette size, side-marker count,
    #        blocked side-marker count, sorted distractor multiplicities)
    "canonical_8_clean": (8, 5, 9, 0, ()),
    "canonical_10_clean": (10, 5, 8, 0, ()),
    "canonical_9_mixed": (9, 8, 9, 1, (1, 1, 2)),
    "canonical_12_dense": (12, 6, 19, 2, (1,)),
    "canonical_13_distractors": (13, 8, 9, 0, (2, 2, 5)),
    "expanded_14_dense": (14, 6, 22, 3, (3,)),
    "expanded_15_mixed": (15, 8, 18, 2, (2, 3, 5)),
}
PROFILE_NAMES = tuple(PROFILE_SPECS)
_PROFILE_BY_FACTS = {facts: name for name, facts in PROFILE_SPECS.items()}
CANONICAL_PROFILES = frozenset(name for name in PROFILE_NAMES if name.startswith("canonical_"))

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "difficulty-aware four-slot schedule",
        "valid": (
            "canonical_8_clean",
            "canonical_10_clean",
            "canonical_9_mixed",
            "canonical_12_dense",
            "canonical_13_distractors",
            "expanded_14_dense",
            "expanded_15_mixed",
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_BAND_SCHEDULES: dict[str, tuple[str, ...]] = {
    "easy": (
        "canonical_8_clean",
        "canonical_9_mixed",
        "canonical_10_clean",
        "canonical_9_mixed",
    ),
    "medium": (
        "canonical_10_clean",
        "canonical_9_mixed",
        "canonical_12_dense",
        "canonical_13_distractors",
    ),
    "hard": (
        "canonical_12_dense",
        "canonical_13_distractors",
        "expanded_14_dense",
        "expanded_15_mixed",
    ),
}
SCHEDULE_PROFILES = PROFILE_NAMES
MIN_STRICT_FRAC = 0.45


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the deterministic curriculum branch selected for this draw."""
    band = difficulty if difficulty in _BAND_SCHEDULES else "medium"
    schedule = _BAND_SCHEDULES[band]
    del seed
    return schedule[int(sample_index) % len(schedule)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    value = overrides.get("scene_profile")
    if value is not None and type(value) is not str:
        raise ValueError("scene_profile must be a string")


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _interior_mode(grid: list[list[int]]) -> tuple[int | None, list[str]]:
    interior = [
        grid[r][c]
        for r in range(1, len(grid) - 1)
        for c in range(1, len(grid[0]) - 1)
    ]
    if not interior:
        return None, ["grid must have a non-empty interior"]
    counts = Counter(interior)
    largest = max(counts.values())
    modes = sorted(color for color, count in counts.items() if count == largest)
    if len(modes) != 1:
        return None, [f"interior background must be a unique mode; tied modes={modes}"]
    return modes[0], []


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return None, errors
    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    if h < 5 or w < 5:
        return None, [f"grid dimensions {h}x{w} are too small for the side-key grammar"]

    bg, mode_errors = _interior_mode(grid)
    if mode_errors:
        return None, mode_errors
    assert bg is not None

    if any(grid[r][c] != bg for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))):
        errors.append("all four corners must equal the interior background")

    sides = {
        "top": [grid[0][c] for c in range(1, w - 1)],
        "bottom": [grid[h - 1][c] for c in range(1, w - 1)],
        "left": [grid[r][0] for r in range(1, h - 1)],
        "right": [grid[r][w - 1] for r in range(1, h - 1)],
    }
    side_colors: dict[str, int] = {}
    for side, values in sides.items():
        if len(set(values)) != 1:
            errors.append(f"{side} non-corner border cells must be uniform")
        else:
            side_colors[side] = values[0]
    if len(side_colors) == 4:
        if len(set(side_colors.values())) != 4:
            errors.append("the four side colors must be pairwise distinct")
        if bg in side_colors.values():
            errors.append("no side color may equal the interior background")
    if errors:
        return None, errors

    directions = {
        side_colors["top"]: (-1, 0, "top"),
        side_colors["bottom"]: (1, 0, "bottom"),
        side_colors["left"]: (0, -1, "left"),
        side_colors["right"]: (0, 1, "right"),
    }
    side_markers: list[dict[str, Any]] = []
    distractor_counts: Counter[int] = Counter()
    final_destinations: dict[tuple[int, int], tuple[int, int]] = {}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value == bg:
                continue
            if value in directions:
                dr, dc, side = directions[value]
                nr, nc = r + dr, c + dc
                blocked = not (1 <= nr <= h - 2 and 1 <= nc <= w - 2)
                destination = (r, c) if blocked else (nr, nc)
                side_markers.append(
                    {
                        "source": (r, c),
                        "destination": destination,
                        "color": value,
                        "side": side,
                        "blocked": blocked,
                    }
                )
            else:
                destination = (r, c)
                distractor_counts[value] += 1
            if destination in final_destinations:
                errors.append(
                    "final destinations must be distinct: "
                    f"{final_destinations[destination]} and {(r, c)} both end at {destination}"
                )
            else:
                final_destinations[destination] = (r, c)

    if not side_markers:
        errors.append("at least one interior side-colored marker is required")
    if not any(not marker["blocked"] for marker in side_markers):
        errors.append("at least one side-colored marker must move")
    if errors:
        return None, errors

    facts = (
        h,
        len({value for row in grid for value in row}),
        len(side_markers),
        sum(marker["blocked"] for marker in side_markers),
        tuple(sorted(distractor_counts.values())),
    )
    return {
        "grid": grid,
        "height": h,
        "width": w,
        "background": bg,
        "side_colors": side_colors,
        "side_markers": side_markers,
        "distractor_counts": distractor_counts,
        "facts": facts,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the task grammar and reject misleading recombinations."""
    del difficulty, meta
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    assert analysis is not None
    h, w = analysis["height"], analysis["width"]
    if h != w:
        errors.append(f"grid must be square; found {h}x{w}")
    if not 8 <= h <= 15:
        errors.append(f"grid size {h} outside supported 8..15 envelope")
    if len({value for row in analysis["grid"] for value in row}) not in (5, 6, 8):
        errors.append("palette size must be one of the canonical/generalized values 5, 6, or 8")
    return errors


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    analysis, _ = _analyze(grid)
    assert analysis is not None
    profile = _PROFILE_BY_FACTS.get(analysis["facts"])
    if profile is None:
        raise ValueError(f"no declared scene_profile matches recovered facts {analysis['facts']}")
    return {"scene_profile": profile}


def strict_canonical_like(grid) -> list[str]:
    """Accept only the five linked profiles observed in canonical pairs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    try:
        profile = observe_overrides(grid)["scene_profile"]
    except ValueError as exc:
        return [str(exc)]
    if profile not in CANONICAL_PROFILES:
        reasons.append("linked scene facts are outside the five canonical profiles")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror only; the synchronized Racket rule owns output."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    assert analysis is not None
    out = [row[:] for row in analysis["grid"]]
    bg = analysis["background"]
    h, w = analysis["height"], analysis["width"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out[r][c] = bg
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value == bg:
                continue
            marker = next(
                (item for item in analysis["side_markers"] if item["source"] == (r, c)),
                None,
            )
            nr, nc = marker["destination"] if marker is not None else (r, c)
            out[nr][nc] = value
    return out


def _rival_move_two_steps(grid: list[list[int]]) -> list[list[int]]:
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    assert analysis is not None
    out = [row[:] for row in analysis["grid"]]
    bg = analysis["background"]
    h, w = analysis["height"], analysis["width"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out[r][c] = bg
    marker_by_source = {item["source"]: item for item in analysis["side_markers"]}
    vectors = {"top": (-1, 0), "bottom": (1, 0), "left": (0, -1), "right": (0, 1)}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value == bg:
                continue
            marker = marker_by_source.get((r, c))
            if marker is None:
                nr, nc = r, c
            else:
                dr, dc = vectors[marker["side"]]
                rr, cc = r + 2 * dr, c + 2 * dc
                nr, nc = (rr, cc) if 1 <= rr <= h - 2 and 1 <= cc <= w - 2 else (r, c)
            out[nr][nc] = value
    return out


def _rival_snap_to_side(grid: list[list[int]]) -> list[list[int]]:
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    assert analysis is not None
    out = [row[:] for row in analysis["grid"]]
    bg = analysis["background"]
    h, w = analysis["height"], analysis["width"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out[r][c] = bg
    marker_by_source = {item["source"]: item for item in analysis["side_markers"]}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value == bg:
                continue
            marker = marker_by_source.get((r, c))
            if marker is None:
                nr, nc = r, c
            else:
                nr, nc = {
                    "top": (1, c),
                    "bottom": (h - 2, c),
                    "left": (r, 1),
                    "right": (r, w - 2),
                }[marker["side"]]
            out[nr][nc] = value
    return out


def _nearest_side_destination(r: int, c: int, h: int, w: int) -> tuple[int, int]:
    choices = [
        (r - 1, (r - 1, c)),
        ((h - 2) - r, (r + 1, c)),
        (c - 1, (r, c - 1)),
        ((w - 2) - c, (r, c + 1)),
    ]
    _, destination = min(choices, key=lambda item: item[0])
    return destination


def _rival_move_distractors(grid: list[list[int]]) -> list[list[int]]:
    out = rule_mirror(grid)
    analysis, _ = _analyze(grid)
    assert analysis is not None
    h, w = analysis["height"], analysis["width"]
    side_values = set(analysis["side_colors"].values())
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value != analysis["background"] and value not in side_values:
                out[r][c] = analysis["background"]
                nr, nc = _nearest_side_destination(r, c, h, w)
                out[nr][nc] = value
    return out


def _rival_drop_blocked(grid: list[list[int]]) -> list[list[int]]:
    out = rule_mirror(grid)
    analysis, _ = _analyze(grid)
    assert analysis is not None
    for marker in analysis["side_markers"]:
        if marker["blocked"]:
            r, c = marker["source"]
            out[r][c] = analysis["background"]
    return out


def _rival_move_one_per_side(grid: list[list[int]]) -> list[list[int]]:
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    assert analysis is not None
    out = [row[:] for row in analysis["grid"]]
    bg = analysis["background"]
    h, w = analysis["height"], analysis["width"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out[r][c] = bg
    moved_sides: set[str] = set()
    marker_by_source = {item["source"]: item for item in analysis["side_markers"]}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value == bg:
                continue
            marker = marker_by_source.get((r, c))
            if marker is not None and marker["side"] not in moved_sides:
                nr, nc = marker["destination"]
                moved_sides.add(marker["side"])
            else:
                nr, nc = r, c
            out[nr][nc] = value
    return out


def _rival_all_move_up(grid: list[list[int]]) -> list[list[int]]:
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed grid: " + "; ".join(errors))
    assert analysis is not None
    out = [row[:] for row in analysis["grid"]]
    bg = analysis["background"]
    h, w = analysis["height"], analysis["width"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            out[r][c] = bg
    side_values = set(analysis["side_colors"].values())
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = analysis["grid"][r][c]
            if value == bg:
                continue
            if value in side_values and r > 1:
                out[r - 1][c] = value
            else:
                out[r][c] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "move_two_steps": _rival_move_two_steps,
    "snap_to_matching_side": _rival_snap_to_side,
    "move_unmatched_colors": _rival_move_distractors,
    "erase_blocked_markers": _rival_drop_blocked,
    "move_only_one_marker_per_side": _rival_move_one_per_side,
    "move_all_side_colors_up": _rival_all_move_up,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    def witness(grid) -> bool:
        if self_check(grid):
            return False
        return rule_mirror(grid) != rival(grid)
    return witness


def _has_distractor(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and bool(analysis and analysis["distractor_counts"])


def _has_blocked(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and bool(analysis and any(item["blocked"] for item in analysis["side_markers"]))


SEMANTIC_WITNESSES = {
    "one_step_not_two": _differs_from(_rival_move_two_steps),
    "one_step_not_snap": _differs_from(_rival_snap_to_side),
    "unmatched_colors_stay": lambda grid: _has_distractor(grid) and rule_mirror(grid) != _rival_move_distractors(grid),
    "blocked_markers_stay": lambda grid: _has_blocked(grid) and rule_mirror(grid) != _rival_drop_blocked(grid),
    "every_marker_moves": _differs_from(_rival_move_one_per_side),
    "side_color_maps_direction": _differs_from(_rival_all_move_up),
}
WITNESS_RIVALS = {
    "one_step_not_two": ["move_two_steps"],
    "one_step_not_snap": ["snap_to_matching_side"],
    "unmatched_colors_stay": ["move_unmatched_colors"],
    "blocked_markers_stay": ["erase_blocked_markers"],
    "every_marker_moves": ["move_only_one_marker_per_side"],
    "side_color_maps_direction": ["move_all_side_colors_up"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a valid four-example lesson that eliminates every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is malformed: {'; '.join(errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the one-step side rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append("query is malformed: " + "; ".join(errors))
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the one-step side rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def _direction_vector(side: str) -> tuple[int, int]:
    return {
        "top": (-1, 0),
        "bottom": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }[side]


def _candidates(size: int, side: str, blocked: bool) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result: list[tuple[tuple[int, int], tuple[int, int]]] = []
    if blocked:
        if side == "top":
            sources = [(1, c) for c in range(1, size - 1)]
        elif side == "bottom":
            sources = [(size - 2, c) for c in range(1, size - 1)]
        elif side == "left":
            sources = [(r, 1) for r in range(1, size - 1)]
        else:
            sources = [(r, size - 2) for r in range(1, size - 1)]
        return [(source, source) for source in sources]

    dr, dc = _direction_vector(side)
    for r in range(1, size - 1):
        for c in range(1, size - 1):
            nr, nc = r + dr, c + dc
            if 1 <= nr <= size - 2 and 1 <= nc <= size - 2:
                result.append(((r, c), (nr, nc)))
    return result


def _place_marker(
    grid: list[list[int]],
    *,
    color: int,
    side: str,
    blocked: bool,
    used_sources: set[tuple[int, int]],
    used_destinations: set[tuple[int, int]],
    rng,
) -> None:
    candidates = _candidates(len(grid), side, blocked)
    rng.shuffle(candidates)
    for source, destination in candidates:
        if source in used_sources or destination in used_destinations:
            continue
        r, c = source
        if grid[r][c] != grid[0][0]:
            continue
        grid[r][c] = color
        used_sources.add(source)
        used_destinations.add(destination)
        return
    raise ValueError(f"no legal placement remains for side={side!r}, blocked={blocked}")


def _build_profile(ctx, profile: str) -> list[list[int]]:
    size, palette_size, side_count, blocked_count, distractor_multiset = PROFILE_SPECS[profile]
    colors = ctx.draw_distinct_colors("colors", n=palette_size, exclude=set())
    bg, top, bottom, left, right, *distractor_colors = colors
    grid = full_grid(size, size, bg)
    for c in range(1, size - 1):
        grid[0][c] = top
        grid[size - 1][c] = bottom
    for r in range(1, size - 1):
        grid[r][0] = left
        grid[r][size - 1] = right

    side_colors = {"top": top, "bottom": bottom, "left": left, "right": right}
    directions = list(side_colors)
    direction_rng = ctx.draw_rng("direction_quotas")
    direction_rng.shuffle(directions)

    movable_count = side_count - blocked_count
    if movable_count < 8:
        raise ValueError("profile must provide at least two movable markers per side")
    movable_quotas = {side: 2 for side in side_colors}
    for index in range(movable_count - 8):
        movable_quotas[directions[index % len(directions)]] += 1
    blocked_quotas = {side: 0 for side in side_colors}
    for index in range(blocked_count):
        blocked_quotas[directions[index % len(directions)]] += 1

    used_sources: set[tuple[int, int]] = set()
    used_destinations: set[tuple[int, int]] = set()
    for side in directions:
        for index in range(blocked_quotas[side]):
            _place_marker(
                grid,
                color=side_colors[side],
                side=side,
                blocked=True,
                used_sources=used_sources,
                used_destinations=used_destinations,
                rng=ctx.draw_rng(f"blocked_{side}_{index}"),
            )
    for side in directions:
        for index in range(movable_quotas[side]):
            _place_marker(
                grid,
                color=side_colors[side],
                side=side,
                blocked=False,
                used_sources=used_sources,
                used_destinations=used_destinations,
                rng=ctx.draw_rng(f"movable_{side}_{index}"),
            )

    distractor_rng = ctx.draw_rng("distractor_positions")
    for color, count in zip(distractor_colors, distractor_multiset):
        candidates = [
            (r, c)
            for r in range(1, size - 1)
            for c in range(1, size - 1)
            if (r, c) not in used_sources and (r, c) not in used_destinations and grid[r][c] == bg
        ]
        distractor_rng.shuffle(candidates)
        if len(candidates) < count:
            raise ValueError("not enough collision-free cells for distractors")
        for r, c in candidates[:count]:
            grid[r][c] = color
            used_sources.add((r, c))
            used_destinations.add((r, c))

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid generator instance: " + "; ".join(errors))
    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise ValueError(f"constructed profile {profile!r} but observed {observed!r}")
    return [row[:] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic authority-valid input; Racket owns output."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    return _build_profile(ctx, profile)
