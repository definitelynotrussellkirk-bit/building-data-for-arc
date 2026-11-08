"""Semantic generator for ARC task 8af64ebfaf77.

The input is exactly four equal horizontal panels separated by three full
color-5 columns.  The first panel contains one cell whose color is the query
color.  Return the candidate panel (panels 1..3) containing the most cells of
that color.  The maximum is unique in every lawful generated lesson.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8af64ebfaf77"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c50711c735d9"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Split the grid into exactly four equal panels at the three full color-5 "
    "separator columns. The first panel is a one-cell query-color key. Count "
    "that color in each of the three candidate panels and return the unique "
    "candidate with the largest count; other colors are distractors."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "exactly four equal panels are separated by three full-height color-5 columns",
    "the first panel contains exactly one nonzero cell, which defines the query color",
    "all three candidates contain the query color and have pairwise-distinct query counts",
    "the query-count maximum is unique",
    "when distractors occur, a losing panel has more total foreground than the winner",
    "the four-sample schedule covers first, middle, and last candidate winners",
]

AXES = {
    "panel_h": {
        "type": "int",
        "default": "slot 0/3 canonical 3; otherwise difficulty-weighted",
        "valid": "3..7",
    },
    "panel_w": {
        "type": "int",
        "default": "slot 0/3 canonical 3; otherwise difficulty-weighted",
        "valid": "3..6",
    },
    "query_color": {
        "type": "int",
        "default": "rng 1..9",
        "valid": "1..9",
    },
    "winner_index": {
        "type": "int",
        "default": "sample_index schedule 0,1,2,1",
        "valid": "0..2",
    },
    "distractor_mode": {
        "type": "str",
        "default": "sample_index schedule none,count_trap,none,none",
        "valid": ["none", "count_trap"],
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_SEPARATOR_COLOR = 5
_N_PANELS = 4
_WINNER_SCHEDULE = (0, 1, 2, 1)
_DISTRACTOR_SCHEDULE = ("none", "count_trap", "none", "none")


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _weighted_values(band: str, axis: str) -> list[int]:
    # Every legal boundary remains available in every band, while ordinary
    # hard draws trend larger. Canonical schedule slots override these to 3.
    if axis == "panel_h":
        return {
            "easy": [3, 3, 3, 4, 4, 5, 6, 7],
            "medium": [3, 3, 4, 4, 5, 5, 6, 7],
            "hard": [3, 4, 5, 5, 6, 6, 7, 7],
        }[band]
    return {
        "easy": [3, 3, 3, 4, 4, 5, 6],
        "medium": [3, 3, 4, 4, 5, 5, 6],
        "hard": [3, 4, 4, 5, 5, 6, 6],
    }[band]


def _split_panels(grid: list[list[int]], panel_w: int) -> list[list[list[int]]]:
    return [
        [row[index * (panel_w + 1): index * (panel_w + 1) + panel_w] for row in grid]
        for index in range(_N_PANELS)
    ]


def _nonzero_count(panel: list[list[int]]) -> int:
    return sum(value != 0 for row in panel for value in row)


def _color_count(panel: list[list[int]], color: int) -> int:
    return sum(value == color for row in panel for value in row)


def _first_nonzero(panel: list[list[int]]) -> int | None:
    for row in panel:
        for value in row:
            if value != 0:
                return value
    return None


def _sample_positions(rng, height: int, width: int, count: int, *, color: int) -> list[tuple[int, int]]:
    """Sample cells without accidentally creating a non-separator full 5 column."""
    positions = [(row, col) for row in range(height) for col in range(width)]
    for _ in range(100):
        rng.shuffle(positions)
        chosen = positions[:count]
        if color != _SEPARATOR_COLOR:
            return chosen
        if all(sum(col == candidate_col for _, col in chosen) < height for candidate_col in range(width)):
            return chosen
    raise RuntimeError("could not place color-5 query cells without a fake separator column")


def _general_counts(rng, capacity: int, winner_index: int) -> tuple[int, int, int]:
    winner_count = rng.randint(3, max(3, min(capacity - 2, max(4, capacity // 2))))
    runner_count = winner_count - 1
    low_count = rng.randint(1, max(1, winner_count - 2))
    if low_count == runner_count:
        low_count = 1
    counts = [low_count, runner_count, low_count]
    loser_indices = [index for index in range(3) if index != winner_index]
    counts[winner_index] = winner_count
    counts[loser_indices[0]] = runner_count
    counts[loser_indices[1]] = low_count
    return tuple(counts)


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"errors": errors}
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be non-empty")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("grid rows must be non-empty")
        return result
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return result
    if not 3 <= height <= 7:
        errors.append("panel height must be in 3..7")
    if (width - 3) % 4 != 0:
        errors.append("width must encode four equal panels plus three separators")
        return result
    panel_w = (width - 3) // 4
    if not 3 <= panel_w <= 6:
        errors.append("panel width must be in 3..6")
        return result

    separators = (panel_w, 2 * panel_w + 1, 3 * panel_w + 2)
    for col in separators:
        if not all(grid[row][col] == _SEPARATOR_COLOR for row in range(height)):
            errors.append(f"separator column {col} must be full color 5")
    extra_full_fives = [
        col for col in range(width)
        if col not in separators and all(grid[row][col] == _SEPARATOR_COLOR for row in range(height))
    ]
    if extra_full_fives:
        errors.append(f"unexpected full color-5 columns outside separators: {extra_full_fives}")

    panels = _split_panels([list(row) for row in grid], panel_w)
    query_cells = [value for row in panels[0] for value in row if value != 0]
    if len(query_cells) != 1:
        errors.append("query panel must contain exactly one nonzero cell")
        query_color = query_cells[0] if query_cells else None
    else:
        query_color = query_cells[0]

    if query_color is None:
        q_counts = (0, 0, 0)
        winner_index = None
        distractor_mode = None
    else:
        q_counts = tuple(_color_count(panel, query_color) for panel in panels[1:])
        if any(count <= 0 for count in q_counts):
            errors.append("every candidate must contain at least one query-color cell")
        if len(set(q_counts)) != 3:
            errors.append("candidate query counts must be pairwise distinct")
        winner_index = max(range(3), key=lambda index: q_counts[index])
        winner_total = _nonzero_count(panels[winner_index + 1])
        distractor_cells = [
            (candidate_index, row, col, value)
            for candidate_index, panel in enumerate(panels[1:])
            for row, values in enumerate(panel)
            for col, value in enumerate(values)
            if value not in (0, query_color)
        ]
        if not distractor_cells:
            distractor_mode = "none"
        else:
            distractor_colors = {value for _, _, _, value in distractor_cells}
            distractor_panels = {candidate_index for candidate_index, _, _, _ in distractor_cells}
            if _SEPARATOR_COLOR in distractor_colors:
                errors.append("candidate distractors may not reuse separator color 5")
            if len(distractor_colors) != 1:
                errors.append("all distractors must use one shared non-query color")
            if len(distractor_panels) != 1:
                errors.append("count-trap distractors must be confined to one losing panel")
            trap_index = next(iter(distractor_panels)) if distractor_panels else winner_index
            trap_total = _nonzero_count(panels[trap_index + 1])
            if trap_index == winner_index or trap_total <= winner_total:
                errors.append("distractor panel must lose by query count but exceed winner total foreground")
            distractor_mode = "count_trap"

    result.update({
        "height": height,
        "width": width,
        "panel_w": panel_w,
        "panels": panels,
        "query_color": query_color,
        "q_counts": q_counts,
        "winner_index": winner_index,
        "distractor_mode": distractor_mode,
    })
    return result


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "panel_h": info["height"],
        "panel_w": info["panel_w"],
        "query_color": info["query_color"],
        "winner_index": info["winner_index"],
        "distractor_mode": info["distractor_mode"],
    }


def canonical_profile_signature(grid: list[list[int]]) -> str | None:
    """Strict linked empirical-manifold signature, not a marginal envelope."""
    info = _analysis(grid)
    if info["errors"] or info["height"] != 3 or info["panel_w"] != 3:
        return None
    if info["distractor_mode"] != "none" or info["query_color"] == _SEPARATOR_COLOR:
        return None
    if info["q_counts"] == (3, 2, 1):
        return "canonical_counts_321"
    if info["q_counts"] == (2, 4, 1):
        return "canonical_counts_241"
    if info["q_counts"] == (3, 4, 1):
        return "canonical_counts_341"
    return None


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror only; the Racket program remains output authority."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["panels"][info["winner_index"] + 1]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    info = _analysis(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed[axis] != value:
                    errors.append(f"{axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md)
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    """[] when `grid` is a lawful canonical-like scene for THIS task.

    This is precisely the predicate the pre-repair generator failed:
    it emitted 4..8 panels behind full color-9 separator columns while
    rule_smoke stayed 120/120 green.  Here a scene is lawful only when it has
    EXACTLY four equal panels split by three full-height color-5 separator
    columns (and no accidental extra full color-5 column), a one-cell query
    panel, all-positive pairwise-distinct candidate counts, and lawful
    distractor structure.  A color-9-separator or variable-panel-count scene
    returns loud reasons.  Pure.
    """
    return list(_analysis(grid)["errors"])


def _lawful_analysis(grid) -> dict[str, Any] | None:
    """Analysis dict for a lawful scene, else None.  Pure."""
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness_field(grid, extract) -> bool:
    info = _lawful_analysis(grid)
    return False if info is None else bool(extract(info))


SEMANTIC_WITNESSES = {
    # the winner must be demonstrated in every candidate position
    "winner_first": lambda grid: _witness_field(grid, lambda a: a["winner_index"] == 0),
    "winner_middle": lambda grid: _witness_field(grid, lambda a: a["winner_index"] == 1),
    "winner_last": lambda grid: _witness_field(grid, lambda a: a["winner_index"] == 2),
    # a losing panel with MORE total foreground kills the foreground-max shortcut
    "count_trap_distractor": lambda grid: _witness_field(
        grid, lambda a: a["distractor_mode"] == "count_trap"
    ),
    "clean_scene": lambda grid: _witness_field(
        grid, lambda a: a["distractor_mode"] == "none"
    ),
    # query color 5 proves 5 is the separator only as a FULL column
    "query_color_is_separator_color": lambda grid: _witness_field(
        grid, lambda a: a["query_color"] == _SEPARATOR_COLOR
    ),
    # canonical 3x3 panel geometry stays represented in every band
    "canonical_panel_geometry": lambda grid: _witness_field(
        grid, lambda a: a["height"] == 3 and a["panel_w"] == 3
    ),
}


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    """Outputs of the plausible competing rules on a lawful scene, else None.

    Competitors implemented (grammar-level shortcuts — color-9 separators,
    variable panel counts — are owned by strict_canonical_like, since they
    never describe a lawful scene at all):
      fixed_panel_first/middle/last — always return candidate panel k
      most_foreground_panel — pick the candidate with the most nonzero cells
      least_query_count_panel — pick the MIN query-color count, not the max
    Pure.
    """
    info = _lawful_analysis(grid)
    if info is None:
        return None
    candidates = [
        [row[:] for row in panel] for panel in info["panels"][1:]
    ]
    query_color = info["query_color"]
    foreground = [_nonzero_count(panel) for panel in candidates]
    q_counts = [_color_count(panel, query_color) for panel in candidates]
    return {
        "fixed_panel_first": candidates[0],
        "fixed_panel_middle": candidates[1],
        "fixed_panel_last": candidates[2],
        "most_foreground_panel": candidates[max(range(3), key=lambda i: foreground[i])],
        "least_query_count_panel": candidates[min(range(3), key=lambda i: q_counts[i])],
    }


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos force the max-query-count selection on the query.

    A competitor that reproduces EVERY demo output yet answers the query
    differently means the lesson underdetermines the rule: e.g. demos whose
    winner is always the same panel index never falsify fixed-panel picking,
    and trap-free demos never falsify total-foreground maximisation.  Pure.
    """
    reasons: list[str] = []
    query_competitors = _competitor_outputs(query.get("input"))
    if query_competitors is None:
        return ["query input is not a lawful scene for this task"]
    query_truth = rule_mirror(query.get("input"))

    demo_rows: list[tuple[dict, dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        competitors = _competitor_outputs(demo.get("input"))
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful scene for this task")
            continue
        if demo.get("output") != rule_mirror(demo.get("input")):
            reasons.append(
                f"demo {index} output disagrees with the max-query-count rule mirror"
            )
            continue
        demo_rows.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        survives = all(
            competitors[name] == demo["output"] for demo, competitors in demo_rows
        )
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the "
                "query differently"
            )
    return sorted(set(reasons))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    slot = int(sample_index) % EXAMPLES_NEEDED

    # Caller overrides win. The default schedule is inserted before GenCtx is
    # built so every exact value is recorded in public draw provenance.
    effective = dict(overrides)
    effective.setdefault("winner_index", _WINNER_SCHEDULE[slot])
    effective.setdefault("distractor_mode", _DISTRACTOR_SCHEDULE[slot])
    if slot in (0, 3):
        effective.setdefault("panel_h", 3)
        effective.setdefault("panel_w", 3)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    panel_h = ctx.draw_choice("panel_h", _weighted_values(band, "panel_h"))
    panel_w = ctx.draw_choice("panel_w", _weighted_values(band, "panel_w"))
    query_color = ctx.draw_int("query_color", 1, 9)
    winner_index = ctx.draw_int("winner_index", 0, 2)
    distractor_mode = ctx.draw_choice("distractor_mode", ["none", "count_trap"])
    rng = ctx.draw_rng("layout")

    width = 4 * panel_w + 3
    grid = full_grid(panel_h, width, 0)
    separators = (panel_w, 2 * panel_w + 1, 3 * panel_w + 2)
    for row in range(panel_h):
        for col in separators:
            grid[row][col] = _SEPARATOR_COLOR

    query_position = _sample_positions(rng, panel_h, panel_w, 1, color=query_color)[0]
    grid[query_position[0]][query_position[1]] = query_color

    if (
        panel_h == 3 and panel_w == 3 and distractor_mode == "none"
        and slot == 0 and winner_index == 0
    ):
        counts = (3, 2, 1)
    elif (
        panel_h == 3 and panel_w == 3 and distractor_mode == "none"
        and slot == 3 and winner_index == 1
    ):
        counts = (2, 4, 1) if rng.randrange(2) == 0 else (3, 4, 1)
    else:
        counts = _general_counts(rng, panel_h * panel_w, winner_index)

    candidate_positions: list[list[tuple[int, int]]] = []
    for candidate_index, count in enumerate(counts):
        local = _sample_positions(rng, panel_h, panel_w, count, color=query_color)
        candidate_positions.append(local)
        offset = (candidate_index + 1) * (panel_w + 1)
        for row, col in local:
            grid[row][offset + col] = query_color

    if distractor_mode == "count_trap":
        loser_indices = [index for index in range(3) if index != winner_index]
        trap_index = max(loser_indices, key=lambda index: counts[index])
        needed = counts[winner_index] - counts[trap_index] + 1
        occupied = set(candidate_positions[trap_index])
        available = [
            (row, col) for row in range(panel_h) for col in range(panel_w)
            if (row, col) not in occupied
        ]
        if len(available) < needed:
            raise RuntimeError("count-trap construction lacks empty cells")
        rng.shuffle(available)
        distractor_color = rng.choice([
            color for color in range(1, 10)
            if color not in (query_color, _SEPARATOR_COLOR)
        ])
        offset = (trap_index + 1) * (panel_w + 1)
        for row, col in available[:needed]:
            grid[row][offset + col] = distractor_color

    observed = observe_overrides(grid)
    expected = {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "query_color": query_color,
        "winner_index": winner_index,
        "distractor_mode": distractor_mode,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes do not match returned grid: {expected!r} != {observed!r}")
    return grid
