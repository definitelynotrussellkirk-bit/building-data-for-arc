"""Generator for ARC task a3325580 / content task 929a3e437ee4.

Rule: count every non-background color, keep all colors tied for the maximum
count, order those winners by their leftmost occupied column, and output one
solid vertical bar per winner.  The output height is the maximum count.

The teaching schedule deliberately includes unique maxima, two- and three-way
ties, ties with and without lower-count distractors, non-numeric winner order,
and several maximum counts.  Every color is one connected object, matching all
seven canonical train/test inputs.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "929a3e437ee4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # canonical grammar, semantic schedule, honest overrides
# sha256[:12] of whitespace-normalized canonical program_solution.
RULE_HASH = "7cfafaaa1f5f"

SUMMARY = (
    "Count non-zero colors, select every color tied for the maximum count, "
    "sort the selected colors by their leftmost input column, and emit a "
    "max-count-tall solid bar for each selected color. Generated colors are "
    "single connected objects; lower-count distractors and 1/2/3/4-way "
    "winner branches are all represented."
)

INVARIANTS = [
    "background is color 0 on a rectangular 8..14 by 8..14 grid",
    "2..5 distinct non-zero colors each form one 4-connected object",
    "each non-zero color occupies 2..9 cells and the maximum count is at least 3",
    "1..4 winner colors share the maximum count; other colors are strictly smaller",
    "winner colors have distinct leftmost columns, so their output order is unambiguous",
]

PALETTE_KINDS = ("warm", "cool", "primary", "broad")
SHAPE_STYLES = ("compact", "snaky", "mixed")
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.10

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted, canonical 10 favored",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted, canonical 10 favored",
        "valid": "8..14",
    },
    "palette_size": {
        "type": "int",
        "default": "five-slot lesson schedule",
        "valid": "2..5",
    },
    "n_winners": {
        "type": "int",
        "default": "five-slot lesson schedule",
        "valid": "1..4",
    },
    "max_count": {
        "type": "int",
        "default": "difficulty-aware five-slot schedule",
        "valid": "3..9",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_KINDS),
    },
    "shape_style": {
        "type": "str",
        "default": "difficulty-aware schedule",
        "valid": "|".join(SHAPE_STYLES),
    },
    "anchor_edge": {
        "type": "bool",
        "default": "five-slot lesson schedule",
        "valid": "true|false",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Consecutive indices 0..4 form four discriminative demonstrations plus a
# query.  The profiles cover canonical winner-cardinality and distractor
# branches, rather than leaving lesson identifiability to chance.
_LESSON_PROFILES = (
    # palette_size, n_winners, winner slot indices, anchor_edge
    (3, 1, (1,), False),       # unique maximum, distractors on both sides
    (2, 2, (0, 1), False),     # two-way tie, no distractor
    (4, 3, (0, 2, 3), True),   # three-way tie, interleaved distractor
    (3, 1, (2,), False),       # unique maximum is rightmost, not first color
    (5, 4, (0, 1, 3, 4), True),  # four-way query, interleaved distractor
)
_MAX_COUNT_SCHEDULE = {
    "easy": (3, 4, 5, 3, 4),
    "medium": (4, 5, 6, 7, 5),
    "hard": (5, 7, 8, 9, 6),
}
_STYLE_SCHEDULE = {
    "easy": ("compact", "compact", "mixed", "compact", "mixed"),
    "medium": ("compact", "mixed", "snaky", "mixed", "snaky"),
    "hard": ("mixed", "snaky", "snaky", "mixed", "snaky"),
}


def _band_name(difficulty: Any) -> str:
    return difficulty if difficulty in _MAX_COUNT_SCHEDULE else "medium"


def _validate_override_domains(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    int_domains = {
        "grid_h": (8, 14),
        "grid_w": (8, 14),
        "palette_size": (2, 5),
        "n_winners": (1, 4),
        "max_count": (3, 9),
    }
    for name, (lo, hi) in int_domains.items():
        if name in overrides and overrides[name] is not None:
            value = int(overrides[name])
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError(f"unknown palette_kind {overrides['palette_kind']!r}")
    if "shape_style" in overrides and overrides["shape_style"] not in SHAPE_STYLES:
        raise ValueError(f"unknown shape_style {overrides['shape_style']!r}")
    if "anchor_edge" in overrides and not isinstance(overrides["anchor_edge"], bool):
        raise ValueError("anchor_edge must be bool")


def _scheduled_axes(sample_index: int, difficulty: Any) -> dict[str, Any]:
    slot = int(sample_index) % len(_LESSON_PROFILES)
    palette_size, n_winners, _, anchor_edge = _LESSON_PROFILES[slot]
    band = _band_name(difficulty)
    return {
        "palette_size": palette_size,
        "n_winners": n_winners,
        "max_count": _MAX_COUNT_SCHEDULE[band][slot],
        "shape_style": _STYLE_SCHEDULE[band][slot],
        "anchor_edge": anchor_edge,
    }


def _resolve_semantic_axes(
    sample_index: int, difficulty: Any, overrides: dict[str, Any]
) -> tuple[dict[str, Any], tuple[int, ...] | None]:
    """Fill schedule defaults while keeping every caller override exact.

    A lone palette_size or n_winners override must always be usable.  When only
    one side is explicit, adjust the scheduled partner; when both are explicit,
    an impossible n_winners > palette_size combination rejects loudly.
    """
    effective = _scheduled_axes(sample_index, difficulty)
    effective.update({k: v for k, v in overrides.items() if v is not None})

    palette_explicit = overrides.get("palette_size") is not None
    winners_explicit = overrides.get("n_winners") is not None
    palette_size = int(effective["palette_size"])
    n_winners = int(effective["n_winners"])
    if palette_explicit and winners_explicit and n_winners > palette_size:
        raise ValueError(
            f"n_winners={n_winners} exceeds palette_size={palette_size}"
        )
    if winners_explicit and not palette_explicit:
        palette_size = max(palette_size, n_winners)
    if palette_explicit and not winners_explicit:
        n_winners = min(n_winners, palette_size)
    effective["palette_size"] = palette_size
    effective["n_winners"] = n_winners

    slot = int(sample_index) % len(_LESSON_PROFILES)
    scheduled_slots = _LESSON_PROFILES[slot][2]
    winner_slots = (
        scheduled_slots
        if not palette_explicit
        and not winners_explicit
        and len(scheduled_slots) == n_winners
        and max(scheduled_slots) < palette_size
        else None
    )
    return effective, winner_slots


def _active_capacity(h: int, w: int, n_colors: int, anchor_edge: bool) -> int:
    active_h = h if anchor_edge else h - 2
    active_w = w if anchor_edge else w - 2
    if active_h <= 0 or active_w < n_colors:
        return 0
    return active_h * (active_w // n_colors)


def _pick_dimensions(ctx, effective: dict[str, Any], original: dict[str, Any]) -> tuple[int, int]:
    n_colors = int(effective["palette_size"])
    max_count = int(effective["max_count"])
    anchor_edge = bool(effective["anchor_edge"])
    explicit_h = int(original["grid_h"]) if original.get("grid_h") is not None else None
    explicit_w = int(original["grid_w"]) if original.get("grid_w") is not None else None

    candidates = [
        (h, w)
        for h in range(8, 15)
        for w in range(8, 15)
        if (explicit_h is None or h == explicit_h)
        and (explicit_w is None or w == explicit_w)
        and _active_capacity(h, w, n_colors, anchor_edge) >= max_count
    ]
    if not candidates:
        raise ValueError(
            "incompatible grid/palette/count/edge overrides: no 8..14 canvas "
            f"fits palette_size={n_colors}, max_count={max_count}, "
            f"anchor_edge={anchor_edge}, grid_h={explicit_h}, grid_w={explicit_w}"
        )

    band = _band_name(ctx.difficulty)
    weighted: list[tuple[int, int]] = list(candidates)
    weighted.extend([(10, 10)] * 24 if (10, 10) in candidates else [])
    if band == "easy":
        weighted.extend([(h, w) for h, w in candidates if h <= 10 and w <= 10] * 2)
    elif band == "hard":
        weighted.extend([(h, w) for h, w in candidates if h >= 11 and w >= 11] * 2)
    else:
        weighted.extend([(h, w) for h, w in candidates if 9 <= h <= 12 and 9 <= w <= 12])
    chosen_h, chosen_w = ctx.draw_rng("dimension_pair").choice(weighted)

    # Record both exact dimensions through the public GenCtx draw path.
    ctx.overrides.setdefault("grid_h", chosen_h)
    ctx.overrides.setdefault("grid_w", chosen_w)
    return ctx.draw_int("grid_h", 8, 14), ctx.draw_int("grid_w", 8, 14)


def _palette(kind: str, n: int, rng) -> list[int]:
    pools = {
        "warm": [2, 3, 4, 6, 7, 9],
        "cool": [1, 3, 5, 6, 8, 9],
        "primary": [1, 2, 3, 4, 8, 9],
        "broad": list(range(1, 10)),
    }
    return rng.sample(pools[kind], n)


def _winner_slots(n_colors: int, n_winners: int, rng) -> tuple[int, ...]:
    if n_winners == 1:
        return (rng.randrange(n_colors),)
    return tuple(sorted(rng.sample(range(n_colors), n_winners)))


def _assign_colors_to_slots(
    colors: list[int], winner_slots: tuple[int, ...], rng
) -> list[int]:
    """Make multi-winner left-to-right order deliberately non-numeric."""
    winners = sorted(colors[: len(winner_slots)], reverse=True)
    distractors = colors[len(winner_slots) :]
    rng.shuffle(distractors)
    assigned: list[int | None] = [None] * len(colors)
    for slot, color in zip(winner_slots, winners):
        assigned[slot] = color
    for slot, color in zip(
        (i for i, value in enumerate(assigned) if value is None), distractors
    ):
        assigned[slot] = color
    return [int(value) for value in assigned]


def _column_zones(w: int, n_colors: int, anchor_edge: bool) -> list[tuple[int, int]]:
    lo = 0 if anchor_edge else 1
    hi = w if anchor_edge else w - 1
    width = hi - lo
    base, extra = divmod(width, n_colors)
    if base < 1:
        raise ValueError("canvas has fewer active columns than colors")
    zones = []
    start = lo
    for index in range(n_colors):
        zone_w = base + (1 if index < extra else 0)
        zones.append((start, start + zone_w))
        start += zone_w
    return zones


def _neighbors(cell: tuple[int, int], rows: range, cols: range) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _DIRECTIONS:
        nr, nc = r + dr, c + dc
        if nr in rows and nc in cols:
            yield nr, nc


def _grow_shape(
    rows: range,
    cols: range,
    count: int,
    style: str,
    rng,
    *,
    forced_seed: tuple[int, int] | None = None,
) -> set[tuple[int, int]]:
    cells_domain = [(r, c) for r in rows for c in cols]
    if count > len(cells_domain):
        raise ValueError(f"shape count {count} exceeds zone capacity {len(cells_domain)}")
    if forced_seed is not None:
        seed = forced_seed
    elif style == "compact":
        seed = ((rows.start + rows.stop - 1) // 2, (cols.start + cols.stop - 1) // 2)
    else:
        seed = rng.choice(cells_domain)
    shape = {seed}
    tip = seed
    center = ((rows.start + rows.stop - 1) / 2, (cols.start + cols.stop - 1) / 2)
    while len(shape) < count:
        frontier = sorted(
            {nb for cell in shape for nb in _neighbors(cell, rows, cols)} - shape
        )
        if not frontier:
            raise ValueError("connected-shape frontier exhausted")
        if style == "compact":
            distances = [abs(r - center[0]) + abs(c - center[1]) for r, c in frontier]
            best = min(distances)
            choices = [cell for cell, dist in zip(frontier, distances) if dist == best]
            chosen = rng.choice(choices)
        elif style == "snaky":
            tip_neighbors = [nb for nb in _neighbors(tip, rows, cols) if nb not in shape]
            chosen = rng.choice(tip_neighbors or frontier)
        else:
            chosen = rng.choice(frontier)
        shape.add(chosen)
        tip = chosen
    return shape


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_domains(overrides)
    effective, scheduled_winner_slots = _resolve_semantic_axes(
        sample_index, difficulty, overrides
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    palette_size = ctx.draw_int("palette_size", 2, 5)
    n_winners = ctx.draw_int("n_winners", 1, 4)
    if n_winners > palette_size:
        raise ValueError(
            f"n_winners={n_winners} exceeds palette_size={palette_size}"
        )
    max_count = ctx.draw_int("max_count", 3, 9)
    anchor_edge = ctx.draw_choice("anchor_edge", (False, True))
    shape_style = ctx.draw_choice("shape_style", SHAPE_STYLES)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    h, w = _pick_dimensions(ctx, effective, overrides)

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    winner_slots = scheduled_winner_slots or _winner_slots(
        palette_size, n_winners, layout_rng
    )
    colors = _palette(palette_kind, palette_size, palette_rng)
    slot_colors = _assign_colors_to_slots(colors, winner_slots, palette_rng)

    loser_counts: dict[int, int] = {}
    for slot in range(palette_size):
        if slot not in winner_slots:
            loser_counts[slot] = layout_rng.randint(2, max_count - 1)

    row_range = range(0, h) if anchor_edge else range(1, h - 1)
    zones = _column_zones(w, palette_size, anchor_edge)
    grid = full_grid(h, w, 0)
    for slot, (c0, c1) in enumerate(zones):
        count = max_count if slot in winner_slots else loser_counts[slot]
        col_range = range(c0, c1)
        forced_seed = None
        if anchor_edge and slot == 0:
            forced_seed = (layout_rng.randrange(row_range.start, row_range.stop), 0)
        shape = _grow_shape(
            row_range,
            col_range,
            count,
            shape_style,
            layout_rng,
            forced_seed=forced_seed,
        )
        for r, c in shape:
            grid[r][c] = slot_colors[slot]
    return grid


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"], 0, 0
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        errors.append("grid must be non-empty and rectangular")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be ARC color integers 0..9")
    return errors, h, w


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        comp = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in _DIRECTIONS:
                nb = (r + dr, c + dc)
                if nb in remaining:
                    remaining.remove(nb)
                    comp.add(nb)
                    stack.append(nb)
        components.append(comp)
    return components


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells_by_color.setdefault(value, []).append((r, c))
    counts = {color: len(cells) for color, cells in cells_by_color.items()}
    max_count = max(counts.values()) if counts else 0
    leftmost = {
        color: min(c for _, c in cells) for color, cells in cells_by_color.items()
    }
    winners = tuple(
        sorted(
            (color for color, count in counts.items() if count == max_count),
            key=lambda color: leftmost[color],
        )
    )
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "palette_size": len(counts),
        "counts": counts,
        "max_count": max_count,
        "leftmost": leftmost,
        "winners": winners,
        "n_winners": len(winners),
        "has_distractor": len(counts) > len(winners),
        "winner_order_not_numeric": len(winners) > 1 and winners != tuple(sorted(winners)),
        "anchor_edge": any(
            value != 0 and (r in (0, h - 1) or c in (0, w - 1))
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
        ),
        "component_counts": {
            color: len(_components(cells)) for color, cells in cells_by_color.items()
        },
    }


def observe_overrides(grid: Any) -> dict[str, int | bool]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "palette_size": int(facts["palette_size"]),
        "n_winners": int(facts["n_winners"]),
        "max_count": int(facts["max_count"]),
        "anchor_edge": bool(facts["anchor_edge"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete canonical input grammar and generated domain."""
    errors, h, w = _grid_errors(grid)
    if errors:
        return errors
    if not 8 <= h <= 14 or not 8 <= w <= 14:
        errors.append(f"expected dimensions 8..14, got {h}x{w}")
    facts = semantic_observables(grid)
    n_colors = facts["palette_size"]
    if not 2 <= n_colors <= 5:
        errors.append(f"expected 2..5 non-zero colors, got {n_colors}")
    counts: dict[int, int] = facts["counts"]
    for color, count in sorted(counts.items()):
        if not 2 <= count <= 9:
            errors.append(f"color {color} count {count} outside 2..9")
        if facts["component_counts"].get(color) != 1:
            errors.append(f"color {color} must form one 4-connected object")
    if counts and facts["max_count"] < 3:
        errors.append(f"maximum color count must be at least 3, got {facts['max_count']}")
    if not 1 <= facts["n_winners"] <= 4:
        errors.append(f"expected 1..4 maximum-count colors, got {facts['n_winners']}")
    winner_leftmost = [facts["leftmost"][color] for color in facts["winners"]]
    if len(set(winner_leftmost)) != len(winner_leftmost):
        errors.append("maximum-count colors must have distinct leftmost columns")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 10 or len(grid[0]) != 10:
        return [f"canonical inputs are 10x10, got {len(grid)}x{len(grid[0])}"]
    return []


def _official_output_from_facts(facts: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    row = tuple(int(color) for color in facts["winners"])
    return tuple(row for _ in range(int(facts["max_count"])))


def _candidate_outputs(grid: Any) -> dict[str, tuple[tuple[int, ...], ...]]:
    facts = semantic_observables(grid)
    if facts.get("errors") or not facts.get("counts"):
        return {}
    counts: dict[int, int] = facts["counts"]
    leftmost: dict[int, int] = facts["leftmost"]
    max_count = max(counts.values())
    min_count = min(counts.values())

    def bars(colors: Iterable[int], height: int) -> tuple[tuple[int, ...], ...]:
        row = tuple(int(color) for color in colors)
        return tuple(row for _ in range(int(height)))

    max_colors = [color for color, count in counts.items() if count == max_count]
    min_colors = [color for color, count in counts.items() if count == min_count]
    all_colors = list(counts)
    left = lambda colors: sorted(colors, key=lambda color: leftmost[color])
    return {
        "max_leftmost": bars(left(max_colors), max_count),
        "max_numeric": bars(sorted(max_colors), max_count),
        "all_leftmost": bars(left(all_colors), max_count),
        "all_numeric": bars(sorted(all_colors), max_count),
        "min_leftmost": bars(left(min_colors), min_count),
        "single_leftmost_max": bars(left(max_colors)[:1], max_count),
        "max_leftmost_height_ncolors": bars(left(max_colors), len(counts)),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Falsify common count/order/size shortcuts on a materialized lesson."""
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    surviving: set[str] | None = None
    max_heights: set[int] = set()
    saw_distractor = False
    saw_multiwinner = False
    saw_non_numeric_order = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        candidates = _candidate_outputs(pair["input"])
        official = tuple(tuple(row) for row in pair["output"])
        consistent = {name for name, output in candidates.items() if output == official}
        surviving = consistent if surviving is None else surviving & consistent
        facts = semantic_observables(pair["input"])
        if facts.get("errors"):
            return [f"demo {index} input is malformed: {facts['errors'][0]}"]
        max_heights.add(int(facts["max_count"]))
        saw_distractor |= bool(facts["has_distractor"])
        saw_multiwinner |= int(facts["n_winners"]) >= 2
        saw_non_numeric_order |= bool(facts["winner_order_not_numeric"])

    reasons: list[str] = []
    if not saw_distractor:
        reasons.append("demos never distinguish maximum-count selection from all-color echo")
    if not saw_multiwinner:
        reasons.append("demos never show a tied maximum")
    if not saw_non_numeric_order:
        reasons.append("demos never distinguish leftmost ordering from numeric color order")
    if len(max_heights) < 2:
        reasons.append("demos do not vary the output height / maximum count")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_candidates = _candidate_outputs(query["input"])
    official_query = tuple(tuple(row) for row in query["output"])
    surviving = surviving or set()
    confounders = sorted(
        name
        for name in surviving
        if query_candidates.get(name) != official_query
    )
    if confounders:
        reasons.append(
            "surviving shortcut(s) predict a different query answer: "
            + ", ".join(confounders)
        )
    if "max_leftmost" not in surviving:
        reasons.append("official rule was not consistent with every demonstration")
    return reasons


SEMANTIC_WITNESSES = {
    "unique_max": lambda grid: semantic_observables(grid).get("n_winners") == 1,
    "two_way_tie": lambda grid: semantic_observables(grid).get("n_winners") == 2,
    "three_plus_tie": lambda grid: semantic_observables(grid).get("n_winners", 0) >= 3,
    "has_lower_count_distractor": lambda grid: bool(
        semantic_observables(grid).get("has_distractor")
    ),
    "no_distractor": lambda grid: (
        semantic_observables(grid).get("palette_size", 0)
        == semantic_observables(grid).get("n_winners", -1)
    ),
    "leftmost_order_differs_from_numeric": lambda grid: bool(
        semantic_observables(grid).get("winner_order_not_numeric")
    ),
    "max_count_at_least_five": lambda grid: semantic_observables(grid).get("max_count", 0) >= 5,
    "edge_anchored": lambda grid: bool(semantic_observables(grid).get("anchor_edge")),
}


def mutation_fixtures():
    """Task-semantic near-misses that self_check must reject."""
    disconnected = full_grid(10, 10, 0)
    for r, c in ((1, 1), (1, 2), (7, 7)):
        disconnected[r][c] = 2
    for r, c in ((4, 5), (4, 6)):
        disconnected[r][c] = 3

    one_color = full_grid(10, 10, 0)
    for r, c in ((2, 2), (2, 3), (3, 2)):
        one_color[r][c] = 4

    tied_left_edge = full_grid(10, 10, 0)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        tied_left_edge[r][c] = 2
    for r, c in ((6, 1), (6, 2), (7, 1)):
        tied_left_edge[r][c] = 8

    six_colors = full_grid(10, 10, 0)
    for color, c0 in enumerate((0, 1, 3, 4, 6, 8), start=1):
        six_colors[1][c0] = color
        six_colors[2][c0] = color
        six_colors[3][c0] = color

    singleton_recombination = full_grid(10, 10, 0)
    for r, c in ((2, 1), (2, 2), (3, 1)):
        singleton_recombination[r][c] = 2
    for r, c in ((5, 6), (5, 7), (6, 6)):
        singleton_recombination[r][c] = 3
    singleton_recombination[8][8] = 9

    return [
        ("disconnected_color", disconnected),
        ("single_nonzero_color", one_color),
        ("winner_leftmost_tie", tied_left_edge),
        ("too_many_colors", six_colors),
        ("absent-feature_singleton_recombination", singleton_recombination),
    ]
