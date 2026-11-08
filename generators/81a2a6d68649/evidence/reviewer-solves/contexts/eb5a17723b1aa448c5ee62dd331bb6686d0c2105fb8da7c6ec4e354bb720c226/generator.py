"""Generator for ARC task 81a2a6d68649.

Every blue (1) connected component is a straight bar. Horizontal blue bars
are recolored yellow (4), vertical blue bars are recolored orange (7), and
all non-blue distractors are preserved.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81a2a6d68649"
TASK_ID = "81a2a6d68649"
VERSION = "3.0.0"
RULE_HASH = "0360b462b672"

SUMMARY = (
    "A modal color-0 background contains separated straight blue (1) bars "
    "of both orientations plus one or two non-blue distractor objects. "
    "Recolor every horizontal blue bar yellow (4) and every vertical blue "
    "bar orange (7); preserve every other cell, including distractors that "
    "already use output colors 4 or 7 and straight non-blue orientation "
    "decoys."
)

INVARIANTS = [
    "background 0 is the unique modal color",
    "there is at least one horizontal and one vertical blue bar",
    "every blue component is a separated straight bar of length 2..7",
    "one or two separated non-blue distractor components remain unchanged",
    "scene_profile is exactly recoverable from the returned grid",
]

SCENE_PROFILES = (
    "minimal_mix",
    "horizontal_heavy",
    "vertical_heavy",
    "orientation_decoys",
    "output_color_decoys",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "keyed uniform choice",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# This generator has no side-channel texture branches. All supported semantic
# variation is represented by the observable scene_profile axis above.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DISTRACTOR_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
_ORIENTATION_DECOY_COLORS = (2, 3, 5, 6, 8, 9)
_PROFILE_BLUE_ORIENTATIONS = {
    "minimal_mix": ("horizontal", "vertical"),
    "horizontal_heavy": ("horizontal", "horizontal", "vertical"),
    "vertical_heavy": ("horizontal", "vertical", "vertical"),
    "orientation_decoys": (
        "horizontal",
        "horizontal",
        "vertical",
        "vertical",
    ),
    "output_color_decoys": (
        "horizontal",
        "horizontal",
        "vertical",
        "vertical",
    ),
}


def _components(grid: list[list[int]]) -> list[dict]:
    """Return same-color non-background 4-connected components."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            row_span = max(rows) - min(rows) + 1
            col_span = max(cols) - min(cols) + 1
            if len(cells) == 1:
                orientation = "point"
            elif row_span == 1 and col_span == len(cells):
                orientation = "horizontal"
            elif col_span == 1 and row_span == len(cells):
                orientation = "vertical"
            else:
                orientation = "other"
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "length": len(cells),
                    "orientation": orientation,
                }
            )
    return result


def _scene_profile(
    blue_components: list[dict], distractor_components: list[dict]
) -> str | None:
    horizontal = sum(
        component["orientation"] == "horizontal"
        for component in blue_components
    )
    vertical = sum(
        component["orientation"] == "vertical"
        for component in blue_components
    )

    if len(distractor_components) == 1:
        if (horizontal, vertical) == (1, 1):
            return "minimal_mix"
        if (horizontal, vertical) == (2, 1):
            return "horizontal_heavy"
        if (horizontal, vertical) == (1, 2):
            return "vertical_heavy"
        return None

    if (horizontal, vertical) != (2, 2) or len(distractor_components) != 2:
        return None

    output_decoys = {
        (component["orientation"], component["color"])
        for component in distractor_components
    }
    if (
        output_decoys == {("horizontal", 7), ("vertical", 4)}
        and all(component["length"] in (2, 3) for component in distractor_components)
    ):
        return "output_color_decoys"

    decoy_orientations = sorted(
        component["orientation"] for component in distractor_components
    )
    if (
        decoy_orientations == ["horizontal", "vertical"]
        and all(component["length"] in (2, 3) for component in distractor_components)
        and all(
            component["color"] in _ORIENTATION_DECOY_COLORS
            for component in distractor_components
        )
        and distractor_components[0]["color"]
        != distractor_components[1]["color"]
    ):
        return "orientation_decoys"
    return None


def _analyze(grid) -> dict:
    reasons: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"reasons": ["empty grid"], "scene_profile": None}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"reasons": ["zero-width grid"], "scene_profile": None}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"reasons": ["ragged grid"], "scene_profile": None}

    height = len(grid)
    if not (6 <= height <= 24 and 6 <= width <= 24):
        reasons.append(f"grid {height}x{width} outside the 6..24 envelope")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {
            "reasons": reasons + ["grid contains a non-integer or color outside 0..9"],
            "scene_profile": None,
        }

    counts = Counter(value for row in grid for value in row)
    largest_nonbackground = max(
        (count for color, count in counts.items() if color != 0),
        default=0,
    )
    if counts[0] <= largest_nonbackground:
        reasons.append("background 0 is not the unique modal color")

    components = _components(grid)
    blue_components = [component for component in components if component["color"] == 1]
    distractor_components = [
        component for component in components if component["color"] != 1
    ]

    if not (2 <= len(blue_components) <= 4):
        reasons.append(
            f"expected 2..4 blue components, found {len(blue_components)}"
        )
    for index, component in enumerate(blue_components):
        if component["orientation"] not in ("horizontal", "vertical"):
            reasons.append(f"blue component {index} is not a straight bar")
        if not (2 <= component["length"] <= 7):
            reasons.append(
                f"blue component {index} length {component['length']} outside 2..7"
            )

    horizontal = sum(
        component["orientation"] == "horizontal"
        for component in blue_components
    )
    vertical = sum(
        component["orientation"] == "vertical"
        for component in blue_components
    )
    if horizontal == 0 or vertical == 0:
        reasons.append("blue bars do not include both orientations")

    if not (1 <= len(distractor_components) <= 2):
        reasons.append(
            "expected one or two non-blue distractor components, found "
            f"{len(distractor_components)}"
        )
    for index, component in enumerate(distractor_components):
        if component["orientation"] not in ("point", "horizontal", "vertical"):
            reasons.append(f"distractor component {index} is not a point or straight bar")
        if not (1 <= component["length"] <= 3):
            reasons.append(
                f"distractor component {index} length {component['length']} outside 1..3"
            )

    # Canonical and generated objects are separated by at least one background
    # cell, including diagonally. This prevents accidental component/cue fusion.
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second = components[second_index]
            minimum_distance = min(
                max(abs(r1 - r2), abs(c1 - c2))
                for r1, c1 in first["cells"]
                for r2, c2 in second["cells"]
            )
            if minimum_distance < 2:
                reasons.append(
                    f"components {first_index} and {second_index} are not separated"
                )

    profile = _scene_profile(blue_components, distractor_components)
    if profile is None:
        reasons.append("component census does not match a declared scene_profile")

    return {
        "reasons": sorted(set(reasons)),
        "scene_profile": profile,
        "height": height,
        "width": width,
        "components": components,
        "blue_components": blue_components,
        "distractor_components": distractor_components,
        "horizontal_blue_bars": horizontal,
        "vertical_blue_bars": vertical,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full task lesson, not merely the palette."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact semantic override from the returned grid."""
    analysis = _analyze(grid)
    if analysis["reasons"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    return {"scene_profile": analysis["scene_profile"]}


def _geometry_for_band(profile: str, difficulty, rng) -> tuple[int, int, int]:
    if difficulty == "easy":
        low, high, maximum_bar_length = 8, 12, 4
    elif difficulty == "hard":
        low, high, maximum_bar_length = 14, 20, 7
    else:
        low, high, maximum_bar_length = 10, 16, 6

    minimum_for_profile = {
        "minimal_mix": 8,
        "horizontal_heavy": 9,
        "vertical_heavy": 9,
        "orientation_decoys": 11,
        "output_color_decoys": 11,
    }[profile]
    low = max(low, minimum_for_profile)
    return rng.randint(low, high), rng.randint(low, high), maximum_bar_length


def _blocked_halo(
    cells: Iterable[tuple[int, int]], height: int, width: int
) -> set[tuple[int, int]]:
    halo: set[tuple[int, int]] = set()
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    halo.add((nr, nc))
    return halo


def _segment_cells(
    row: int, col: int, orientation: str, length: int
) -> tuple[tuple[int, int], ...]:
    if orientation == "horizontal":
        return tuple((row, col + offset) for offset in range(length))
    if orientation == "vertical":
        return tuple((row + offset, col) for offset in range(length))
    if orientation == "point":
        return ((row, col),)
    raise ValueError(f"unknown orientation {orientation!r}")


def _candidate_segments(
    height: int,
    width: int,
    orientation: str,
    lengths: Iterable[int],
) -> list[tuple[tuple[int, int], ...]]:
    candidates: list[tuple[tuple[int, int], ...]] = []
    for length in lengths:
        row_limit = height - length + 1 if orientation == "vertical" else height
        col_limit = width - length + 1 if orientation == "horizontal" else width
        for row in range(row_limit):
            for col in range(col_limit):
                candidates.append(_segment_cells(row, col, orientation, length))
    return candidates


def _place_object(
    grid: list[list[int]],
    blocked: set[tuple[int, int]],
    *,
    color: int,
    orientation: str,
    lengths: Iterable[int],
    rng,
) -> bool:
    height, width = len(grid), len(grid[0])
    candidates = _candidate_segments(height, width, orientation, lengths)
    rng.shuffle(candidates)
    for cells in candidates:
        if any(cell in blocked for cell in cells):
            continue
        for row, col in cells:
            grid[row][col] = color
        blocked.update(_blocked_halo(cells, height, width))
        return True
    return False


def _length_order(maximum: int, rng) -> tuple[int, ...]:
    lengths = list(range(2, maximum + 1))
    preferred = rng.choice(lengths)
    rng.shuffle(lengths)
    lengths.remove(preferred)
    return (preferred, *lengths)


def _object_specs(profile: str, maximum_bar_length: int, layout_rng, color_rng):
    specs: list[dict] = []
    for orientation in _PROFILE_BLUE_ORIENTATIONS[profile]:
        specs.append(
            {
                "color": 1,
                "orientation": orientation,
                "lengths": _length_order(maximum_bar_length, layout_rng),
            }
        )

    if profile in ("minimal_mix", "horizontal_heavy", "vertical_heavy"):
        distractor_orientation = color_rng.choice(("horizontal", "vertical"))
        forbidden_output_color = 4 if distractor_orientation == "horizontal" else 7
        legal_colors = tuple(
            color for color in _DISTRACTOR_COLORS
            if color != forbidden_output_color
        )
        specs.append(
            {
                "color": color_rng.choice(legal_colors),
                "orientation": distractor_orientation,
                "lengths": (2, 3),
            }
        )
    elif profile == "orientation_decoys":
        colors = color_rng.sample(_ORIENTATION_DECOY_COLORS, 2)
        specs.extend(
            [
                {
                    "color": colors[0],
                    "orientation": "horizontal",
                    "lengths": (2, 3),
                },
                {
                    "color": colors[1],
                    "orientation": "vertical",
                    "lengths": (2, 3),
                },
            ]
        )
    elif profile == "output_color_decoys":
        # Deliberately cross the output colors with the opposite orientations:
        # a color-blind "recolor every bar by orientation" shortcut would alter
        # both decoys, while the intended blue-only rule preserves them.
        specs.extend(
            [
                {"color": 7, "orientation": "horizontal", "lengths": (2, 3)},
                {"color": 4, "orientation": "vertical", "lengths": (2, 3)},
            ]
        )
    else:
        raise ValueError(f"unknown scene_profile {profile!r}")

    layout_rng.shuffle(specs)
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    geometry_rng = ctx.draw_rng("geometry")
    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("distractor_colors")
    height, width, maximum_bar_length = _geometry_for_band(
        profile, difficulty, geometry_rng
    )
    specs = _object_specs(
        profile, maximum_bar_length, layout_rng, color_rng
    )

    for _ in range(40):
        grid = full_grid(height, width, 0)
        blocked: set[tuple[int, int]] = set()
        placed_all = all(
            _place_object(
                grid,
                blocked,
                color=spec["color"],
                orientation=spec["orientation"],
                lengths=spec["lengths"],
                rng=layout_rng,
            )
            for spec in specs
        )
        if not placed_all:
            continue
        analysis = _analyze(grid)
        if not analysis["reasons"] and analysis["scene_profile"] == profile:
            return grid

    raise RuntimeError(
        f"unable to place a valid {profile!r} scene in {height}x{width}"
    )
