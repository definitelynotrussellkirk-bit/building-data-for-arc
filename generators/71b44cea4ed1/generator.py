"""Generator for arc_puzzle_bank_sixth21:E36 — diagonal midpoint bridge.

The input is a sparse zero-background grid containing equal-color endpoint
pairs exactly two rows and two columns apart.  The canonical rule fills each
blank diagonal midpoint with its endpoints' color.  Every draw contains both
diagonal orientations.  A four-slot schedule combines one exact canonical
morphology with three overlapping near-miss lessons, so every three-of-four
query rotation still teaches diagonal/exact-distance/same-color/blank-midpoint
semantics.
"""
from __future__ import annotations

from collections import defaultdict
from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71b44cea4ed1"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "814976eb9ffc"

SUMMARY = (
    "Fill a blank cell only when equal nonzero endpoints lie exactly two rows "
    "and two columns apart; copy the endpoint color into that diagonal "
    "midpoint. Every scene has both diagonal orientations. A four-slot lesson "
    "schedule contains one exact 7x7, 8x8, or 9x9 canonical morphology and "
    "three overlapping combinations of axis-aligned, wrong-distance/"
    "different-color, and blocked-midpoint near misses. Thus every "
    "three-of-four query rotation retains all shortcut witnesses. Exact "
    "grid-size and pair-count overrides remain authoritative."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25
LESSON_SCHEDULE_PERIOD = 4

INVARIANTS = [
    "background is 0 and every scene has two or three active pairs",
    "active pairs have equal-color diagonal endpoints at displacement (2, ±2)",
    "active midpoints are blank, distinct, and include both orientations",
    "active pairs use distinct colors",
    "non-anchor samples carry scheduled near misses without creating extra fills",
    "every three-of-four consecutive query rotation retains every near-miss family",
    "every fourth non-override sample exactly rehearses a canonical morphology",
]

COUNTER_HYPOTHESES = [
    "copy the input unchanged",
    "fill only one diagonal orientation",
    "fill axis-aligned equal-color pairs",
    "fill longer diagonal spans",
    "ignore endpoint-color equality or overwrite a blocked midpoint",
    "use a fixed fill color instead of the endpoint color",
]

# Only exact, recoverable controls are public axes. Colors, positions, and the
# sample-index near-miss schedule are deterministic nuisance variation.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor every fourth sample; otherwise difficulty-skewed",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor every fourth sample; otherwise difficulty-skewed",
        "valid": "7..16",
    },
    "pair_count": {
        "type": "int",
        "default": "3 on canonical anchors; otherwise difficulty-skewed within 2..3",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
DECOY_MODES = (
    "canonical_profile",
    "axis_aligned+wrong_distance_and_color",
    "wrong_distance_and_color+blocked_midpoint",
    "blocked_midpoint+axis_aligned",
)
CANONICAL_MORPHOLOGY_PROFILES = (
    (7, 7, 4),
    (8, 8, 4),
    (9, 9, 4),
)
_CANONICAL_SHAPES = tuple((h, w) for h, w, _ in CANONICAL_MORPHOLOGY_PROFILES)
_CANONICAL_ANCHOR_PERIOD = LESSON_SCHEDULE_PERIOD


class _Pair(NamedTuple):
    color: int
    a: tuple[int, int]
    midpoint: tuple[int, int]
    b: tuple[int, int]
    orientation: str


class _Candidate(NamedTuple):
    a: tuple[int, int]
    midpoint: tuple[int, int]
    b: tuple[int, int]
    orientation: str

    @property
    def cells(self) -> frozenset[tuple[int, int]]:
        return frozenset((self.a, self.midpoint, self.b))


def _valid_grid_shape(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _fillable_pairs(grid: list[list[int]]) -> list[_Pair]:
    """Recover exactly the branch applications made by the Racket rule."""
    h, w = len(grid), len(grid[0])
    pairs: list[_Pair] = []
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            for dc, orientation in ((2, "down_right"), (-2, "down_left")):
                c2 = c + dc
                if not 0 <= c2 < w:
                    continue
                midpoint = (r + 1, c + dc // 2)
                if (
                    grid[r + 2][c2] == color
                    and grid[midpoint[0]][midpoint[1]] == 0
                ):
                    pairs.append(
                        _Pair(
                            color,
                            (r, c),
                            midpoint,
                            (r + 2, c2),
                            orientation,
                        )
                    )
    return pairs


def _pairs(grid: list[list[int]]) -> list[_Pair]:
    """Backward-compatible internal alias used by focused tests."""
    return _fillable_pairs(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Return exact semantic-axis values recoverable from a valid scene."""
    return {"pair_count": len(_fillable_pairs(grid))}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket rule is authoritative."""
    if not _valid_grid_shape(grid):
        raise ValueError("rule_mirror expects a rectangular non-empty grid")
    out = [row[:] for row in grid]
    for pair in _fillable_pairs(grid):
        r, c = pair.midpoint
        out[r][c] = pair.color
    return out


def _is_axis_aligned_pair(cells: list[tuple[int, int]], grid) -> bool:
    if len(cells) != 2:
        return False
    (r1, c1), (r2, c2) = cells
    if r1 == r2 and abs(c2 - c1) == 2:
        return grid[r1][(c1 + c2) // 2] == 0
    if c1 == c2 and abs(r2 - r1) == 2:
        return grid[(r1 + r2) // 2][c1] == 0
    return False


def _is_wrong_distance_pair(cells: list[tuple[int, int]]) -> bool:
    if len(cells) != 2:
        return False
    (r1, c1), (r2, c2) = cells
    return abs(r2 - r1) == 3 and abs(c2 - c1) == 3


def _is_blocked_pair(cells: list[tuple[int, int]], grid) -> bool:
    if len(cells) != 2:
        return False
    (r1, c1), (r2, c2) = cells
    if abs(r2 - r1) != 2 or abs(c2 - c1) != 2:
        return False
    return grid[(r1 + r2) // 2][(c1 + c2) // 2] != 0


def _is_mismatch_endpoint(
    cell: tuple[int, int],
    color: int,
    grid: list[list[int]],
) -> bool:
    h, w = len(grid), len(grid[0])
    r, c = cell
    for dr in (-2, 2):
        for dc in (-2, 2):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w):
                continue
            other = grid[rr][cc]
            if other != 0 and other != color:
                if grid[(r + rr) // 2][(c + cc) // 2] == 0:
                    return True
    return False


def _is_blocker_cell(cell: tuple[int, int], grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    r, c = cell
    for dr in (-1, 1):
        for dc in (-1, 1):
            a = (r - dr, c - dc)
            b = (r + dr, c + dc)
            if not (
                0 <= a[0] < h
                and 0 <= a[1] < w
                and 0 <= b[0] < h
                and 0 <= b[1] < w
            ):
                continue
            endpoint_color = grid[a[0]][a[1]]
            if endpoint_color != 0 and endpoint_color == grid[b[0]][b[1]]:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task-local generation grammar.

    Lawful scenes contain two or three distinct-color active pairs, both
    diagonal orientations, and only the four explicitly supported near-miss
    roles.  This is deliberately stronger than merely checking that a fill is
    possible: it rejects blank/minimal scenes and arbitrary repeated colors.
    """
    del difficulty, meta
    if not _valid_grid_shape(grid):
        return ["grid must be nonempty and rectangular"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (7 <= h <= 16 and 7 <= w <= 16):
        errors.append(f"grid dimensions {h}x{w} are outside 7..16")
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC limits: {h}x{w}")

    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid color at ({r},{c}): {value!r}")
            elif value != 0:
                positions[value].append((r, c))

    # Do not continue structural analysis on malformed cell values.
    if errors and any("invalid color" in error for error in errors):
        return errors

    pairs = _fillable_pairs(grid)
    if not 2 <= len(pairs) <= 3:
        errors.append(
            f"expected two or three fillable diagonal midpoints, found {len(pairs)}"
        )

    orientations = {pair.orientation for pair in pairs}
    if pairs and orientations != {"down_right", "down_left"}:
        errors.append("active pairs must include both diagonal orientations")

    midpoint_roles: dict[tuple[int, int], set[int]] = defaultdict(set)
    for pair in pairs:
        midpoint_roles[pair.midpoint].add(pair.color)
    ambiguous = {
        midpoint: colors
        for midpoint, colors in midpoint_roles.items()
        if len(colors) != 1
    }
    if ambiguous:
        errors.append(f"ambiguous active midpoint ownership: {ambiguous}")

    active_by_color: dict[int, list[_Pair]] = defaultdict(list)
    for pair in pairs:
        active_by_color[pair.color].append(pair)
    repeated_active_colors = {
        color: len(color_pairs)
        for color, color_pairs in active_by_color.items()
        if len(color_pairs) != 1
    }
    if repeated_active_colors:
        errors.append(
            "active pairs must use distinct colors: "
            f"{repeated_active_colors}"
        )

    for color, cells in sorted(positions.items()):
        active = active_by_color.get(color, [])
        if len(cells) == 1:
            if not _is_blocker_cell(cells[0], grid):
                errors.append(
                    f"singleton color {color} is not a blocked-midpoint marker"
                )
            continue
        if len(cells) not in (2, 3):
            errors.append(
                f"color {color} has {len(cells)} cells; expected one to three"
            )
            continue
        if len(cells) == 2:
            recognized = (
                len(active) == 1
                or _is_axis_aligned_pair(cells, grid)
                or _is_wrong_distance_pair(cells)
                or _is_blocked_pair(cells, grid)
            )
            if not recognized:
                errors.append(
                    f"color {color} is not an active pair or recognized near miss"
                )
            continue
        if len(active) != 1:
            errors.append(
                f"three-cell color {color} must contain exactly one active pair"
            )
            continue
        active_cells = {active[0].a, active[0].b}
        extras = [cell for cell in cells if cell not in active_cells]
        if len(extras) != 1 or not (
            _is_mismatch_endpoint(extras[0], color, grid)
            or _is_blocker_cell(extras[0], grid)
        ):
            errors.append(
                f"color {color} extra cell is neither mismatch endpoint nor blocker"
            )
    return errors


# --- Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md) ---

# Canonical inputs are exact 7x7 / 8x8 / 9x9 sparse scenes with three
# active pairs in three distinct colors (palette cardinality four including
# background).  The strict manifold intentionally excludes all curriculum
# decoys, while self_check accepts the broader generated lesson grammar.
_CANONICAL_DIM_ENVELOPE = (7, 9)


def strict_canonical_like(grid):
    """Return [] exactly for task-linked canonical morphology scenes."""
    errors = self_check(grid)
    if errors:
        return errors

    reasons = []
    h, w = len(grid), len(grid[0])
    palette_size = len({value for row in grid for value in row})
    if (h, w, palette_size) not in CANONICAL_MORPHOLOGY_PROFILES:
        reasons.append(
            f"profile {(h, w, palette_size)} is not one of "
            f"{CANONICAL_MORPHOLOGY_PROFILES}"
        )

    pairs = _fillable_pairs(grid)
    if len(pairs) != 3:
        reasons.append(f"canonical scenes have exactly three active pairs, found {len(pairs)}")
    if {pair.orientation for pair in pairs} != {"down_right", "down_left"}:
        reasons.append("canonical scenes fill both diagonal orientations")
    colors = [pair.color for pair in pairs]
    if len(set(colors)) != len(colors):
        reasons.append("canonical active pairs each use a distinct color")

    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    active_endpoints = {cell for pair in pairs for cell in (pair.a, pair.b)}
    if len(nonzero) != 6 or set(nonzero) != active_endpoints:
        reasons.append("canonical scenes contain only the six active endpoints")
    return reasons


def _scan_equal_axis_pairs(grid):
    """Equal-color axis-aligned distance-2 pairs with a blank midpoint."""
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            if c + 2 < w and grid[r][c + 2] == color and grid[r][c + 1] == 0:
                yield (r, c), (r, c + 2), (r, c + 1)
            if r + 2 < h and grid[r + 2][c] == color and grid[r + 1][c] == 0:
                yield (r, c), (r + 2, c), (r + 1, c)


def _scan_long_diagonal_pairs(grid):
    """Equal-color diagonal pairs at (d, +-d), d >= 3, with a blank between."""
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            for step in (1, -1):
                for d in range(3, max(h, w)):
                    r2, c2 = r + d, c + step * d
                    if not (0 <= r2 < h and 0 <= c2 < w):
                        break
                    if grid[r2][c2] != color:
                        continue
                    betweens = [
                        (r + k, c + step * k) for k in range(1, d)
                    ]
                    if any(grid[rr][cc] == 0 for rr, cc in betweens):
                        yield (r, c), (r2, c2), betweens
                        break


def _scan_mismatch_diagonal_pairs(grid):
    """Different-color nonzero diagonal (2, +-2) endpoints, blank midpoint."""
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            for dc in (2, -2):
                c2 = c + dc
                if not 0 <= c2 < w:
                    continue
                other = grid[r + 2][c2]
                if (
                    other != 0
                    and other != color
                    and grid[r + 1][c + dc // 2] == 0
                ):
                    yield (r, c), (r + 2, c2), (r + 1, c + dc // 2)


def _scan_blocked_diagonal_pairs(grid):
    """Equal-color diagonal (2, +-2) endpoints whose midpoint is occupied."""
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color == 0:
                continue
            for dc in (2, -2):
                c2 = c + dc
                if not 0 <= c2 < w:
                    continue
                if grid[r + 2][c2] == color and grid[r + 1][c + dc // 2] != 0:
                    yield (r, c), (r + 2, c2), (r + 1, c + dc // 2)


def _lawful(grid):
    return not self_check(grid)


def _w_fills_down_right(grid):
    return _lawful(grid) and any(
        pair.orientation == "down_right" for pair in _fillable_pairs(grid)
    )


def _w_fills_down_left(grid):
    return _lawful(grid) and any(
        pair.orientation == "down_left" for pair in _fillable_pairs(grid)
    )


def _w_near_miss_axis_aligned(grid):
    return _lawful(grid) and any(True for _ in _scan_equal_axis_pairs(grid))


def _w_near_miss_wrong_distance(grid):
    return _lawful(grid) and any(True for _ in _scan_long_diagonal_pairs(grid))


def _w_near_miss_different_color(grid):
    return _lawful(grid) and any(
        True for _ in _scan_mismatch_diagonal_pairs(grid)
    )


def _w_near_miss_blocked_midpoint(grid):
    return _lawful(grid) and any(
        True for _ in _scan_blocked_diagonal_pairs(grid)
    )


SEMANTIC_WITNESSES = {
    "fills_down_right": _w_fills_down_right,
    "fills_down_left": _w_fills_down_left,
    "near_miss_axis_aligned": _w_near_miss_axis_aligned,
    "near_miss_wrong_distance": _w_near_miss_wrong_distance,
    "near_miss_different_color": _w_near_miss_different_color,
    "near_miss_blocked_midpoint": _w_near_miss_blocked_midpoint,
}


def _comp_identity(grid):
    return [row[:] for row in grid]


def _comp_one_orientation(orientation):
    def apply(grid):
        out = [row[:] for row in grid]
        for pair in _fillable_pairs(grid):
            if pair.orientation == orientation:
                out[pair.midpoint[0]][pair.midpoint[1]] = pair.color
        return out

    return apply


def _comp_axis_too(grid):
    out = rule_mirror(grid)
    for (r, c), _, (mr, mc) in _scan_equal_axis_pairs(grid):
        out[mr][mc] = grid[r][c]
    return out


def _comp_any_distance(grid):
    out = rule_mirror(grid)
    for (r, c), _, betweens in _scan_long_diagonal_pairs(grid):
        for rr, cc in betweens:
            if grid[rr][cc] == 0:
                out[rr][cc] = grid[r][c]
    return out


def _comp_ignore_color(grid):
    out = rule_mirror(grid)
    for (r, c), _, (mr, mc) in _scan_mismatch_diagonal_pairs(grid):
        out[mr][mc] = grid[r][c]
    return out


def _comp_overwrite_blocked(grid):
    out = rule_mirror(grid)
    for (r, c), _, (mr, mc) in _scan_blocked_diagonal_pairs(grid):
        out[mr][mc] = grid[r][c]
    return out


def _comp_fixed_color(fill_color):
    def apply(grid):
        out = [row[:] for row in grid]
        for pair in _fillable_pairs(grid):
            out[pair.midpoint[0]][pair.midpoint[1]] = fill_color
        return out

    return apply


SEMANTIC_RIVALS = {
    "copy_input": _comp_identity,
    "fill_only_down_right": _comp_one_orientation("down_right"),
    "fill_only_down_left": _comp_one_orientation("down_left"),
    "fill_axis_aligned_too": _comp_axis_too,
    "fill_longer_diagonal_spans": _comp_any_distance,
    "ignore_endpoint_color_equality": _comp_ignore_color,
    "overwrite_blocked_midpoints": _comp_overwrite_blocked,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "fill_axis_aligned_too",
        "fill_longer_diagonal_spans",
        "ignore_endpoint_color_equality",
        "overwrite_blocked_midpoints",
    )
}
WITNESS_RIVALS = {
    "fills_down_right": ["fill_only_down_left"],
    "fills_down_left": ["fill_only_down_right"],
    "near_miss_axis_aligned": ["fill_axis_aligned_too"],
    "near_miss_wrong_distance": ["fill_longer_diagonal_spans"],
    "near_miss_different_color": ["ignore_endpoint_color_equality"],
    "near_miss_blocked_midpoint": ["overwrite_blocked_midpoints"],
}


def lesson_identifiable(demos, query):
    """[] iff every plausible competing rule consistent with all demos gives
    the same query answer as the canonical rule.  Competitors cover the
    documented COUNTER_HYPOTHESES: identity, one-orientation-only,
    axis-aligned fills, longer diagonal spans, color-blind fills, blocked-
    midpoint overwrites, and a fixed fill color."""
    checked = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(demo["input"])
        if errors:
            return [f"demo {index} input off-grammar: {errors[0]}"]
        if demo["output"] != rule_mirror(demo["input"]):
            return [f"demo {index} output does not match the canonical rule"]
        checked.append((demo["input"], demo["output"]))
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    q_errors = self_check(query["input"])
    if q_errors:
        return [f"query input off-grammar: {q_errors[0]}"]
    q_in = query["input"]
    q_answer = rule_mirror(q_in)

    competitors = [
        ("copy-the-input-unchanged", _comp_identity),
        ("fill-only-down-right", _comp_one_orientation("down_right")),
        ("fill-only-down-left", _comp_one_orientation("down_left")),
        ("fill-axis-aligned-midpoints-too", _comp_axis_too),
        ("fill-longer-diagonal-spans", _comp_any_distance),
        ("ignore-endpoint-color-equality", _comp_ignore_color),
        ("overwrite-blocked-midpoints", _comp_overwrite_blocked),
    ]
    fill_colors = {
        pair.color for grid, _ in checked for pair in _fillable_pairs(grid)
    }
    if len(fill_colors) == 1:
        competitors.append(
            (
                f"always-fill-color-{next(iter(fill_colors))}",
                _comp_fixed_color(next(iter(fill_colors))),
            )
        )

    reasons = []
    for name, apply in competitors:
        if all(apply(grid) == output for grid, output in checked):
            if apply(q_in) != q_answer:
                reasons.append(
                    f"competitor '{name}' is consistent with every demo but "
                    "answers the query differently"
                )
    return reasons


def _active_candidates(h: int, w: int) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for r in range(h - 2):
        for c in range(w - 2):
            candidates.append(
                _Candidate(
                    (r, c),
                    (r + 1, c + 1),
                    (r + 2, c + 2),
                    "down_right",
                )
            )
        for c in range(2, w):
            candidates.append(
                _Candidate(
                    (r, c),
                    (r + 1, c - 1),
                    (r + 2, c - 2),
                    "down_left",
                )
            )
    return candidates


def _choose_active_layout(h: int, w: int, pair_count: int, rng) -> list[_Candidate]:
    base = _active_candidates(h, w)
    for _ in range(128):
        candidates = base[:]
        rng.shuffle(candidates)
        selected: list[_Candidate] = []
        used: set[tuple[int, int]] = set()
        first = rng.choice(("down_right", "down_left"))
        required = (first, "down_left" if first == "down_right" else "down_right")
        for orientation in required:
            options = [
                candidate
                for candidate in candidates
                if candidate.orientation == orientation
                and not (candidate.cells & used)
            ]
            if not options:
                break
            chosen = rng.choice(options)
            selected.append(chosen)
            used.update(chosen.cells)
        if len(selected) != 2:
            continue
        for candidate in candidates:
            if len(selected) >= pair_count:
                break
            if candidate.cells & used:
                continue
            selected.append(candidate)
            used.update(candidate.cells)
        if len(selected) == pair_count:
            return selected
    raise ValueError(
        f"could not place {pair_count} disjoint diagonal pairs on {h}x{w}"
    )


def _pair_signature(pair: _Pair) -> tuple:
    return (pair.color, pair.a, pair.midpoint, pair.b)


def _try_decoy(
    grid: list[list[int]],
    reserved: set[tuple[int, int]],
    occupied_values: dict[tuple[int, int], int],
    reserve_cells: set[tuple[int, int]],
    expected_pairs: set[tuple],
) -> bool:
    if reserve_cells & reserved:
        return False
    if any(grid[r][c] != 0 for r, c in occupied_values):
        return False
    trial = [row[:] for row in grid]
    for (r, c), value in occupied_values.items():
        trial[r][c] = value
    if {_pair_signature(pair) for pair in _fillable_pairs(trial)} != expected_pairs:
        return False
    for (r, c), value in occupied_values.items():
        grid[r][c] = value
    reserved.update(reserve_cells)
    return True


def _add_axis_decoy(grid, reserved, color, rng, expected_pairs) -> None:
    h, w = len(grid), len(grid[0])
    candidates: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = []
    for r in range(h):
        for c in range(w - 2):
            candidates.append(((r, c), (r, c + 1), (r, c + 2)))
    for r in range(h - 2):
        for c in range(w):
            candidates.append(((r, c), (r + 1, c), (r + 2, c)))
    rng.shuffle(candidates)
    for a, midpoint, b in candidates:
        if _try_decoy(
            grid,
            reserved,
            {a: color, b: color},
            {a, midpoint, b},
            expected_pairs,
        ):
            return
    raise ValueError("could not place axis-aligned near miss")


def _add_wrong_distance_decoy(grid, reserved, color, rng, expected_pairs) -> None:
    h, w = len(grid), len(grid[0])
    candidates = []
    for r in range(h - 3):
        for c in range(w):
            for dc in (-3, 3):
                c2 = c + dc
                if 0 <= c2 < w:
                    path = {
                        (r, c),
                        (r + 1, c + dc // 3),
                        (r + 2, c + 2 * dc // 3),
                        (r + 3, c2),
                    }
                    candidates.append(((r, c), (r + 3, c2), path))
    rng.shuffle(candidates)
    for a, b, path in candidates:
        if _try_decoy(
            grid,
            reserved,
            {a: color, b: color},
            path,
            expected_pairs,
        ):
            return
    raise ValueError("could not place wrong-distance near miss")


def _add_mismatch_decoy(grid, reserved, colors, rng, expected_pairs) -> None:
    candidates = _active_candidates(len(grid), len(grid[0]))
    rng.shuffle(candidates)
    for candidate in candidates:
        if _try_decoy(
            grid,
            reserved,
            {candidate.a: colors[0], candidate.b: colors[1]},
            set(candidate.cells),
            expected_pairs,
        ):
            return
    raise ValueError("could not place different-color near miss")


def _add_blocked_decoy(
    grid,
    reserved,
    endpoint_color,
    blocker_color,
    rng,
    expected_pairs,
) -> None:
    candidates = _active_candidates(len(grid), len(grid[0]))
    rng.shuffle(candidates)
    for candidate in candidates:
        if _try_decoy(
            grid,
            reserved,
            {
                candidate.a: endpoint_color,
                candidate.midpoint: blocker_color,
                candidate.b: endpoint_color,
            },
            set(candidate.cells),
            expected_pairs,
        ):
            return
    raise ValueError("could not place blocked-midpoint near miss")


def decoy_mode(sample_index: int) -> str:
    """Return the deterministic four-slot curriculum mode."""
    return DECOY_MODES[sample_index % LESSON_SCHEDULE_PERIOD]


def schedule_profile(seed: int, sample_index: int) -> dict[str, object]:
    """Expose the deterministic curriculum slot for census/debug tooling."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    mode = decoy_mode(sample_index)
    return {
        "period": LESSON_SCHEDULE_PERIOD,
        "slot": sample_index % LESSON_SCHEDULE_PERIOD,
        "mode": mode,
        "canonical_anchor": mode == "canonical_profile",
    }


def _default_axis_range(label: str, difficulty) -> tuple[int, int]:
    """Difficulty skews defaults without narrowing the public override domain."""
    ranges = {
        None: {
            "grid_h": (7, 16),
            "grid_w": (7, 16),
            "pair_count": (2, 3),
        },
        "easy": {
            "grid_h": (7, 10),
            "grid_w": (7, 10),
            "pair_count": (2, 2),
        },
        "medium": {
            "grid_h": (9, 13),
            "grid_w": (9, 13),
            "pair_count": (2, 3),
        },
        "hard": {
            "grid_h": (12, 16),
            "grid_w": (12, 16),
            "pair_count": (3, 3),
        },
    }
    return ranges[difficulty][label]


def _draw_axis_int(ctx, label: str, lo: int, hi: int, difficulty) -> int:
    """Consume an exact integer axis while keeping all declared overrides legal."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    default_lo, default_hi = _default_axis_range(label, difficulty)
    value = ctx.draw_rng(f"{label}_default").randint(default_lo, default_hi)
    return ctx.draw_int_strict(label, value, value)


def _build_scene(
    h: int,
    w: int,
    pair_count: int,
    mode: str,
    rng,
) -> list[list[int]]:
    """Construct one scene, raising ValueError when a sampled layout is crowded."""
    active_layout = _choose_active_layout(h, w, pair_count, rng)
    # Color 9 remains unused intentionally, making unsupported repeated-color
    # mutations unambiguous to the validator while retaining ample diversity.
    active_colors = rng.sample(range(1, 9), pair_count)
    grid = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    for color, candidate in zip(active_colors, active_layout):
        grid[candidate.a[0]][candidate.a[1]] = color
        grid[candidate.b[0]][candidate.b[1]] = color
        reserved.update(candidate.cells)

    expected_pairs = {_pair_signature(pair) for pair in _fillable_pairs(grid)}
    if len(expected_pairs) != pair_count:
        raise ValueError("active layout did not produce the requested pair count")

    if mode == "canonical_profile":
        return grid

    unused_colors = [color for color in range(1, 9) if color not in active_colors]
    if mode == "axis_aligned+wrong_distance_and_color":
        _add_axis_decoy(grid, reserved, unused_colors[0], rng, expected_pairs)
        _add_wrong_distance_decoy(
            grid, reserved, unused_colors[1], rng, expected_pairs
        )
        _add_mismatch_decoy(
            grid, reserved, active_colors[:2], rng, expected_pairs
        )
    elif mode == "wrong_distance_and_color+blocked_midpoint":
        _add_wrong_distance_decoy(
            grid, reserved, unused_colors[0], rng, expected_pairs
        )
        _add_mismatch_decoy(
            grid, reserved, active_colors[:2], rng, expected_pairs
        )
        _add_blocked_decoy(
            grid,
            reserved,
            unused_colors[1],
            unused_colors[2],
            rng,
            expected_pairs,
        )
    elif mode == "blocked_midpoint+axis_aligned":
        _add_blocked_decoy(
            grid,
            reserved,
            unused_colors[0],
            active_colors[0],
            rng,
            expected_pairs,
        )
        _add_axis_decoy(grid, reserved, unused_colors[1], rng, expected_pairs)
    else:
        raise ValueError(f"unknown curriculum mode: {mode}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, task-linked lesson scene."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; "
            f"valid axes: {', '.join(sorted(AXES))}"
        )
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    exact_axis_override = any(value is not None for value in overrides.values())
    mode = decoy_mode(sample_index)
    canonical_anchor = mode == "canonical_profile" and not exact_axis_override
    if canonical_anchor:
        anchor_h, anchor_w = _CANONICAL_SHAPES[
            (sample_index // LESSON_SCHEDULE_PERIOD) % len(_CANONICAL_SHAPES)
        ]
        h = ctx.draw_int_strict("grid_h", anchor_h, anchor_h)
        w = ctx.draw_int_strict("grid_w", anchor_w, anchor_w)
        pair_count = ctx.draw_int_strict("pair_count", 3, 3)
    else:
        h = _draw_axis_int(ctx, "grid_h", 7, 16, difficulty)
        w = _draw_axis_int(ctx, "grid_w", 7, 16, difficulty)
        pair_count = _draw_axis_int(ctx, "pair_count", 2, 3, difficulty)

    # Placement is constructive but decoys can make a particular random layout
    # too crowded, especially at 7x7.  Retry deterministically within the local
    # keyed RNG; no global state is read or mutated.
    rng = ctx.draw_rng("layout")
    last_error: Exception | None = None
    for _ in range(256):
        try:
            grid = _build_scene(h, w, pair_count, mode, rng)
        except ValueError as exc:
            last_error = exc
            continue
        errors = self_check(grid)
        if not errors:
            return grid
        last_error = ValueError("; ".join(errors))
    raise ValueError(
        f"could not construct a valid {h}x{w} {mode!r} scene after retries: "
        f"{last_error}"
    )
