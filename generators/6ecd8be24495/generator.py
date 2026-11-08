"""Generator for ``Fill the chamber with the most seeds`` (6ecd8be24495).

Gray (5) walls split a bordered board into rectangular chambers.  Exactly one
chamber has strictly more nonzero seed cells than every other chamber; only its
zero cells are filled, using the unique majority seed color inside that
chamber.

The canonical examples use four equal chambers and monochromatic seed sets.
Normal generated lessons retain the same rule but also include mixed-color
winning chambers and a losing chamber with a stronger single-color pile.  That
pair of witnesses distinguishes "most total seeds, then local majority" from
both global-modal and strongest-monochromatic-pile shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6ecd8be24495"
TASK_ID = "6ecd8be24495"
VERSION = "2.0.2"  # strict integer overrides + distinct-color shortcut witness
RULE_HASH = "296d35a8cea3"

SUMMARY = (
    "Gray (5) walls partition a bordered grid into rectangular chambers. "
    "Count every nonzero, non-wall seed in each chamber, select the unique "
    "chamber with the greatest total seed count, find that chamber's unique "
    "majority seed color, and fill only its zero cells with that color."
)

INVARIANTS = [
    "the outer border and complete internal dividers are gray (5)",
    "the non-wall cells form two to four rectangular chambers",
    "every chamber contains at least one colored seed and at least one blank cell",
    "one chamber has strictly more total seeds than every other chamber",
    "the winning chamber has a unique majority seed color",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..18",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..18",
        "valid": "9..18",
    },
    "n_chambers": {
        "type": "int",
        "default": "sample_index cycle 2..4",
        "valid": "2..4",
    },
    "winner_rank": {
        "type": "int",
        "default": "sample_index cycle over reading-order chambers",
        "valid": "0..3",
    },
    "n_seed_colors": {
        "type": "int",
        "default": "sample_index cycle 2..4",
        "valid": "2..4",
    },
    "majority_margin": {
        "type": "int",
        "default": "sample_index cycle 1..3",
        "valid": "1..3",
    },
}

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CHAMBER_WINNER_SCHEDULE = (
    (2, 0), (2, 1),
    (3, 0), (3, 1), (3, 2),
    (4, 0), (4, 1), (4, 2), (4, 3),
)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, rule-identifying input grid.

    Explicit axis overrides are exact.  ``winner_rank`` values that require
    more chambers automatically raise the lower bound for an otherwise-free
    ``n_chambers`` draw; an explicitly incompatible pair rejects loudly.
    """
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for axis, value in overrides.items():
        if value is not None and AXES[axis]["type"] == "int" and type(value) is not int:
            raise TypeError(f"{axis} override must be an exact integer")

    requested_rank = overrides.get("winner_rank")
    if requested_rank is not None:
        requested_rank = int(requested_rank)
        if not 0 <= requested_rank <= 3:
            raise ValueError(f"winner_rank override {requested_rank} outside 0..3")

    # The count/rank pair is scheduled before constructing GenCtx so both
    # values still pass through public typed draws and appear in provenance.
    # A single winner_rank boundary override is always satisfiable; an
    # explicitly incompatible n_chambers/winner_rank pair rejects loudly.
    effective_overrides = dict(overrides)
    requested_chambers = effective_overrides.get("n_chambers")
    if requested_chambers is None and requested_rank is None:
        scheduled_chambers, scheduled_rank = _CHAMBER_WINNER_SCHEDULE[
            sample_index % len(_CHAMBER_WINNER_SCHEDULE)
        ]
        effective_overrides["n_chambers"] = scheduled_chambers
        effective_overrides["winner_rank"] = scheduled_rank
    elif requested_chambers is None:
        effective_overrides["n_chambers"] = max(2, requested_rank + 1)
    n_chambers_requested = int(effective_overrides["n_chambers"])
    if requested_rank is None and "winner_rank" not in effective_overrides:
        effective_overrides["winner_rank"] = sample_index % n_chambers_requested
    elif requested_rank is not None and requested_rank >= n_chambers_requested:
        raise ValueError(
            f"winner_rank={requested_rank} requires at least "
            f"{requested_rank + 1} chambers, got n_chambers={n_chambers_requested}"
        )
    if effective_overrides.get("n_seed_colors") is None:
        effective_overrides["n_seed_colors"] = 2 + (sample_index // 3) % 3
    if effective_overrides.get("majority_margin") is None:
        effective_overrides["majority_margin"] = 1 + (sample_index // 9) % 3

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int_diff("grid_h", 9, 18)
    w = ctx.draw_int_diff("grid_w", 9, 18)
    n_chambers = ctx.draw_int("n_chambers", 2, 4)
    winner_rank = ctx.draw_int("winner_rank", 0, n_chambers - 1)

    n_seed_colors = ctx.draw_int("n_seed_colors", 2, 4)
    majority_margin = ctx.draw_int("majority_margin", 1, 3)
    colors = ctx.draw_distinct_colors(
        "seed_palette", n=n_seed_colors, exclude=(0, 5)
    )

    grid, chambers, layout = _partition_grid(
        h, w, n_chambers, ctx.draw_rng("walls")
    )
    _plant_seeds(
        grid,
        chambers,
        winner_rank=winner_rank,
        colors=colors,
        majority_margin=majority_margin,
        rng=ctx.draw_rng("seeds"),
    )

    errors = _structure_errors(grid)
    if errors:
        raise AssertionError(
            f"internal generator error for layout={layout}: {errors}"
        )
    return grid


def _partition_grid(h: int, w: int, n_chambers: int, rng):
    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][0] = 5
        grid[r][w - 1] = 5
    for c in range(w):
        grid[0][c] = 5
        grid[h - 1][c] = 5

    if n_chambers == 2:
        layout = rng.choice(("rows", "columns"))
        if layout == "rows":
            wall = rng.randint(3, h - 4)
            for c in range(1, w - 1):
                grid[wall][c] = 5
        else:
            wall = rng.randint(3, w - 4)
            for r in range(1, h - 1):
                grid[r][wall] = 5
    elif n_chambers == 3:
        # A T divider preserves three rectangular chambers of area >=9 even
        # at the declared 9x9 minimum. Parallel three-strip layouts can create
        # a 1x7 chamber and silently make the 4-color/margin-3 boundary
        # impossible while leaving a blank cell.
        layout = "t"
        orientation = rng.choice(("vertical", "horizontal"))
        split_first_side = rng.choice((False, True))
        if orientation == "vertical":
            wall_c = rng.randint(4, w - 5)
            wall_r = rng.randint(4, h - 5)
            for r in range(1, h - 1):
                grid[r][wall_c] = 5
            if split_first_side:
                for c in range(1, wall_c):
                    grid[wall_r][c] = 5
            else:
                for c in range(wall_c + 1, w - 1):
                    grid[wall_r][c] = 5
        else:
            wall_r = rng.randint(4, h - 5)
            wall_c = rng.randint(4, w - 5)
            for c in range(1, w - 1):
                grid[wall_r][c] = 5
            if split_first_side:
                for r in range(1, wall_r):
                    grid[r][wall_c] = 5
            else:
                for r in range(wall_r + 1, h - 1):
                    grid[r][wall_c] = 5
    elif n_chambers == 4:
        layout = "cross"
        wall_r = rng.randint(4, h - 5)
        wall_c = rng.randint(4, w - 5)
        for c in range(1, w - 1):
            grid[wall_r][c] = 5
        for r in range(1, h - 1):
            grid[r][wall_c] = 5
    else:
        raise ValueError(f"n_chambers must be in 2..4, got {n_chambers}")

    chambers = _chambers(grid)
    if len(chambers) != n_chambers:
        raise AssertionError(
            f"partition produced {len(chambers)} chambers, expected {n_chambers}"
        )
    return grid, chambers, layout


def _plant_seeds(
    grid,
    chambers,
    *,
    winner_rank: int,
    colors: tuple[int, ...],
    majority_margin: int,
    rng,
) -> None:
    n_colors = len(colors)
    majority_color = rng.choice(colors)
    minority_colors = [color for color in colors if color != majority_color]
    rng.shuffle(minority_colors)

    losing_indices = [i for i in range(len(chambers)) if i != winner_rank]

    if n_colors >= 3 and len(chambers) >= 3:
        # Keep the winner's requested local-majority margin exact while making
        # a different losing chamber carry the broadest palette.  A second
        # losing chamber carries a stronger monochromatic pile.  Together
        # these witnesses break both "most distinct colors" and "strongest
        # color pile" shortcuts without changing the canonical task rule.
        winner_counts = {
            majority_color: majority_margin + 2,
            minority_colors[0]: 2,
        }
        winner_total = sum(winner_counts.values())
        shuffled_losers = list(losing_indices)
        rng.shuffle(shuffled_losers)
        distinct_index, peak_index = shuffled_losers[:2]
        peak_color = minority_colors[-1]
        special_counts = {
            distinct_index: {color: 1 for color in colors},
            peak_index: {peak_color: majority_margin + 3},
        }
    else:
        # The two-color / two-chamber boundary cannot host two independent
        # decoys while keeping the winner uniquely largest.  Preserve the
        # original compact grammar there.
        winner_counts = {majority_color: majority_margin + 1}
        winner_counts.update({color: 1 for color in minority_colors})
        winner_total = sum(winner_counts.values())
        peak_index = rng.choice(losing_indices)
        peak_color = rng.choice(minority_colors)
        peak_count = majority_margin + 2 if n_colors >= 3 else winner_total - 1
        special_counts = {peak_index: {peak_color: peak_count}}

    winner_cells = chambers[winner_rank]
    if winner_total >= len(winner_cells):
        raise ValueError(
            "requested winner grammar does not fit while leaving a blank cell: "
            f"area={len(winner_cells)}, seeds={winner_total}"
        )
    _paint_counts(grid, winner_cells, winner_counts, rng)

    for index in losing_indices:
        cells = chambers[index]
        capacity = len(cells) - 1  # every chamber must retain a blank cell
        if index in special_counts:
            counts = special_counts[index]
            total = sum(counts.values())
            if total >= winner_total or total > capacity:
                raise ValueError(
                    "shortcut witness does not fit below the winner total: "
                    f"rank={index}, area={len(cells)}, seeds={total}, winner={winner_total}"
                )
        else:
            upper = min(winner_total - 1, capacity)
            if upper < 1:
                raise ValueError("a losing chamber has no room for a seed and blank")
            total = rng.randint(1, upper)
            order = list(colors)
            rng.shuffle(order)
            counts = Counter()
            for _ in range(total):
                # Mildly concentrated distractors preserve local color
                # structure without making color identity predict the winner.
                color = order[0] if rng.random() < 0.65 else rng.choice(order)
                counts[color] += 1
            counts = dict(counts)
        _paint_counts(grid, cells, counts, rng)


def _paint_counts(grid, chamber_cells, counts: dict[int, int], rng) -> None:
    total = sum(counts.values())
    positions = _spread_positions(chamber_cells, total, rng)
    values = [color for color, count in counts.items() for _ in range(count)]
    rng.shuffle(values)
    for (r, c), color in zip(positions, values):
        grid[r][c] = color


def _spread_positions(cells: Iterable[tuple[int, int]], count: int, rng):
    """Prefer isolated seeds, then fill remaining requested cells."""
    pool = list(cells)
    rng.shuffle(pool)
    chosen: list[tuple[int, int]] = []
    for cell in pool:
        if all(abs(cell[0] - r) + abs(cell[1] - c) > 1 for r, c in chosen):
            chosen.append(cell)
            if len(chosen) == count:
                return chosen
    for cell in pool:
        if cell not in chosen:
            chosen.append(cell)
            if len(chosen) == count:
                return chosen
    raise ValueError(f"cannot place {count} seeds in chamber of area {len(pool)}")


def _chambers(grid) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    chambers: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            chambers.append(sorted(cells))
    return sorted(chambers, key=lambda cells: cells[0])


def _analysis(grid) -> dict[str, Any]:
    chambers = _chambers(grid)
    records = []
    for cells in chambers:
        seeds = [grid[r][c] for r, c in cells if grid[r][c] != 0]
        counts = Counter(seeds)
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        records.append(
            {
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "area": len(cells),
                "seed_total": len(seeds),
                "counts": dict(counts),
                "ordered_counts": ordered,
                "blank_count": sum(grid[r][c] == 0 for r, c in cells),
            }
        )

    totals = [record["seed_total"] for record in records]
    winner_rank = None
    if totals:
        maximum = max(totals)
        winners = [i for i, value in enumerate(totals) if value == maximum]
        if len(winners) == 1:
            winner_rank = winners[0]

    majority_color = None
    majority_margin = None
    if winner_rank is not None:
        ordered = records[winner_rank]["ordered_counts"]
        if ordered:
            top = ordered[0][1]
            second = ordered[1][1] if len(ordered) > 1 else 0
            if len(ordered) == 1 or top > second:
                majority_color = ordered[0][0]
                majority_margin = top - second

    wall_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    layout = _layout_name(grid)
    return {
        "chambers": records,
        "winner_rank": winner_rank,
        "majority_color": majority_color,
        "majority_margin": majority_margin,
        "seed_colors": sorted(
            {
                value
                for row in grid
                for value in row
                if value not in (0, 5)
            }
        ),
        "wall_cells": wall_cells,
        "layout": layout,
    }


def _layout_name(grid) -> str:
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(1, h - 1) if all(grid[r][c] == 5 for c in range(w))]
    full_cols = [c for c in range(1, w - 1) if all(grid[r][c] == 5 for r in range(h))]
    chamber_count = len(_chambers(grid))
    if full_rows and full_cols:
        return "cross"
    if chamber_count == 3 and (full_rows or full_cols):
        return "t"
    if full_rows:
        return "rows"
    if full_cols:
        return "columns"
    return "irregular"


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact non-dimension axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["winner_rank"] is None or analysis["majority_margin"] is None:
        return {}
    return {
        "n_chambers": len(analysis["chambers"]),
        "winner_rank": analysis["winner_rank"],
        "n_seed_colors": len(analysis["seed_colors"]),
        "majority_margin": analysis["majority_margin"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or semantically ambiguous lesson inputs."""
    return _structure_errors(grid)


def _structure_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    flat = [value for row in grid for value in row]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in flat):
        return ["grid colors must be integers"]
    if any(value < 0 or value > 9 for value in flat):
        return ["grid colors must stay in 0..9"]

    errors: list[str] = []
    if h < 3 or w < 3:
        errors.append("grid is too small to contain bordered chambers")
        return errors
    if not (
        all(grid[0][c] == 5 for c in range(w))
        and all(grid[h - 1][c] == 5 for c in range(w))
        and all(grid[r][0] == 5 for r in range(h))
        and all(grid[r][w - 1] == 5 for r in range(h))
    ):
        errors.append("outer border is not entirely gray (5)")

    analysis = _analysis(grid)
    chambers = analysis["chambers"]
    if not 2 <= len(chambers) <= 4:
        errors.append(f"expected 2..4 chambers, found {len(chambers)}")
        return errors

    if analysis["layout"] == "irregular":
        errors.append("walls do not form complete row/column dividers")

    # Every non-wall chamber in this task is a filled rectangle bounded by
    # complete walls; a hole/notch is a malformed recombination.
    for index, record in enumerate(chambers):
        r1, c1, r2, c2 = record["bbox"]
        expected = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        if set(record["cells"]) != expected:
            errors.append(f"chamber {index} is not rectangular")
        if record["seed_total"] == 0:
            errors.append(f"chamber {index} has no seed")
        if record["blank_count"] == 0:
            errors.append(f"chamber {index} has no blank cell to fill")

    if analysis["winner_rank"] is None:
        errors.append("there is no unique chamber with the most total seeds")
    elif analysis["majority_color"] is None:
        errors.append("the winning chamber has no unique majority seed color")
    return errors


def expected_output(grid):
    """Python mirror for tests and visual review; Racket remains authority."""
    errors = _structure_errors(grid)
    if errors:
        raise ValueError(f"invalid input: {errors}")
    analysis = _analysis(grid)
    winner = analysis["chambers"][analysis["winner_rank"]]
    color = analysis["majority_color"]
    output = [row[:] for row in grid]
    for r, c in winner["cells"]:
        if output[r][c] == 0:
            output[r][c] = color
    return output


def profile_signature(grid) -> tuple[Any, ...]:
    """Strict linked semantic profile used by count-backed review censuses."""
    analysis = _analysis(grid)
    winner_rank = analysis["winner_rank"]
    if winner_rank is None:
        return ("invalid",)
    winner = analysis["chambers"][winner_rank]
    losing = [
        record
        for index, record in enumerate(analysis["chambers"])
        if index != winner_rank
    ]
    winner_top = winner["ordered_counts"][0][1]
    losing_peak = max(
        record["ordered_counts"][0][1] for record in losing if record["ordered_counts"]
    )
    return (
        len(grid),
        len(grid[0]),
        analysis["layout"],
        len(analysis["chambers"]),
        winner_rank,
        tuple(record["seed_total"] for record in analysis["chambers"]),
        tuple(winner["ordered_counts"]),
        analysis["majority_margin"],
        len(analysis["seed_colors"]),
        losing_peak > winner_top,
        winner["area"],
    )


def semantic_observables(grid) -> dict[str, Any]:
    """Named task-linked observables for reports and focused tests."""
    analysis = _analysis(grid)
    winner_rank = analysis["winner_rank"]
    winner = analysis["chambers"][winner_rank] if winner_rank is not None else None
    losing = [
        record
        for index, record in enumerate(analysis["chambers"])
        if index != winner_rank
    ]
    winner_top = winner["ordered_counts"][0][1] if winner else 0
    losing_peak = max(
        (record["ordered_counts"][0][1] for record in losing if record["ordered_counts"]),
        default=0,
    )
    return {
        "layout": analysis["layout"],
        "n_chambers": len(analysis["chambers"]),
        "winner_rank": winner_rank,
        "seed_totals": [record["seed_total"] for record in analysis["chambers"]],
        "winner_color_counts": dict(winner["counts"]) if winner else {},
        "majority_color": analysis["majority_color"],
        "majority_margin": analysis["majority_margin"],
        "n_seed_colors": len(analysis["seed_colors"]),
        "losing_peak_exceeds_winner_majority": losing_peak > winner_top,
        "winner_area": winner["area"] if winner else None,
        "changed_cells": sum(
            a != b
            for row_a, row_b in zip(grid, expected_output(grid))
            for a, b in zip(row_a, row_b)
        ) if winner else 0,
    }


def mutation_fixtures():
    """Task-specific malformed lessons that ``self_check`` must reject."""
    no_walls = full_grid(9, 9, 0)
    no_walls[2][2] = 1
    no_walls[4][4] = 2

    no_seeds, _, _ = _partition_grid(9, 9, 4, _FixtureRng())

    tied, chambers, _ = _partition_grid(9, 9, 2, _FixtureRng())
    for index, cells in enumerate(chambers):
        tied[cells[0][0]][cells[0][1]] = 1 + index
        tied[cells[1][0]][cells[1][1]] = 1 + index

    majority_tie, chambers, _ = _partition_grid(9, 9, 2, _FixtureRng())
    left, right = chambers
    for cell, color in zip(left[:4], (1, 1, 2, 2)):
        majority_tie[cell[0]][cell[1]] = color
    for cell, color in zip(right[:3], (3, 3, 3)):
        majority_tie[cell[0]][cell[1]] = color

    broken_border, chambers, _ = _partition_grid(9, 9, 2, _FixtureRng())
    broken_border[0][4] = 0
    for cell, color in zip(chambers[0][:3], (1, 1, 2)):
        broken_border[cell[0]][cell[1]] = color
    broken_border[chambers[1][0][0]][chambers[1][0][1]] = 3

    return [
        ("no_gray_walls", no_walls),
        ("no_seeds", no_seeds),
        ("tied_chamber_totals", tied),
        ("winner_majority_tie", majority_tie),
        ("broken_outer_border", broken_border),
    ]


class _FixtureRng:
    """Tiny deterministic chooser used only to build static mutation fixtures."""

    @staticmethod
    def choice(values):
        return list(values)[0]

    @staticmethod
    def randint(lo, hi):
        return (lo + hi) // 2
