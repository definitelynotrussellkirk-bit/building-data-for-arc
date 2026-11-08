"""Generator for Directed Pair Extension (task 8de3465b4dbd).

Semantic rule: scan each row for the exact consecutive triple ``[2, 3, 0]``.
For every match, recolor only the trailing zero to 8.  Reversed ``[3, 2]``
pairs and blocked ``[2, 3, 3]`` near-matches remain unchanged.

The generator keeps the canonical fixed colors and sparse horizontal geometry,
while varying exact grid dimensions and motif counts.  A keyed canonical-family
prior preserves the demonstrated 7x8 / 8x9 / 9x10 scale and 3-4 trigger regime;
the complementary branch expands dimensions, counts, row packing, edge cases,
same-row multiple matches, mixed-direction rows, and blocked near-matches.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8de3465b4dbd"
TASK_ID = "8de3465b4dbd"
VERSION = "3.0.0"
RULE_HASH = "613cb83aac3f"

SUMMARY = (
    "Sparse 0-background grids contain 2-6 exact horizontal [2,3,0] "
    "triggers, 1-2 reversed [3,2] negative witnesses, and optionally 0-3 "
    "blocked [2,3,3] near-matches. Scan every row left to right: for each "
    "exact [2,3,0], recolor only the trailing 0 to cyan 8. Reversed and "
    "blocked arrangements are unchanged. Layouts deliberately vary edge "
    "positions, multiple triggers in one row, and trigger/reverse motifs in "
    "the same row so row-count, fixed-position, and one-match shortcuts fail."
)

INVARIANTS = [
    "grid dimensions are 7..14 by 8..14 and the input palette is exactly {0,2,3}",
    "exactly 2..6 disjoint [2,3,0] trigger triples are present",
    "exactly 1..2 disjoint [3,2] reversed-pair negative witnesses are present",
    "exactly 0..3 disjoint [2,3,3] blocked near-matches are present",
    "every nonzero input cell belongs to exactly one recognized motif",
    "at least two rows contain foreground motifs",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "35% canonical-family prior; otherwise difficulty-skewed",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "35% canonical-family prior; otherwise difficulty-skewed",
        "valid": "8..14",
    },
    "n_triggers": {
        "type": "int",
        "default": "3..4 in canonical-family prior; otherwise difficulty-skewed",
        "valid": "2..6",
    },
    "n_reverse": {
        "type": "int",
        "default": "1 in canonical-family prior; otherwise difficulty-skewed",
        "valid": "1..2",
    },
    "blocked_pairs": {
        "type": "int",
        "default": "0 in canonical-family prior; otherwise difficulty-skewed",
        "valid": "0..3",
    },
}

_TRIGGER = "trigger"
_REVERSE = "reverse"
_BLOCKED = "blocked"
_CANONICAL_SHAPES = ((7, 8), (8, 9), (9, 10))
_CANONICAL_PRIOR_PERCENT = 35


def _canonical_shapes_for(difficulty: Any) -> tuple[tuple[int, int], ...]:
    if difficulty == "easy":
        return _CANONICAL_SHAPES[:2]
    if difficulty == "hard":
        return _CANONICAL_SHAPES[1:]
    return _CANONICAL_SHAPES


def _draw_axes(ctx, overrides: dict[str, Any]) -> tuple[int, int, int, int, int, bool]:
    """Draw exact observable axes, using a canonical-family prior only by default.

    Any explicit override disables the prior, so every declared boundary remains
    valid in every difficulty band and mixed override combinations are exact.
    """
    has_explicit_override = any(value is not None for value in overrides.values())
    prior_rng = ctx.draw_rng("canonical_family_prior")
    canonical_family = (
        not has_explicit_override
        and prior_rng.randrange(100) < _CANONICAL_PRIOR_PERCENT
    )

    if canonical_family:
        shape = prior_rng.choice(_canonical_shapes_for(ctx.difficulty))
        h = ctx.draw_int("grid_h", shape[0], shape[0])
        w = ctx.draw_int("grid_w", shape[1], shape[1])
        n_triggers = ctx.draw_int("n_triggers", 3, 4)
        n_reverse = ctx.draw_int("n_reverse", 1, 1)
        blocked_pairs = ctx.draw_int("blocked_pairs", 0, 0)
    else:
        # Full declared bounds are used in every band; draw_int_diff only skews
        # the default mass and never narrows an exact override's valid domain.
        h = ctx.draw_int_diff("grid_h", 7, 14)
        w = ctx.draw_int_diff("grid_w", 8, 14)
        n_triggers = ctx.draw_int_diff("n_triggers", 2, 6)
        n_reverse = ctx.draw_int_diff("n_reverse", 1, 2)
        blocked_pairs = ctx.draw_int_diff("blocked_pairs", 0, 3)

    return h, w, n_triggers, n_reverse, blocked_pairs, canonical_family


def _row_slots(width: int, *, right_packed: bool) -> list[int]:
    """Return non-overlapping width-3 slots separated by at least one zero."""
    if right_packed:
        starts: list[int] = []
        c = width - 3
        while c >= 0:
            starts.append(c)
            c -= 4
        return sorted(starts)
    return list(range(0, width - 2, 4))


def _stamp(grid: list[list[int]], row: int, col: int, motif: str) -> None:
    if motif == _TRIGGER:
        grid[row][col:col + 3] = [2, 3, 0]
    elif motif == _REVERSE:
        grid[row][col:col + 3] = [3, 2, 0]
    elif motif == _BLOCKED:
        grid[row][col:col + 3] = [2, 3, 3]
    else:  # defensive: construction calls only the constants above
        raise ValueError(f"unknown motif {motif!r}")


def _place_motifs(
    grid: list[list[int]],
    *,
    n_triggers: int,
    n_reverse: int,
    blocked_pairs: int,
    rng,
    canonical_family: bool,
) -> None:
    """Place exact motif counts with varied but collision-free row layouts."""
    h, w = len(grid), len(grid[0])
    row_order = list(range(h))
    rng.shuffle(row_order)

    free: dict[int, list[int]] = {}
    for row in range(h):
        starts = _row_slots(w, right_packed=bool(rng.getrandbits(1)))
        rng.shuffle(starts)
        free[row] = starts

    assignments: dict[tuple[int, int], str] = {}
    remaining = Counter({
        _TRIGGER: n_triggers,
        _REVERSE: n_reverse,
        _BLOCKED: blocked_pairs,
    })
    active_rows: set[int] = set()
    edge_trigger_placed = False

    profiles = ("separate", "multi", "mixed", "multi_mixed")
    # Canonical-family draws still rotate through all three demonstrated layout
    # ideas; expanded draws also use the combined branch more often at scale.
    profile = rng.choice(profiles if canonical_family else profiles + ("multi_mixed",))
    want_edge_trigger = rng.random() < (0.25 if canonical_family else 0.55)

    def choose_slot(row: int, edge_preference: bool | None = None) -> int:
        choices = free[row]
        if not choices:
            raise ValueError(f"row {row} has no free motif slot")
        preferred: list[int] = []
        if edge_preference is not None:
            preferred = [
                col
                for col in choices
                if (col in (0, w - 3)) == edge_preference
            ]
        col = rng.choice(preferred or choices)
        choices.remove(col)
        return col

    def place(motif: str, row: int, *, edge_preference: bool | None = None) -> None:
        nonlocal edge_trigger_placed
        if remaining[motif] <= 0:
            raise ValueError(f"attempted to over-place motif {motif}")
        col = choose_slot(row, edge_preference=edge_preference)
        assignments[(row, col)] = motif
        remaining[motif] -= 1
        active_rows.add(row)
        if motif == _TRIGGER and col in (0, w - 3):
            edge_trigger_placed = True

    next_row_index = 0

    def next_distinct_row() -> int:
        nonlocal next_row_index
        while next_row_index < len(row_order):
            row = row_order[next_row_index]
            next_row_index += 1
            if free[row] and row not in active_rows:
                return row
        candidates = [row for row in row_order if free[row]]
        if not candidates:
            raise ValueError("no free row remains for motif placement")
        return rng.choice(candidates)

    edge_preference_for_first_trigger = True if want_edge_trigger else False

    if profile in {"multi", "multi_mixed"} and remaining[_TRIGGER] >= 2:
        row = next_distinct_row()
        place(_TRIGGER, row, edge_preference=edge_preference_for_first_trigger)
        edge_preference_for_first_trigger = None
        place(_TRIGGER, row)

    if (
        profile in {"mixed", "multi_mixed"}
        and remaining[_TRIGGER] >= 1
        and remaining[_REVERSE] >= 1
    ):
        row = next_distinct_row()
        place(_TRIGGER, row, edge_preference=edge_preference_for_first_trigger)
        edge_preference_for_first_trigger = None
        place(_REVERSE, row)

    # If the selected profile consumed all triggers, the first forced trigger
    # already honored the requested edge policy. Otherwise reserve one edge
    # witness before random filling when requested.
    if want_edge_trigger and not edge_trigger_placed and remaining[_TRIGGER] > 0:
        candidates = [
            row
            for row in row_order
            if any(col in (0, w - 3) for col in free[row])
        ]
        if not candidates:
            raise ValueError("no edge slot remains for requested edge trigger")
        unused = [row for row in candidates if row not in active_rows]
        place(_TRIGGER, rng.choice(unused or candidates), edge_preference=True)

    motifs = (
        [_TRIGGER] * remaining[_TRIGGER]
        + [_REVERSE] * remaining[_REVERSE]
        + [_BLOCKED] * remaining[_BLOCKED]
    )
    rng.shuffle(motifs)

    for motif in motifs:
        candidate_rows = [row for row in row_order if free[row]]
        if not candidate_rows:
            raise ValueError("grid has insufficient collision-free motif slots")

        # Guarantee at least two active rows. The separate profile additionally
        # spreads motifs over new rows before reusing any row, matching the
        # canonical sparse-row family without making that the only lesson.
        unused_rows = [row for row in candidate_rows if row not in active_rows]
        if len(active_rows) < 2 and unused_rows:
            candidate_rows = unused_rows
        elif profile == "separate" and unused_rows:
            candidate_rows = unused_rows

        row = rng.choice(candidate_rows)
        edge_preference: bool | None = None
        if motif == _TRIGGER and not want_edge_trigger:
            # Avoiding an edge is a preference, not a hard restriction: large
            # exact count overrides may legitimately require all available slots.
            edge_preference = False
        place(motif, row, edge_preference=edge_preference)

    if any(remaining.values()):
        raise RuntimeError(f"motif placement left nonzero counts: {dict(remaining)}")

    for (row, col), motif in assignments.items():
        _stamp(grid, row, col, motif)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_triggers, n_reverse, blocked_pairs, canonical_family = _draw_axes(
        ctx, overrides
    )

    grid = full_grid(h, w, 0)
    _place_motifs(
        grid,
        n_triggers=n_triggers,
        n_reverse=n_reverse,
        blocked_pairs=blocked_pairs,
        rng=ctx.draw_rng("layout"),
        canonical_family=canonical_family,
    )

    errors = self_check(grid, difficulty=difficulty, meta=None)
    if errors:
        raise RuntimeError("internal construction failed self_check: " + "; ".join(errors))
    return grid


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    h = len(grid)
    w = len(grid[0])
    triggers: list[tuple[int, int]] = []
    reverses: list[tuple[int, int]] = []
    blocked: list[tuple[int, int]] = []
    dangling: list[tuple[int, int]] = []
    malformed: list[tuple[int, int, int]] = []
    coverage: Counter[tuple[int, int]] = Counter()

    for row_index, row in enumerate(grid):
        for col in range(w - 1):
            if row[col:col + 2] == [3, 2]:
                reverses.append((row_index, col))
                coverage[(row_index, col)] += 1
                coverage[(row_index, col + 1)] += 1
            if row[col:col + 2] != [2, 3]:
                continue
            if col + 2 >= w:
                dangling.append((row_index, col))
                continue
            tail = row[col + 2]
            if tail == 0:
                triggers.append((row_index, col))
                coverage[(row_index, col)] += 1
                coverage[(row_index, col + 1)] += 1
            elif tail == 3:
                blocked.append((row_index, col))
                coverage[(row_index, col)] += 1
                coverage[(row_index, col + 1)] += 1
                coverage[(row_index, col + 2)] += 1
            else:
                malformed.append((row_index, col, tail))

    foreground = {
        (row_index, col)
        for row_index, row in enumerate(grid)
        for col, value in enumerate(row)
        if value != 0
    }
    active_rows = {row for row, _ in foreground}
    return {
        "grid_h": h,
        "grid_w": w,
        "n_triggers": len(triggers),
        "n_reverse": len(reverses),
        "blocked_pairs": len(blocked),
        "triggers": triggers,
        "reverses": reverses,
        "blocked": blocked,
        "dangling": dangling,
        "malformed": malformed,
        "foreground": foreground,
        "active_rows": active_rows,
        "uncovered": sorted(cell for cell in foreground if coverage[cell] == 0),
        "overcovered": sorted(cell for cell, count in coverage.items() if count > 1),
    }


def observe_overrides(grid):
    """Recover every declared exact axis from a returned input grid."""
    analysis = _analyze(grid)
    return {
        axis: analysis[axis]
        for axis in ("grid_h", "grid_w", "n_triggers", "n_reverse", "blocked_pairs")
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes, not merely generated-default violations."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    height = len(grid)
    if not 7 <= height <= 14:
        errors.append(f"grid height must be in 7..14, got {height}")
    if not 8 <= width <= 14:
        errors.append(f"grid width must be in 8..14, got {width}")

    invalid_values = sorted({
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 2, 3)
    }, key=repr)
    if invalid_values:
        errors.append(f"input contains values outside fixed palette 0,2,3: {invalid_values}")
        return sorted(set(errors))

    palette = {value for row in grid for value in row}
    if palette != {0, 2, 3}:
        errors.append(f"input palette must be exactly {{0,2,3}}, got {sorted(palette)}")

    analysis = _analyze(grid)
    if not 2 <= analysis["n_triggers"] <= 6:
        errors.append(
            f"need exactly 2..6 [2,3,0] triggers, got {analysis['n_triggers']}"
        )
    if not 1 <= analysis["n_reverse"] <= 2:
        errors.append(
            f"need exactly 1..2 [3,2] reverse witnesses, got {analysis['n_reverse']}"
        )
    if not 0 <= analysis["blocked_pairs"] <= 3:
        errors.append(
            f"need exactly 0..3 [2,3,3] blocked near-matches, got {analysis['blocked_pairs']}"
        )
    if analysis["dangling"]:
        errors.append(
            "[2,3] may not start in the final two columns without a testable trailing cell"
        )
    if analysis["malformed"]:
        errors.append(
            "every [2,3] pair must have trailing 0 (trigger) or 3 (blocked near-match)"
        )
    if analysis["uncovered"]:
        errors.append(
            f"every nonzero cell must belong to one recognized motif; uncovered={analysis['uncovered'][:8]}"
        )
    if analysis["overcovered"]:
        errors.append(
            f"motifs must be disjoint; multiply covered={analysis['overcovered'][:8]}"
        )
    if len(analysis["active_rows"]) < 2:
        errors.append("foreground motifs must occupy at least two rows")

    return sorted(set(errors))
