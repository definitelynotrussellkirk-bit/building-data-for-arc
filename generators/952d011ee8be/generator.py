"""Generator for ``Fill Chambers by Legend Dot Count``.

A three-color legend appears in row 0.  Color-5 walls partition the body
(starting at row 2) into rectangular chambers.  A chamber with 1, 2, or 3
blue dots is filled with legend entry 1, 2, or 3; a chamber with no dots uses
the final legend entry.  The authoritative rule paints the *entire* chamber,
including the blue dots.

The production sampler uses two horizontal bands with independently partitioned
columns.  Every generated input contains four chambers whose dot counts are a
permutation of 0, 1, 2, 3, so every individual example exercises the full
lookup table while varied legend offsets and count orders defeat positional
shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import permutations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "952d011ee8be"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0b4a544c9655"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Three distinct legend colors occupy three consecutive cells in row 0. "
    "Rows below a blank separator contain color-5 walls forming rectangular "
    "chambers. Count color-1 dots in each chamber: counts 1, 2, and 3 select "
    "the corresponding legend entry, while count 0 selects the last entry. "
    "Flood-fill the whole chamber, replacing dots as well as background. "
    "Generated scenes vary grid size, legend position/order, horizontal band "
    "split, chamber partition, and the row-major permutation of counts 0..3."
)

INVARIANTS = [
    "row 0 contains exactly three consecutive distinct legend colors",
    "row 1 is blank; row 2, one interior row, and the last row are full color-5 walls",
    "outer side walls and band-local separators partition the body into four rectangles",
    "the four generated chambers carry dot counts 0, 1, 2, and 3 exactly once",
    "legend, walls, dots, and background use disjoint roles",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 11..15", "valid": "11..15"},
    "grid_w": {"type": "int", "default": "scheduled 10..16", "valid": "10..16"},
    "legend_offset": {"type": "int", "default": "scheduled 0..2", "valid": "0..2"},
    "upper_chambers": {"type": "int", "default": "scheduled 1..3", "valid": "1..3"},
    "split_offset": {"type": "int", "default": "scheduled 0..2", "valid": "0..2"},
    "legend_order": {"type": "int", "default": "scheduled permutation 0..5", "valid": "0..5"},
    "count_order": {"type": "int", "default": "scheduled permutation 0..23", "valid": "0..23"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_COLOR_SHIFT = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_LEGEND_COLORS = (2, 3, 4, 6, 7, 8, 9)
_LEGEND_PERMUTATIONS = tuple(permutations(range(3)))
_COUNT_PERMUTATIONS = tuple(permutations(range(4)))

# Twelve profiles give every 20-draw probe several literal canonical-size
# anchors while retaining broad dimensions.  Semantic axes use coprime block
# rotations rather than one shared slot: every exact override remains
# independently represented in default draws, while every four-pair lesson
# still includes shifted legends and nontrivial count orders.
_DIMENSION_SCHEDULE = (
    (11, 10), (12, 12), (11, 11), (12, 11),
    (13, 14), (14, 15), (15, 16), (13, 10),
    (14, 12), (15, 14), (12, 16), (11, 15),
)
_LEGEND_ORDERS = (0, 1, 4, 5)
_COUNT_ORDERS = (0, 7, 14, 23)


def schedule_profile(seed: int, sample_index: int | None = None) -> dict[str, int]:
    """Return the deterministic curriculum profile expected by checker hooks.

    The one-argument form is retained for local callers; the checker supplies
    ``(seed, sample_index)``.  Profiles intentionally depend only on index so
    lesson windows are reproducible across seed probes.
    """
    index = int(seed if sample_index is None else sample_index)
    grid_h, grid_w = _DIMENSION_SCHEDULE[index % len(_DIMENSION_SCHEDULE)]
    legend_slot = index % 4
    count_slot = (index // 4 + legend_slot) % 4
    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "legend_offset": index % 3,
        "upper_chambers": 1 + (((index // 9) + (index % 3) + ((index // 3) % 3)) % 3),
        "split_offset": (index // 3) % 3,
        "legend_order": _LEGEND_ORDERS[legend_slot],
        "count_order": _COUNT_ORDERS[count_slot],
    }


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")


def _effective_overrides(sample_index: int, overrides: dict) -> dict:
    effective = schedule_profile(sample_index)
    effective.update({name: value for name, value in overrides.items() if value is not None})
    return effective


def _composition(total: int, parts: int, rng) -> list[int]:
    """Random positive composition with at least two cells per chamber."""
    minimum = 2 * parts
    if total < minimum:
        raise ValueError(f"cannot split {total} cells into {parts} width>=2 chambers")
    widths = [2] * parts
    for _ in range(total - minimum):
        widths[rng.randrange(parts)] += 1
    rng.shuffle(widths)
    return widths


def _put_band(
    grid: list[list[int]],
    row_lo: int,
    row_hi: int,
    widths: Iterable[int],
) -> list[list[tuple[int, int]]]:
    chambers: list[list[tuple[int, int]]] = []
    col = 1
    widths = list(widths)
    for index, width in enumerate(widths):
        cells = [
            (row, c)
            for row in range(row_lo, row_hi + 1)
            for c in range(col, col + width)
        ]
        chambers.append(cells)
        col += width
        if index + 1 < len(widths):
            for row in range(row_lo, row_hi + 1):
                grid[row][col] = 5
            col += 1
    if col != len(grid[0]) - 1:
        raise RuntimeError("band partition did not terminate at the right outer wall")
    return chambers


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; canonical Racket owns the label."""
    _validate_request(difficulty, overrides)
    effective = _effective_overrides(int(sample_index), overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h = ctx.draw_int_strict("grid_h", 11, 15)
    w = ctx.draw_int_strict("grid_w", 10, 16)
    legend_offset = ctx.draw_int_strict("legend_offset", 0, 2)
    upper_chambers = ctx.draw_int_strict("upper_chambers", 1, 3)
    split_offset = ctx.draw_int_strict("split_offset", 0, 2)
    legend_order = ctx.draw_int_strict("legend_order", 0, 5)
    count_order = ctx.draw_int_strict("count_order", 0, 23)

    grid = full_grid(h, w, 0)

    # Exact canonical palette/shape anchor at every twelfth sample.  Difficulty
    # rotates color roles through the seven legal legend colors, keeping the
    # grammar and exact axes fixed while ensuring the advertised bands are not
    # byte-identical aliases.
    if int(sample_index) % len(_DIMENSION_SCHEDULE) == 0:
        palette_indices = [0, 2, 3]  # colors 2, 4, 6 before band rotation
    else:
        palette_indices = sorted(ctx.draw_rng("legend_palette").sample(range(len(_LEGEND_COLORS)), 3))
    shift = _DIFFICULTY_COLOR_SHIFT[difficulty]
    palette = sorted(_LEGEND_COLORS[(index + shift) % len(_LEGEND_COLORS)] for index in palette_indices)
    perm = _LEGEND_PERMUTATIONS[legend_order]
    legend = [palette[index] for index in perm]
    for index, color in enumerate(legend):
        grid[0][legend_offset + index] = color

    split_row = 5 + split_offset
    for col in range(w):
        grid[2][col] = 5
        grid[split_row][col] = 5
        grid[h - 1][col] = 5
    for row in range(2, h):
        grid[row][0] = 5
        grid[row][w - 1] = 5

    lower_chambers = 4 - upper_chambers
    usable_cols = w - 2
    upper_widths = _composition(
        usable_cols - (upper_chambers - 1),
        upper_chambers,
        ctx.draw_rng("upper_partition"),
    )
    lower_widths = _composition(
        usable_cols - (lower_chambers - 1),
        lower_chambers,
        ctx.draw_rng("lower_partition"),
    )
    chambers = _put_band(grid, 3, split_row - 1, upper_widths)
    chambers.extend(_put_band(grid, split_row + 1, h - 2, lower_widths))
    if len(chambers) != 4:
        raise RuntimeError("production construction must create exactly four chambers")

    counts = _COUNT_PERMUTATIONS[count_order]
    for chamber_index, (cells, dot_count) in enumerate(zip(chambers, counts)):
        slots = ctx.draw_rng(f"dots:{chamber_index}").sample(cells, dot_count)
        for row, col in slots:
            grid[row][col] = 1
    return grid


def _components_open(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(2, h)
        for col in range(w)
        if grid[row][col] != 5
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        cells: list[tuple[int, int]] = []
        for row, col in queue:
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: (min(cells), max(cells)))


def analyze(grid) -> dict:
    errors: list[str] = []
    facts = {
        "errors": errors,
        "legend": [],
        "legend_offset": None,
        "components": [],
        "full_wall_rows": [],
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("expected a nonempty rectangular grid")
        return facts
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("expected a nonempty rectangular grid")
        return facts
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("ragged grid")
        return facts
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer colors 0..9")
        return facts

    h, w = len(grid), width
    if not 11 <= h <= 15 or not 10 <= w <= 16:
        errors.append(f"grid dimensions {h}x{w} outside 11..15 by 10..16")

    legend_cells = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if len(legend_cells) != 3:
        errors.append(f"row 0 must contain exactly three legend cells, found {len(legend_cells)}")
    else:
        cols = [col for col, _ in legend_cells]
        legend = [value for _, value in legend_cells]
        facts["legend"] = legend
        facts["legend_offset"] = cols[0]
        if cols != list(range(cols[0], cols[0] + 3)):
            errors.append("legend cells must be consecutive")
        if cols[0] not in (0, 1, 2):
            errors.append("legend offset must be 0, 1, or 2")
        if len(set(legend)) != 3:
            errors.append("legend colors must be distinct")
        if any(value not in _LEGEND_COLORS for value in legend):
            errors.append("legend colors must avoid background, dot, and wall roles")

    if h >= 2 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be blank")
    allowed_body = {0, 1, 5}
    if any(value not in allowed_body for row in grid[2:] for value in row):
        errors.append("body may contain only background 0, dots 1, and walls 5")

    if h >= 3:
        full_wall_rows = [
            row for row in range(2, h) if all(value == 5 for value in grid[row])
        ]
        facts["full_wall_rows"] = full_wall_rows
        if len(full_wall_rows) != 3 or full_wall_rows[0] != 2 or full_wall_rows[-1] != h - 1:
            errors.append("body must have exactly three full wall rows: row 2, one interior, and last")
        if any(grid[row][0] != 5 or grid[row][w - 1] != 5 for row in range(2, h)):
            errors.append("body must have full outer side walls")

    if errors:
        return facts

    components = []
    for cells in _components_open([list(row) for row in grid]):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        expected = {
            (row, col)
            for row in range(bbox[0], bbox[2] + 1)
            for col in range(bbox[1], bbox[3] + 1)
        }
        if set(cells) != expected:
            errors.append(f"open chamber at {bbox} is not a solid rectangle")
        dot_count = sum(grid[row][col] == 1 for row, col in cells)
        if not 0 <= dot_count <= 3:
            errors.append(f"chamber at {bbox} has unsupported dot count {dot_count}")
        components.append({"cells": cells, "bbox": bbox, "dot_count": dot_count})
    facts["components"] = components

    if len(components) not in (3, 4):
        errors.append(f"expected three or four chambers, found {len(components)}")
    distinct_counts = {component["dot_count"] for component in components}
    if not any(count > 0 for count in distinct_counts):
        errors.append("at least one chamber must contain dots")
    if len(distinct_counts) < 2:
        errors.append("chambers must exhibit at least two distinct dot counts")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    facts = analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    requested = (meta or {}).get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"override observation failed: {exc}")
        else:
            for name, value in requested.items():
                if name in observed and value is not None and observed[name] != value:
                    errors.append(f"override {name} requested {value}, observed {observed[name]}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the selected authority's rectangular-chamber grammar."""
    return self_check(grid)


def _legend_rank_order(legend: list[int]) -> int:
    sorted_values = sorted(legend)
    rank = {value: index for index, value in enumerate(sorted_values)}
    signature = tuple(rank[value] for value in legend)
    try:
        return _LEGEND_PERMUTATIONS.index(signature)
    except ValueError as exc:  # pragma: no cover - protected by validation
        raise ValueError(f"unknown legend permutation {signature}") from exc


def observe_overrides(grid) -> dict[str, int]:
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError(facts["errors"][0])
    components = facts["components"]
    if len(components) != 4:
        raise ValueError("exact override observation requires four chambers")
    split_row = facts["full_wall_rows"][1]
    upper = sum(component["bbox"][2] < split_row for component in components)
    counts = tuple(component["dot_count"] for component in components)
    try:
        count_order = _COUNT_PERMUTATIONS.index(counts)
    except ValueError as exc:
        raise ValueError(f"dot counts are not a permutation of 0..3: {counts}") from exc
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "legend_offset": int(facts["legend_offset"]),
        "upper_chambers": upper,
        "split_offset": split_row - 5,
        "legend_order": _legend_rank_order(list(facts["legend"])),
        "count_order": count_order,
    }


def _apply_lookup(
    grid,
    *,
    legend: list[int] | None = None,
    zero_uses_first: bool = False,
    preserve_dots: bool = False,
    position_counts: bool = False,
):
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError(facts["errors"][0])
    actual_legend = list(facts["legend"] if legend is None else legend)
    if len(actual_legend) != 3:
        raise ValueError("lookup requires exactly three legend entries")
    out = deepcopy(grid)
    for index, component in enumerate(facts["components"]):
        dot_count = index if position_counts else component["dot_count"]
        if dot_count == 0:
            color = actual_legend[0] if zero_uses_first else actual_legend[-1]
        else:
            color = actual_legend[dot_count - 1]
        for row, col in component["cells"]:
            if preserve_dots and grid[row][col] == 1:
                continue
            out[row][col] = color
    return out


def rule_mirror(grid):
    """Independent Python mirror of the selected canonical Racket rule."""
    return _apply_lookup(grid)


def _legend_at_columns_0_2(grid):
    return _apply_lookup(grid, legend=list(grid[0][:3]))


def _zero_uses_first(grid):
    return _apply_lookup(grid, zero_uses_first=True)


def _leave_dots_blue(grid):
    return _apply_lookup(grid, preserve_dots=True)


def _chamber_position_lookup(grid):
    return _apply_lookup(grid, position_counts=True)


def _shifted_legend(grid) -> bool:
    return observe_overrides(grid)["legend_offset"] > 0


def _has_zero_dot_chamber(grid) -> bool:
    return any(component["dot_count"] == 0 for component in analyze(grid)["components"])


def _has_painted_dot(grid) -> bool:
    return any(component["dot_count"] > 0 for component in analyze(grid)["components"])


def _permuted_chamber_counts(grid) -> bool:
    return observe_overrides(grid)["count_order"] != 0


SEMANTIC_RIVALS = {
    "legend_at_columns_0_2": _legend_at_columns_0_2,
    "zero_uses_first": _zero_uses_first,
    "leave_dots_blue": _leave_dots_blue,
    "chamber_position_lookup": _chamber_position_lookup,
}
SEMANTIC_WITNESSES = {
    "shifted_legend": _shifted_legend,
    "zero_dot_uses_last": _has_zero_dot_chamber,
    "dots_are_overwritten": _has_painted_dot,
    "count_not_position": _permuted_chamber_counts,
}
WITNESS_RIVALS = {
    "shifted_legend": ["legend_at_columns_0_2"],
    "zero_dot_uses_last": ["zero_uses_first"],
    "dots_are_overwritten": ["leave_dots_blue"],
    "count_not_position": ["chamber_position_lookup"],
}
CANONICAL_SHORTCUTS = {"legend_at_columns_0_2": _legend_at_columns_0_2}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} is outside the grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the chamber-count rule")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} survives every demonstration and changes the query")
    return sorted(set(reasons))


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    base = generate(991, 0, difficulty="easy")
    facts = analyze(base)

    broken_wall = deepcopy(base)
    split_row = facts["full_wall_rows"][1]
    broken_wall[split_row][len(base[0]) // 2] = 0

    duplicate_header = deepcopy(base)
    duplicate_header[1] = duplicate_header[0][:]

    four_dots = deepcopy(base)
    zero = next(component for component in facts["components"] if component["dot_count"] == 0)
    for row, col in zero["cells"][:4]:
        four_dots[row][col] = 1

    return [
        ("broken_interior_wall", broken_wall),
        ("duplicate_legend_row", duplicate_header),
        ("four_dot_chamber", four_dots),
    ]
