"""Generator for fc999420d3aa — complete every one-arm-missing plus.

The authoritative transformation is local and simultaneous: a nonzero center
with exactly three same-colour cardinal neighbours and one zero cardinal
neighbour receives its fourth arm in the center colour.  Generated lessons use
an explicit four-slot schedule.  Three slots contain decisive counterexamples
to plausible shortcuts; the remaining slot anchors the canonical grid/palette
profiles.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc999420d3aa"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "75975e426e4b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, find every nonzero center whose four in-bounds "
    "cardinal neighbours contain exactly three cells of the center colour and "
    "one zero. Fill that one zero with the center colour, completing the plus; "
    "leave every other cell unchanged. Generated targets use distinct colours. "
    "Scheduled lessons also include isolated two-arm decoys and non-downward "
    "missing arms so the demonstrations identify the exact precondition rather "
    "than a canonical-template shortcut."
)

INVARIANTS = [
    "background is color 0",
    "each firing target is an in-bounds center with exactly three matching arms and one zero arm",
    "different firing targets use different nonzero colors",
    "all firing targets are completed simultaneously and every non-target cell is preserved",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile teaching schedule with canonical 5/6/9-row anchors",
        "valid": "5..18",
        "doc": "Exact input height; every value 5..18 is constructible in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile teaching schedule with canonical 7/9-column anchors",
        "valid": "5..20",
        "doc": "Exact input width; every value 5..20 is constructible in every band.",
    },
    "n_motifs": {
        "type": "int",
        "default": "1 on canonical anchors; 2 on decisive profiles",
        "valid": "1..2",
        "doc": "Exact number of completable three-arm plus targets.",
    },
}

# Every Cartesian combination is constructible.  In particular, a 5x5 grid can
# hold two disjoint targets at centers (1,1) and (3,3).  The empty declaration
# opts into strict multi-axis override validation rather than legacy warnings.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
Delta = tuple[int, int]

_DIRS: tuple[Delta, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DOWN: Delta = (1, 0)

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "rotated_controls_a",
    "rotated_controls_b",
    "rotated_controls_c",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Period four; every consecutive three samples include decisive evidence."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "canonical_anchor":
        # These triples reproduce every canonical (height, width, palette-size)
        # profile under the profile-floor probe.  Hard uses a second decoy color.
        return {
            "easy": (5, 7, 1),
            "medium": (6, 9, 1),
            "hard": (9, 9, 1),
        }.get(difficulty, (9, 9, 1))
    if profile == "rotated_controls_a":
        return {
            "easy": (7, 9, 2),
            "medium": (9, 11, 2),
            "hard": (12, 14, 2),
        }.get(difficulty, (9, 11, 2))
    if profile == "rotated_controls_b":
        return {
            "easy": (8, 10, 2),
            "medium": (10, 12, 2),
            "hard": (14, 16, 2),
        }.get(difficulty, (10, 12, 2))
    return {
        "easy": (9, 11, 2),
        "medium": (11, 13, 2),
        "hard": (16, 18, 2),
    }.get(difficulty, (11, 13, 2))


def _draw_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Record exact axes while preserving the full advertised override domain."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _firing_centers(grid: Grid) -> list[tuple[int, int, Cell]]:
    """Return ``(row, col, missing_cell)`` for every authority-firing center."""
    if not isinstance(grid, list) or not grid:
        return []
    if not isinstance(grid[0], list) or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return []

    firing: list[tuple[int, int, Cell]] = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if type(value) is not int or value == 0:
                continue
            neighbours = [(r + dr, c + dc) for dr, dc in _DIRS]
            if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in neighbours):
                continue
            same = [(rr, cc) for rr, cc in neighbours if grid[rr][cc] == value]
            zero = [(rr, cc) for rr, cc in neighbours if grid[rr][cc] == 0]
            if len(same) == 3 and len(zero) == 1:
                firing.append((r, c, zero[0]))
    return firing


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for tests/witnesses; the Racket program is authority."""
    out = deepcopy(grid)
    for r, c, (mr, mc) in _firing_centers(grid):
        out[mr][mc] = grid[r][c]
    return out


def _downward_only(grid: Grid) -> Grid:
    """Canonical shortcut: complete only upright-T targets missing the down arm."""
    out = deepcopy(grid)
    for r, c, (mr, mc) in _firing_centers(grid):
        if (mr - r, mc - c) == _DOWN:
            out[mr][mc] = grid[r][c]
    return out


def _first_target_only(grid: Grid) -> Grid:
    """Canonical shortcut: complete the first target but ignore later targets."""
    out = deepcopy(grid)
    firing = _firing_centers(grid)
    if firing:
        r, c, (mr, mc) = firing[0]
        out[mr][mc] = grid[r][c]
    return out


def _complete_two_or_more(grid: Grid) -> Grid:
    """Wrong broad rule: fill every zero arm around centers with >=2 same arms."""
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out
    h, w = len(grid), len(grid[0])
    fills: list[tuple[int, int, int]] = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if type(value) is not int or value == 0:
                continue
            neighbours = [(r + dr, c + dc) for dr, dc in _DIRS]
            if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in neighbours):
                continue
            same_count = sum(grid[rr][cc] == value for rr, cc in neighbours)
            if same_count >= 2:
                fills.extend(
                    (rr, cc, value)
                    for rr, cc in neighbours
                    if grid[rr][cc] == 0
                )
    for r, c, value in fills:
        out[r][c] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "downward_only": _downward_only,
    "first_target_only": _first_target_only,
    "complete_two_or_more": _complete_two_or_more,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Both shortcuts fit all labeled canonical examples; generated controls must
# supply the counterexamples.  The >=2-arms rival is already false canonically.
CANONICAL_SHORTCUTS = {
    "downward_only": _downward_only,
    "first_target_only": _first_target_only,
}


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], 0, 0
    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 18 and 5 <= w <= 20):
        errors.append(f"grid dimensions must be within 5..18 by 5..20, found {h}x{w}")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            errors.append(f"row {r} has inconsistent width")
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                if len(errors) >= 8:
                    return errors, h, w
    return errors, h, w


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-compatible grammar shared by canonical and generated inputs."""
    del difficulty, meta
    errors, _h, _w = _validate_grid(grid)
    if errors:
        return errors
    firing = _firing_centers(grid)
    if not (1 <= len(firing) <= 2):
        errors.append(f"expected 1-2 completable plus targets, found {len(firing)}")
        return errors
    colors = [grid[r][c] for r, c, _missing in firing]
    if len(colors) != len(set(colors)):
        errors.append("completable plus targets must use distinct colors")
    missing = [cell for _r, _c, cell in firing]
    if len(missing) != len(set(missing)):
        errors.append("completable plus targets must not share a missing arm cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Bounded teaching grammar; all generated and canonical inputs satisfy it."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_motifs": len(_firing_centers(grid)),
    }


def _valid_and_diff(grid: Grid, rival: Callable[[Grid], Grid]) -> bool:
    return not strict_canonical_like(grid) and rival(grid) != rule_mirror(grid)


def _has_non_down_missing_arm(grid: Grid) -> bool:
    return _valid_and_diff(grid, _downward_only) and any(
        (mr - r, mc - c) != _DOWN
        for r, c, (mr, mc) in _firing_centers(grid)
    )


def _has_multiple_targets(grid: Grid) -> bool:
    return _valid_and_diff(grid, _first_target_only) and len(_firing_centers(grid)) >= 2


def _has_two_arm_decoy(grid: Grid) -> bool:
    if strict_canonical_like(grid):
        return False
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value == 0:
                continue
            neighbours = [(r + dr, c + dc) for dr, dc in _DIRS]
            same = sum(grid[rr][cc] == value for rr, cc in neighbours)
            zero = sum(grid[rr][cc] == 0 for rr, cc in neighbours)
            if same == 2 and zero == 2:
                return _complete_two_or_more(grid) != rule_mirror(grid)
    return False


SEMANTIC_WITNESSES = {
    "non_down_missing_arm": _has_non_down_missing_arm,
    "multiple_targets": _has_multiple_targets,
    "two_arm_decoy": _has_two_arm_decoy,
}
WITNESS_RIVALS = {
    "non_down_missing_arm": ["downward_only"],
    "multiple_targets": ["first_target_only"],
    "two_arm_decoy": ["complete_two_or_more"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to falsify every declared plausible wrong rule."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query input is outside teaching grammar: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not exactly complete every firing plus")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    for name, killed in refuted.items():
        if not killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _structure_cells(center: Cell, filled_dirs: tuple[Delta, ...]) -> tuple[set[Cell], set[Cell]]:
    r, c = center
    filled = {(r, c)} | {(r + dr, c + dc) for dr, dc in filled_dirs}
    reserved = {
        (r + dr, c + dc)
        for dr, dc in _DIRS
        if (dr, dc) not in filled_dirs
    }
    return filled, reserved


def _place_structures(
    h: int,
    w: int,
    specs: list[tuple[str, tuple[Delta, ...], int]],
    rng,
) -> list[tuple[str, Cell, tuple[Delta, ...], int]] | None:
    """Backtrack over interior centers while protecting every absent arm cell."""
    centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    candidates: list[list[tuple[Cell, set[Cell], set[Cell]]]] = []
    for _kind, filled_dirs, _color in specs:
        options = []
        for center in centers:
            filled, reserved = _structure_cells(center, filled_dirs)
            options.append((center, filled, reserved))
        rng.shuffle(options)
        candidates.append(options)

    chosen: list[tuple[str, Cell, tuple[Delta, ...], int]] = []

    def search(index: int, occupied: set[Cell], reserved: set[Cell]) -> bool:
        if index == len(specs):
            return True
        kind, filled_dirs, color = specs[index]
        for center, filled, absent in candidates[index]:
            if filled & occupied or filled & reserved:
                continue
            if absent & occupied or absent & reserved:
                continue
            chosen.append((kind, center, filled_dirs, color))
            if search(index + 1, occupied | filled, reserved | absent):
                return True
            chosen.pop()
        return False

    return chosen if search(0, set(), set()) else None


def _target_missing_directions(profile: str, n_motifs: int) -> list[Delta]:
    if profile == "canonical_anchor":
        return [_DOWN] * n_motifs
    by_profile = {
        "rotated_controls_a": ((-1, 0), (0, 1)),
        "rotated_controls_b": ((0, -1), _DOWN),
        "rotated_controls_c": ((0, 1), (-1, 0)),
    }
    options = by_profile[profile]
    return [options[i % len(options)] for i in range(n_motifs)]


def _build_grid(
    h: int,
    w: int,
    n_motifs: int,
    profile: str,
    difficulty,
    rng,
) -> Grid:
    target_missing = _target_missing_directions(profile, n_motifs)
    include_decoy = profile != "canonical_anchor" or difficulty in (None, "hard")
    color_count = n_motifs + int(include_decoy)
    colors = rng.sample(list(range(1, 10)), color_count)

    specs: list[tuple[str, tuple[Delta, ...], int]] = []
    for index, missing in enumerate(target_missing):
        filled_dirs = tuple(direction for direction in _DIRS if direction != missing)
        specs.append(("target", filled_dirs, colors[index]))
    if include_decoy:
        decoy_arms = {
            "canonical_anchor": ((-1, 0), (0, 1)),
            "rotated_controls_a": ((-1, 0), (0, 1)),
            "rotated_controls_b": ((1, 0), (0, -1)),
            "rotated_controls_c": ((-1, 0), (1, 0)),
        }[profile]
        specs.append(("decoy", decoy_arms, colors[-1]))

    placements = _place_structures(h, w, specs, rng)
    if placements is None and include_decoy:
        # Exact exposed axes take precedence on tiny override geometries.  The
        # decoy is an internal curriculum control, not an advertised axis.
        specs = specs[:n_motifs]
        placements = _place_structures(h, w, specs, rng)
    if placements is None:
        raise ValueError(f"{h}x{w} cannot place {n_motifs} completable plus targets")

    grid = full_grid(h, w, 0)
    for _kind, (r, c), filled_dirs, color in placements:
        grid[r][c] = color
        for dr, dc in filled_dirs:
            grid[r + dr][c + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n = _profile_defaults(sample_index, difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", default_h, 5, 18)
    w = _draw_axis(ctx, overrides, "grid_w", default_w, 5, 20)
    n_motifs = _draw_axis(ctx, overrides, "n_motifs", default_n, 1, 2)

    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")
    grid = _build_grid(h, w, n_motifs, profile, difficulty, rng)

    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError(f"internal construction violated teaching grammar: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_motifs": n_motifs}
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")

    # Decisive default profiles are the semantic contract: fail loudly rather
    # than silently emit an ambiguous lesson if construction changes later.
    if not overrides and profile != "canonical_anchor":
        missing = [name for name, witness in SEMANTIC_WITNESSES.items() if not witness(grid)]
        if missing:
            raise RuntimeError(f"decisive profile lost semantic witness(es): {missing}")
    return grid
