"""Generator for ``easy_12_diagonal_shadow_down_right`` (e443791433ff).

Canonical rule: each green(3) source whose down-right neighbour is in bounds
and background(0) paints gray(5) into that neighbour.  A non-background
neighbour blocks the shadow, and all input cells are otherwise preserved.

The official inputs use only 0/2/3.  Every example contains both a casting
source and a source blocked by color 2; two examples additionally contain a
source blocked by another color-3 source.  Ordinary generated lessons preserve
that grammar and alternate the source-blocker branch so every two consecutive
demonstrations expose it without making it a fixed texture cue.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e443791433ff"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d9de6efb6a97"

SUMMARY = (
    "On a 0-background grid containing green(3) sources and blue(2) blockers, "
    "inspect each green source independently. If its one-step down-right cell "
    "is in bounds and 0, paint that destination gray(5); if the destination is "
    "already nonzero, leave it unchanged. Preserve all original 2s and 3s."
)

EXAMPLES_NEEDED = 2

INVARIANTS = [
    "input palette is exactly drawn from {0,2,3}; gray(5) appears only in output",
    "all color-3 sources have an in-bounds down-right neighbour",
    "at least one source has an empty down-right target and therefore casts",
    "at least one source is blocked by a color-2 down-right neighbour",
    "ordinary two-example windows include a source blocked by another source",
    "ordinary draws include an unrelated color-2 distractor that casts nothing",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..10",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 10..12",
        "valid": "10..12",
    },
    "n_sources": {
        "type": "int",
        "default": "difficulty-skewed 6..12",
        "valid": "6..12",
    },
    "n_decoys": {
        "type": "int",
        "default": "difficulty-skewed 2..4; exact overrides 1..4",
        "valid": "1..4",
    },
}

# Every declared combination is constructible, including the smallest grid
# with the maximum source/decoy counts.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _candidate_cells(h: int, w: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(h - 1) for c in range(w - 1)]


def _try_draw_scene(
    h: int,
    w: int,
    n_sources: int,
    n_decoys: int,
    *,
    include_source_blocker: bool,
    rng,
) -> list[list[int]] | None:
    """Construct one scene while reserving every intended empty shadow cell.

    The reservation is the key semantic constraint: a later source or decoy may
    not land on a previously active source's down-right target.  The pre-repair
    generator checked only the candidate's own target, so a later source could
    silently turn an intended casting branch into a blocked branch.
    """
    g = full_grid(h, w, 0)
    sources: list[tuple[int, int]] = []
    reserved_empty_targets: set[tuple[int, int]] = set()

    cells = _candidate_cells(h, w)
    rng.shuffle(cells)

    if include_source_blocker:
        # A -> B is intentionally blocked by source B; B itself casts.
        pair_candidates = [
            (r, c)
            for r, c in cells
            if r + 2 < h and c + 2 < w
        ]
        if not pair_candidates:
            return None
        ar, ac = pair_candidates[0]
        br, bc = ar + 1, ac + 1
        g[ar][ac] = 3
        g[br][bc] = 3
        sources.extend(((ar, ac), (br, bc)))
        reserved_empty_targets.add((br + 1, bc + 1))

    # One canonical blocker: a color-2 cell sits exactly down-right of C.
    blocker_candidates = list(cells)
    rng.shuffle(blocker_candidates)
    blocked_source = None
    for r, c in blocker_candidates:
        target = (r + 1, c + 1)
        if g[r][c] != 0 or g[target[0]][target[1]] != 0:
            continue
        if (r, c) in reserved_empty_targets or target in reserved_empty_targets:
            continue
        g[r][c] = 3
        g[target[0]][target[1]] = 2
        sources.append((r, c))
        blocked_source = (r, c)
        break
    if blocked_source is None:
        return None

    # Every remaining source demonstrates the active cast branch.  Keep both
    # its own cell and its target disjoint from every prior active target.
    active_candidates = list(cells)
    rng.shuffle(active_candidates)
    for r, c in active_candidates:
        if len(sources) >= n_sources:
            break
        target = (r + 1, c + 1)
        if g[r][c] != 0 or g[target[0]][target[1]] != 0:
            continue
        if (r, c) in reserved_empty_targets or target in reserved_empty_targets:
            continue
        g[r][c] = 3
        sources.append((r, c))
        reserved_empty_targets.add(target)
    if len(sources) != n_sources:
        return None

    # The first 2 is the blocker above. Extra 2s are genuine distractors: they
    # must not occupy any active shadow target, so they are preserved unchanged
    # and cannot themselves be mistaken for sources.
    twos_now = sum(value == 2 for row in g for value in row)
    extras_needed = n_decoys - twos_now
    if extras_needed < 0:
        return None
    # Keep every unrelated 2 as a discriminating negative-source cue: if a
    # shortcut treated color 2 as a source, its down-right shadow would be
    # visible.  Reserve those empty targets too so later distractors cannot
    # erase the counterexample.
    decoy_targets: set[tuple[int, int]] = set()
    for _ in range(extras_needed):
        candidates = [
            (r, c)
            for r in range(h - 1)
            for c in range(w - 1)
            if g[r][c] == 0
            and g[r + 1][c + 1] == 0
            and (r, c) not in reserved_empty_targets
            and (r, c) not in decoy_targets
            and (r + 1, c + 1) not in reserved_empty_targets
            and (r + 1, c + 1) not in decoy_targets
        ]
        if not candidates:
            return None
        rng.shuffle(candidates)
        r, c = candidates[0]
        g[r][c] = 2
        decoy_targets.add((r + 1, c + 1))
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Full declared domains remain valid in every difficulty band. Difficulty
    # changes only the ordinary prior, never the exact override contract.
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 10, 12)
    if "n_sources" in overrides:
        n_sources = ctx.draw_int("n_sources", 6, 12)
    elif difficulty == "easy":
        n_sources = ctx.draw_int("n_sources", 6, 8)
    elif difficulty == "hard":
        n_sources = ctx.draw_int("n_sources", 10, 12)
    else:
        n_sources = ctx.draw_int("n_sources", 8, 10)
    if "n_decoys" in overrides:
        n_decoys = ctx.draw_int("n_decoys", 1, 4)
    elif difficulty == "easy":
        n_decoys = ctx.draw_int("n_decoys", 2, 3)
    elif difficulty == "hard":
        n_decoys = ctx.draw_int("n_decoys", 3, 4)
    else:
        n_decoys = ctx.draw_int("n_decoys", 2, 4)

    include_source_blocker = sample_index % 2 == 1
    rng = ctx.draw_rng("placement")
    for _ in range(64):
        grid = _try_draw_scene(
            h,
            w,
            n_sources,
            n_decoys,
            include_source_blocker=include_source_blocker,
            rng=rng,
        )
        if grid is not None:
            return grid
    raise ValueError(
        "could not construct a valid shadow scene for "
        f"{h}x{w}, n_sources={n_sources}, n_decoys={n_decoys}"
    )


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty 2D list"]}
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular and nonempty"]}
    h = len(grid)
    if not (8 <= h <= 10 and 10 <= w <= 12):
        errors.append(f"grid dimensions {h}x{w} outside 8..10 by 10..12")

    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return {"errors": errors, "height": h, "width": w}

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 2, 3})
    if unexpected:
        errors.append(f"input contains unexpected colors {unexpected}; expected only 0,2,3")

    sources = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 3
    ]
    twos = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    ]
    if not (6 <= len(sources) <= 12):
        errors.append(f"expected 6..12 color-3 sources, found {len(sources)}")
    if not (1 <= len(twos) <= 4):
        errors.append(f"expected 1..4 color-2 blockers/decoys, found {len(twos)}")

    border_sources = [
        (r, c) for r, c in sources if r + 1 >= h or c + 1 >= w
    ]
    if border_sources:
        errors.append(
            f"all sources must have an in-bounds down-right neighbour; found {border_sources[:4]}"
        )

    casting: list[tuple[int, int]] = []
    blocked_by_two: list[tuple[int, int]] = []
    blocked_by_three: list[tuple[int, int]] = []
    two_targets: set[tuple[int, int]] = set()
    for r, c in sources:
        if r + 1 >= h or c + 1 >= w:
            continue
        target = (r + 1, c + 1)
        value = grid[target[0]][target[1]]
        if value == 0:
            casting.append((r, c))
        elif value == 2:
            blocked_by_two.append((r, c))
            two_targets.add(target)
        elif value == 3:
            blocked_by_three.append((r, c))

    if not casting:
        errors.append("no color-3 source has an empty down-right target")
    if not blocked_by_two:
        errors.append("no color-3 source is blocked by a color-2 down-right neighbour")

    unrelated_twos = [cell for cell in twos if cell not in two_targets]
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "palette": palette,
        "sources": sources,
        "twos": twos,
        "casting": casting,
        "blocked_by_two": blocked_by_two,
        "blocked_by_three": blocked_by_three,
        "unrelated_twos": unrelated_twos,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar and the conditional shadow cues."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned input grid."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    return {
        "grid_h": h,
        "grid_w": w,
        "n_sources": sum(value == 3 for row in grid for value in row),
        "n_decoys": sum(value == 2 for row in grid for value in row),
    }


def profile_signature(grid) -> dict[str, Any]:
    """Linked task features used by strict/stability censuses."""
    facts = _analyze(grid)
    return {
        "valid": not facts["errors"],
        "height": facts.get("height"),
        "width": facts.get("width"),
        "n_sources": len(facts.get("sources", [])),
        "n_decoys": len(facts.get("twos", [])),
        "casting": len(facts.get("casting", [])),
        "blocked_by_two": len(facts.get("blocked_by_two", [])),
        "blocked_by_three": len(facts.get("blocked_by_three", [])),
        "unrelated_twos": len(facts.get("unrelated_twos", [])),
    }


def strict_canonical_like(grid) -> list[str]:
    """Strict task-linked predicate: canonical grammar plus both rule branches."""
    return list(_analyze(grid)["errors"])


MIN_STRICT_FRAC = 0.95


def _witness_casting(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["casting"])


def _witness_color2_blocker(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["blocked_by_two"])


def _witness_source_blocker(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["blocked_by_three"])


def _witness_no_source_blocker(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and not facts["blocked_by_three"]


def _witness_irrelevant_two(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["unrelated_twos"])


SEMANTIC_WITNESSES = {
    "empty_target_casts_gray": _witness_casting,
    "color2_target_blocks_shadow": _witness_color2_blocker,
    "source_target_blocks_shadow": _witness_source_blocker,
    "source_blocker_absent_control": _witness_no_source_blocker,
    "unrelated_color2_is_not_a_source": _witness_irrelevant_two,
}


def _rival_no_shadow(grid):
    return [list(row) for row in grid]


def _rival_paint_through_blockers(grid):
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h - 1):
        for c in range(w - 1):
            if grid[r][c] == 3:
                out[r + 1][c + 1] = 5
    return out


def _rival_block_only_color2(grid):
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h - 1):
        for c in range(w - 1):
            if grid[r][c] == 3 and grid[r + 1][c + 1] != 2:
                out[r + 1][c + 1] = 5
    return out


def _rival_color2_also_source(grid):
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h - 1):
        for c in range(w - 1):
            if grid[r][c] in (2, 3) and grid[r + 1][c + 1] == 0:
                out[r + 1][c + 1] = 5
    return out


SEMANTIC_RIVALS = {
    "no_shadow": _rival_no_shadow,
    "paint_through_blockers": _rival_paint_through_blockers,
    "block_only_color2": _rival_block_only_color2,
    "color2_also_source": _rival_color2_also_source,
}

WITNESS_RIVALS = {
    "empty_target_casts_gray": ["no_shadow"],
    "color2_target_blocks_shadow": ["paint_through_blockers"],
    "source_target_blocks_shadow": ["block_only_color2"],
    "unrelated_color2_is_not_a_source": ["color2_also_source"],
}

# Absence of a source-on-source blocker is a scheduled positive control, not a
# claim that one specific rival must disagree on every such scene.
BRANCH_WITNESSES = ["source_blocker_absent_control"]

LESSON_COMPETITORS = SEMANTIC_RIVALS


def rule_mirror(grid) -> list[list[int]]:
    """Exact Python test mirror; the Racket program remains output authority."""
    out = [list(row) for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w):
            nr, nc = r + 1, c + 1
            if (
                grid[r][c] == 3
                and nr < h
                and nc < w
                and grid[nr][nc] == 0
            ):
                out[nr][nc] = 5
    return out


def lesson_identifiable(demos, query) -> list[str]:
    """Require each two-demo window to falsify the main shortcut rules."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    aggregate = {
        "casting": 0,
        "blocked_by_two": 0,
        "blocked_by_three": 0,
        "unrelated_twos": 0,
    }
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} must contain input and output"]
        facts = _analyze(pair["input"])
        if facts["errors"]:
            return [f"demo {index} invalid: {facts['errors'][0]}"]
        if rule_mirror(pair["input"]) != pair["output"]:
            return [f"demo {index} output disagrees with the conditional down-right rule"]
        for key in aggregate:
            aggregate[key] += len(facts[key])

    missing = [name for name, count in aggregate.items() if count == 0]
    if missing:
        return ["demonstrations miss shortcut-killing cue(s): " + ", ".join(missing)]
    query_errors = self_check(query["input"])
    if query_errors:
        return ["query input invalid: " + query_errors[0]]
    return []


def mutation_fixtures():
    """Task-linked malformed near-misses that structural checks must reject."""
    base = generate(
        901,
        0,
        difficulty="medium",
        grid_h=9,
        grid_w=10,
        n_sources=8,
        n_decoys=2,
    )
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_sources = [list(row) for row in base]
    for r, row in enumerate(no_sources):
        for c, value in enumerate(row):
            if value == 3:
                no_sources[r][c] = 0
    fixtures.append(("no_sources", no_sources))

    no_color2_blocker = [list(row) for row in base]
    facts = _analyze(no_color2_blocker)
    for r, c in facts["blocked_by_two"]:
        no_color2_blocker[r + 1][c + 1] = 0
    fixtures.append(("no_color2_blocker", no_color2_blocker))

    no_castable_source = [list(row) for row in base]
    for r, c in _analyze(no_castable_source)["casting"]:
        no_castable_source[r + 1][c + 1] = 2
    fixtures.append(("no_castable_source", no_castable_source))

    unexpected_gray = [list(row) for row in base]
    for r, row in enumerate(unexpected_gray):
        for c, value in enumerate(row):
            if value == 0:
                unexpected_gray[r][c] = 5
                break
        else:
            continue
        break
    fixtures.append(("gray_in_input", unexpected_gray))

    border_source = [list(row) for row in base]
    sr, sc = next(
        (r, c)
        for r, row in enumerate(border_source)
        for c, value in enumerate(row)
        if value == 3
    )
    border_source[sr][sc] = 0
    border_source[-1][0] = 3
    fixtures.append(("border_source", border_source))

    unexpected_color = [list(row) for row in base]
    for r, row in enumerate(unexpected_color):
        for c, value in enumerate(row):
            if value == 0:
                unexpected_color[r][c] = 7
                break
        else:
            continue
        break
    fixtures.append(("unexpected_color", unexpected_color))
    return fixtures
