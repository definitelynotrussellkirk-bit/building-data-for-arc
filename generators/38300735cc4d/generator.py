"""Generator for ``additional_scaffolded:M3`` — bridge aligned color pairs.

For every non-background color that occurs exactly twice, the two cells define
an eligible bridge only when they share a row or a column.  If every cell
strictly between the endpoints is black (0), fill that inclusive segment with
the endpoint color.  A blocker, a nonaligned pair, or a color with any count
other than two is preserved unchanged.

The teaching schedule keeps two canonical-scale clean profiles and adds three
independent counterexamples plus a mixed profile.  Each blocker-bearing profile
contains separate singleton-color and repeated-color blockers, so every five
consecutive samples also refute shortcuts that condition obstruction on blocker
frequency.  The same window rejects "copy the input", one-orientation rules,
ignoring blockers, using extrema of any repeated color, and box-filling two
nonaligned equal cells.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "38300735cc4d"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "e1f30dfc7d44"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.10

SUMMARY = (
    "Find every nonzero color occurring exactly twice. If its two cells are "
    "row- or column-aligned and the strict interior is all 0, fill the whole "
    "inclusive segment with that color. Blocked pairs, nonaligned pairs, and "
    "colors occurring three times stay unchanged. Generated five-sample "
    "windows contain horizontal and vertical bridges, singleton- and "
    "repeated-color blockers, and explicit wrong-count and nonalignment "
    "counterexamples."
)

INVARIANTS = [
    "background is 0 and all nonzero roles use distinct colors",
    "two or three disjoint eligible pair segments are present",
    "at least one clear horizontal and one clear vertical bridge are present",
    "blocker profiles have one singleton blocker and one scattered three-count blocker",
    "each blocked pair has exactly one blocker and blocker roles use separate colors",
    "a count decoy has exactly three collinear markers and remains unchanged",
    "an alignment decoy has exactly two markers in different rows and columns",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCENE_PROFILES = (
    "canonical_long",
    "blocked",
    "count_decoy",
    "clean_varied",
    "alignment_decoy",
    "mixed",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed; canonical profiles pin 9..11",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed; canonical profiles pin 9..11",
        "valid": "6..12",
    },
    "scene_profile": {
        "type": "str",
        "default": "six-step semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_CANONICAL_COLORS = (2, 3, 4, 6, 7)
_HORIZONTAL = "horizontal"
_VERTICAL = "vertical"


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public six-residue semantic schedule."""
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _basic_grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list"
    if not all(isinstance(row, list) and row for row in grid):
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if type(value) is not int or not 0 <= value <= 9:
                return f"cell ({row},{col}) must be an integer ARC color 0..9"
    return None


def _segment(orientation: str, fixed: int, start: int, end: int) -> dict[str, Any]:
    if orientation == _HORIZONTAL:
        path = tuple((fixed, col) for col in range(start, end + 1))
    else:
        path = tuple((row, fixed) for row in range(start, end + 1))
    return {
        "orientation": orientation,
        "endpoints": (path[0], path[-1]),
        "path": path,
        "interior": path[1:-1],
        "span": end - start,
    }


def _candidate_segments(
    height: int,
    width: int,
    orientation: str,
    span_mode: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if orientation == _HORIZONTAL:
        axis_size = width
        for row in range(height):
            for start in range(width - 2):
                for end in range(start + 2, width):
                    candidates.append(_segment(orientation, row, start, end))
    else:
        axis_size = height
        for col in range(width):
            for start in range(height - 2):
                for end in range(start + 2, height):
                    candidates.append(_segment(orientation, col, start, end))

    long_floor = max(4, axis_size - 3)
    if span_mode == "long":
        candidates = [item for item in candidates if item["span"] >= long_floor]
    elif span_mode == "short":
        candidates = [item for item in candidates if item["span"] == 2]
    elif span_mode == "medium":
        candidates = [item for item in candidates if item["span"] >= 3]
    elif span_mode != "any":
        raise ValueError(f"unknown span mode {span_mode!r}")
    return candidates


def _select_disjoint_segments(
    rng,
    height: int,
    width: int,
    specs: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    options: list[list[dict[str, Any]]] = []
    for orientation, span_mode in specs:
        candidates = _candidate_segments(height, width, orientation, span_mode)
        rng.shuffle(candidates)
        options.append(candidates)

    chosen: list[dict[str, Any]] = []

    def search(index: int, used: set[tuple[int, int]]) -> bool:
        if index == len(options):
            return True
        for candidate in options[index]:
            path = set(candidate["path"])
            if path & used:
                continue
            chosen.append(candidate)
            if search(index + 1, used | path):
                return True
            chosen.pop()
        return False

    if not search(0, set()):
        raise ValueError(
            f"could not place disjoint pair segments in {height}x{width} for {specs}"
        )
    return [dict(item) for item in chosen]


def _place_count_decoy(
    rng,
    height: int,
    width: int,
    reserved: set[tuple[int, int]],
) -> dict[str, Any]:
    candidates = (
        _candidate_segments(height, width, _HORIZONTAL, "medium")
        + _candidate_segments(height, width, _VERTICAL, "medium")
    )
    rng.shuffle(candidates)
    for candidate in candidates:
        path = tuple(candidate["path"])
        if set(path) & reserved:
            continue
        middle_choices = list(range(1, len(path) - 1))
        rng.shuffle(middle_choices)
        for middle_index in middle_choices:
            markers = (path[0], path[middle_index], path[-1])
            if len(set(path) - set(markers)) >= 1:
                result = dict(candidate)
                result["markers"] = markers
                return result
    raise ValueError("could not place a disjoint three-marker count decoy")


def _place_unaligned_decoy(
    rng,
    height: int,
    width: int,
    reserved: set[tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int]]:
    free = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in reserved
    ]
    candidates = [
        (left, right)
        for index, left in enumerate(free)
        for right in free[index + 1 :]
        if left[0] != right[0] and left[1] != right[1]
    ]
    rng.shuffle(candidates)
    if not candidates:
        raise ValueError("could not place a nonaligned two-marker decoy")
    return candidates[0]


def _place_scattered_blocker(
    rng,
    height: int,
    width: int,
    target_pair: dict[str, Any],
    reserved: set[tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Place a three-count blocker with one marker in the target interior.

    The other two markers stay outside every reserved semantic span, and the
    three markers are deliberately noncollinear.  This isolates blocker-color
    frequency from the aligned wrong-count branch.
    """
    interiors = list(target_pair["interior"])
    free = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in reserved
    ]
    rng.shuffle(interiors)
    rng.shuffle(free)
    for blocker_cell in interiors:
        for left_index, left in enumerate(free):
            for right in free[left_index + 1 :]:
                markers = (blocker_cell, left, right)
                if len({row for row, _ in markers}) > 1 and len(
                    {col for _, col in markers}
                ) > 1:
                    return markers
    raise ValueError("could not place a noncollinear three-count blocker")


def _pair_specs(scene_profile: str, rng) -> list[tuple[str, str]]:
    if scene_profile == "canonical_long":
        return [(_HORIZONTAL, "long"), (_VERTICAL, "short")]
    if scene_profile == "clean_varied":
        return [(_HORIZONTAL, "short"), (_VERTICAL, "medium")]
    specs = [(_HORIZONTAL, "any"), (_VERTICAL, "any")]
    if scene_profile in ("blocked", "mixed"):
        specs.append((rng.choice((_HORIZONTAL, _VERTICAL)), "any"))
    return specs


def _build_scene(
    rng,
    height: int,
    width: int,
    scene_profile: str,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any] | None,
    tuple | None,
    int | None,
    tuple[tuple[int, int], tuple[int, int], tuple[int, int]] | None,
]:
    wants_blockers = scene_profile in ("blocked", "mixed")
    wants_count = scene_profile in ("count_decoy", "mixed")
    wants_unaligned = scene_profile in ("alignment_decoy", "mixed")

    last_error: Exception | None = None
    for _ in range(160):
        try:
            pairs = _select_disjoint_segments(
                rng, height, width, _pair_specs(scene_profile, rng)
            )
            reserved = {cell for pair in pairs for cell in pair["path"]}
            count_decoy = None
            if wants_count:
                count_decoy = _place_count_decoy(
                    rng, height, width, reserved
                )
                reserved.update(count_decoy["path"])
            unaligned = None
            if wants_unaligned:
                unaligned = _place_unaligned_decoy(
                    rng, height, width, reserved
                )
                reserved.update(unaligned)

            singleton_blocked_index = None
            scattered_blocker = None
            if wants_blockers:
                indices = list(range(len(pairs)))
                rng.shuffle(indices)
                singleton_blocked_index, repeated_blocked_index = indices[:2]
                scattered_blocker = _place_scattered_blocker(
                    rng,
                    height,
                    width,
                    pairs[repeated_blocked_index],
                    reserved,
                )
            return (
                pairs,
                count_decoy,
                unaligned,
                singleton_blocked_index,
                scattered_blocker,
            )
        except ValueError as exc:
            last_error = exc
    raise ValueError(
        f"could not realize scene_profile={scene_profile!r} in {height}x{width}: "
        f"{last_error}"
    )


def _positions_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions[value].append((row, col))
    return dict(positions)


def _record_for_cells(
    grid: list[list[int]], color: int, cells: list[tuple[int, int]]
) -> dict[str, Any] | None:
    if len(cells) not in (2, 3):
        return None
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1:
        row = next(iter(rows))
        start, end = min(cols), max(cols)
        record = _segment(_HORIZONTAL, row, start, end)
    elif len(cols) == 1:
        col = next(iter(cols))
        start, end = min(rows), max(rows)
        record = _segment(_VERTICAL, col, start, end)
    else:
        return None
    record["color"] = color
    record["cells"] = tuple(sorted(cells))
    record["blocker_cells"] = tuple(
        cell for cell in record["interior"] if grid[cell[0]][cell[1]] != 0
    )
    record["clear"] = not record["blocker_cells"]
    return record


def _canonical_long_geometry(facts: dict[str, Any]) -> bool:
    if facts["n_pairs"] != 2:
        return False
    horizontal = [
        pair for pair in facts["pairs"] if pair["orientation"] == _HORIZONTAL
    ]
    vertical = [
        pair for pair in facts["pairs"] if pair["orientation"] == _VERTICAL
    ]
    if len(horizontal) != 1 or len(vertical) != 1:
        return False
    return (
        horizontal[0]["span"] >= max(4, facts["grid_w"] - 3)
        and vertical[0]["span"] == 2
    )


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the exact axes and decisive rule branches from returned cells."""
    basic_error = _basic_grid_error(grid)
    if basic_error:
        raise ValueError(basic_error)

    positions = _positions_by_color(grid)
    pairs: list[dict[str, Any]] = []
    unaligned: list[dict[str, Any]] = []
    count_decoys: list[dict[str, Any]] = []
    repeated_unaligned: list[dict[str, Any]] = []
    singletons: list[dict[str, Any]] = []
    unsupported_counts: list[tuple[int, int]] = []

    for color, cells in sorted(positions.items()):
        if len(cells) == 1:
            singletons.append({"color": color, "cell": cells[0]})
        elif len(cells) == 2:
            record = _record_for_cells(grid, color, cells)
            if record is None:
                unaligned.append({"color": color, "cells": tuple(sorted(cells))})
            else:
                pairs.append(record)
        elif len(cells) == 3:
            record = _record_for_cells(grid, color, cells)
            if record is None:
                repeated_unaligned.append(
                    {"color": color, "cells": tuple(sorted(cells))}
                )
            else:
                count_decoys.append(record)
        else:
            unsupported_counts.append((color, len(cells)))

    blocker_membership: dict[int, list[int]] = defaultdict(list)
    for pair_index, pair in enumerate(pairs):
        for cell in pair["blocker_cells"]:
            value = grid[cell[0]][cell[1]]
            blocker_membership[value].append(pair_index)

    isolated_singletons = [
        item for item in singletons if item["color"] not in blocker_membership
    ]
    scattered_blockers: list[dict[str, Any]] = []
    for item in repeated_unaligned:
        memberships = blocker_membership.get(item["color"], [])
        if len(memberships) == 1:
            scattered_blockers.append(
                {**item, "blocked_pair_indices": tuple(memberships)}
            )
        else:
            unsupported_counts.append((item["color"], len(item["cells"])))
    orientations = {pair["orientation"] for pair in pairs}
    signature = (
        sum(not pair["clear"] for pair in pairs),
        len(count_decoys),
        len(unaligned),
    )
    profile_map = {
        (2, 0, 0): "blocked",
        (0, 1, 0): "count_decoy",
        (0, 0, 1): "alignment_decoy",
        (2, 1, 1): "mixed",
    }

    facts: dict[str, Any] = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "positions": positions,
        "pairs": pairs,
        "n_pairs": len(pairs),
        "clear_pairs": [pair for pair in pairs if pair["clear"]],
        "blocked_pairs": [pair for pair in pairs if not pair["clear"]],
        "count_decoys": count_decoys,
        "unaligned_decoys": unaligned,
        "scattered_blockers": scattered_blockers,
        "singletons": singletons,
        "isolated_singletons": isolated_singletons,
        "blocker_membership": dict(blocker_membership),
        "blocker_color_counts": sorted(
            len(positions[color]) for color in blocker_membership
        ),
        "unsupported_counts": unsupported_counts,
        "orientations": orientations,
    }
    if signature == (0, 0, 0):
        facts["scene_profile"] = (
            "canonical_long" if _canonical_long_geometry(facts) else "clean_varied"
        )
    else:
        facts["scene_profile"] = profile_map.get(signature, "unsupported")
    return facts


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover every declared exact override axis from the grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = semantic_observables(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "scene_profile": facts["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full bounded bridge grammar and reject rule-hiding scenes."""
    del difficulty, meta
    basic_error = _basic_grid_error(grid)
    if basic_error:
        return [basic_error]

    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 5 <= height <= 14 or not 5 <= width <= 14:
        errors.append(f"grid dimensions {height}x{width} must be within 5..14")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    facts = semantic_observables(grid)
    if facts["unsupported_counts"]:
        errors.append(
            "unsupported nonzero color counts: "
            + repr(facts["unsupported_counts"])
        )
    if not 2 <= facts["n_pairs"] <= 3:
        errors.append(f"expected 2 or 3 aligned two-marker pairs, got {facts['n_pairs']}")
    if _HORIZONTAL not in facts["orientations"]:
        errors.append("at least one horizontal pair is required")
    if _VERTICAL not in facts["orientations"]:
        errors.append("at least one vertical pair is required")
    if not facts["clear_pairs"]:
        errors.append("at least one pair must have a clear interior")

    pair_paths = [set(pair["path"]) for pair in facts["pairs"]]
    for left in range(len(pair_paths)):
        for right in range(left + 1, len(pair_paths)):
            if pair_paths[left] & pair_paths[right]:
                errors.append(f"pair segments {left} and {right} intersect")

    singleton_colors = {item["color"] for item in facts["singletons"]}
    scattered_colors = {item["color"] for item in facts["scattered_blockers"]}
    if facts["isolated_singletons"]:
        errors.append(
            "singleton colors may appear only as blockers inside one pair: "
            + repr(facts["isolated_singletons"])
        )
    blocker_counts: list[int] = []
    for pair_index, pair in enumerate(facts["pairs"]):
        if pair["clear"]:
            continue
        if len(pair["blocker_cells"]) != 1:
            errors.append(
                f"blocked pair color {pair['color']} must contain exactly one blocker"
            )
            continue
        cell = pair["blocker_cells"][0]
        blocker_color = grid[cell[0]][cell[1]]
        blocker_count = len(facts["positions"].get(blocker_color, ()))
        blocker_counts.append(blocker_count)
        if blocker_count == 1:
            if blocker_color not in singleton_colors:
                errors.append(
                    f"singleton blocker color {blocker_color} was not classified"
                )
        elif blocker_count == 3:
            if blocker_color not in scattered_colors:
                errors.append(
                    f"repeated blocker color {blocker_color} must be noncollinear"
                )
        else:
            errors.append(
                f"blocker color {blocker_color} must occur once or three times"
            )
        memberships = facts["blocker_membership"].get(blocker_color, [])
        if memberships != [pair_index]:
            errors.append(
                f"blocker color {blocker_color} must block exactly pair {pair_index}"
            )

    if len(facts["blocked_pairs"]) > 2:
        errors.append("at most two blocked pairs are supported")
    if len(facts["scattered_blockers"]) > 1:
        errors.append("at most one scattered repeated-color blocker is supported")
    if facts["scene_profile"] in ("blocked", "mixed") and sorted(blocker_counts) != [1, 3]:
        errors.append(
            "blocker profiles require one singleton and one three-count blocker"
        )
    if len(facts["count_decoys"]) > 1:
        errors.append("at most one three-marker count decoy is supported")
    if len(facts["unaligned_decoys"]) > 1:
        errors.append("at most one nonaligned two-marker decoy is supported")

    all_pair_cells = set().union(*pair_paths) if pair_paths else set()
    for decoy in facts["count_decoys"]:
        if set(decoy["path"]) & all_pair_cells:
            errors.append("count-decoy span must be disjoint from eligible pair spans")
        if not any(grid[row][col] == 0 for row, col in decoy["path"]):
            errors.append("count decoy must leave a zero gap that a wrong rule would fill")
    count_paths = {
        cell for decoy in facts["count_decoys"] for cell in decoy["path"]
    }
    for decoy in facts["unaligned_decoys"]:
        if set(decoy["cells"]) & (all_pair_cells | count_paths):
            errors.append("nonaligned decoy cells must be outside all line spans")

    if facts["scene_profile"] not in SCENE_PROFILES:
        errors.append(
            "unsupported semantic branch combination: "
            f"blocked={len(facts['blocked_pairs'])}, "
            f"count_decoys={len(facts['count_decoys'])}, "
            f"unaligned={len(facts['unaligned_decoys'])}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked manifold represented by all three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["grid_h"] != facts["grid_w"] or facts["grid_h"] not in (9, 10, 11):
        reasons.append("canonical grids are square with side 9, 10, or 11")
    if facts["scene_profile"] != "canonical_long":
        reasons.append("canonical scenes have one long horizontal and one short vertical pair")
    if facts["n_pairs"] != 2:
        reasons.append("canonical scenes contain exactly two eligible colors")
    if not set(facts["positions"]).issubset(_CANONICAL_COLORS):
        reasons.append("canonical nonzero colors come from 2,3,4,6,7")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains output authority."""
    basic_error = _basic_grid_error(grid)
    if basic_error:
        raise ValueError(basic_error)
    output = deepcopy(grid)
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        record = _record_for_cells(grid, color, cells)
        if record is None or record["span"] < 2:
            continue
        if any(grid[row][col] != 0 for row, col in record["interior"]):
            continue
        for row, col in record["path"]:
            output[row][col] = color
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    scheduled: dict[str, Any] = {"scene_profile": scheduled_profile}
    if scheduled_profile in ("canonical_long", "clean_varied"):
        side = (9, 10, 11)[(int(seed) + int(sample_index)) % 3]
        scheduled.update({"grid_h": side, "grid_w": side})
    effective = {**scheduled, **overrides}

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_diff("grid_h", 6, 12)
    width = ctx.draw_int_diff("grid_w", 6, 12)
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    layout_rng = ctx.draw_rng("layout")

    (
        pairs,
        count_decoy,
        unaligned,
        singleton_blocked_index,
        scattered_blocker,
    ) = _build_scene(layout_rng, height, width, scene_profile)
    needs_blockers = singleton_blocked_index is not None
    needed_colors = (
        len(pairs)
        + int(needs_blockers)
        + int(scattered_blocker is not None)
        + int(count_decoy is not None)
        + int(unaligned is not None)
    )
    palette_rng = ctx.draw_rng("palette")
    palette_source = (
        list(_CANONICAL_COLORS)
        if scene_profile in ("canonical_long", "clean_varied")
        else list(range(1, 10))
    )
    if needed_colors > len(palette_source):
        raise ValueError(f"scene needs {needed_colors} colors, only {len(palette_source)} available")
    colors = palette_rng.sample(palette_source, needed_colors)
    color_index = 0

    grid = full_grid(height, width, 0)
    for pair_index, pair in enumerate(pairs):
        color = colors[color_index]
        color_index += 1
        pair["color"] = color
        for row, col in pair["endpoints"]:
            grid[row][col] = color
        if singleton_blocked_index == pair_index:
            blocker_cell = layout_rng.choice(list(pair["interior"]))
            blocker_color = colors[color_index]
            color_index += 1
            grid[blocker_cell[0]][blocker_cell[1]] = blocker_color

    if scattered_blocker is not None:
        color = colors[color_index]
        color_index += 1
        for row, col in scattered_blocker:
            grid[row][col] = color

    if count_decoy is not None:
        color = colors[color_index]
        color_index += 1
        for row, col in count_decoy["markers"]:
            grid[row][col] = color
    if unaligned is not None:
        color = colors[color_index]
        color_index += 1
        for row, col in unaligned:
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": scene_profile,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(
            f"axis realization drift: expected {expected}, observed {observed}"
        )
    if rule_mirror(grid) == grid:
        raise AssertionError("generated scene has no clear bridge and would teach identity")
    return grid


# ---------------------------------------------------------------------------
# Named plausible wrong rules and task-linked discriminating witnesses.
# ---------------------------------------------------------------------------


def _rival_copy_input(grid):
    return deepcopy(grid)


def _rival_one_orientation(grid, orientation: str):
    output = deepcopy(grid)
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        record = _record_for_cells(grid, color, cells)
        if record is None or record["orientation"] != orientation:
            continue
        if any(grid[row][col] != 0 for row, col in record["interior"]):
            continue
        for row, col in record["path"]:
            output[row][col] = color
    return output


def _rival_horizontal_only(grid):
    return _rival_one_orientation(grid, _HORIZONTAL)


def _rival_vertical_only(grid):
    return _rival_one_orientation(grid, _VERTICAL)


def _rival_ignore_blockers(grid):
    output = deepcopy(grid)
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        record = _record_for_cells(grid, color, cells)
        if record is None:
            continue
        for row, col in record["path"]:
            output[row][col] = color
    return output


def _rival_fill_extrema_any_count(grid):
    output = deepcopy(grid)
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) < 2:
            continue
        record = _record_for_cells(grid, color, cells) if len(cells) in (2, 3) else None
        if record is None:
            continue
        if any(grid[row][col] not in (0, color) for row, col in record["path"]):
            continue
        for row, col in record["path"]:
            output[row][col] = color
    return output


def _rival_block_by_frequency(
    grid: list[list[int]], blocker_is_active: Callable[[int], bool]
) -> list[list[int]]:
    """Bridge pairs while recognizing blockers only at selected frequencies."""
    output = deepcopy(grid)
    positions = _positions_by_color(grid)
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            continue
        record = _record_for_cells(grid, color, cells)
        if record is None:
            continue
        active_blocker = any(
            grid[row][col] != 0
            and blocker_is_active(len(positions[grid[row][col]]))
            for row, col in record["interior"]
        )
        if active_blocker:
            continue
        for row, col in record["path"]:
            output[row][col] = color
    return output


def _rival_block_only_singletons(grid):
    return _rival_block_by_frequency(grid, lambda count: count == 1)


def _rival_block_only_repeated(grid):
    return _rival_block_by_frequency(grid, lambda count: count > 1)


def _rival_fill_bbox_for_two(grid):
    """Respect all aligned-pair conditions, but box-fill nonaligned pairs."""
    output = deepcopy(grid)
    for color, cells in sorted(_positions_by_color(grid).items()):
        if len(cells) != 2:
            continue
        record = _record_for_cells(grid, color, cells)
        if record is not None:
            if any(grid[row][col] != 0 for row, col in record["interior"]):
                continue
            for row, col in record["path"]:
                output[row][col] = color
            continue
        (r1, c1), (r2, c2) = cells
        for row in range(min(r1, r2), max(r1, r2) + 1):
            for col in range(min(c1, c2), max(c1, c2) + 1):
                output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy_input": _rival_copy_input,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "ignore_blockers": _rival_ignore_blockers,
    "block_only_singletons": _rival_block_only_singletons,
    "block_only_repeated": _rival_block_only_repeated,
    "fill_extrema_any_count": _rival_fill_extrema_any_count,
    "fill_bbox_for_two": _rival_fill_bbox_for_two,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_blockers": _rival_ignore_blockers,
    "block_only_singletons": _rival_block_only_singletons,
    "block_only_repeated": _rival_block_only_repeated,
    "fill_extrema_any_count": _rival_fill_extrema_any_count,
    "fill_bbox_for_two": _rival_fill_bbox_for_two,
}


def _lawful_difference(rival_name: str, predicate: Callable[[dict[str, Any]], bool]):
    rival = SEMANTIC_RIVALS[rival_name]

    def witness(grid):
        if self_check(grid):
            return False
        facts = semantic_observables(grid)
        return predicate(facts) and rival(grid) != rule_mirror(grid)

    return witness


SEMANTIC_WITNESSES = {
    "clear_bridge_changes_grid": _lawful_difference(
        "copy_input", lambda facts: bool(facts["clear_pairs"])
    ),
    "horizontal_branch": _lawful_difference(
        "vertical_only",
        lambda facts: any(
            pair["clear"] and pair["orientation"] == _HORIZONTAL
            for pair in facts["pairs"]
        ),
    ),
    "vertical_branch": _lawful_difference(
        "horizontal_only",
        lambda facts: any(
            pair["clear"] and pair["orientation"] == _VERTICAL
            for pair in facts["pairs"]
        ),
    ),
    "blocked_segment_is_conditional": _lawful_difference(
        "ignore_blockers", lambda facts: bool(facts["blocked_pairs"])
    ),
    "singleton_blocker_is_real": _lawful_difference(
        "block_only_repeated",
        lambda facts: 1 in facts["blocker_color_counts"],
    ),
    "repeated_color_blocks_too": _lawful_difference(
        "block_only_singletons",
        lambda facts: 3 in facts["blocker_color_counts"],
    ),
    "exactly_two_markers_required": _lawful_difference(
        "fill_extrema_any_count", lambda facts: bool(facts["count_decoys"])
    ),
    "row_or_column_alignment_required": _lawful_difference(
        "fill_bbox_for_two", lambda facts: bool(facts["unaligned_decoys"])
    ),
}
WITNESS_RIVALS = {
    "clear_bridge_changes_grid": ["copy_input"],
    "horizontal_branch": ["vertical_only"],
    "vertical_branch": ["horizontal_only"],
    "blocked_segment_is_conditional": ["ignore_blockers"],
    "singleton_blocker_is_real": ["block_only_repeated"],
    "repeated_color_blocks_too": ["block_only_singletons"],
    "exactly_two_markers_required": ["fill_extrema_any_count"],
    "row_or_column_alignment_required": ["fill_bbox_for_two"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every named shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        grammar = self_check(pair["input"])
        if grammar:
            reasons.append(f"demo {index} input is outside the bridge grammar: {grammar[:2]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the straight-bridge rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output grids")
    else:
        grammar = self_check(query["input"])
        if grammar:
            reasons.append(f"query input is outside the bridge grammar: {grammar[:2]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the straight-bridge rule")
    if reasons:
        return reasons

    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            relation = (
                "same query answer"
                if rival(query["input"]) == query["output"]
                else "different query answer"
            )
            reasons.append(
                f"competing rule {name!r} survives every demonstration ({relation})"
            )
    return reasons


def mutation_impostors(grid):
    """Small task-local destructive fixtures used by focused tests/review."""
    if self_check(grid):
        raise ValueError("mutation_impostors requires a lawful source grid")
    facts = semantic_observables(grid)
    out = []

    missing_endpoint = deepcopy(grid)
    endpoint = facts["pairs"][0]["endpoints"][0]
    missing_endpoint[endpoint[0]][endpoint[1]] = 0
    out.append(("missing_endpoint", missing_endpoint))

    fourth_marker = deepcopy(grid)
    color = facts["pairs"][0]["color"]
    occupied = {cell for cells in facts["positions"].values() for cell in cells}
    free = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) not in occupied
    )
    fourth_marker[free[0]][free[1]] = color
    out.append(("third_marker_on_endpoint_color", fourth_marker))

    isolated_singleton = deepcopy(grid)
    unused_color = next(color for color in range(1, 10) if color not in facts["positions"])
    free = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0
        and all((row, col) not in pair["path"] for pair in facts["pairs"])
    )
    isolated_singleton[free[0]][free[1]] = unused_color
    out.append(("isolated_singleton", isolated_singleton))

    one_orientation = deepcopy(grid)
    for vertical in (
        pair for pair in facts["pairs"] if pair["orientation"] == _VERTICAL
    ):
        for row, col in vertical["endpoints"]:
            one_orientation[row][col] = 0
    out.append(("remove_all_vertical_pairs", one_orientation))
    return out
