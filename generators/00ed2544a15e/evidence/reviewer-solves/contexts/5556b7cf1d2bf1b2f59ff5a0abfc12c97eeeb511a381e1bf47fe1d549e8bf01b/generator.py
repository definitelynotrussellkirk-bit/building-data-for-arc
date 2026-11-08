"""Constructive curriculum for ARC task 00ed2544a15e.

Canonical rule
--------------
For each pair of red (2) cells in one row or one column, paint the strictly
interior cells cyan (8) exactly when the complete segment contains only black
(0) and those two red endpoints.  A third red or any other color blocks that
particular span.  Endpoints and unrelated cells are unchanged.

Every ordinary generated input is a labelled counterexample bundle: it shows a
horizontal connection, a vertical connection, a blocked aligned pair, an
isolated red, and either a three-red chain or a shared-endpoint cross.  Thus a
single example already refutes horizontal-only, vertical-only, ignore-blocker,
identity, and isolated-pairs-only rivals; the three-example schedule rotates
which chain topology receives emphasis.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00ed2544a15e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "92ea0e00d9a5"

SUMMARY = (
    "Red(2) markers aligned horizontally or vertically are joined with cyan(8) "
    "only when the entire inclusive segment contains black plus exactly those "
    "two reds. Constructive h-chain, v-chain, and cross profiles also include "
    "a blocked pair and an isolated red to refute canonical-fitting shortcuts."
)

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("h_chain", "v_chain", "cross")
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted draw over 8..12",
        "valid": "8..12",
        "doc": "Input height; every value is realizable in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted draw over 9..13",
        "valid": "9..13",
        "doc": "Input width; every value is realizable in every difficulty band.",
    },
    "profile": {
        "type": "enum",
        "default": "cyclic h_chain|v_chain|cross by sample_index",
        "valid": "h_chain|v_chain|cross",
        "doc": "Which chain topology is emphasized while all core rule branches remain visible.",
    },
}

INVARIANTS = [
    "input palette is black(0), red(2), and at most one non-cyan distractor color",
    "every default draw has a visible canonical transformation",
    "every default draw includes clear horizontal and vertical segments",
    "every default draw includes a blocked aligned pair and an isolated red",
    "the cyclic profiles expose a horizontal chain, vertical chain, or shared-endpoint cross",
    "all outputs are computed by a pure Python mirror pinned to the selected Racket source",
]

_HEIGHT_OPTIONS = (8, 8, 8, 9, 9, 10, 11, 12)
_WIDTH_OPTIONS = (9, 9, 9, 10, 10, 11, 12, 13)
_BLOCKER_COLORS = (1, 3, 4, 5, 6, 7, 9)
_LOCAL_H = 8
_LOCAL_W = 9

# Coordinates are local to an 8x9 frame.  Endpoint rows/columns are otherwise
# unique, preventing accidental connections outside the intended structures.
_TEMPLATES = {
    "h_chain": {
        "red": (
            (3, 1), (3, 4), (3, 7),       # horizontal chain A-B-C
            (0, 4),                       # clear vertical pair sharing B
            (7, 1),                       # blocked vertical pair sharing A
            (6, 8),                       # isolated red
        ),
        "blockers": ((5, 1),),
    },
    "v_chain": {
        "red": (
            (1, 3), (4, 3), (7, 3),       # vertical chain A-B-C
            (4, 7),                       # clear horizontal pair sharing B
            (1, 8),                       # blocked horizontal pair sharing A
            (6, 0),                       # isolated red
        ),
        "blockers": ((1, 6),),
    },
    "cross": {
        "red": (
            (3, 1), (3, 4), (3, 7),       # horizontal arm
            (0, 4), (6, 4),               # vertical arm, shared center (3,4)
            (7, 8),                       # isolated red
        ),
        # The left arm is deliberately blocked; the right and vertical arms
        # remain clear, so both orientations and the shared endpoint survive.
        "blockers": ((3, 2),),
    },
}



def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9 (booleans are invalid)"]
    return []


def _segment(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    if a[0] == b[0]:
        row = a[0]
        lo, hi = sorted((a[1], b[1]))
        return [(row, col) for col in range(lo, hi + 1)]
    if a[1] == b[1]:
        col = a[1]
        lo, hi = sorted((a[0], b[0]))
        return [(row, col) for row in range(lo, hi + 1)]
    return []


def _red_points(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]


def _pair_facts(grid: list[list[int]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return clear and color-blocked two-red aligned spans in the original input."""
    clear: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    points = _red_points(grid)
    for index, first in enumerate(points):
        for second in points[index + 1 :]:
            cells = _segment(first, second)
            if not cells:
                continue
            values = [grid[row][col] for row, col in cells]
            # Outer spans across a 3+-red chain are not directly eligible.
            if values.count(2) != 2:
                continue
            fact = {
                "a": first,
                "b": second,
                "orientation": "h" if first[0] == second[0] else "v",
                "cells": cells,
                "interior": cells[1:-1],
            }
            if all(value in (0, 2) for value in values):
                clear.append(fact)
            else:
                blocked.append(fact)
    return clear, blocked


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    shape_errors = _grid_shape_errors(grid)
    if shape_errors:
        return {"errors": shape_errors, "profile": None}

    points = _red_points(grid)
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    for row, col in points:
        rows[row].append(col)
        cols[col].append(row)
    for values in rows.values():
        values.sort()
    for values in cols.values():
        values.sort()

    clear, blocked = _pair_facts(grid)
    clear_h = [fact for fact in clear if fact["orientation"] == "h"]
    clear_v = [fact for fact in clear if fact["orientation"] == "v"]
    h_chain_rows = sorted(row for row, values in rows.items() if len(values) >= 3)
    v_chain_cols = sorted(col for col, values in cols.items() if len(values) >= 3)
    shared = sorted(
        point
        for point in points
        if len(rows[point[0]]) >= 3 and len(cols[point[1]]) >= 3
    )
    if shared:
        profile = "cross"
    elif h_chain_rows and not v_chain_cols:
        profile = "h_chain"
    elif v_chain_cols and not h_chain_rows:
        profile = "v_chain"
    else:
        profile = None

    isolated = sorted(
        point
        for point in points
        if len(rows[point[0]]) == 1 and len(cols[point[1]]) == 1
    )
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "reds": points,
        "rows": dict(rows),
        "cols": dict(cols),
        "clear": clear,
        "clear_h": clear_h,
        "clear_v": clear_v,
        "blocked": blocked,
        "h_chain_rows": h_chain_rows,
        "v_chain_cols": v_chain_cols,
        "shared": shared,
        "isolated": isolated,
        "profile": profile,
    }


def _paint_clear_segments(
    grid: list[list[int]], *, orientations: frozenset[str]
) -> list[list[int]]:
    out = deepcopy(grid)
    clear, _ = _pair_facts(grid)
    for fact in clear:
        if fact["orientation"] not in orientations:
            continue
        for row, col in fact["interior"]:
            out[row][col] = 8
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket program."""
    return _paint_clear_segments(grid, orientations=frozenset(("h", "v")))


# Historical name retained for compatibility with older task-local probes.
_mirror = rule_mirror


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _rival_horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    return _paint_clear_segments(grid, orientations=frozenset(("h",)))


def _rival_vertical_only(grid: list[list[int]]) -> list[list[int]]:
    return _paint_clear_segments(grid, orientations=frozenset(("v",)))


def _rival_ignore_blockers(grid: list[list[int]]) -> list[list[int]]:
    """Connect every exactly-two-red aligned span, ignoring other colors.

    Every interior cell is painted, including a blocker. This reproduces every
    canonical example because none places a distractor inside a red-red span,
    but it disagrees on every generated blocked pair.
    """
    out = deepcopy(grid)
    points = _red_points(grid)
    for index, first in enumerate(points):
        for second in points[index + 1 :]:
            cells = _segment(first, second)
            if not cells:
                continue
            if sum(grid[row][col] == 2 for row, col in cells) != 2:
                continue
            for row, col in cells[1:-1]:
                out[row][col] = 8
    return out


def _rival_simple_pairs_only(grid: list[list[int]]) -> list[list[int]]:
    """Connect only isolated clear pairs whose endpoints have clear degree one.

    Canonical demonstrations contain disjoint pairs, so this rival fits all of
    them.  It fails on three-red chains and on the shared endpoint of a cross.
    """
    out = deepcopy(grid)
    clear, _ = _pair_facts(grid)
    degree: Counter[tuple[int, int]] = Counter()
    for fact in clear:
        degree[fact["a"]] += 1
        degree[fact["b"]] += 1
    for fact in clear:
        if degree[fact["a"]] == degree[fact["b"]] == 1:
            for row, col in fact["interior"]:
                out[row][col] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "ignore_blockers": _rival_ignore_blockers,
    "simple_pairs_only": _rival_simple_pairs_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_blockers": _rival_ignore_blockers,
    "simple_pairs_only": _rival_simple_pairs_only,
}


def _has_painted_edge(facts: list[dict[str, Any]]) -> bool:
    return any(fact["interior"] for fact in facts)


def _witness_horizontal(grid: list[list[int]]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and _has_painted_edge(analysis["clear_h"])


def _witness_vertical(grid: list[list[int]]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and _has_painted_edge(analysis["clear_v"])


def _witness_blocker(grid: list[list[int]]) -> bool:
    if _grid_shape_errors(grid):
        return False
    return _rival_ignore_blockers(grid) != rule_mirror(grid)


def _witness_profile(profile: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        analysis = _analyze(grid)
        return (
            not analysis["errors"]
            and analysis["profile"] == profile
            and _rival_simple_pairs_only(grid) != rule_mirror(grid)
        )

    return predicate


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "horizontal_connection": _witness_horizontal,
    "vertical_connection": _witness_vertical,
    "blocked_pair_control": _witness_blocker,
    "horizontal_chain": _witness_profile("h_chain"),
    "vertical_chain": _witness_profile("v_chain"),
    "shared_endpoint_cross": _witness_profile("cross"),
}
WITNESS_RIVALS = {
    "horizontal_connection": ["vertical_only", "identity"],
    "vertical_connection": ["horizontal_only", "identity"],
    "blocked_pair_control": ["ignore_blockers"],
    "horizontal_chain": ["simple_pairs_only"],
    "vertical_chain": ["simple_pairs_only"],
    "shared_endpoint_cross": ["simple_pairs_only"],
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 8, 12), ("grid_w", 9, 13)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    if "profile" in overrides:
        profile = overrides["profile"]
        if not isinstance(profile, str) or profile not in SCHEDULE_PROFILES:
            raise ValueError(
                f"profile override must be one of {SCHEDULE_PROFILES}, got {profile!r}"
            )


def _transform_local(
    point: tuple[int, int], *, flip_rows: bool, flip_cols: bool
) -> tuple[int, int]:
    row, col = point
    if flip_rows:
        row = _LOCAL_H - 1 - row
    if flip_cols:
        col = _LOCAL_W - 1 - col
    return row, col


def _add_safe_distractors(
    grid: list[list[int]], *, color: int, count: int, rng: Any
) -> None:
    if count <= 0:
        return
    analysis = _analyze(grid)
    row_reds = Counter(row for row, _ in analysis["reds"])
    col_reds = Counter(col for _, col in analysis["reds"])
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (
            grid[row][col] == 0
            and row_reds[row] < 2
            and col_reds[col] < 2
            and any(
                0 <= row + dr < len(grid)
                and 0 <= col + dc < len(grid[0])
                and grid[row + dr][col + dc] == color
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
        )
    ]
    rng.shuffle(candidates)
    if len(candidates) < count:
        raise ValueError("not enough safe cells for requested distractors")
    for row, col in candidates[:count]:
        grid[row][col] = color


def _teaching_contract_errors(grid: list[list[int]], expected_profile: str | None = None) -> list[str]:
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if expected_profile is not None and analysis["profile"] != expected_profile:
        errors.append(
            f"profile mismatch: expected {expected_profile}, observed {analysis['profile']}"
        )
    if not _has_painted_edge(analysis["clear_h"]):
        errors.append("missing a visible horizontal connection")
    if not _has_painted_edge(analysis["clear_v"]):
        errors.append("missing a visible vertical connection")
    if not analysis["blocked"] or _rival_ignore_blockers(grid) == rule_mirror(grid):
        errors.append("missing an answer-changing blocked aligned pair")
    if not analysis["isolated"]:
        errors.append("missing an isolated red marker")
    if _rival_simple_pairs_only(grid) == rule_mirror(grid):
        errors.append("missing a chain/shared-endpoint counterexample")
    for name, rival in LESSON_COMPETITORS.items():
        if rival(grid) == rule_mirror(grid):
            errors.append(f"declared competitor {name!r} still matches this lesson")
    return errors


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Duplicated options intentionally weight ordinary draws toward canonical
    # dimensions while retaining exact support for every declared boundary.
    height = ctx.draw_choice("grid_h", _HEIGHT_OPTIONS)
    width = ctx.draw_choice("grid_w", _WIDTH_OPTIONS)
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile = (
        ctx.draw_choice("profile", SCHEDULE_PROFILES)
        if "profile" in overrides
        else ctx.draw_choice("profile", (scheduled_profile,))
    )
    blocker_color = ctx.draw_color("blocker_color", exclude=(0, 2, 8))
    rng = ctx.draw_rng("layout")

    flip_rows = bool(rng.randrange(2))
    flip_cols = bool(rng.randrange(2))
    row_offset = rng.randrange(height - _LOCAL_H + 1)
    col_offset = rng.randrange(width - _LOCAL_W + 1)

    grid = full_grid(height, width, 0)
    template = _TEMPLATES[profile]
    for point in template["red"]:
        row, col = _transform_local(point, flip_rows=flip_rows, flip_cols=flip_cols)
        grid[row + row_offset][col + col_offset] = 2
    for point in template["blockers"]:
        row, col = _transform_local(
            point, flip_rows=flip_rows, flip_cols=flip_cols
        )
        grid[row + row_offset][col + col_offset] = blocker_color

    if difficulty == "easy":
        extra_count = 0
    elif difficulty == "medium":
        extra_count = 1
    elif difficulty == "hard":
        extra_count = 2
    else:
        extra_count = rng.randrange(3)
    _add_safe_distractors(grid, color=blocker_color, count=extra_count, rng=rng)

    findings = _teaching_contract_errors(grid, expected_profile=profile)
    if findings:
        raise AssertionError("constructive template violated its contract: " + "; ".join(findings))
    return grid


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """Recognize the broad lawful task manifold, including all canonical inputs."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append(f"unexpected task scale {height}x{width}")
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("black(0) background is absent")
    if 8 in palette:
        errors.append("cyan(8) is an output role and must not appear in the input")
    if 2 not in palette:
        errors.append("red(2) markers are absent")
    distractors = palette - {0, 2}
    if len(distractors) > 1:
        errors.append(
            f"expected at most one unrelated distractor color, found {sorted(distractors)}"
        )
    if not errors:
        output = rule_mirror(grid)
        if output == grid:
            errors.append("canonical rule is a no-op: no clear red-red gap is painted")
    return errors


def self_check(
    grid: list[list[int]], *, difficulty: str | None = None, meta: Any = None
) -> list[str]:
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unknown difficulty {difficulty!r}")
    expected = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(expected, dict) and expected:
        try:
            observed = observe_overrides(grid)
        except Exception as exc:
            errors.append(f"could not observe overrides: {type(exc).__name__}: {exc}")
        else:
            for name in AXES:
                if name in expected and observed.get(name) != expected[name]:
                    errors.append(
                        f"override {name!r} expected {expected[name]!r}, observed {observed.get(name)!r}"
                    )
    return errors


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    if analysis["profile"] not in SCHEDULE_PROFILES:
        raise ValueError("grid does not realize one of the declared lesson profiles")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "profile": analysis["profile"],
    }


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Finite declared-rival certificate for one generated lesson."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    normalized: list[dict[str, list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labelled input/output pair")
            continue
        if strict_canonical_like(pair["input"]):
            reasons.append(f"demo {index} is outside the declared task manifold")
            continue
        expected = rule_mirror(pair["input"])
        if expected != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the canonical mirror")
            continue
        normalized.append(pair)
    if reasons:
        return reasons

    survivors = [
        name
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in normalized)
    ]
    if survivors:
        reasons.append("declared competitors survive all demos: " + ", ".join(sorted(survivors)))

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append("query is outside the declared task manifold")
        if "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the canonical mirror")
    return reasons
