"""High-integrity generator for ARC task ``9edcccd1341f``.

The first row is a preserved nonzero color key.  Below it, a uniform outer
frame encloses sparse interior colors.  The unique most-frequent non-frame
interior color is the winner.  The output preserves the key row, recolors the
outer frame with the winner, draws a second hollow winner-colored frame around
the winner cells' bounding box, and clears every other interior cell.

Ordinary draws deliberately contain both a winner cell strictly inside its
bounding box and a missing bounding-box perimeter cell.  That makes the output
distinguish the intended hollow-frame rule from merely retaining winner cells.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "9edcccd1341f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d1ac07400a65"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.10

SUMMARY = (
    "Preserve the nonzero key row. In the framed area, find the unique most-"
    "frequent non-border interior color. Recolor the outer frame with that "
    "winner, draw a hollow winner-colored frame around all winner cells' "
    "bounding box, and clear the remaining interior."
)

INVARIANTS = [
    "row 0 is a nonzero color key containing every active scene color",
    "rows 1 and h-1 plus columns 0 and w-1 form one complete uniform nonzero frame",
    "the framed interior contains no copies of the frame color",
    "at least two non-frame interior colors are present",
    "exactly one interior color has strictly greatest frequency",
    "the winner's bounding box spans at least two rows and two columns",
    "ordinary draws add a missing bbox-edge cell and remove an interior winner cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted keyed draw, canonical height 10 most often",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted keyed draw, canonical width 10 most often",
        "valid": "10..14",
    },
    "winner_count": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "4..24",
    },
    "distractor_count": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "2..9",
    },
    "border_color": {
        "type": "color",
        "default": "weighted keyed draw, canonical colors 1..5 favored",
        "valid": "1..9",
    },
    "winner_color": {
        "type": "color",
        "default": "weighted keyed draw distinct from border_color",
        "valid": "1..9",
    },
}

# Equal border/winner colors are semantically impossible: the Racket rule
# explicitly excludes the border color from winner selection.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"border_color": color, "winner_color": color}
    for color in range(1, 10)
]

_COLOR_OPTIONS = (1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9)
_DIM_OPTIONS = (10, 10, 10, 10, 10, 10, 10, 11, 12, 13, 14)
_CANONICAL_KEY = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name, value in overrides.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name!r} must be an integer")
    if (
        "border_color" in overrides
        and "winner_color" in overrides
        and overrides["border_color"] == overrides["winner_color"]
    ):
        raise ValueError("border_color and winner_color must differ")


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                raise ValueError("row strings must be non-empty decimal colors")
            values = [int(ch) for ch in row]
        elif isinstance(row, list):
            values = list(row)
        else:
            raise ValueError("grid rows must be lists or digit strings")
        if not values:
            raise ValueError("grid rows must be non-empty")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid values must be integer colors in 0..9")
        out.append(values)
    width = len(out[0])
    if any(len(row) != width for row in out):
        raise ValueError("grid must be rectangular")
    return out


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not cells:
        raise ValueError("cannot take a bounding box of zero cells")
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def _bbox_perimeter(
    r1: int, r2: int, c1: int, c2: int
) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _scene_facts(grid: Any) -> dict[str, Any]:
    g = _coerce_grid(grid)
    h, w = len(g), len(g[0])
    if h < 5 or w < 5:
        raise ValueError(f"grid too small for keyed framed scene: {h}x{w}")

    key = list(g[0])
    border_cells = (
        [(1, c) for c in range(w)]
        + [(h - 1, c) for c in range(w)]
        + [(r, 0) for r in range(2, h - 1)]
        + [(r, w - 1) for r in range(2, h - 1)]
    )
    border_values = [g[r][c] for r, c in border_cells]
    border_color = g[1][0]

    interior_positions = [
        (r, c)
        for r in range(2, h - 1)
        for c in range(1, w - 1)
    ]
    interior_nonzero = [
        (r, c, g[r][c])
        for r, c in interior_positions
        if g[r][c] != 0
    ]
    candidate_cells = [
        item for item in interior_nonzero if item[2] != border_color
    ]
    counts = Counter(value for _, _, value in candidate_cells)
    winner_color: int | None = None
    winner_cells: list[tuple[int, int]] = []
    winner_bbox: tuple[int, int, int, int] | None = None
    if counts:
        max_count = max(counts.values())
        winners = [color for color, count in counts.items() if count == max_count]
        if len(winners) == 1:
            winner_color = winners[0]
            winner_cells = [
                (r, c) for r, c, value in candidate_cells if value == winner_color
            ]
            winner_bbox = _bbox(winner_cells)

    return {
        "grid": g,
        "height": h,
        "width": w,
        "key": key,
        "key_colors": set(key),
        "border_cells": border_cells,
        "border_values": border_values,
        "border_color": border_color,
        "interior_positions": interior_positions,
        "interior_nonzero": interior_nonzero,
        "candidate_cells": candidate_cells,
        "counts": counts,
        "winner_color": winner_color,
        "winner_cells": winner_cells,
        "winner_bbox": winner_bbox,
        "palette": {value for row in g for value in row},
    }


def self_check(
    grid: Any,
    *,
    difficulty: str | None = None,
    meta: dict[str, Any] | None = None,
) -> list[str]:
    """Reject malformed keyed-frame scenes while accepting all canonical inputs."""
    del difficulty
    try:
        facts = _scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []
    key = facts["key"]
    border_color = facts["border_color"]
    if any(value == 0 for value in key):
        errors.append("row 0 color key must contain no zero cells")
    if border_color == 0:
        errors.append("outer frame color must be nonzero")
    if any(value != border_color for value in facts["border_values"]):
        errors.append("outer frame must be complete and uniformly one color")
    if any(value == border_color for _, _, value in facts["interior_nonzero"]):
        errors.append("frame color must not appear in the framed interior")

    counts: Counter[int] = facts["counts"]
    if len(counts) < 2:
        errors.append("interior must contain at least two non-frame colors")
    elif list(sorted(counts.values(), reverse=True))[:2][0] == list(
        sorted(counts.values(), reverse=True)
    )[:2][1]:
        errors.append(f"interior has no unique most-frequent color: {dict(counts)}")

    winner = facts["winner_color"]
    bbox = facts["winner_bbox"]
    if winner is not None:
        if counts[winner] < 2:
            errors.append("winner must appear in at least two interior cells")
        if bbox is not None:
            r1, r2, c1, c2 = bbox
            if r1 == r2 or c1 == c2:
                errors.append("winner bounding box must span at least two rows and columns")

    active_colors = {
        facts["border_color"],
        *(value for _, _, value in facts["interior_nonzero"]),
    }
    missing_from_key = sorted(active_colors - facts["key_colors"])
    if missing_from_key:
        errors.append(
            "row 0 color key omits active color(s): "
            + ", ".join(map(str, missing_from_key))
        )

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested = dict(meta["overrides"])
        else:
            requested = {name: meta[name] for name in AXES if name in meta}
    if requested and not errors:
        try:
            observed = observe_overrides(facts["grid"])
        except ValueError as exc:
            errors.append(f"could not observe overrides: {exc}")
        else:
            for name, value in requested.items():
                if observed.get(name) != value:
                    errors.append(
                        f"override {name!r} requested {value!r}, observed "
                        f"{observed.get(name)!r}"
                    )
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact public axis from the emitted input grid."""
    facts = _scene_facts(grid)
    if facts["winner_color"] is None:
        raise ValueError("grid has no unique winner")
    winner = facts["winner_color"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "winner_count": facts["counts"][winner],
        "distractor_count": sum(
            count for color, count in facts["counts"].items() if color != winner
        ),
        "border_color": facts["border_color"],
        "winner_color": winner,
    }


def _choose_palette(
    rng: Any, border_color: int, winner_color: int
) -> tuple[int, int, int]:
    if {border_color, winner_color} <= set(range(1, 6)):
        remaining = [
            color
            for color in range(1, 6)
            if color not in (border_color, winner_color)
        ]
        rng.shuffle(remaining)
        return tuple(remaining)  # exactly the canonical five-color key palette
    remaining = [
        color
        for color in range(1, 10)
        if color not in (border_color, winner_color)
    ]
    return tuple(rng.sample(remaining, 3))


def _key_row(
    rng: Any,
    width: int,
    palette: tuple[int, int, int, int, int],
) -> list[int]:
    if width == 10 and set(palette) == set(range(1, 6)):
        return list(_CANONICAL_KEY)
    row = list(palette)
    while len(row) < width:
        row.append(rng.choice(palette))
    rng.shuffle(row)
    return row[:width]


def _choose_bbox(
    rng: Any,
    interior_h: int,
    interior_w: int,
    winner_count: int,
    distractor_count: int,
    difficulty: str | None,
) -> tuple[int, int]:
    candidates = [
        (bh, bw)
        for bh in range(3, interior_h + 1)
        for bw in range(3, interior_w + 1)
        if bh * bw - 1 >= winner_count
        and interior_h * interior_w - bh * bw >= distractor_count
    ]
    if not candidates:
        raise ValueError(
            f"winner_count={winner_count} cannot fit a pedagogical bbox in "
            f"interior {interior_h}x{interior_w}"
        )
    candidates.sort(key=lambda dims: (dims[0] * dims[1], dims[0] + dims[1], dims))
    if difficulty == "easy":
        pool = candidates[: max(1, len(candidates) // 3)]
    elif difficulty == "hard":
        pool = candidates[max(0, 2 * len(candidates) // 3) :]
    else:
        pool = candidates
    return rng.choice(pool)


def _distribute_distractors(
    rng: Any,
    colors: tuple[int, int, int],
    total: int,
) -> list[int]:
    ordered = list(colors)
    rng.shuffle(ordered)
    assignments = [ordered[index % len(ordered)] for index in range(total)]
    rng.shuffle(assignments)
    return assignments


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = ctx.draw_choice("grid_h", _DIM_OPTIONS)
    w = ctx.draw_choice("grid_w", _DIM_OPTIONS)
    winner_count = ctx.draw_int_diff("winner_count", 4, 24)
    distractor_count = ctx.draw_int_diff("distractor_count", 2, 9)

    winner_override = overrides.get("winner_color")
    border_options = tuple(
        color for color in _COLOR_OPTIONS if color != winner_override
    )
    border_color = ctx.draw_choice("border_color", border_options)
    winner_options = tuple(
        color for color in _COLOR_OPTIONS if color != border_color
    )
    band_rotation = {None: 0, "easy": 0, "medium": 3, "hard": 6}[difficulty]
    if winner_options:
        offset = band_rotation % len(winner_options)
        winner_options = winner_options[offset:] + winner_options[:offset]
    winner_color = ctx.draw_choice("winner_color", winner_options)

    palette_rng = ctx.draw_rng("palette")
    distractor_colors = _choose_palette(
        palette_rng, border_color, winner_color
    )
    palette = (border_color, winner_color, *distractor_colors)

    g = full_grid(h, w, 0)
    key_rng = ctx.draw_rng("key-row")
    g[0] = _key_row(key_rng, w, palette)
    draw_frame(g, 1, 0, h - 1, w - 1, border_color)

    layout_rng = ctx.draw_rng("winner-layout")
    interior_h, interior_w = h - 3, w - 2
    bbox_h, bbox_w = _choose_bbox(
        layout_rng,
        interior_h,
        interior_w,
        winner_count,
        distractor_count,
        difficulty,
    )
    top = layout_rng.randint(2, h - 1 - bbox_h)
    left = layout_rng.randint(1, w - 1 - bbox_w)
    bottom = top + bbox_h - 1
    right = left + bbox_w - 1

    reserved_perimeter = (top, right)
    mandatory_winner = {
        (top, left),
        (bottom, right),
        (top + 1, left + 1),  # strict bbox interior; official output clears it
    }
    bbox_cells = [
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if (r, c) != reserved_perimeter
        and (r, c) not in mandatory_winner
    ]
    layout_rng.shuffle(bbox_cells)
    winner_cells = set(mandatory_winner)
    winner_cells.update(bbox_cells[: winner_count - len(winner_cells)])
    if len(winner_cells) != winner_count:
        raise ValueError("could not realize exact winner_count")
    for r, c in winner_cells:
        g[r][c] = winner_color

    outside_bbox = [
        (r, c)
        for r in range(2, h - 1)
        for c in range(1, w - 1)
        if not (top <= r <= bottom and left <= c <= right)
    ]
    layout_rng.shuffle(outside_bbox)
    if len(outside_bbox) < distractor_count:
        raise ValueError("not enough outside-bbox cells for distractors")
    assignments = _distribute_distractors(
        ctx.draw_rng("distractor-colors"), distractor_colors, distractor_count
    )
    for (r, c), color in zip(outside_bbox, assignments):
        g[r][c] = color

    errors = self_check(
        g,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid grid: " + "; ".join(errors))
    return g


def _render_rule(
    facts: dict[str, Any],
    *,
    chosen_color: int,
    chosen_cells: list[tuple[int, int]],
    outer: bool = True,
    bbox: bool = True,
    retain_cells: bool = False,
) -> list[list[int]]:
    h, w = facts["height"], facts["width"]
    out = full_grid(h, w, 0)
    out[0] = list(facts["key"])
    if outer:
        draw_frame(out, 1, 0, h - 1, w - 1, chosen_color)
    if retain_cells:
        for r, c in chosen_cells:
            out[r][c] = chosen_color
    if bbox:
        r1, r2, c1, c2 = _bbox(chosen_cells)
        draw_frame(out, r1, c1, r2, c2, chosen_color)
    return out


def _rule_unchecked(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    winner = facts["winner_color"]
    if winner is None:
        raise ValueError("input has no unique interior winner")
    return _render_rule(
        facts,
        chosen_color=winner,
        chosen_cells=facts["winner_cells"],
    )


def rule_mirror(grid: Any) -> list[list[int]]:
    """Audit mirror only; the canonical Racket program remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid keyed-frame scene: " + "; ".join(errors))
    return _rule_unchecked(grid)


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the canonical 10x10, six-color keyed-frame profile."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _scene_facts(grid)
    if (facts["height"], facts["width"]) != (10, 10):
        reasons.append(
            f"canonical grid is 10x10, got {facts['height']}x{facts['width']}"
        )
    if facts["key"] != _CANONICAL_KEY:
        reasons.append("canonical key row is 1122334455")
    if facts["palette"] != set(range(6)):
        reasons.append("canonical palette is exactly colors 0..5")
    return reasons


def _rival_outer_only(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    winner = facts["winner_color"]
    if winner is None:
        raise ValueError("no unique winner")
    return _render_rule(
        facts,
        chosen_color=winner,
        chosen_cells=facts["winner_cells"],
        bbox=False,
    )


def _rival_bbox_only(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    winner = facts["winner_color"]
    if winner is None:
        raise ValueError("no unique winner")
    return _render_rule(
        facts,
        chosen_color=winner,
        chosen_cells=facts["winner_cells"],
        outer=False,
    )


def _rival_retain_winner_cells(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    winner = facts["winner_color"]
    if winner is None:
        raise ValueError("no unique winner")
    return _render_rule(
        facts,
        chosen_color=winner,
        chosen_cells=facts["winner_cells"],
        bbox=False,
        retain_cells=True,
    )


def _rival_use_border_color(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    if facts["winner_color"] is None:
        raise ValueError("no unique winner")
    return _render_rule(
        facts,
        chosen_color=facts["border_color"],
        chosen_cells=facts["winner_cells"],
    )


def _rival_least_frequent(grid: Any) -> list[list[int]]:
    facts = _scene_facts(grid)
    if len(facts["counts"]) < 2:
        raise ValueError("not enough colors for a least-frequency rival")
    least = min(facts["counts"], key=lambda color: (facts["counts"][color], color))
    cells = [
        (r, c)
        for r, c, value in facts["candidate_cells"]
        if value == least
    ]
    return _render_rule(facts, chosen_color=least, chosen_cells=cells)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "draw_only_outer_frame": _rival_outer_only,
    "draw_only_winner_bbox": _rival_bbox_only,
    "retain_winner_cells_instead_of_bbox": _rival_retain_winner_cells,
    "use_original_border_color": _rival_use_border_color,
    "choose_least_frequent_interior_color": _rival_least_frequent,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These are pedagogical competitors, not hypotheses that fit every canonical pair.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _witness_outer_required(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    return facts["winner_color"] is not None and bool(facts["border_cells"])


def _witness_bbox_required(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    if facts["winner_bbox"] is None:
        return False
    perimeter = _bbox_perimeter(*facts["winner_bbox"])
    return bool(perimeter - set(facts["winner_cells"]))


def _witness_retain_cells_wrong(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    if facts["winner_bbox"] is None:
        return False
    perimeter = _bbox_perimeter(*facts["winner_bbox"])
    return bool(set(facts["winner_cells"]) - perimeter) and bool(
        perimeter - set(facts["winner_cells"])
    )


def _witness_border_color_wrong(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    return (
        facts["winner_color"] is not None
        and facts["winner_color"] != facts["border_color"]
    )


def _witness_least_frequency_wrong(grid: Any) -> bool:
    try:
        facts = _scene_facts(grid)
    except ValueError:
        return False
    if facts["winner_color"] is None or len(facts["counts"]) < 2:
        return False
    winner_count = facts["counts"][facts["winner_color"]]
    return any(count < winner_count for count in facts["counts"].values())


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "outer_frame_refutes_bbox_only": _witness_outer_required,
    "missing_bbox_edge_refutes_outer_only": _witness_bbox_required,
    "interior_winner_and_missing_edge_refute_cell_retention": _witness_retain_cells_wrong,
    "winner_differs_from_border": _witness_border_color_wrong,
    "strict_frequency_majority_refutes_least": _witness_least_frequency_wrong,
}

WITNESS_RIVALS = {
    "outer_frame_refutes_bbox_only": ["draw_only_winner_bbox"],
    "missing_bbox_edge_refutes_outer_only": ["draw_only_outer_frame"],
    "interior_winner_and_missing_edge_refute_cell_retention": [
        "retain_winner_cells_instead_of_bbox"
    ],
    "winner_differs_from_border": ["use_original_border_color"],
    "strict_frequency_majority_refutes_least": [
        "choose_least_frequent_interior_color"
    ],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require the demonstrations to eliminate every named plausible rival."""
    if not isinstance(demos, list) or not demos:
        return ["lesson must contain at least one demonstration"]
    if not isinstance(query, dict):
        return ["query must be a materialized pair"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            query_differs = rival(query["input"]) != query["output"]
            suffix = " and answers the query differently" if query_differs else ""
            reasons.append(f"competitor {name} survives every demo{suffix}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-specific malformed scenes that self_check must reject."""
    valid = generate(
        93_701,
        4,
        difficulty="medium",
        grid_h=10,
        grid_w=10,
        winner_count=4,
        distractor_count=9,
        border_color=2,
        winner_color=4,
    )
    facts = _scene_facts(valid)
    fixtures: list[tuple[str, list[list[int]]]] = []

    zero_key = [list(row) for row in valid]
    zero_key[0][0] = 0
    fixtures.append(("zero_in_key_row", zero_key))

    broken_frame = [list(row) for row in valid]
    broken_frame[1][2] = 0
    fixtures.append(("broken_outer_frame", broken_frame))

    split_frame = [list(row) for row in valid]
    split_frame[-1][2] = facts["winner_color"]
    fixtures.append(("two_color_outer_frame", split_frame))

    tied = [list(row) for row in valid]
    distractor = min(
        (color for color in facts["counts"] if color != facts["winner_color"]),
        key=lambda color: (-facts["counts"][color], color),
    )
    empty = next(
        (r, c)
        for r, c in facts["interior_positions"]
        if tied[r][c] == 0
    )
    tied[empty[0]][empty[1]] = distractor
    fixtures.append(("tied_maximum_frequency", tied))

    border_inside = [list(row) for row in valid]
    empty2 = next(
        (r, c)
        for r, c in facts["interior_positions"]
        if border_inside[r][c] == 0 and (r, c) != empty
    )
    border_inside[empty2[0]][empty2[1]] = facts["border_color"]
    fixtures.append(("border_color_inside_frame", border_inside))

    key_missing_winner = [list(row) for row in valid]
    key_missing_winner[0] = [
        facts["border_color"] if value == facts["winner_color"] else value
        for value in key_missing_winner[0]
    ]
    fixtures.append(("key_omits_winner", key_missing_winner))
    return fixtures


def negative_recombination_fixture() -> tuple[list[list[int]], int]:
    """Inject an unseen interior color absent from every other scene part."""
    grid = generate(
        91_337,
        5,
        difficulty="medium",
        grid_h=10,
        grid_w=10,
        winner_count=8,
        distractor_count=6,
        border_color=2,
        winner_color=4,
    )
    facts = _scene_facts(grid)
    replacement = next(color for color in range(1, 10) if color not in facts["palette"])
    r, c = next(
        (r, c)
        for r, c in facts["interior_positions"]
        if grid[r][c] == 0
    )
    out = [list(row) for row in grid]
    out[r][c] = replacement
    return out, replacement
