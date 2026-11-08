"""Generator for ARC task 5383f0933057 — nearest-seed fill inside 9-walled chambers.

Color 9 is an immovable wall.  The non-9 cells form one or more 4-connected
chambers.  Every chamber contains at least one colored seed; each zero cell is
filled from the nearest seed in *that chamber* by Manhattan distance.  Ties are
resolved by the smaller seed color (then row/column, which is answer-equivalent
when colors match).

The distribution includes exact canonical-scale profiles, seeds embedded in an
outer wall (as in the canonical test), disconnected chambers that rebut a
global-nearest shortcut, and ordinary same-chamber color-tie witnesses.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5383f0933057"
TASK_ID = "5383f0933057"
VERSION = "4.0.0"
RULE_HASH = "6347b4079eb5"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A grid of 9-walls encloses one or more 4-connected non-9 chambers. "
    "Each chamber has colored seed cells and zero cells. Fill every zero from "
    "the Manhattan-nearest seed in the same chamber; on an equal-distance "
    "color tie, use the smaller color. Walls and seeds stay unchanged."
)

INVARIANTS = [
    "9-cells are walls and are copied unchanged",
    "every non-9 chamber contains at least one non-{0,9} seed",
    "every zero is assigned using only seeds in its own 4-connected chamber",
    "equal Manhattan distances are broken by smaller seed color",
    "output dimensions equal input dimensions",
]

# These are the exact values that can be recovered from a returned grid.  The
# override matrix intentionally exercises incompatible pairs too; those reject
# with ValueError rather than silently clamping or falling back.
AXES = {
    "grid_h": {"type": "int", "default": "banded with canonical prior", "valid": "6..16"},
    "grid_w": {"type": "int", "default": "banded with canonical prior", "valid": "8..18"},
    "n_chambers": {"type": "int", "default": "banded 1..4", "valid": "1..4"},
    "n_seeds": {"type": "int", "default": "3..8 and enough for chambers", "valid": "2..8"},
    "palette_size": {"type": "int", "default": "2..6", "valid": "2..6"},
    "border_seeds": {"type": "int", "default": "0..1", "valid": "0..1"},
}

_H_RANGE = (6, 16)
_W_RANGE = (8, 18)
_CHAMBER_RANGE = (1, 4)
_SEED_RANGE = (2, 8)
_PALETTE_RANGE = (2, 6)
_BORDER_SEED_RANGE = (0, 1)
_CANONICAL_PROFILES = ((6, 8), (7, 9))
_CANONICAL_PRIOR = 0.35
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _is_arc_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected components of cells whose value is not wall color 9."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 9 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 9
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append(cells)
    return out


def _facts(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    """Structural analysis shared by self_check and observe_overrides."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], None
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], None
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"], None
    if any(not _is_arc_int(v) for row in grid for v in row):
        return ["all cells must be literal ARC integers 0..9"], None

    if not (_H_RANGE[0] <= h <= _H_RANGE[1]):
        errors.append(f"height {h} outside {_H_RANGE[0]}..{_H_RANGE[1]}")
    if not (_W_RANGE[0] <= w <= _W_RANGE[1]):
        errors.append(f"width {w} outside {_W_RANGE[0]}..{_W_RANGE[1]}")

    wall_count = sum(v == 9 for row in grid for v in row)
    zero_count = sum(v == 0 for row in grid for v in row)
    seeds = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 9)
    ]
    seed_colors = {v for _, _, v in seeds}
    regions = _regions(grid)

    if wall_count == 0:
        errors.append("expected color-9 walls")
    if zero_count == 0:
        errors.append("expected at least one fillable zero cell")
    if len(seeds) < 2:
        errors.append("expected at least two seed cells")
    if len(seed_colors) < 2:
        errors.append("expected at least two distinct seed colors")
    if not regions:
        errors.append("walls leave no non-9 chamber")

    seed_positions = {(r, c) for r, c, _ in seeds}
    unseeded: list[int] = []
    for index, region in enumerate(regions):
        if not any(pos in seed_positions for pos in region):
            unseeded.append(index)
    if unseeded:
        errors.append(
            "every non-9 chamber needs a seed; unseeded chamber indices "
            + ",".join(map(str, unseeded[:5]))
        )

    border_seeds = sum(
        r in (0, h - 1) or c in (0, w - 1) for r, c, _ in seeds
    )
    facts = {
        "grid_h": h,
        "grid_w": w,
        "n_chambers": len(regions),
        "n_seeds": len(seeds),
        "palette_size": len(seed_colors),
        "border_seeds": border_seeds,
        "wall_count": wall_count,
        "zero_count": zero_count,
        "regions": regions,
        "seeds": seeds,
    }
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting every canonical input.

    This checks the input grammar needed by the oracle: real walls, fillable
    cells, multiple seed colors, and at least one seed in every open component.
    It deliberately permits a colored seed to replace an outer-wall cell,
    because the official test contains exactly that branch.
    """
    return _facts(grid)[0]


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact semantic axes directly from the returned grid."""
    errors, facts = _facts(grid)
    if facts is None or errors:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_chambers": facts["n_chambers"],
        "n_seeds": facts["n_seeds"],
        "palette_size": facts["palette_size"],
        "border_seeds": facts["border_seeds"],
    }


def _draw_axis_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    """Band ordinary draws, but validate explicit overrides over the full domain."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _parallel_positions(length: int, count: int, rng) -> list[int]:
    """Choose `count` full divider indices with a nonempty lane between each."""
    candidates = list(range(2, length - 2))
    valid: list[tuple[int, ...]] = []
    if count == 1:
        valid = [(value,) for value in candidates]
    elif count == 2:
        valid = [
            (left, right)
            for left in candidates
            for right in candidates
            if left + 2 <= right
        ]
    if not valid:
        raise ValueError(
            f"dimension {length} cannot host {count} separated full dividers"
        )
    return list(rng.choice(valid))


def _build_walls(h: int, w: int, n_chambers: int, rng) -> list[list[int]]:
    """Construct exactly 1..4 open components using full or gapped dividers."""
    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 9
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 9

    if n_chambers == 1:
        # A nearly complete divider supplies internal wall cues while one or
        # two gaps keep the entire interior connected.
        if rng.random() < 0.5:
            r = rng.randrange(2, h - 2)
            gap_count = 1 if w <= 9 else rng.randint(1, 2)
            gaps = set(rng.sample(range(1, w - 1), gap_count))
            for c in range(1, w - 1):
                if c not in gaps:
                    grid[r][c] = 9
        else:
            c = rng.randrange(2, w - 2)
            gap_count = 1 if h <= 7 else rng.randint(1, 2)
            gaps = set(rng.sample(range(1, h - 1), gap_count))
            for r in range(1, h - 1):
                if r not in gaps:
                    grid[r][c] = 9
    elif n_chambers == 2:
        if rng.random() < 0.5:
            r = _parallel_positions(h, 1, rng)[0]
            for c in range(w):
                grid[r][c] = 9
        else:
            c = _parallel_positions(w, 1, rng)[0]
            for r in range(h):
                grid[r][c] = 9
    elif n_chambers == 3:
        options: list[str] = []
        if h >= 7:
            options.append("rows")
        if w >= 7:
            options.append("cols")
        if not options:
            raise ValueError(f"{h}x{w} cannot host three nonempty chambers")
        orientation = rng.choice(options)
        if orientation == "rows":
            for r in _parallel_positions(h, 2, rng):
                for c in range(w):
                    grid[r][c] = 9
        else:
            for c in _parallel_positions(w, 2, rng):
                for r in range(h):
                    grid[r][c] = 9
    elif n_chambers == 4:
        r = _parallel_positions(h, 1, rng)[0]
        c = _parallel_positions(w, 1, rng)[0]
        for cc in range(w):
            grid[r][cc] = 9
        for rr in range(h):
            grid[rr][c] = 9
    else:  # defensive: draw validation should make this unreachable
        raise ValueError(f"unsupported n_chambers={n_chambers}")

    actual = len(_regions(grid))
    if actual != n_chambers:
        raise RuntimeError(
            f"wall constructor produced {actual} chambers, requested {n_chambers}"
        )
    return grid


def _cell_to_region(regions: list[list[tuple[int, int]]]) -> dict[tuple[int, int], int]:
    return {cell: index for index, region in enumerate(regions) for cell in region}


def _interior_tie_candidates(
    grid: list[list[int]], regions: list[list[tuple[int, int]]]
) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int], int]]:
    """(seed_a, zero_midpoint, seed_b, chamber) straight distance-2 triples."""
    lookup = _cell_to_region(regions)
    out = []
    for middle, region_index in lookup.items():
        r, c = middle
        if grid[r][c] != 0:
            continue
        for dr, dc in ((1, 0), (0, 1)):
            a, b = (r - dr, c - dc), (r + dr, c + dc)
            if (
                lookup.get(a) == region_index
                and lookup.get(b) == region_index
                and grid[a[0]][a[1]] == 0
                and grid[b[0]][b[1]] == 0
            ):
                out.append((a, middle, b, region_index))
    return out


def _border_tie_candidates(
    grid: list[list[int]], regions: list[list[tuple[int, int]]]
) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int], int]]:
    """Border seed, open midpoint, interior seed triples for the test branch."""
    h, w = len(grid), len(grid[0])
    lookup = _cell_to_region(regions)
    triples = []
    for c in range(1, w - 1):
        triples.extend([
            ((0, c), (1, c), (2, c)),
            ((h - 1, c), (h - 2, c), (h - 3, c)),
        ])
    for r in range(1, h - 1):
        triples.extend([
            ((r, 0), (r, 1), (r, 2)),
            ((r, w - 1), (r, w - 2), (r, w - 3)),
        ])
    out = []
    for border, middle, inner in triples:
        region_index = lookup.get(middle)
        if (
            grid[border[0]][border[1]] == 9
            and region_index is not None
            and lookup.get(inner) == region_index
            and grid[middle[0]][middle[1]] == 0
            and grid[inner[0]][inner[1]] == 0
        ):
            out.append((border, middle, inner, region_index))
    return out


def _place_seeds(
    grid: list[list[int]],
    *,
    n_seeds: int,
    palette: tuple[int, ...],
    border_seeds: int,
    rng,
) -> None:
    """Place exact seed/color counts; ordinary spare capacity creates a tie witness."""
    regions = _regions(grid)
    n_chambers = len(regions)
    if n_seeds < n_chambers:
        raise ValueError(
            f"n_seeds={n_seeds} cannot seed all {n_chambers} chambers"
        )
    if len(palette) > n_seeds:
        raise ValueError(
            f"palette_size={len(palette)} cannot exceed n_seeds={n_seeds}"
        )
    if border_seeds not in (0, 1):
        raise ValueError("border_seeds must be 0 or 1")

    # Position records are (cell, original chamber index).  A border seed is
    # associated with the chamber reached through its inward neighbor.
    positions: list[tuple[tuple[int, int], int]] = []
    reserved_zero: set[tuple[int, int]] = set()
    tie_possible = n_seeds >= n_chambers + 1

    if tie_possible:
        candidates = (
            _border_tie_candidates(grid, regions)
            if border_seeds
            else _interior_tie_candidates(grid, regions)
        )
        if not candidates:
            raise ValueError(
                "requested topology has no room for the required color-tie witness"
            )
        first, middle, second, region_index = rng.choice(candidates)
        positions.extend([(first, region_index), (second, region_index)])
        reserved_zero.add(middle)
    elif border_seeds:
        candidates = _border_tie_candidates(grid, regions)
        if not candidates:
            raise ValueError("requested border seed has no lawful inward chamber cell")
        border, _middle, _inner, region_index = rng.choice(candidates)
        positions.append((border, region_index))

    occupied = {cell for cell, _ in positions}
    seeded_regions = {region_index for _, region_index in positions}

    # First satisfy the chamber-locality invariant.
    for region_index, region in enumerate(regions):
        if region_index in seeded_regions:
            continue
        choices = [
            cell
            for cell in region
            if grid[cell[0]][cell[1]] == 0
            and cell not in occupied
            and cell not in reserved_zero
        ]
        if not choices:
            raise ValueError(f"chamber {region_index} has no free seed position")
        cell = rng.choice(choices)
        positions.append((cell, region_index))
        occupied.add(cell)
        seeded_regions.add(region_index)

    # Then spread remaining seeds across chambers rather than clustering all
    # extras in the first rectangle.
    while len(positions) < n_seeds:
        chamber_order = list(range(n_chambers))
        rng.shuffle(chamber_order)
        placed = False
        for region_index in chamber_order:
            choices = [
                cell
                for cell in regions[region_index]
                if grid[cell[0]][cell[1]] == 0
                and cell not in occupied
                and cell not in reserved_zero
            ]
            if choices:
                cell = rng.choice(choices)
                positions.append((cell, region_index))
                occupied.add(cell)
                placed = True
                break
        if not placed:
            raise ValueError(
                f"{len(positions)} seed positions fit, requested {n_seeds}"
            )

    if len(positions) != n_seeds:
        raise RuntimeError("internal seed-placement count mismatch")

    colors = list(palette)
    if tie_possible:
        # The first pair forms the equal-distance witness. Randomize which side
        # holds the smaller color so a fixed-position shortcut fails.
        pair = colors[:2]
        if rng.random() < 0.5:
            pair.reverse()
        color_plan = pair + colors[2:]
    else:
        color_plan = colors[:]
    while len(color_plan) < n_seeds:
        color_plan.append(colors[len(color_plan) % len(colors)])
    # Keep the tie pair fixed, but shuffle all remaining assignments.
    suffix_start = 2 if tie_possible else 0
    suffix = color_plan[suffix_start:]
    rng.shuffle(suffix)
    color_plan[suffix_start:] = suffix

    for ((r, c), _region_index), color in zip(positions, color_plan, strict=True):
        grid[r][c] = color

    observed = observe_overrides(grid)
    expected = {
        "n_chambers": n_chambers,
        "n_seeds": n_seeds,
        "palette_size": len(palette),
        "border_seeds": border_seeds,
    }
    for key, value in expected.items():
        if observed.get(key) != value:
            raise RuntimeError(
                f"seed placement observed {key}={observed.get(key)!r}, expected {value}"
            )


def _has_cross_chamber_rebuttal(grid: list[list[int]]) -> bool:
    """Whether a global-nearest shortcut gives a different answer somewhere.

    The intended oracle first restricts seeds to the zero cell's 4-connected
    non-9 chamber.  This witness finds a zero for which ignoring walls would
    select a differently colored seed from another chamber.
    """
    regions = _regions(grid)
    if len(regions) < 2:
        return False
    cell_region = _cell_to_region(regions)
    seeds = [
        (r, c, grid[r][c], cell_region[(r, c)])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 9)
    ]
    for (r, c), region_index in cell_region.items():
        if grid[r][c] != 0:
            continue
        local = [seed for seed in seeds if seed[3] == region_index]
        local_best = min(
            (abs(r - sr) + abs(c - sc), color, sr, sc)
            for sr, sc, color, _ in local
        )
        global_best = min(
            (abs(r - sr) + abs(c - sc), color, sr, sc, owner)
            for sr, sc, color, owner in seeds
        )
        if global_best[4] != region_index and global_best[1] != local_best[1]:
            return True
    return False


def _fill_with(
    grid: list[list[int]],
    *,
    restrict_to_chamber: bool,
    distance,
    tie_color,
) -> list[list[int]]:
    """Shared fill engine for the mirror and its competitors (pure)."""
    h, w = len(grid), len(grid[0])
    regions = _regions(grid)
    cell_region = _cell_to_region(regions)
    seeds = [
        (r, c, grid[r][c], cell_region[(r, c)])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 9)
    ]
    out = [row[:] for row in grid]
    for region_index, region in enumerate(regions):
        for r, c in region:
            if grid[r][c] != 0:
                continue
            pool = (
                [s for s in seeds if s[3] == region_index]
                if restrict_to_chamber
                else seeds
            )
            if not pool:
                continue  # canonical rule leaves seedless chambers unchanged
            best = min(
                pool,
                key=lambda s: (distance(r, c, s[0], s[1]), tie_color(s[2]), s[0], s[1]),
            )
            out[r][c] = best[2]
    return out


def _manhattan(r, c, sr, sc):
    return abs(r - sr) + abs(c - sc)


def _chebyshev(r, c, sr, sc):
    return max(abs(r - sr), abs(c - sc))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror of the canonical rule; Racket is authoritative.

    Each zero takes the colour of the Manhattan-nearest seed IN ITS OWN
    4-connected non-9 chamber; ties break by smaller colour, then row, then
    column.  Walls and seeds are copied unchanged.
    """
    errors, facts = _facts(grid)
    if facts is None:
        raise ValueError("; ".join(errors))
    return _fill_with(
        grid,
        restrict_to_chamber=True,
        distance=_manhattan,
        tie_color=lambda v: v,
    )


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold check (SEMANTIC_GATE_CONTRACT hook 1).

    The full teaching grammar plus a reviewer-level constraint the grammar
    does not state: the outer boundary must be sealed — every border cell is
    a 9-wall or an embedded seed, never a fillable zero.  All three canonical
    inputs (including the border-seed test pair) satisfy this.
    """
    errors, facts = _facts(grid)
    reasons = list(errors)
    if facts is None or reasons:
        return reasons
    h, w = facts["grid_h"], facts["grid_w"]
    for r in range(h):
        for c in range(w):
            if (r in (0, h - 1) or c in (0, w - 1)) and grid[r][c] == 0:
                reasons.append(
                    f"border cell ({r},{c}) is a fillable zero; the canonical "
                    "boundary is sealed by walls or embedded seeds"
                )
                return reasons
    return reasons


def _facts_or_none(grid):
    errors, facts = _facts(grid)
    return None if (facts is None or errors) else facts


def _witness_cross_wall(grid) -> bool:
    """A zero cell whose globally-nearest seed sits in ANOTHER chamber and has
    a different colour than its in-chamber answer — the counterexample that
    rebuts the wall-blind global-nearest shortcut."""
    return _facts_or_none(grid) is not None and _has_cross_chamber_rebuttal(grid)


def _witness_color_tie(grid) -> bool:
    """A zero cell equidistant from two differently-coloured nearest seeds in
    its own chamber, so the smaller-colour tie-break is load-bearing."""
    facts = _facts_or_none(grid)
    if facts is None:
        return False
    cell_region = _cell_to_region(facts["regions"])
    seeds_by_region: dict[int, list[tuple[int, int, int]]] = {}
    for r, c, color in facts["seeds"]:
        seeds_by_region.setdefault(cell_region[(r, c)], []).append((r, c, color))
    for region_index, region in enumerate(facts["regions"]):
        seeds = seeds_by_region.get(region_index, [])
        if len(seeds) < 2:
            continue
        for r, c in region:
            if grid[r][c] != 0:
                continue
            distances = [(_manhattan(r, c, sr, sc), color) for sr, sc, color in seeds]
            best = min(d for d, _ in distances)
            nearest_colors = {color for d, color in distances if d == best}
            if len(nearest_colors) >= 2:
                return True
    return False


def _witness_multi_chamber(grid) -> bool:
    facts = _facts_or_none(grid)
    return facts is not None and facts["n_chambers"] >= 2


def _witness_border_seed(grid) -> bool:
    """A coloured seed embedded in the outer wall — the canonical test branch."""
    facts = _facts_or_none(grid)
    return facts is not None and facts["border_seeds"] >= 1


SEMANTIC_WITNESSES = {
    "cross_wall_locality_counterexample": _witness_cross_wall,
    "equal_distance_smaller_color_tie": _witness_color_tie,
    "multi_chamber_partition": _witness_multi_chamber,
    "border_embedded_seed": _witness_border_seed,
}


_COMPETING_RULES = {
    "global_nearest_ignores_walls": lambda g: _fill_with(
        g, restrict_to_chamber=False, distance=_manhattan, tie_color=lambda v: v
    ),
    "chebyshev_nearest_in_chamber": lambda g: _fill_with(
        g, restrict_to_chamber=True, distance=_chebyshev, tie_color=lambda v: v
    ),
    "larger_color_wins_ties": lambda g: _fill_with(
        g, restrict_to_chamber=True, distance=_manhattan, tie_color=lambda v: -v
    ),
    "copy_input_unchanged": lambda g: [row[:] for row in g],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Demos must pin chamber-local Manhattan fill with smaller-colour ties
    against the documented shortcuts (SEMANTIC_GATE_CONTRACT hook 3)."""
    reasons: list[str] = []
    episodes = list(demos) + [query]
    labels = [f"demo {i}" for i in range(len(demos))] + ["query"]
    for label, episode in zip(labels, episodes):
        errors, facts = _facts(episode.get("input"))
        if facts is None:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
    if reasons:
        return reasons
    for i, demo in enumerate(demos):
        if demo.get("output") != rule_mirror(demo["input"]):
            reasons.append(f"demo {i}: output does not match the task rule")
    if reasons:
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query: provided output does not match the task rule")
    for name, competitor in _COMPETING_RULES.items():
        if all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a "
                "different query answer"
            )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if band not in ("easy", "medium", "hard"):
        band = "medium"

    declared = set(AXES)
    unknown = sorted(k for k, value in overrides.items() if value is not None and k not in declared)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    explicit = {k for k, value in overrides.items() if value is not None}
    # Sequential lesson schedule (3 demos + query): slots 0 and 2 are forced
    # multi-chamber locality witnesses; slot 1 is a canonical-scale example
    # with the official border-seed branch; slot 3 stays varied. Exact
    # overrides bypass the schedule and retain full-domain behavior.
    schedule_slot = int(sample_index) % 4
    scheduled_canonical = not explicit and schedule_slot == 1
    forced_multi = not explicit and schedule_slot in (0, 2)
    canonical_prior = scheduled_canonical or (
        not explicit and schedule_slot == 3 and rng.random() < _CANONICAL_PRIOR
    )

    if canonical_prior:
        h0, w0 = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n_chambers = ctx.draw_int("n_chambers", 1, 1)
        n_seeds = ctx.draw_int("n_seeds", 2, 2)
        palette_size = ctx.draw_int("palette_size", 2, 2)
        border_seeds = ctx.draw_int(
            "border_seeds", 1, 1
        ) if scheduled_canonical else ctx.draw_int("border_seeds", 0, 1)
    else:
        if band == "easy":
            h_band, w_band, chamber_band, seed_band, palette_hi = (6, 10), (8, 12), (1, 2), (3, 5), 3
        elif band == "hard":
            h_band, w_band, chamber_band, seed_band, palette_hi = (11, 16), (13, 18), (2, 4), (5, 8), 6
        else:
            h_band, w_band, chamber_band, seed_band, palette_hi = (8, 13), (10, 15), (1, 3), (4, 7), 5

        h = _draw_axis_int(ctx, overrides, "grid_h", *h_band, *_H_RANGE)
        w = _draw_axis_int(ctx, overrides, "grid_w", *w_band, *_W_RANGE)

        requested_seeds = (
            int(overrides["n_seeds"])
            if overrides.get("n_seeds") is not None
            else None
        )
        if overrides.get("n_chambers") is not None:
            n_chambers = ctx.draw_int("n_chambers", *_CHAMBER_RANGE)
        else:
            chamber_lo, chamber_hi = chamber_band
            if forced_multi:
                chamber_lo = max(2, chamber_lo)
            if requested_seeds is not None:
                chamber_hi = min(chamber_hi, requested_seeds)
                chamber_lo = min(chamber_lo, chamber_hi)
            n_chambers = ctx.draw_int("n_chambers", chamber_lo, chamber_hi)

        requested_palette = (
            int(overrides["palette_size"])
            if overrides.get("palette_size") is not None
            else None
        )
        if requested_seeds is not None:
            n_seeds = ctx.draw_int("n_seeds", *_SEED_RANGE)
            if n_seeds < n_chambers:
                raise ValueError(
                    f"n_seeds={n_seeds} cannot seed n_chambers={n_chambers}"
                )
            if requested_palette is not None and requested_palette > n_seeds:
                raise ValueError(
                    f"palette_size={requested_palette} exceeds n_seeds={n_seeds}"
                )
        else:
            seed_lo = max(seed_band[0], n_chambers + 1)
            if requested_palette is not None:
                seed_lo = max(seed_lo, requested_palette)
            seed_hi = max(seed_lo, seed_band[1])
            if seed_hi > _SEED_RANGE[1]:
                raise ValueError("requested axes need more than eight seeds")
            n_seeds = ctx.draw_int("n_seeds", seed_lo, seed_hi)

        if overrides.get("palette_size") is not None:
            palette_size = ctx.draw_int("palette_size", *_PALETTE_RANGE)
            if palette_size > n_seeds:
                raise ValueError(
                    f"palette_size={palette_size} exceeds n_seeds={n_seeds}"
                )
        else:
            palette_size = ctx.draw_int(
                "palette_size", 2, min(palette_hi, n_seeds, _PALETTE_RANGE[1])
            )
        border_seeds = _draw_axis_int(
            ctx,
            overrides,
            "border_seeds",
            *_BORDER_SEED_RANGE,
            *_BORDER_SEED_RANGE,
        )

    wall_grid = _build_walls(h, w, n_chambers, rng)
    palette = ctx.draw_distinct_colors(
        "seed_colors", n=palette_size, exclude={0, 9}
    )
    placement_rng = ctx.draw_rng("seed_placement")
    # On ordinary multi-chamber draws, require a concrete counterexample to
    # the tempting global-nearest shortcut.  Exact override combinations are
    # still honored even when their tight counts happen not to permit one.
    require_cross_rebuttal = not explicit and n_chambers > 1
    grid = None
    for _attempt in range(128):
        candidate = [row[:] for row in wall_grid]
        _place_seeds(
            candidate,
            n_seeds=n_seeds,
            palette=palette,
            border_seeds=border_seeds,
            rng=placement_rng,
        )
        if not require_cross_rebuttal or _has_cross_chamber_rebuttal(candidate):
            grid = candidate
            break
    if grid is None:
        raise RuntimeError(
            "could not construct a multi-chamber global-nearest rebuttal "
            "within 128 deterministic attempts"
        )

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"generator built an invalid lesson: {findings}")
    return grid
