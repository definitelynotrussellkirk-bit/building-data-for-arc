"""Semantic generator for ARC task 28b87bd4c441.

The input contains one red marker (2) and one four-connected gray component
(5).  Translate the component so that the top-left coordinate of its bounding
box coincides with the marker, erase the source and marker, and preserve the
component's exact shape on an otherwise empty canvas.

The public examples only show diagonal moves, and only one public component
has an empty bounding-box corner.  The generated curriculum deliberately adds
all four axis-aligned directions and repeatedly exercises connected concave
components whose bbox corner is empty; those are decisive counterexamples to
diagonal-only and "put the first gray cell on red" shortcuts.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "28b87bd4c441"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "0af5c7008ee7"

SUMMARY = (
    "Move the sole color-5 component without rotation so its bounding-box "
    "top-left coordinate lands on the sole color-2 marker; emit only the "
    "translated component on a same-size black grid."
)

INVARIANTS = [
    "the input uses only background 0, one marker 2, and one four-connected component of 5s",
    "the marker is outside the source component and the translation is non-zero",
    "the whole translated component remains in bounds",
    "the source and marker disappear from the output",
    "component cell count, shape, and orientation are preserved exactly",
    "the marker denotes the destination bbox origin, even when that bbox corner is empty",
    "the returned grid belongs to one exact observable scene profile",
]

# Eight profiles cross every sign/axis relation with canonical-scale and broader
# connected shapes.  A single categorical axis avoids impossible independent
# override combinations while keeping every declaration exactly observable.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "zig4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "hollow_tee4": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "p5": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    # The next three have an empty top-left bbox corner.  They distinguish
    # bbox-origin alignment from aligning the first occupied cell to marker 2.
    "hollow_l3": ((0, 1), (1, 0), (1, 1)),
    "hollow_u5": ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "branch6": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    "stair7": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
}

_PROFILE_SPECS: dict[str, dict[str, object]] = {
    "canonical_down_right_l4": {
        "dims": (10, 10), "shape": "l4", "relation": "down_right"
    },
    "canonical_up_left_zig4": {
        "dims": (11, 11), "shape": "zig4", "relation": "up_left"
    },
    "canonical_down_left_tee4": {
        "dims": (12, 12), "shape": "hollow_tee4", "relation": "down_left"
    },
    "canonical_up_right_p5": {
        "dims": (12, 13), "shape": "p5", "relation": "up_right"
    },
    "row_left_hollow_l3": {
        "dims": (9, 12), "shape": "hollow_l3", "relation": "row_left"
    },
    "row_right_hollow_u5": {
        "dims": (12, 9), "shape": "hollow_u5", "relation": "row_right"
    },
    "column_up_branch6": {
        "dims": (13, 13), "shape": "branch6", "relation": "column_up"
    },
    "column_down_stair7": {
        "dims": (14, 14), "shape": "stair7", "relation": "column_down"
    },
}
PROFILE_NAMES = tuple(_PROFILE_SPECS)
CANONICAL_PROFILES = frozenset(tuple(_PROFILE_SPECS)[:4])
RELATIONS = tuple(spec["relation"] for spec in _PROFILE_SPECS.values())

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic (seed + sample_index) cycle over all eight profiles",
        "valid": "canonical_down_right_l4|canonical_up_left_zig4|canonical_down_left_tee4|canonical_up_right_p5|row_left_hollow_l3|row_right_hollow_u5|column_up_branch6|column_down_stair7",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
MIN_STRICT_FRAC = 0.45
EXAMPLES_NEEDED = len(PROFILE_NAMES)
SCHEDULE_PROFILES = PROFILE_NAMES

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell {(r, c)} is not a literal ARC color 0..9: {value!r}"]
    return []


def _cells_of(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _components(cells: Iterable[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    unseen = set(cells)
    found: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        found.append(tuple(sorted(component)))
    return sorted(found, key=lambda component: component[0])


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = list(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _normalized_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = list(cells)
    r0, c0, _, _ = _bbox(points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = list(shape)
    return max(r for r, _ in points) + 1, max(c for _, c in points) + 1


def _relation(dr: int, dc: int) -> str | None:
    if dr < 0 and dc < 0:
        return "up_left"
    if dr < 0 and dc > 0:
        return "up_right"
    if dr > 0 and dc < 0:
        return "down_left"
    if dr > 0 and dc > 0:
        return "down_right"
    if dr == 0 and dc < 0:
        return "row_left"
    if dr == 0 and dc > 0:
        return "row_right"
    if dr < 0 and dc == 0:
        return "column_up"
    if dr > 0 and dc == 0:
        return "column_down"
    return None


def _scene_facts(grid) -> dict[str, object]:
    marker_cells = _cells_of(grid, 2)
    blob_cells = _cells_of(grid, 5)
    if len(marker_cells) != 1 or not blob_cells:
        raise ValueError("scene facts require one marker and at least one blob cell")
    r0, c0, r1, c1 = _bbox(blob_cells)
    mr, mc = marker_cells[0]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "marker": (mr, mc),
        "blob_cells": tuple(sorted(blob_cells)),
        "shape": _normalized_shape(blob_cells),
        "bbox": (r0, c0, r1, c1),
        "bbox_dims": (r1 - r0 + 1, c1 - c0 + 1),
        "shift": (mr - r0, mc - c0),
        "relation": _relation(mr - r0, mc - c0),
        "anchor_occupied": (r0, c0) in blob_cells,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, clipped, or rule-hiding scenes."""
    del meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    try:
        _band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 14):
        errors.append(f"height {height} outside 8..14")
    if not (8 <= width <= 14):
        errors.append(f"width {width} outside 8..14")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 5}:
        errors.append(f"only colors 0, 2, and 5 are lawful, found {sorted(palette)}")

    marker_cells = _cells_of(grid, 2)
    blob_cells = _cells_of(grid, 5)
    if len(marker_cells) != 1:
        errors.append(f"expected exactly one color-2 marker, found {len(marker_cells)}")
    if not (3 <= len(blob_cells) <= 9):
        errors.append(f"expected 3..9 color-5 cells, found {len(blob_cells)}")
    if errors:
        return errors

    components = _components(blob_cells)
    if len(components) != 1:
        errors.append(f"expected one four-connected color-5 component, found {len(components)}")
        return errors

    r0, c0, r1, c1 = _bbox(blob_cells)
    bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    if not (2 <= bbox_h <= 4 and 2 <= bbox_w <= 4):
        errors.append(f"component bbox {bbox_h}x{bbox_w} outside 2..4 by 2..4")

    mr, mc = marker_cells[0]
    dr, dc = mr - r0, mc - c0
    if _relation(dr, dc) is None:
        errors.append("marker must specify one of eight non-zero translation directions")
    if r0 <= mr <= r1 and c0 <= mc <= c1:
        errors.append("marker must lie outside the source component bounding box")

    translated = {(r + dr, c + dc) for r, c in blob_cells}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in translated):
        errors.append("translated component leaves the grid")
    if len(translated) != len(blob_cells):
        errors.append("translation must preserve one-to-one component positions")
    if translated == set(blob_cells):
        errors.append("translation must move the component")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] on the public task's dimension/shape/diagonal manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = _scene_facts(grid)
    dims = (facts["height"], facts["width"])
    if dims not in {(10, 10), (11, 11), (12, 12), (12, 13)}:
        reasons.append(f"canonical dimensions are 10x10, 11x11, 12x12, or 12x13; found {dims}")
    count = len(facts["blob_cells"])
    if count not in {4, 5}:
        reasons.append(f"canonical components contain 4 or 5 cells, found {count}")
    if facts["bbox_dims"] not in {(3, 2), (2, 3)}:
        reasons.append(f"canonical bbox is 3x2 or 2x3, found {facts['bbox_dims']}")
    dr, dc = facts["shift"]
    if dr == 0 or dc == 0:
        reasons.append(f"canonical marker displacement is diagonal, found {(dr, dc)}")
    return reasons


def _profile_of(grid) -> str | None:
    if self_check(grid):
        return None
    facts = _scene_facts(grid)
    signature = (
        (facts["height"], facts["width"]),
        facts["shape"],
        facts["relation"],
    )
    for name, spec in _PROFILE_SPECS.items():
        candidate = (
            spec["dims"],
            _SHAPES[str(spec["shape"])],
            spec["relation"],
        )
        if signature == candidate:
            return name
    return None


def canonical_profile_signature(grid):
    profile = _profile_of(grid)
    return profile if profile in CANONICAL_PROFILES else None


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid does not match any declared scene profile")
    return {"scene_profile": profile}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _scene_facts(grid)
    dr, dc = facts["shift"]
    output = full_grid(int(facts["height"]), int(facts["width"]), 0)
    for r, c in facts["blob_cells"]:
        output[r + dr][c + dc] = 5
    return output


def _translated_with_shift(grid, dr: int, dc: int, *, limit: int | None = None) -> list[list[int]]:
    facts = _scene_facts(grid)
    output = full_grid(int(facts["height"]), int(facts["width"]), 0)
    cells = list(facts["blob_cells"])
    if limit is not None:
        cells = cells[:limit]
    shifted = [(r + dr, c + dc) for r, c in cells]
    if any(not (0 <= r < len(output) and 0 <= c < len(output[0])) for r, c in shifted):
        return output
    for r, c in shifted:
        output[r][c] = 5
    return output


def _rival_first_blob_cell_anchor(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    first_r, first_c = facts["blob_cells"][0]
    marker_r, marker_c = facts["marker"]
    return _translated_with_shift(grid, marker_r - first_r, marker_c - first_c)


def _rival_diagonal_only(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    dr, dc = facts["shift"]
    if dr == 0 or dc == 0:
        return full_grid(int(facts["height"]), int(facts["width"]), 0)
    return _translated_with_shift(grid, dr, dc)


def _signed_nonzero(value: int, sign: int) -> int:
    magnitude = max(1, abs(value))
    return magnitude if sign > 0 else -magnitude


def _rival_always_down_right(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    dr, dc = facts["shift"]
    return _translated_with_shift(grid, _signed_nonzero(dr, 1), _signed_nonzero(dc, 1))


def _rival_always_up_left(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    dr, dc = facts["shift"]
    return _translated_with_shift(grid, _signed_nonzero(dr, -1), _signed_nonzero(dc, -1))



def _rival_observed_diagonals_only(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    if facts["relation"] not in {"down_right", "up_left", "down_left"}:
        return full_grid(int(facts["height"]), int(facts["width"]), 0)
    dr, dc = facts["shift"]
    return _translated_with_shift(grid, dr, dc)


def _rival_filled_destination_bbox(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    marker_r, marker_c = facts["marker"]
    bbox_h, bbox_w = facts["bbox_dims"]
    output = full_grid(int(facts["height"]), int(facts["width"]), 0)
    for r in range(marker_r, marker_r + bbox_h):
        for c in range(marker_c, marker_c + bbox_w):
            if 0 <= r < len(output) and 0 <= c < len(output[0]):
                output[r][c] = 5
    return output


def _rival_first_four_cells_only(grid) -> list[list[int]]:
    facts = _scene_facts(grid)
    dr, dc = facts["shift"]
    return _translated_with_shift(grid, dr, dc, limit=4)


def _relation_witness(expected: str):
    return lambda grid: not self_check(grid) and _scene_facts(grid)["relation"] == expected


def _witness_hollow_bbox_anchor(grid) -> bool:
    return not self_check(grid) and not bool(_scene_facts(grid)["anchor_occupied"])


def _witness_axis_aligned(grid) -> bool:
    if self_check(grid):
        return False
    dr, dc = _scene_facts(grid)["shift"]
    return (dr == 0) ^ (dc == 0)


def _witness_concave_blob(grid) -> bool:
    if self_check(grid):
        return False
    facts = _scene_facts(grid)
    bbox_h, bbox_w = facts["bbox_dims"]
    return len(facts["blob_cells"]) < bbox_h * bbox_w


def _witness_large_blob(grid) -> bool:
    return not self_check(grid) and len(_scene_facts(grid)["blob_cells"]) > 4


SEMANTIC_WITNESSES = {
    **{f"relation_{name}": _relation_witness(name) for name in RELATIONS},
    "hollow_bbox_anchor": _witness_hollow_bbox_anchor,
    "axis_aligned_translation": _witness_axis_aligned,
    "concave_shape_preserved": _witness_concave_blob,
    "more_than_four_cells_preserved": _witness_large_blob,
}

SEMANTIC_RIVALS = {
    "first_blob_cell_anchor": _rival_first_blob_cell_anchor,
    "diagonal_only": _rival_diagonal_only,
    "always_down_right": _rival_always_down_right,
    "always_up_left": _rival_always_up_left,
    "observed_diagonals_only": _rival_observed_diagonals_only,
    "filled_destination_bbox": _rival_filled_destination_bbox,
    "first_four_cells_only": _rival_first_four_cells_only,
}

WITNESS_RIVALS = {
    "relation_down_right": ["always_up_left"],
    "relation_up_left": ["always_down_right"],
    "relation_down_left": ["always_down_right"],
    "relation_up_right": ["observed_diagonals_only"],
    "relation_row_left": ["always_down_right"],
    "relation_row_right": ["always_up_left"],
    "relation_column_up": ["always_down_right"],
    "relation_column_down": ["always_up_left"],
    "hollow_bbox_anchor": ["first_blob_cell_anchor"],
    "axis_aligned_translation": ["diagonal_only"],
    "concave_shape_preserved": ["filled_destination_bbox"],
    "more_than_four_cells_preserved": ["first_four_cells_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every public move is diagonal, and the public set omits the up-right
    # quadrant.  Generated axis-aligned and up-right profiles must refute both.
    "diagonal_only": _rival_diagonal_only,
    "observed_diagonals_only": _rival_observed_diagonals_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a full profile cycle that refutes every named competitor."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    profiles: set[str] = set()
    valid_demos: list[dict] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match bbox-origin translation")
        profile = _profile_of(demo["input"])
        if profile is None:
            reasons.append(f"demo {index} has no declared profile")
        else:
            profiles.add(profile)
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])

    missing = sorted(set(PROFILE_NAMES) - profiles)
    if missing:
        reasons.append(f"demonstrations omit scene profiles: {missing}")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in valid_demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} matches every demo but answers the query differently"
            )
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    band = _band(difficulty)
    offset = {"easy": 0, "medium": 3, "hard": 5}[band]
    return PROFILE_NAMES[(int(seed) + int(sample_index) + offset) % len(PROFILE_NAMES)]


def _relation_matches(relation: str, dr: int, dc: int) -> bool:
    return _relation(dr, dc) == relation


@lru_cache(maxsize=None)
def _placements(
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    relation: str,
) -> list[tuple[int, int, int, int]]:
    """All source-bbox/destination-bbox origins satisfying one profile."""
    bbox_h, bbox_w = _shape_dims(shape)
    placements: list[tuple[int, int, int, int]] = []
    for source_r in range(height - bbox_h + 1):
        for source_c in range(width - bbox_w + 1):
            for marker_r in range(height - bbox_h + 1):
                for marker_c in range(width - bbox_w + 1):
                    dr, dc = marker_r - source_r, marker_c - source_c
                    if not _relation_matches(relation, dr, dc):
                        continue
                    # Keep source and destination bboxes disjoint so the move
                    # is unmistakable and source erasure remains observable.
                    row_disjoint = source_r + bbox_h <= marker_r or marker_r + bbox_h <= source_r
                    col_disjoint = source_c + bbox_w <= marker_c or marker_c + bbox_w <= source_c
                    if not (row_disjoint or col_disjoint):
                        continue
                    placements.append((source_r, source_c, marker_r, marker_c))
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    _band(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    spec = _PROFILE_SPECS[profile]
    height, width = spec["dims"]
    shape = _SHAPES[str(spec["shape"])]
    relation = str(spec["relation"])
    choices = _placements(int(height), int(width), shape, relation)
    if not choices:
        raise RuntimeError(f"profile {profile!r} has no lawful placements")
    source_r, source_c, marker_r, marker_c = ctx.draw_rng(f"layout:{profile}").choice(choices)

    grid = full_grid(int(height), int(width), 0)
    for dr, dc in shape:
        grid[source_r + dr][source_c + dc] = 5
    grid[marker_r][marker_c] = 2

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal invalid scene for {profile}: {errors}")
    if _profile_of(grid) != profile:
        raise AssertionError(f"profile observation mismatch for {profile}")
    return grid
