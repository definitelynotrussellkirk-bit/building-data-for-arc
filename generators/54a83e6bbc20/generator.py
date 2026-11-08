"""Generator for ARC task 18447a8d: match complementary jigsaw pieces.

Each three-row band contains one cyan(8) left piece and one colored right
piece.  Across the whole grid the right pieces are permuted.  A right piece
belongs with the unique cyan piece whose shape complements it to a solid 3x5
rectangle.  The completed rectangles are drawn at column 0 in cyan plus the
matched color, preserving the cyan pieces' top-to-bottom order.

The distribution mixes equal-area pieces, one-row near-collisions, and mixed
areas across all 64 three-row cut vectors. Equal area defeats size matching;
near-collisions make each row necessary rather than inferable from a fixed sum.
Scenes with a tied rectangle-width mode in the unchanged authority are rejected.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from functools import lru_cache
from itertools import combinations, permutations, product
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "54a83e6bbc20"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "82f172ba82d3"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "On a 7 background, match each cyan(8) left jigsaw piece with the unique "
    "colored right piece that completes a solid 3x5 rectangle. Right pieces "
    "are permuted across 2-4 bands, with equal-area and row-critical shapes; "
    "redraw each completed rectangle at column 0."
)

INVARIANTS = [
    "the canvas is 11 columns wide with 2-4 three-row bands separated by full background-7 rows",
    "every band contains one connected cyan(8) left piece and one connected, uniquely colored right piece",
    "each cyan piece and exactly one colored piece form a solid 3x5 rectangle after translation",
    "the shape-complement relation is a unique bijection across all bands",
    "cyan row cuts are in 1..4; right pieces are contiguous suffixes and left pieces contiguous prefixes",
    "shape profiles mix equal-area, row-collision, and other mixed-area sets",
    "width 5 is the unique mode of first rectangular placements in the selected authority",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLORS = (1, 2, 3, 4, 5, 6, 9)
_RECT_H = 3
_RECT_W = 5
_CANVAS_W = 11
_RIGHT_EDGE = _CANVAS_W - 1

# All canonical row-prefix cuts. Equal-area scenes still occupy one area bucket,
# but that bucket varies; near-collision scenes differ in exactly one row.
_CUT_BANK = tuple(product(range(1, 5), repeat=3))
_CUTS_BY_AREA = {
    area: tuple(cut for cut in _CUT_BANK if sum(cut) == area)
    for area in range(3, 13)
}
SHAPE_PROFILES = ("equal_area", "row_collision", "mixed_area")
# Variety slots use period 7, coprime with the 2/6/24 permutation cycles.
# With the two anchor slots, asymptotic shape weights are 3/7, 3/7, 1/7.
_SHAPE_SCHEDULE = (
    "equal_area", "row_collision", "mixed_area", "equal_area",
    "mixed_area", "row_collision", "mixed_area",
)

# Candidate order lists which cyan pair occupies each right-side vertical slot.
_PROFILE_ROWS = (
    ("pairs2_identity", "easy", (0, 1)),
    ("pairs2_swap", "easy", (1, 0)),
    ("pairs3_identity", "medium", (0, 1, 2)),
    ("pairs3_rotate", "medium", (1, 2, 0)),
    ("pairs3_reverse", "medium", (2, 1, 0)),
    ("pairs4_identity", "hard", (0, 1, 2, 3)),
    ("pairs4_rotate_left", "hard", (1, 2, 3, 0)),
    ("pairs4_rotate_right", "hard", (3, 0, 1, 2)),
    ("pairs4_reverse", "hard", (3, 2, 1, 0)),
    ("pairs4_woven", "hard", (2, 0, 3, 1)),
)
# Keep all original override names; add the previously absent permutations.
_PROFILE_ROWS += tuple(
    (f"pairs{n}_perm_{''.join(map(str, order))}", band, order)
    for n, band in ((2, "easy"), (3, "medium"), (4, "hard"))
    for order in permutations(range(n))
    if order not in {row[2] for row in _PROFILE_ROWS}
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {name: (band, order) for name, band, order in _PROFILE_ROWS}
_PROFILE_BY_ORDER = {tuple(order): name for name, _band, order in _PROFILE_ROWS}
_PROFILES_BY_BAND = {
    band: tuple(name for name, row_band, _order in _PROFILE_ROWS if row_band == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic curriculum within the selected difficulty band",
        "valid": 'pairs2_identity|pairs2_swap|pairs3_identity|pairs3_rotate|pairs3_reverse|pairs4_identity|pairs4_rotate_left|pairs4_rotate_right|pairs4_reverse|pairs4_woven|pairs3_perm_021|pairs3_perm_102|pairs3_perm_201|pairs4_perm_0132|pairs4_perm_0213|pairs4_perm_0231|pairs4_perm_0312|pairs4_perm_0321|pairs4_perm_1023|pairs4_perm_1032|pairs4_perm_1203|pairs4_perm_1302|pairs4_perm_1320|pairs4_perm_2013|pairs4_perm_2103|pairs4_perm_2130|pairs4_perm_2301|pairs4_perm_2310|pairs4_perm_3021|pairs4_perm_3102|pairs4_perm_3120|pairs4_perm_3201',
        "doc": "Exact pair count and right-piece permutation, recoverable from the returned grid.",
        "probe": "manual",
        "probe_evidence": "tests/test_distribution_54a83e6bbc20.py::test_shape_axis_round_trips_and_is_validated (all 32 x 3 combinations)",
        "probe_reason": "The shared automatic enum matrix is capped at 16 values; all 32 exact values are tested task-locally.",
    },
    "shape_profile": {
        "type": "str",
        "default": "three-slot anchors plus variety: 3/7 equal area, 3/7 row collision, 1/7 mixed",
        "valid": "equal_area|row_collision|mixed_area",
        "doc": "Observable geometry class; near-collisions require inspecting the differing row.",
    }
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Two identifying anchors plus one varied scene in every three draws.

    At a fixed seed/band, every consecutive three-demo window contains an
    equal-area permutation and a row-critical reverse permutation. The third
    slot ranges over *all* permutations. This is a finite-rival guarantee, not
    a claim that three examples identify the rule among every possible program.
    """
    del seed
    band = _band(difficulty)
    count = {"easy": 2, "medium": 3, "hard": 4}[band]
    index = int(sample_index)
    if index % 3 == 0:
        return {2: "pairs2_swap", 3: "pairs3_rotate", 4: "pairs4_rotate_left"}[count]
    if index % 3 == 1:
        return {2: "pairs2_swap", 3: "pairs3_reverse", 4: "pairs4_reverse"}[count]
    profiles = _PROFILES_BY_BAND[band]
    return profiles[(index // 3) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
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


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _normalize(cells: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    if not cells:
        return set()
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return {(row - top, col - left) for row, col in cells}


def _placement(
    left_cells: Sequence[tuple[int, int]],
    candidate_cells: Sequence[tuple[int, int]],
) -> tuple[int, int] | None:
    """Return the unique candidate shift that fills a 3x5 rectangle, if any."""
    left = _normalize(left_cells)
    candidate = _normalize(candidate_cells)
    target = {(row, col) for row in range(_RECT_H) for col in range(_RECT_W)}
    missing = target - left
    if not left <= target or not missing or not candidate:
        return None
    # The missing cells have only one possible translated bounding-box origin.
    # Comparing normalized sets replaces 77 trial translations without changing
    # the exact-complement contract (regression: all 4096 cut-vector pairs).
    dr = min(row for row, _col in missing)
    dc = min(col for _row, col in missing)
    return (dr, dc) if _normalize(missing) == candidate else None


@lru_cache(maxsize=4096)
def _first_rectangle_width(left_cut: tuple[int, ...], right_cut: tuple[int, ...]) -> int | None:
    """First rectangular placement in the unchanged Racket search order.

    This guard is about the authority's width vote, not the matching key.
    Negative shifts cannot leave bbox origin at zero. The first nonnegative
    dr/dc whose disjoint union has bounding-box area equal to its cardinality
    therefore agrees with the authority's full -5.. search on these shapes.
    """
    left = _cuts_to_left(left_cut)
    right = _normalize(_cuts_to_candidate(right_cut))
    area = len(left) + len(right)
    left_width = max(left_cut)
    right_width = _RECT_W - min(right_cut)
    for dr in range(6):
        for dc in range(8):
            width = max(left_width, dc + right_width)
            if (_RECT_H + dr) * width != area:
                continue
            if left.isdisjoint((r + dr, c + dc) for r, c in right):
                return width
    return None


def _width_mode_is_safe(cuts: Sequence[tuple[int, ...]]) -> bool:
    counts = Counter(
        width for a in cuts for b in cuts
        if (width := _first_rectangle_width(a, b)) is not None
    )
    # Do not depend on mode-list's unspecified tie ordering. Each diagonal
    # contributes a width-five placement and all other widths must lose.
    return counts[_RECT_W] == len(cuts) and all(
        count < counts[_RECT_W] for width, count in counts.items() if width != _RECT_W
    )


def _shape_profile(cuts: Sequence[tuple[int, ...]]) -> str:
    if len({sum(cut) for cut in cuts}) == 1:
        return "equal_area"
    if any(sum(x != y for x, y in zip(a, b)) == 1 for a, b in combinations(cuts, 2)):
        return "row_collision"
    return "mixed_area"


def _draw_cuts(rng, count: int, profile: str, *, critical_rows: Sequence[int], anchor: bool) -> list[tuple[int, ...]]:
    """Bounded construction; failures are explicit, never a silent fallback."""
    for _attempt in range(128):
        if profile == "equal_area":
            areas = [area for area, bank in _CUTS_BY_AREA.items() if len(bank) >= count]
            cuts = rng.sample(_CUTS_BY_AREA[rng.choice(areas)], count)
        elif profile == "row_collision":
            base = rng.choice(_CUT_BANK)
            cuts = [base]
            for row in critical_rows:
                neighbor = list(base)
                neighbor[row] = rng.choice([n for n in range(1, 5) if n != base[row]])
                cuts.append(tuple(neighbor))
            if not anchor:
                rng.shuffle(cuts)
        else:
            cuts = rng.sample(_CUT_BANK, count)
        if _shape_profile(cuts) == profile and _width_mode_is_safe(cuts):
            return cuts
    raise RuntimeError(f"could not construct a safe {count}-piece {profile} scene in 128 attempts")


def _component(cells: set[tuple[int, int]]) -> bool:
    return bool(cells) and _connected(cells)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if width != _CANVAS_W:
        errors.append(f"expected width {_CANVAS_W}, found {width}")
    if height not in (9, 13, 17):
        errors.append(f"expected height 9, 13, or 17, found {height}")
    if errors:
        return {"errors": errors, "height": height, "width": width}

    pair_count = (height - 1) // 4
    lefts: list[set[tuple[int, int]]] = []
    candidates: list[dict[str, Any]] = []
    colors: set[int] = set()

    for separator in range(0, height, 4):
        if any(value != 7 for value in grid[separator]):
            errors.append(f"separator row {separator} must be all background 7")

    for band_index in range(pair_count):
        top = 1 + 4 * band_index
        band_rows = range(top, top + _RECT_H)
        if any(grid[row][5] != 7 or grid[row][6] != 7 for row in band_rows):
            errors.append(f"band {band_index} must keep columns 5 and 6 as background")

        left = {
            (row - top, col)
            for row in band_rows
            for col in range(0, _RECT_W)
            if grid[row][col] == 8
        }
        unexpected_left = sorted({
            grid[row][col]
            for row in band_rows
            for col in range(0, 7)
            if grid[row][col] not in (7, 8)
        })
        if unexpected_left:
            errors.append(f"band {band_index} has non-cyan colors on the left: {unexpected_left}")
        if not _component(left):
            errors.append(f"band {band_index} cyan piece must be one connected object")
        elif any(not any((row, col) in left for col in range(_RECT_W)) for row in range(_RECT_H)):
            errors.append(f"band {band_index} cyan piece must occupy all three rows")
        elif any((row, 0) not in left for row in range(_RECT_H)):
            errors.append(f"band {band_index} cyan piece must include the full left edge")
        if left and any(
            {col for r, col in left if r == row} != set(range(sum(r == row for r, _ in left)))
            for row in range(_RECT_H)
        ):
            errors.append(f"band {band_index} cyan rows must be contiguous prefixes")
        lefts.append(left)

        right_values = {
            grid[row][col]
            for row in band_rows
            for col in range(7, _CANVAS_W)
            if grid[row][col] != 7
        }
        if len(right_values) != 1:
            errors.append(
                f"band {band_index} must contain exactly one right-piece color, found {sorted(right_values)}"
            )
            candidates.append({"color": None, "cells": set(), "slot": band_index})
            continue
        color = next(iter(right_values))
        if color in (7, 8):
            errors.append(f"band {band_index} right-piece color must differ from 7 and 8")
        if color in colors:
            errors.append(f"right-piece color {color} is reused; colors must identify distinct objects")
        colors.add(color)
        cells = {
            (row - top, col)
            for row in band_rows
            for col in range(7, _CANVAS_W)
            if grid[row][col] == color
        }
        if not _component(cells):
            errors.append(f"band {band_index} colored piece must be one connected object")
        elif any(not any((row, col) in cells for col in range(7, _CANVAS_W)) for row in range(_RECT_H)):
            errors.append(f"band {band_index} colored piece must occupy all three rows")
        elif any((row, _RIGHT_EDGE) not in cells for row in range(_RECT_H)):
            errors.append(f"band {band_index} colored piece must include the full right edge")
        if cells and any(
            {col for r, col in cells if r == row} != set(range(_CANVAS_W - sum(r == row for r, _ in cells), _CANVAS_W))
            for row in range(_RECT_H)
        ):
            errors.append(f"band {band_index} colored rows must be contiguous suffixes")
        candidates.append({"color": color, "cells": cells, "slot": band_index})

    extra_values = sorted({value for row in grid for value in row if value not in colors | {7, 8}})
    if extra_values:
        errors.append(f"unexpected colors outside the band grammar: {extra_values}")

    compatibility: list[list[int]] = []
    for left in lefts:
        matches = [
            index
            for index, candidate in enumerate(candidates)
            if candidate["cells"] and _placement(left, candidate["cells"]) is not None
        ]
        compatibility.append(matches)
    if any(len(matches) != 1 for matches in compatibility):
        errors.append(f"each cyan piece must have exactly one shape-complement match: {compatibility}")
    matched = [matches[0] for matches in compatibility if len(matches) == 1]
    if len(matched) == pair_count and len(set(matched)) != pair_count:
        errors.append(f"shape-complement matches must form a bijection, found {matched}")

    cuts = [tuple(sum(r == row for r, _col in left) for row in range(_RECT_H)) for left in lefts]
    if not errors and not _width_mode_is_safe(cuts):
        errors.append("width 5 is not the unique rectangle-width mode of the selected Racket authority")

    candidate_order: tuple[int, ...] | None = None
    if not errors:
        inverse = {candidate_slot: left_index for left_index, candidate_slot in enumerate(matched)}
        candidate_order = tuple(inverse[slot] for slot in range(pair_count))

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "pair_count": pair_count,
        "lefts": lefts,
        "candidates": candidates,
        "matches": matched,
        "candidate_order": candidate_order,
        "scene_profile": _PROFILE_BY_ORDER.get(candidate_order),
        "shape_profile": _shape_profile(cuts) if not errors else None,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical input grammar and reject malformed/ambiguous scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact scene profile from shape matching in the input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"], "shape_profile": analysis["shape_profile"]}


def _cuts_to_left(cuts: Sequence[int]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, length in enumerate(cuts)
        for col in range(length)
    }


def _cuts_to_candidate(cuts: Sequence[int]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, length in enumerate(cuts)
        for col in range(length, _RECT_W)
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    requested_shape = overrides.get("shape_profile")
    if requested_shape is not None and requested_shape not in SHAPE_PROFILES:
        raise ValueError(f"unknown shape_profile: {requested_shape!r}")
    slot = int(sample_index) % 3
    default_shape = ("equal_area" if slot == 0 else "row_collision" if slot == 1 else
                     _SHAPE_SCHEDULE[(int(sample_index) // 3 + int(seed)) % len(_SHAPE_SCHEDULE)])
    scheduled_shape = requested_shape or default_shape

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    _profile_band, candidate_order = _PROFILE_BY_NAME[profile]
    pair_count = len(candidate_order)

    shape_rng = ctx.draw_rng("shape_selection")
    shape_profile = ctx.draw_choice("shape_profile", [scheduled_shape])
    # Stable for an entire seed, deliberately independent of sample_index.
    # Only these rows can create one-row collisions for this seed/band; the
    # reverse anchor exhibits every one of them. Other rows cannot generate
    # a new query-changing partial-row rival absent from the anchor.
    row_rng = stable_rng(int(seed), "54a83e6bbc20:critical-rows", version=VERSION)
    critical_rows = row_rng.sample(range(_RECT_H), pair_count - 1)
    cut_vectors = _draw_cuts(shape_rng, pair_count, shape_profile,
                             critical_rows=critical_rows, anchor=slot == 1)

    color_rng = ctx.draw_rng("color_assignment")
    colors = list(_COLORS)
    color_rng.shuffle(colors)
    colors = colors[:pair_count]
    # Ensure a sorted-color competitor is wrong on every generated scene.
    if colors == sorted(colors):
        colors.reverse()

    height = 4 * pair_count + 1
    grid = full_grid(height, _CANVAS_W, 7)

    # Left cyan pieces remain in canonical order.
    for pair_index, cuts in enumerate(cut_vectors):
        top = 1 + 4 * pair_index
        for row, col in _cuts_to_left(cuts):
            grid[top + row][col] = 8

    # Right colored pieces are permuted vertically and right-aligned.
    for slot, pair_index in enumerate(candidate_order):
        top = 1 + 4 * slot
        normalized = _normalize(_cuts_to_candidate(cut_vectors[pair_index]))
        piece_width = max(col for _row, col in normalized) + 1
        left_col = _CANVAS_W - piece_width
        for row, col in normalized:
            grid[top + row][left_col + col] = colors[pair_index]

    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror used only for semantic tests and rivals."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid jigsaw scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 7)
    for left_index, candidate_slot in enumerate(analysis["matches"]):
        top = 1 + 4 * left_index
        left = analysis["lefts"][left_index]
        candidate = analysis["candidates"][candidate_slot]
        shift = _placement(left, candidate["cells"])
        assert shift is not None
        dr, dc = shift
        for row, col in left:
            output[top + row][col] = 8
        for row, col in _normalize(candidate["cells"]):
            output[top + row + dr][col + dc] = candidate["color"]
    return output


def strict_canonical_like(grid) -> list[str]:
    """The task grammar is already canonical-exact; retain a named strict hook."""
    return self_check(grid)


def _paint_slot_assignment(grid, candidate_slots: Sequence[int]) -> list[list[int]]:
    """Paint candidates by a rival assignment, right-aligned inside each 3x5 box."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = full_grid(analysis["height"], analysis["width"], 7)
    for left_index, candidate_slot in enumerate(candidate_slots):
        top = 1 + 4 * left_index
        left = analysis["lefts"][left_index]
        candidate = analysis["candidates"][candidate_slot]
        normalized = _normalize(candidate["cells"])
        piece_width = max(col for _row, col in normalized) + 1
        dc = _RECT_W - piece_width
        for row, col in left:
            output[top + row][col] = 8
        for row, col in normalized:
            output[top + row][dc + col] = candidate["color"]
    return output


def _rival_same_input_row(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _paint_slot_assignment(grid, list(range(analysis["pair_count"])))


def _rival_sorted_colors(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    slots = sorted(
        range(analysis["pair_count"]),
        key=lambda slot: analysis["candidates"][slot]["color"],
    )
    return _paint_slot_assignment(grid, slots)


def _rival_area_first(grid):
    """Pair by complementary area only, taking the first unused candidate."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    unused = list(range(analysis["pair_count"]))
    assignment: list[int] = []
    for left in analysis["lefts"]:
        needed = _RECT_H * _RECT_W - len(left)
        chosen = next(
            (slot for slot in unused if len(analysis["candidates"][slot]["cells"]) == needed),
            unused[0],
        )
        assignment.append(chosen)
        unused.remove(chosen)
    return _paint_slot_assignment(grid, assignment)


def _rival_ignoring_row(grid, omitted: int):
    """Match on just two row lengths, resolve ties by input order, fill gaps."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    remaining = list(range(analysis["pair_count"]))
    output = full_grid(analysis["height"], analysis["width"], 7)
    for index, left in enumerate(analysis["lefts"]):
        cut = tuple(sum(r == row for r, _col in left) for row in range(_RECT_H))
        def agrees(slot):
            cells = analysis["candidates"][slot]["cells"]
            return all(cut[row] + sum(r == row for r, _col in cells) == _RECT_W
                       for row in range(_RECT_H) if row != omitted)
        slot = next((s for s in remaining if agrees(s)), remaining[0])
        remaining.remove(slot)
        color = analysis["candidates"][slot]["color"]
        for row, length in enumerate(cut):
            output[1 + 4 * index + row][:_RECT_W] = [8] * length + [color] * (_RECT_W - length)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "pair_by_input_row": _rival_same_input_row,
    "pair_by_sorted_color": _rival_sorted_colors,
    "pair_by_area_only": _rival_area_first,
    "ignore_row_0": lambda grid: _rival_ignoring_row(grid, 0),
    "ignore_row_1": lambda grid: _rival_ignoring_row(grid, 1),
    "ignore_row_2": lambda grid: _rival_ignoring_row(grid, 2),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _official_color_order(grid) -> tuple[int, ...]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return ()
    return tuple(
        analysis["candidates"][slot]["color"] for slot in analysis["matches"]
    )


def _input_color_order(grid) -> tuple[int, ...]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return ()
    return tuple(candidate["color"] for candidate in analysis["candidates"])


SEMANTIC_WITNESSES = {
    "right_pieces_are_permuted": lambda grid: _official_color_order(grid) != _input_color_order(grid),
    "color_order_is_not_the_rule": lambda grid: _official_color_order(grid) != tuple(sorted(_official_color_order(grid))),
    "equal_area_requires_shape_matching": lambda grid: (
        not _analysis(grid)["errors"]
        and len({len(left) for left in _analysis(grid)["lefts"]}) == 1
        and _rival_area_first(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "right_pieces_are_permuted": ["pair_by_input_row"],
    "color_order_is_not_the_rule": ["pair_by_sorted_color"],
    "equal_area_requires_shape_matching": ["pair_by_area_only"],
}

for _row in range(_RECT_H):
    _witness_name = f"row_{_row}_is_required"
    SEMANTIC_WITNESSES[_witness_name] = (
        lambda grid, row=_row: not _analysis(grid)["errors"]
        and _rival_ignoring_row(grid, row) != rule_mirror(grid)
    )
    WITNESS_RIVALS[_witness_name] = [f"ignore_row_{_row}"]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits every demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # pragma: no cover - defensive contract reporting
            reasons.append(f"demo {index} is outside the jigsaw grammar: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the shape-complement rule")
    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:  # pragma: no cover - defensive contract reporting
        reasons.append(f"query is outside the jigsaw grammar: {exc}")
    else:
        if query_expected != query["output"]:
            reasons.append("query disagrees with the shape-complement rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
