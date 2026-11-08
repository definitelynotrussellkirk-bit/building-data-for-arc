"""Generator for ARC task d1bdd8b75ba4 — global color frequency to bottom bar.

Count every non-background color globally.  The unique most-frequent color is
reproduced as a left-anchored bar on the bottom row; the bar length equals that
color's input count.  The generator deliberately separates global frequency
from local component size so a connected-component shortcut cannot explain the
lesson.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1bdd8b75ba4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f3ba832b2a8e"

SUMMARY = (
    "Three non-background colors appear on a zero background with pairwise "
    "distinct global cell counts. Count cells of each color, choose the unique "
    "most-frequent color, then output a fresh same-size zero grid whose bottom "
    "row begins at column 0 with a bar in that color; the bar length is exactly "
    "the winning global count. Generated lessons vary winner color rank, count "
    "gap, and local connectivity so color identity, first occurrence, and "
    "largest connected component cannot replace global counting."
)

INVARIANTS = [
    "exactly three non-background ARC colors are present",
    "their global cell counts are pairwise distinct, hence the winner is unique",
    "the winning count does not exceed the grid width",
    "one scheduled control includes a compact losing component while the winner is fragmented",
]

# Four semantic controls are cycled in every band.  Any four consecutive
# sample_index values therefore contain all decisive controls, independent of
# the lesson's starting residue.
_PROFILE_KINDS = (
    "low_gap1_connected",
    "mid_gap2_connected",
    "high_gap1_connected",
    "mid_gap1_compact_runner",
)
_BAND_SHAPES = {
    "easy": (6, 8),
    "medium": (7, 10),
    "hard": (8, 11),
}
_BAND_PREFIX = {"easy": "e", "medium": "m", "hard": "h"}
SCENE_PROFILES = tuple(
    f"{_BAND_PREFIX[band]}_{kind}"
    for band in ("easy", "medium", "hard")
    for kind in _PROFILE_KINDS
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-control curriculum; default draws also cycle canonical scales",
        "valid": "e_low_gap1_connected|e_mid_gap2_connected|e_high_gap1_connected|e_mid_gap1_compact_runner|m_low_gap1_connected|m_mid_gap2_connected|m_high_gap1_connected|m_mid_gap1_compact_runner|h_low_gap1_connected|h_mid_gap2_connected|h_high_gap1_connected|h_mid_gap1_compact_runner",
    }
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic curriculum; explicit bands cycle four semantic controls."""
    del seed
    index = int(sample_index)
    if difficulty is None:
        band = ("easy", "medium", "hard")[index % 3]
        kind = _PROFILE_KINDS[(index // 3) % 4]
    else:
        band = _band(difficulty)
        kind = _PROFILE_KINDS[index % 4]
    return f"{_BAND_PREFIX[band]}_{kind}"


def _profile_parts(profile: str) -> tuple[str, str]:
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    prefix, kind = profile.split("_", 1)
    band = {v: k for k, v in _BAND_PREFIX.items()}[prefix]
    return band, kind


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 4 <= len(grid) <= 14 or not 4 <= width <= 14:
        return [f"grid dimensions must be in 4..14, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"]
    return []


def _components_for_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    comps: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        q = deque([start])
        comp = []
        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen:
                    unseen.remove(p)
                    q.append(p)
        comps.append(comp)
    return comps


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    flat = [v for row in grid for v in row]
    counts = Counter(v for v in flat if v != 0)
    if 0 not in flat:
        errors.append("literal zero background must be present")
    if len(counts) != 3:
        errors.append(f"expected exactly three non-background colors, found {len(counts)}")
    if counts and len(set(counts.values())) != len(counts):
        errors.append("non-background colors must have pairwise distinct global counts")
    if not counts:
        return {"errors": errors, "height": h, "width": w, "counts": counts}
    winner, winner_count = min(counts.items(), key=lambda item: (-item[1], item[0]))
    if winner_count > w:
        errors.append(f"winning count {winner_count} exceeds grid width {w}")

    ordered_colors = sorted(counts)
    winner_rank = ordered_colors.index(winner) + 1 if winner in ordered_colors else None
    ordered_counts = sorted(counts.values(), reverse=True)
    gap = ordered_counts[0] - ordered_counts[1] if len(ordered_counts) >= 2 else None
    runner = None
    if len(counts) >= 2:
        runner = sorted(counts, key=lambda c: (-counts[c], c))[1]
    components = {color: _components_for_color(grid, color) for color in counts}
    max_components = {
        color: max((len(comp) for comp in components[color]), default=0)
        for color in counts
    }
    compact_runner = bool(
        runner is not None
        and max_components.get(runner, 0) >= 4
        and max_components.get(winner, 0) == 1
    )
    all_fragmented = bool(counts) and all(size == 1 for size in max_components.values())
    all_connected = bool(counts) and all(len(components[color]) == 1 for color in counts)

    shape_band = next((band for band, shape in _BAND_SHAPES.items() if shape == (h, w)), None)
    kind = None
    if shape_band and not errors:
        if winner_rank == 1 and gap == 1 and all_connected:
            kind = "low_gap1_connected"
        elif winner_rank == 2 and gap == 2 and all_connected:
            kind = "mid_gap2_connected"
        elif winner_rank == 3 and gap == 1 and all_connected:
            kind = "high_gap1_connected"
        elif winner_rank == 2 and gap == 1 and compact_runner:
            kind = "mid_gap1_compact_runner"
    scene_profile = f"{_BAND_PREFIX[shape_band]}_{kind}" if shape_band and kind else None
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "counts": counts,
        "winner": winner,
        "winner_count": winner_count,
        "winner_rank": winner_rank,
        "gap": gap,
        "runner": runner,
        "max_components": max_components,
        "compact_runner": compact_runner,
        "all_fragmented": all_fragmented,
        "all_connected": all_connected,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid input grammar; accepts every canonical input."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    nested = meta.get("overrides") if isinstance(meta, dict) else None
    requested = nested if isinstance(nested, dict) else (meta if isinstance(meta, dict) else {})
    for name, value in requested.items():
        if name in AXES:
            observed = observe_overrides(grid).get(name)
            if observed != value:
                errors.append(f"override {name}={value!r} realized as {observed!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict teaching predicate: canonical shapes plus the authority-valid grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in set(_BAND_SHAPES.values()):
        errors.append("strict lessons use one of the three canonical (height,width) profiles")
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _scatter_positions(h: int, w: int, rng, *, forbidden: set[tuple[int, int]] | None = None) -> list[tuple[int, int]]:
    forbidden = forbidden or set()
    # Same-parity cells are never 4-neighbours, so every same-color component
    # remains size one when all scattered cells are drawn from this pool.
    pool = [(r, c) for r in range(h) for c in range(w) if (r + c) % 2 == 0 and (r, c) not in forbidden]
    rng.shuffle(pool)
    return pool


def _build_scene(profile: str, rng) -> list[list[int]]:
    band, kind = _profile_parts(profile)
    h, w = _BAND_SHAPES[band]
    grid = full_grid(h, w, 0)

    colors = sorted(rng.sample(range(1, 10), 3))
    if kind.startswith("low_"):
        winner = colors[0]
    elif kind.startswith("high_"):
        winner = colors[2]
    else:
        winner = colors[1]
    losers = [c for c in colors if c != winner]

    gap = 2 if "gap2" in kind else 1
    if kind.endswith("compact_runner"):
        runner_count = rng.randint(4, min(5, w - gap))
    else:
        runner_count = rng.randint(3, min(5, w - gap))
    winner_count = runner_count + gap
    third_count = rng.randint(1, min(2, runner_count - 1))
    counts = {winner: winner_count, losers[0]: runner_count, losers[1]: third_count}
    # Randomize which losing color is runner-up so palette order itself carries
    # no information beyond the explicitly scheduled winner rank.
    if rng.randint(0, 1):
        counts[losers[0]], counts[losers[1]] = counts[losers[1]], counts[losers[0]]
    runner = max((c for c in colors if c != winner), key=lambda c: counts[c])
    third = next(c for c in colors if c not in (winner, runner))

    if kind.endswith("compact_runner"):
        # Variable anchor avoids a fixed-location cue.  A connected losing
        # component of size >=4 is intentionally larger than every winner
        # component (winner cells remain isolated), falsifying component-size.
        anchors = [(0, w - 3), (h - 2, w - 3)]
        ar, ac = rng.choice(anchors)
        compact_order = [(ar, ac), (ar, ac + 1), (ar + 1, ac), (ar + 1, ac + 1), (ar, ac + 2)]
        runner_cells = compact_order[: counts[runner]]
        forbidden = set(runner_cells)
        for r, c in runner_cells:
            grid[r][c] = runner
        # Reserve (0,0) for the third-place loser.  That makes first-nonzero a
        # guaranteed wrong rival while leaving the compact component's anchor variable.
        if (0, 0) in forbidden:
            raise AssertionError("compact runner unexpectedly overlaps reserved distractor")
        grid[0][0] = third
        forbidden.add((0, 0))
        pool = _scatter_positions(h, w, rng, forbidden=forbidden)
        remaining_third = counts[third] - 1
        needed = counts[winner] + remaining_third
        if len(pool) < needed:
            raise ValueError("insufficient isolated placement capacity")
        third_cells = pool[:remaining_third]
        winner_cells = pool[remaining_third:needed]
        for r, c in third_cells:
            grid[r][c] = third
        for r, c in winner_cells:
            grid[r][c] = winner
    else:
        # Canonical examples contain three connected color objects.  Preserve
        # that morphology in three of four curriculum slots so the task stays
        # anchored to its real manifold; only the compact-runner slot breaks
        # component-size equivalence on purpose.
        if h == 6:
            rows = [0, 2, 4]
        else:
            rows = [0, 3, 6]
        # The first visible object is always a loser, refuting first-occurrence.
        other_loser = third
        row_colors = [other_loser, winner, runner]
        if rng.randint(0, 1):
            row_colors[1], row_colors[2] = row_colors[2], row_colors[1]
            # keep winner off row 0 while still varying its row among the lower two
            if row_colors[1] != winner and row_colors[2] != winner:
                raise AssertionError("winner row assignment failed")
        for row, color in zip(rows, row_colors):
            length = counts[color]
            start = rng.randint(0, w - length)
            for c in range(start, start + length):
                grid[row][c] = color

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise ValueError(
            f"constructed scene drifted from profile {profile!r}: "
            f"observed={analysis.get('scene_profile')!r} errors={analysis['errors']}"
        )
    return grid


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
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    grid = _build_scene(profile, ctx.draw_rng("layout"))
    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise ValueError(f"scene_profile realization failed: {profile!r} -> {observed!r}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic rivals and lesson checks.
# ---------------------------------------------------------------------------

def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror for tests/rivals only; Racket remains the output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["width"], 0)
    for c in range(analysis["winner_count"]):
        out[-1][c] = analysis["winner"]
    return out


def _bar_for_color(grid: list[list[int]], color: int, length: int | None = None) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    count = sum(v == color for row in grid for v in row) if length is None else int(length)
    out = full_grid(h, w, 0)
    for c in range(min(count, w)):
        out[-1][c] = color
    return out


def _rival_smallest_color(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    return _bar_for_color(grid, colors[0])


def _rival_largest_color(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    return _bar_for_color(grid, colors[-1])


def _rival_first_nonzero(grid):
    color = next(v for row in grid for v in row if v != 0)
    return _bar_for_color(grid, color)


def _rival_largest_component(grid):
    colors = sorted({v for row in grid for v in row if v != 0})
    ranked = []
    for color in colors:
        size = max((len(comp) for comp in _components_for_color(grid, color)), default=0)
        ranked.append((size, -color, color))
    _, _, color = max(ranked)
    # This shortcut assumes the largest connected component is the decisive
    # count, not the total global frequency of that color.
    size = max(len(comp) for comp in _components_for_color(grid, color))
    return _bar_for_color(grid, color, size)


SEMANTIC_RIVALS = {
    "smallest_color": _rival_smallest_color,
    "largest_color": _rival_largest_color,
    "first_nonzero": _rival_first_nonzero,
    "largest_component": _rival_largest_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All three canonical inputs consist of solid same-color components whose
    # component sizes equal global counts, so this rival fits canonical and
    # needs generated counterexamples.
    "largest_component": _rival_largest_component,
}


def _winner_rank(grid) -> int | None:
    return _analysis(grid).get("winner_rank")


def _gap(grid) -> int | None:
    return _analysis(grid).get("gap")


def _compact_runner(grid) -> bool:
    return bool(_analysis(grid).get("compact_runner"))


SEMANTIC_WITNESSES = {
    "winner_is_lowest_color": lambda grid: _winner_rank(grid) == 1,
    "winner_is_middle_color": lambda grid: _winner_rank(grid) == 2,
    "winner_is_highest_color": lambda grid: _winner_rank(grid) == 3,
    "near_tie_requires_exact_count": lambda grid: _gap(grid) == 1,
    "compact_runner_refutes_component_size": _compact_runner,
}
WITNESS_RIVALS = {
    "winner_is_lowest_color": ["largest_color"],
    "winner_is_middle_color": ["smallest_color", "largest_color"],
    "winner_is_highest_color": ["smallest_color"],
    "near_tie_requires_exact_count": ["first_nonzero"],
    "compact_runner_refutes_component_size": ["largest_component"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each four-demo window to identify global frequency, color, and length."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    profiles = []
    winning_counts = set()
    winning_ranks = set()
    compact_seen = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the global-frequency bar rule")
            continue
        analysis = _analysis(demo["input"])
        profiles.append(analysis.get("scene_profile"))
        winning_counts.add(analysis["winner_count"])
        winning_ranks.add(analysis["winner_rank"])
        compact_seen = compact_seen or analysis["compact_runner"]

    qerr = self_check(query["input"])
    if qerr:
        reasons.append(f"query input is not lawful: {qerr[0]}")
    if reasons:
        return reasons
    if winning_ranks != {1, 2, 3}:
        reasons.append(f"demos must show winner color ranks 1,2,3; saw {sorted(winning_ranks)}")
    if len(winning_counts) < 2:
        reasons.append("demos must vary the winning count/bar length")
    if not compact_seen:
        reasons.append("demos must include a compact losing component against a fragmented winner")
    if not any(_gap(demo["input"]) == 1 for demo in demos):
        reasons.append("demos must include a one-cell near tie")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with rival {name!r}, which changes the query answer"
                )
    return reasons
