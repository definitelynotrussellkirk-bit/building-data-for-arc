"""Generator for ``fa51c5b2de09`` — bridge exactly two-cell gaps.

Each nonzero color marks exactly two aligned endpoints.  When the endpoints are
three cells apart, the two intervening background cells are filled with that
color.  Same-color pairs at distance two or four are distractors and remain
unchanged.  Row bridges are applied first and column bridges second, both read
from the original input, so a perpendicular crossing is colored by the column
bridge.

Four consecutive ``sample_index`` values cover a canonical-scale anchor,
distance-two and distance-four distractors, and a crossing-precedence example.
This makes every sliding four-example lesson refute the principal shortcuts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fa51c5b2de09"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "aef86a306de9"

SUMMARY = (
    "Every nonzero color appears as two aligned endpoints. If the endpoints "
    "are exactly three cells apart, fill the two intervening zero cells with "
    "that color. Pairs at distance two or four are distractors and stay "
    "unchanged. Horizontal bridges are written first and vertical bridges "
    "second from the original input, so a perpendicular gap crossing takes "
    "the vertical bridge color. Four-example schedules include canonical "
    "scale, both distractor distances, both orientations, and crossing "
    "precedence."
)

INVARIANTS = [
    "the grid is rectangular with background color 0",
    "each nonzero color occurs exactly twice as one horizontal or vertical pair",
    "pair endpoint distance is exactly 2, 3, or 4 cells",
    "at least one distance-3 pair is present",
    "distance-2 and distance-4 pairs are negative controls and are not bridged",
    "pair endpoints never lie inside another pair's interval",
    "interior overlap is allowed only for one perpendicular distance-3 crossing",
    "row bridges are applied before column bridges, both detected in the input",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "scheduled 9..16", "valid": "9..16"},
    "bridge_count": {"type": "int", "default": "scheduled 2..5", "valid": "1..5"},
    "n_distractor": {"type": "int", "default": "scheduled 0..3", "valid": "0..3"},
}

# Every boundary combination is constructible.  The maximum request is eight
# disjoint colored pairs in an 8x9 grid, which the backtracking layout handles.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "canonical_anchor",
    "distance_two_control",
    "distance_four_control",
    "crossing_precedence",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
_CANONICAL_PROFILES = ((8, 10, 4), (9, 9, 4), (10, 11, 4), (9, 12, 5))


@dataclass(frozen=True)
class _Pair:
    r: int
    c: int
    axis: str
    dist: int

    @property
    def endpoints(self) -> tuple[tuple[int, int], tuple[int, int]]:
        if self.axis == "h":
            return (self.r, self.c), (self.r, self.c + self.dist)
        return (self.r, self.c), (self.r + self.dist, self.c)

    @property
    def interior(self) -> frozenset[tuple[int, int]]:
        if self.axis == "h":
            return frozenset((self.r, self.c + step) for step in range(1, self.dist))
        return frozenset((self.r + step, self.c) for step in range(1, self.dist))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every four consecutive indices contain all decisive controls."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _grid_errors(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _analyze_pairs(grid) -> tuple[list[tuple[int, _Pair]], list[str]]:
    """Recover one pair per nonzero color and reject ambiguous pair grammars."""
    _, _, errors = _grid_errors(grid)
    if errors:
        return [], errors
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))
    if not by_color:
        return [], ["at least one nonzero endpoint pair is required"]

    pairs: list[tuple[int, _Pair]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} must occur exactly twice, found {len(cells)}")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r1 == r2:
            dist = abs(c2 - c1)
            pair = _Pair(r1, min(c1, c2), "h", dist)
        elif c1 == c2:
            dist = abs(r2 - r1)
            pair = _Pair(min(r1, r2), c1, "v", dist)
        else:
            errors.append(f"color {color} endpoints must share one row or column")
            continue
        if pair.dist not in (2, 3, 4):
            errors.append(
                f"color {color} endpoint distance must be 2, 3, or 4, found {pair.dist}"
            )
        pairs.append((color, pair))

    for i, (color_a, pair_a) in enumerate(pairs):
        endpoints_a = set(pair_a.endpoints)
        for color_b, pair_b in pairs[i + 1 :]:
            endpoints_b = set(pair_b.endpoints)
            if endpoints_a & endpoints_b:
                errors.append(f"colors {color_a} and {color_b} share an endpoint")
            if endpoints_a & pair_b.interior or endpoints_b & pair_a.interior:
                errors.append(
                    f"an endpoint of color {color_a} or {color_b} lies inside the other interval"
                )
            overlap = pair_a.interior & pair_b.interior
            if overlap and not (
                pair_a.dist == pair_b.dist == 3
                and pair_a.axis != pair_b.axis
                and len(overlap) == 1
            ):
                errors.append(
                    f"colors {color_a} and {color_b} have an illegal interval overlap"
                )
    return pairs, errors


def _bridge_pairs(grid) -> list[tuple[int, _Pair]]:
    pairs, errors = _analyze_pairs(grid)
    return [] if errors else [(color, pair) for color, pair in pairs if pair.dist == 3]


def _distractor_pairs(grid) -> list[tuple[int, _Pair]]:
    pairs, errors = _analyze_pairs(grid)
    return [] if errors else [(color, pair) for color, pair in pairs if pair.dist in (2, 4)]


def _has_crossing(grid) -> bool:
    bridges = _bridge_pairs(grid)
    for i, (_, first) in enumerate(bridges):
        for _, second in bridges[i + 1 :]:
            if first.axis != second.axis and first.interior & second.interior:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the pair grammar and reject malformed or shortcut-hiding scenes."""
    del difficulty
    height, width, errors = _grid_errors(grid)
    if errors:
        return errors
    if not (4 <= height <= 30 and 4 <= width <= 30):
        errors.append(f"grid shape {height}x{width} is outside ARC bounds 4..30")

    pairs, pair_errors = _analyze_pairs(grid)
    errors.extend(pair_errors)
    if pair_errors:
        return errors
    bridges = [pair for _, pair in pairs if pair.dist == 3]
    if not bridges:
        errors.append("at least one exactly-two-gap bridge pair is required")
    if len(pairs) > 9:
        errors.append(f"at most nine distinct nonzero pair colors are supported, found {len(pairs)}")

    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(f"{axis} requested {expected!r}, observed {observed[axis]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Narrow profile shared by all four canonical train/test inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    pair_count = len(_bridge_pairs(grid)) + len(_distractor_pairs(grid))
    if (height, width) not in {(h, w) for h, w, _ in _CANONICAL_PROFILES}:
        reasons.append(f"shape {height}x{width} is not a canonical shape")
    if pair_count not in (4, 5):
        reasons.append(f"canonical scenes contain four or five pairs, found {pair_count}")
    if _distractor_pairs(grid):
        reasons.append("canonical scenes contain no distance-2/4 distractors")
    orientations = {pair.axis for _, pair in _bridge_pairs(grid)}
    if orientations != {"h", "v"}:
        reasons.append("canonical scenes contain both horizontal and vertical bridges")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "bridge_count": len(_bridge_pairs(grid)),
        "n_distractor": len(_distractor_pairs(grid)),
    }


def rule_mirror(grid):
    """Python mirror of the selected Racket rule, used only for checks."""
    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r in range(height):
        for c in range(width - 3):
            value = grid[r][c]
            if (
                value != 0
                and grid[r][c + 1] == 0
                and grid[r][c + 2] == 0
                and grid[r][c + 3] == value
            ):
                out[r][c + 1] = value
                out[r][c + 2] = value
    for r in range(height - 3):
        for c in range(width):
            value = grid[r][c]
            if (
                value != 0
                and grid[r + 1][c] == 0
                and grid[r + 2][c] == 0
                and grid[r + 3][c] == value
            ):
                out[r + 1][c] = value
                out[r + 2][c] = value
    return out


def _rival_fill_all_aligned(grid):
    """Wrong shortcut: fill every aligned pair at distance 2, 3, or 4."""
    out = [list(row) for row in grid]
    pairs, errors = _analyze_pairs(grid)
    if errors:
        return out
    # Preserve the true rule's row-before-column order while widening distance.
    for axis in ("h", "v"):
        for color, pair in pairs:
            if pair.axis == axis:
                for r, c in pair.interior:
                    out[r][c] = color
    return out


def _rival_horizontal_only(grid):
    out = [list(row) for row in grid]
    for color, pair in _bridge_pairs(grid):
        if pair.axis == "h":
            for r, c in pair.interior:
                out[r][c] = color
    return out


def _rival_vertical_only(grid):
    out = [list(row) for row in grid]
    for color, pair in _bridge_pairs(grid):
        if pair.axis == "v":
            for r, c in pair.interior:
                out[r][c] = color
    return out


def _rival_row_wins_crossing(grid):
    """Wrong tie-break: apply columns first, then rows, so rows win crossings."""
    out = [list(row) for row in grid]
    bridges = _bridge_pairs(grid)
    for axis in ("v", "h"):
        for color, pair in bridges:
            if pair.axis == axis:
                for r, c in pair.interior:
                    out[r][c] = color
    return out


def _valid(grid) -> bool:
    return not self_check(grid)


def _witness_distance_two(grid) -> bool:
    return _valid(grid) and any(pair.dist == 2 for _, pair in _distractor_pairs(grid))


def _witness_distance_four(grid) -> bool:
    return _valid(grid) and any(pair.dist == 4 for _, pair in _distractor_pairs(grid))


def _witness_horizontal(grid) -> bool:
    return _valid(grid) and any(pair.axis == "h" for _, pair in _bridge_pairs(grid))


def _witness_vertical(grid) -> bool:
    return _valid(grid) and any(pair.axis == "v" for _, pair in _bridge_pairs(grid))


def _witness_crossing(grid) -> bool:
    return _valid(grid) and _has_crossing(grid)


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "distance_two_refutes_fill_any_gap": _witness_distance_two,
    "distance_four_refutes_fill_any_gap": _witness_distance_four,
    "horizontal_bridge_refutes_vertical_only": _witness_horizontal,
    "vertical_bridge_refutes_horizontal_only": _witness_vertical,
    "crossing_refutes_row_wins": _witness_crossing,
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "fill_any_aligned_gap": _rival_fill_all_aligned,
    "vertical_only": _rival_vertical_only,
    "horizontal_only": _rival_horizontal_only,
    "row_wins_crossing": _rival_row_wins_crossing,
}

WITNESS_RIVALS = {
    "distance_two_refutes_fill_any_gap": ["fill_any_aligned_gap"],
    "distance_four_refutes_fill_any_gap": ["fill_any_aligned_gap"],
    "horizontal_bridge_refutes_vertical_only": ["vertical_only"],
    "vertical_bridge_refutes_horizontal_only": ["horizontal_only"],
    "crossing_refutes_row_wins": ["row_wins_crossing"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All canonical inputs contain only distance-3 pairs, so this wider-gap rule
# fits every canonical demonstration and needs generated negative controls.
CANONICAL_SHORTCUTS = {"fill_any_aligned_gap": _rival_fill_all_aligned}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each sliding four-demo lesson to kill every named rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the exact-gap rule")
        for name, rival in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or rival(demo["input"]) != expected
    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _candidate_pairs(height: int, width: int, dist: int, axis: str) -> list[_Pair]:
    if axis == "h":
        return [
            _Pair(r, c, axis, dist)
            for r in range(height)
            for c in range(width - dist)
        ]
    return [
        _Pair(r, c, axis, dist)
        for r in range(height - dist)
        for c in range(width)
    ]


def _compatible(candidate: _Pair, selected: list[_Pair]) -> bool:
    endpoints = set(candidate.endpoints)
    for other in selected:
        other_endpoints = set(other.endpoints)
        if endpoints & other_endpoints:
            return False
        if endpoints & other.interior or other_endpoints & candidate.interior:
            return False
        # Crossings are inserted explicitly; all other interior overlaps are
        # excluded so distractors stay unchanged and witnesses remain decisive.
        if candidate.interior & other.interior:
            return False
    return True


def _crossing_pairs(height: int, width: int) -> list[tuple[_Pair, _Pair]]:
    horizontals = _candidate_pairs(height, width, 3, "h")
    verticals = _candidate_pairs(height, width, 3, "v")
    crossings: list[tuple[_Pair, _Pair]] = []
    for horizontal in horizontals:
        for vertical in verticals:
            overlap = horizontal.interior & vertical.interior
            if len(overlap) != 1:
                continue
            if set(horizontal.endpoints) & (set(vertical.endpoints) | vertical.interior):
                continue
            if set(vertical.endpoints) & horizontal.interior:
                continue
            crossings.append((horizontal, vertical))
    return crossings


def _select_slots(
    rng,
    height: int,
    width: int,
    slots: list[tuple[int, str | None]],
    selected: list[_Pair],
) -> list[_Pair] | None:
    if not slots:
        return list(selected)
    dist, axis = slots[0]
    axes = (axis,) if axis is not None else ("h", "v")
    options = [
        pair
        for candidate_axis in axes
        for pair in _candidate_pairs(height, width, dist, candidate_axis)
        if _compatible(pair, selected)
    ]
    rng.shuffle(options)
    # The candidate space is highly redundant.  A bounded deterministic search
    # keeps worst-case override checks fast while retaining ample alternatives.
    for pair in options[:160]:
        found = _select_slots(rng, height, width, slots[1:], selected + [pair])
        if found is not None:
            return found
    return None


def _construct_pairs(
    height: int,
    width: int,
    bridge_count: int,
    distractor_count: int,
    *,
    rng,
    force_crossing: bool,
    distractor_mode: str,
    require_both_orientations: bool,
) -> list[_Pair]:
    selected: list[_Pair] = []
    remaining_bridges = bridge_count
    if force_crossing:
        if bridge_count < 2:
            raise ValueError("crossing profile requires at least two bridge pairs")
        choices = _crossing_pairs(height, width)
        rng.shuffle(choices)
        if not choices:
            raise ValueError("no perpendicular crossing fits requested dimensions")
        selected.extend(choices[0])
        remaining_bridges -= 2

    bridge_slots: list[tuple[int, str | None]] = []
    existing_axes = {pair.axis for pair in selected}
    if require_both_orientations and bridge_count >= 2:
        for axis in ("h", "v"):
            if axis not in existing_axes and remaining_bridges:
                bridge_slots.append((3, axis))
                remaining_bridges -= 1
    bridge_slots.extend((3, None) for _ in range(remaining_bridges))

    if distractor_mode == "distance_two":
        distractor_distances = [2] * distractor_count
    elif distractor_mode == "distance_four":
        distractor_distances = [4] * distractor_count
    elif distractor_mode == "mixed" and distractor_count:
        distractor_distances = [2, 4] + [2 if i % 2 == 0 else 4 for i in range(distractor_count - 2)]
        distractor_distances = distractor_distances[:distractor_count]
    else:
        distractor_distances = [2 if i % 2 == 0 else 4 for i in range(distractor_count)]
    slots = bridge_slots + [(dist, None) for dist in distractor_distances]
    found = _select_slots(rng, height, width, slots, selected)
    if found is None:
        # Deterministic packed fallback for exact override boundary cases.  It
        # still goes through the same structural checks and never changes axes.
        packed_slots = [(3, "h")] * bridge_count + [
            (dist, "h") for dist in distractor_distances
        ]
        found = _select_slots(rng, height, width, packed_slots, [])
    if found is None:
        raise ValueError(
            f"could not place bridge_count={bridge_count}, n_distractor={distractor_count} "
            f"in {height}x{width}"
        )
    return found


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _profile_defaults(seed: int, sample_index: int, difficulty) -> dict[str, object]:
    profile = schedule_profile(seed, sample_index, difficulty)
    selector = (int(seed) * 17 + int(sample_index) * 31) % 97
    if profile == "canonical_anchor":
        height, width, bridges = _CANONICAL_PROFILES[selector % len(_CANONICAL_PROFILES)]
        return {
            "profile": profile,
            "grid_h": height,
            "grid_w": width,
            "bridge_count": bridges,
            "n_distractor": 0,
            "force_crossing": selector % 2 == 0,
            "distractor_mode": "none",
            "require_both": True,
        }
    if difficulty == "easy":
        height, width, bridges, distractors = 8 + selector % 3, 9 + (selector // 3) % 4, 2, 1
    elif difficulty == "hard":
        height, width, bridges, distractors = 12 + selector % 3, 14 + (selector // 3) % 3, 5, 3
    else:
        height, width, bridges, distractors = 10 + selector % 3, 11 + (selector // 3) % 4, 3, 2
    return {
        "profile": profile,
        "grid_h": height,
        "grid_w": width,
        "bridge_count": bridges,
        "n_distractor": 0 if profile == "crossing_precedence" else distractors,
        "force_crossing": profile == "crossing_precedence",
        "distractor_mode": (
            "distance_two" if profile == "distance_two_control" else
            "distance_four" if profile == "distance_four_control" else
            "none"
        ),
        "require_both": True,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(seed, sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", int(defaults["grid_h"]), 8, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", int(defaults["grid_w"]), 9, 16)
    bridge_count = _scheduled_int(
        ctx, overrides, "bridge_count", int(defaults["bridge_count"]), 1, 5
    )
    distractor_count = _scheduled_int(
        ctx, overrides, "n_distractor", int(defaults["n_distractor"]), 0, 3
    )

    # Explicit controls request exact geometry, not a curriculum profile.  Do
    # not let the profile introduce an incompatible hidden crossing/distance.
    force_crossing = bool(defaults["force_crossing"]) and not overrides
    require_both = bool(defaults["require_both"]) and not overrides
    distractor_mode = str(defaults["distractor_mode"]) if not overrides else "mixed"

    layout_rng = ctx.draw_rng("layout")
    pairs = _construct_pairs(
        height,
        width,
        bridge_count,
        distractor_count,
        rng=layout_rng,
        force_crossing=force_crossing,
        distractor_mode=distractor_mode,
        require_both_orientations=require_both,
    )
    colors = ctx.draw_distinct_colors("pair_colors", n=len(pairs), exclude={0})
    ordered_pairs = sorted(pairs, key=lambda pair: (pair.r, pair.c, pair.axis, pair.dist))
    grid = full_grid(height, width, 0)
    for color, pair in zip(colors, ordered_pairs):
        for r, c in pair.endpoints:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if observed[axis] != requested:
            raise ValueError(
                f"realized axis {axis!r}={observed[axis]!r} does not match keyed draw {requested!r}"
            )
    return [row[:] for row in grid]
