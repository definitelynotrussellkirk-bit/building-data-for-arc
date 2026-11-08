"""Generator for ARC task b6edfc119780 — longest closed row wins.

For every occupied row, close the inclusive horizontal interval between its
leftmost and rightmost nonzero markers.  Select the row with the longest
interval; when several rows tie, the canonical Racket authority selects the
topmost tied row.  Emit only that interval as cyan (8) on a blank grid.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6edfc119780"
TASK_ID = "b6edfc119780"
# 2.0.0: rebuild the teaching distribution around the executable rule.  The
# prior generator silently ignored four declared axes, made color 2 the winner
# on every draw, required a unique maximum even though a canonical train pair
# contains a topmost-resolved tie, and had a nearly toothless self_check.
VERSION = "2.0.0"
RULE_HASH = "ec0b18e51f58"

SUMMARY = (
    "Close each occupied row from its leftmost to rightmost marker, compare "
    "the inclusive span lengths, and output the longest span as cyan (8) on "
    "a blank same-size grid. If maximum spans tie, choose the topmost tied row."
)

INVARIANTS = [
    "background is 0 and every active row has 2..4 same-color markers",
    "there are 3..5 active rows and at least one row is strictly shorter than the maximum",
    "the maximum is either unique or shared by exactly two rows",
    "a tied maximum is resolved by selecting the topmost tied row",
    "marker color and marker count do not determine the selected row",
]

AXES = {
    "height": {
        "type": "int",
        "default": "difficulty-aware 6..14 with a scheduled canonical-profile anchor",
        "valid": "6..14",
    },
    "width": {
        "type": "int",
        "default": "difficulty-aware 8..16 with a scheduled canonical-profile anchor",
        "valid": "8..16",
    },
    "num_active_rows": {
        "type": "int",
        "default": "sample_index schedule covering 3..5",
        "valid": "3..5",
    },
    "winner_rank": {
        "type": "int",
        "default": "sample_index schedule over every reading-order active-row rank",
        "valid": "0..4",
    },
    "tie_mode": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "unique|top_tie",
    },
    "color_mode": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "monochrome|winner_shared|all_distinct",
    },
    "marker_mode": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "endpoints_only|loser_dense|winner_dense",
    },
}

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_DIMS = ((8, 10), (9, 11), (8, 12))

# Slots 0..2 are the three default demonstrations and slot 3 is the default
# query.  Together they explicitly falsify marker-count, fixed-row, color-2,
# first-two-markers, and unique-maximum shortcuts.  The remaining slots close
# the full (num_active_rows, winner_rank) codomain.
_DEFAULT_SCHEDULE = (
    (4, 1, "unique",  "all_distinct", "loser_dense"),
    (3, 0, "top_tie", "monochrome",   "endpoints_only"),
    (5, 4, "unique",  "winner_shared", "winner_dense"),
    (4, 2, "top_tie", "all_distinct", "endpoints_only"),
    (3, 1, "top_tie", "winner_shared", "loser_dense"),
    (3, 2, "unique",  "monochrome",   "winner_dense"),
    (4, 0, "top_tie", "all_distinct", "loser_dense"),
    (4, 3, "unique",  "winner_shared", "endpoints_only"),
    (5, 0, "top_tie", "all_distinct", "winner_dense"),
    (5, 1, "top_tie", "monochrome",   "loser_dense"),
    (5, 2, "top_tie", "winner_shared", "endpoints_only"),
    (5, 3, "top_tie", "all_distinct", "winner_dense"),
)


def _validate_requested_axes(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")


def _effective_overrides(sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    """Resolve lawful defaults while keeping every declared axis typed/exact."""
    effective = dict(overrides)
    scheduled = _DEFAULT_SCHEDULE[int(sample_index) % len(_DEFAULT_SCHEDULE)]
    sched_rows, sched_rank, sched_tie, sched_color, sched_markers = scheduled

    requested_rows = effective.get("num_active_rows")
    requested_rank = effective.get("winner_rank")
    requested_tie = effective.get("tie_mode")

    if requested_rows is None and requested_rank is None:
        effective["num_active_rows"] = sched_rows
        # A single tie_mode override must be executable for every sample.
        # Clamp only the DEFAULT rank; explicit incompatible rank/count pairs
        # still reject loudly below.
        effective["winner_rank"] = (
            min(sched_rank, sched_rows - 2)
            if requested_tie == "top_tie"
            else sched_rank
        )
    elif requested_rows is None:
        rank = int(requested_rank)
        if not 0 <= rank <= 4:
            raise ValueError(f"winner_rank override {rank} outside 0..4")
        effective["num_active_rows"] = max(3, rank + 1)
    elif requested_rank is None:
        rows = int(requested_rows)
        if not 3 <= rows <= 5:
            raise ValueError(f"num_active_rows override {rows} outside 3..5")
        if requested_tie == "top_tie":
            effective["winner_rank"] = int(sample_index) % (rows - 1)
        else:
            effective["winner_rank"] = int(sample_index) % rows

    rows = int(effective["num_active_rows"])
    rank = int(effective["winner_rank"])
    if not 3 <= rows <= 5:
        raise ValueError(f"num_active_rows override {rows} outside 3..5")
    if not 0 <= rank < rows:
        raise ValueError(
            f"winner_rank={rank} is incompatible with num_active_rows={rows}"
        )

    if "tie_mode" not in effective or effective["tie_mode"] is None:
        effective["tie_mode"] = sched_tie if rank < rows - 1 else "unique"
    if effective["tie_mode"] == "top_tie" and rank >= rows - 1:
        raise ValueError(
            f"tie_mode='top_tie' requires a lower tied row; winner_rank={rank} "
            f"is last among {rows} active rows"
        )

    effective.setdefault("color_mode", sched_color)
    effective.setdefault("marker_mode", sched_markers)

    # One third of ordinary draws are anchored to one of the three official
    # (height, width, palette-size) profiles.  Pin the otherwise-free color
    # mode to monochrome on those draws so the exact two-color input profile
    # is observable at a comfortable margin above the 25% envelope floor.
    if (
        effective.get("height") is None
        and effective.get("width") is None
        and int(sample_index) % 3 == 1
    ):
        h, w = _CANONICAL_DIMS[(int(sample_index) // 3) % len(_CANONICAL_DIMS)]
        effective["height"] = h
        effective["width"] = w
        if overrides.get("color_mode") is None:
            effective["color_mode"] = "monochrome"
    return effective


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket program is the oracle."""
    _validate_requested_axes(overrides)
    effective = _effective_overrides(int(sample_index), overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    # Full declared ranges remain legal in every difficulty band.  Difficulty
    # only changes the draw distribution, never the override contract.
    height = ctx.draw_int_diff("height", 6, 14)
    width = ctx.draw_int_diff("width", 8, 16)
    n_rows = ctx.draw_int("num_active_rows", 3, 5)
    winner_rank = ctx.draw_int("winner_rank", 0, n_rows - 1)
    tie_mode = ctx.draw_choice("tie_mode", ("unique", "top_tie"))
    color_mode = ctx.draw_choice(
        "color_mode", ("monochrome", "winner_shared", "all_distinct")
    )
    marker_mode = ctx.draw_choice(
        "marker_mode", ("endpoints_only", "loser_dense", "winner_dense")
    )

    if tie_mode == "top_tie" and winner_rank >= n_rows - 1:
        raise ValueError(
            f"tie_mode='top_tie' incompatible with winner_rank={winner_rank} "
            f"and num_active_rows={n_rows}"
        )

    row_rng = ctx.draw_rng("active_rows")
    active_rows = sorted(row_rng.sample(range(height), n_rows))

    span_rng = ctx.draw_rng("span_lengths")
    winner_len = span_rng.randint(5, width - 1)
    lengths = [0] * n_rows
    lengths[winner_rank] = winner_len
    tied_rank = None
    if tie_mode == "top_tie":
        tied_rank = winner_rank + 1
        lengths[tied_rank] = winner_len

    dense_loser_rank = None
    if marker_mode == "loser_dense":
        if tied_rank is not None:
            dense_loser_rank = tied_rank
        else:
            dense_loser_rank = next(
                rank for rank in range(n_rows) if rank != winner_rank
            )
            lengths[dense_loser_rank] = winner_len - 1

    for rank in range(n_rows):
        if lengths[rank]:
            continue
        upper = winner_len - 1
        if dense_loser_rank is not None and rank != dense_loser_rank:
            upper = min(upper, winner_len - 2)
        lengths[rank] = span_rng.randint(2, max(2, upper))

    colors = _assign_colors(
        n_rows=n_rows,
        winner_rank=winner_rank,
        mode=color_mode,
        rng=ctx.draw_rng("row_colors"),
    )

    grid = full_grid(height, width, 0)
    placement_slot = int(sample_index) % 3
    placement_rng = ctx.draw_rng("span_positions")
    for rank, (row, span_len, color) in enumerate(
        zip(active_rows, lengths, colors)
    ):
        if rank == winner_rank:
            start = _scheduled_winner_start(width, span_len, placement_slot)
        else:
            start = placement_rng.randint(0, width - span_len)
        end = start + span_len - 1
        marker_columns = [start, end]
        if marker_mode == "winner_dense" and rank == winner_rank:
            marker_columns.append(start + span_len // 2)
        elif marker_mode == "loser_dense" and rank == dense_loser_rank:
            marker_columns.extend((start + 1, end - 1))
        for column in sorted(set(marker_columns)):
            grid[row][column] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator error: {errors}")
    return grid


def _scheduled_winner_start(width: int, span_len: int, slot: int) -> int:
    max_start = width - span_len
    if slot == 0:
        return 0
    if slot == 1:
        return max_start // 2
    return max_start


def _assign_colors(*, n_rows: int, winner_rank: int, mode: str, rng) -> list[int]:
    if mode == "monochrome":
        color = rng.choice(_MARKER_COLORS)
        return [color] * n_rows

    loser_ranks = [rank for rank in range(n_rows) if rank != winner_rank]
    winner_color = rng.choice(tuple(c for c in _MARKER_COLORS if c != 2))
    colors: list[int | None] = [None] * n_rows
    colors[winner_rank] = winner_color

    if mode == "all_distinct":
        colors[loser_ranks[0]] = 2
        remaining = [
            c for c in _MARKER_COLORS if c not in (2, winner_color)
        ]
        rng.shuffle(remaining)
        for rank, color in zip(loser_ranks[1:], remaining):
            colors[rank] = color
    elif mode == "winner_shared":
        colors[loser_ranks[0]] = winner_color
        colors[loser_ranks[1]] = 2
        remaining = [
            c for c in _MARKER_COLORS if c not in (2, winner_color)
        ]
        rng.shuffle(remaining)
        for rank, color in zip(loser_ranks[2:], remaining):
            colors[rank] = color
    else:
        raise ValueError(f"unsupported color_mode {mode!r}")
    return [int(color) for color in colors]


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return ["grid must be nonempty and rectangular"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _records(grid) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row_index, row in enumerate(grid):
        columns = [column for column, value in enumerate(row) if value != 0]
        if not columns:
            continue
        colors = sorted({row[column] for column in columns})
        records.append(
            {
                "row": row_index,
                "columns": columns,
                "colors": colors,
                "color": colors[0] if len(colors) == 1 else None,
                "count": len(columns),
                "start": columns[0],
                "end": columns[-1],
                "span_len": columns[-1] - columns[0] + 1,
            }
        )
    return records


def _analysis(grid) -> dict[str, Any]:
    records = _records(grid)
    if not records:
        return {"records": [], "max_len": None, "max_ranks": [], "winner_rank": None}
    max_len = max(record["span_len"] for record in records)
    max_ranks = [
        rank for rank, record in enumerate(records) if record["span_len"] == max_len
    ]
    return {
        "records": records,
        "max_len": max_len,
        "max_ranks": max_ranks,
        "winner_rank": max_ranks[0],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting all official inputs."""
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 14:
        errors.append(f"height must be 6..14, got {height}")
    if not 8 <= width <= 16:
        errors.append(f"width must be 8..16, got {width}")

    analysis = _analysis(grid)
    records = analysis["records"]
    if not 3 <= len(records) <= 5:
        errors.append(f"expected 3..5 active rows, found {len(records)}")
        return errors

    for record in records:
        if len(record["colors"]) != 1:
            errors.append(
                f"row {record['row']} mixes marker colors {record['colors']}"
            )
        if not 2 <= record["count"] <= 4:
            errors.append(
                f"row {record['row']} must contain 2..4 markers, got {record['count']}"
            )
        if record["span_len"] < 2:
            errors.append(f"row {record['row']} has no endpoint span")

    max_ranks = analysis["max_ranks"]
    if analysis["max_len"] is not None and analysis["max_len"] < 4:
        errors.append("longest span must be at least four cells")
    if len(max_ranks) not in (1, 2):
        errors.append(
            f"maximum span must be unique or a two-row tie, got {len(max_ranks)} rows"
        )
    if records and all(
        record["span_len"] == analysis["max_len"] for record in records
    ):
        errors.append("at least one active row must be shorter than the maximum")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    if self_check(grid):
        return {}
    analysis = _analysis(grid)
    records = analysis["records"]
    winner_rank = int(analysis["winner_rank"])
    winner_color = records[winner_rank]["color"]
    color_counts = Counter(record["color"] for record in records)
    if len(color_counts) == 1:
        color_mode = "monochrome"
    elif len(color_counts) == len(records):
        color_mode = "all_distinct"
    elif (
        color_counts[winner_color] == 2
        and sorted(color_counts.values()) == [1] * (len(records) - 2) + [2]
    ):
        color_mode = "winner_shared"
    else:
        color_mode = "unknown"

    marker_counts = [record["count"] for record in records]
    if all(count == 2 for count in marker_counts):
        marker_mode = "endpoints_only"
    elif marker_counts[winner_rank] == 3 and all(
        count == 2 for rank, count in enumerate(marker_counts) if rank != winner_rank
    ):
        marker_mode = "winner_dense"
    elif marker_counts[winner_rank] == 2 and sum(
        count == 4 for rank, count in enumerate(marker_counts) if rank != winner_rank
    ) == 1 and all(
        count in (2, 4) for rank, count in enumerate(marker_counts) if rank != winner_rank
    ):
        marker_mode = "loser_dense"
    else:
        marker_mode = "unknown"

    return {
        "height": len(grid),
        "width": len(grid[0]),
        "num_active_rows": len(records),
        "winner_rank": winner_rank,
        "tie_mode": "unique" if len(analysis["max_ranks"]) == 1 else "top_tie",
        "color_mode": color_mode,
        "marker_mode": marker_mode,
    }


def semantic_observables(grid) -> dict[str, Any]:
    """Task-linked facts describing the exact output grammar."""
    errors = self_check(grid)
    if errors:
        return {"valid": False, "errors": errors}
    analysis = _analysis(grid)
    records = analysis["records"]
    winner_rank = analysis["winner_rank"]
    winner = records[winner_rank]
    return {
        "valid": True,
        **observe_overrides(grid),
        "active_grid_rows": [record["row"] for record in records],
        "span_lengths": [record["span_len"] for record in records],
        "marker_counts": [record["count"] for record in records],
        "row_colors": [record["color"] for record in records],
        "max_tie_count": len(analysis["max_ranks"]),
        "winner_grid_row": winner["row"],
        "winner_start": winner["start"],
        "winner_end": winner["end"],
        "winner_span_len": winner["span_len"],
        "output_signature": (
            len(grid), len(grid[0]), winner["row"], winner["start"], winner["end"]
        ),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analysis(grid)
    winner = analysis["records"][analysis["winner_rank"]]
    output = full_grid(len(grid), len(grid[0]), 0)
    for column in range(winner["start"], winner["end"] + 1):
        output[winner["row"]][column] = 8
    return output


def strict_canonical_like(grid) -> list[str]:
    return list(self_check(grid))


def _lawful_obs(grid) -> dict[str, Any] | None:
    obs = semantic_observables(grid)
    return obs if obs.get("valid") else None


def _witness(grid, predicate) -> bool:
    obs = _lawful_obs(grid)
    return False if obs is None else bool(predicate(obs))


SEMANTIC_WITNESSES = {
    "unique_longest": lambda grid: _witness(grid, lambda o: o["tie_mode"] == "unique"),
    "topmost_tie_break": lambda grid: _witness(grid, lambda o: o["tie_mode"] == "top_tie"),
    "monochrome_rows": lambda grid: _witness(grid, lambda o: o["color_mode"] == "monochrome"),
    "all_distinct_row_colors": lambda grid: _witness(grid, lambda o: o["color_mode"] == "all_distinct"),
    "winner_color_reused": lambda grid: _witness(grid, lambda o: o["color_mode"] == "winner_shared"),
    "endpoints_only": lambda grid: _witness(grid, lambda o: o["marker_mode"] == "endpoints_only"),
    "denser_loser_count_shortcut_rebuttal": lambda grid: _witness(grid, lambda o: o["marker_mode"] == "loser_dense"),
    "winner_has_interior_marker": lambda grid: _witness(grid, lambda o: o["marker_mode"] == "winner_dense"),
    "winner_first_active_row": lambda grid: _witness(grid, lambda o: o["winner_rank"] == 0),
    "winner_middle_active_row": lambda grid: _witness(grid, lambda o: 0 < o["winner_rank"] < o["num_active_rows"] - 1),
    "winner_last_active_row": lambda grid: _witness(grid, lambda o: o["winner_rank"] == o["num_active_rows"] - 1),
    "color_2_is_loser": lambda grid: _witness(
        grid,
        lambda o: 2 in o["row_colors"] and o["row_colors"][o["winner_rank"]] != 2,
    ),
    "left_anchored_output": lambda grid: _witness(grid, lambda o: o["winner_start"] == 0),
    "right_anchored_output": lambda grid: _witness(grid, lambda o: o["winner_end"] == o["width"] - 1),
    "interior_output": lambda grid: _witness(
        grid, lambda o: o["winner_start"] > 0 and o["winner_end"] < o["width"] - 1
    ),
}


def _paint_record(grid, record, *, start=None, end=None, color=8):
    output = full_grid(len(grid), len(grid[0]), 0)
    start = record["start"] if start is None else start
    end = record["end"] if end is None else end
    for column in range(start, end + 1):
        output[record["row"]][column] = color
    return output


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    if self_check(grid):
        return None
    analysis = _analysis(grid)
    records = analysis["records"]
    truth_rank = analysis["winner_rank"]
    truth = records[truth_rank]
    max_len = analysis["max_len"]
    first_max = truth_rank
    last_max = max(
        rank for rank, record in enumerate(records) if record["span_len"] == max_len
    )
    most_markers = max(range(len(records)), key=lambda rank: records[rank]["count"])
    shortest = min(range(len(records)), key=lambda rank: records[rank]["span_len"])
    color_two = next(
        (rank for rank, record in enumerate(records) if record["color"] == 2), 0
    )
    first_two_end = truth["columns"][1]

    all_max = full_grid(len(grid), len(grid[0]), 0)
    for record in records:
        if record["span_len"] == max_len:
            for column in range(record["start"], record["end"] + 1):
                all_max[record["row"]][column] = 8

    return {
        "topmost_active": _paint_record(grid, records[0]),
        "bottommost_active": _paint_record(grid, records[-1]),
        "most_markers": _paint_record(grid, records[most_markers]),
        "shortest_span": _paint_record(grid, records[shortest]),
        "color_2_priority": _paint_record(grid, records[color_two]),
        "bottommost_longest": _paint_record(grid, records[last_max]),
        "first_two_markers_only": _paint_record(
            grid, truth, start=truth["columns"][0], end=first_two_end
        ),
        "preserve_source_color": _paint_record(grid, truth, color=truth["color"]),
        "paint_all_maxima": all_max,
        # Explicit alias documents that stable topmost is the canonical tie rule.
        "first_longest": _paint_record(grid, records[first_max]),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut survives all demonstrations."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_competitors = _competitor_outputs(query_input)
    if query_competitors is None:
        return ["query input is not a lawful longest-row scene"]
    query_truth = rule_mirror(query_input)

    checked_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict):
            reasons.append(f"demo {index} is not a pair dict")
            continue
        inp = demo.get("input")
        competitors = _competitor_outputs(inp)
        if competitors is None:
            reasons.append(f"demo {index} input is not lawful")
            continue
        truth = rule_mirror(inp)
        if demo.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with the rule mirror")
            continue
        checked_demos.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name, query_output in sorted(query_competitors.items()):
        if name == "first_longest":
            continue  # canonical alias, not a competing rule
        survives = all(
            competitors[name] == demo["output"]
            for demo, competitors in checked_demos
        )
        if survives and query_output != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but changes the query answer"
            )
    return sorted(set(reasons))
