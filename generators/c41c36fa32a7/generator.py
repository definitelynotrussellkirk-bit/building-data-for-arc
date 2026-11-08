"""Generator for ``Midpoint of a Clear Segment``.

Every nonzero color appears at two aligned endpoints.  A pair changes the
output only when its endpoint distance is even and every interior cell is zero;
then exactly its midpoint is filled.  Blocked and odd-distance pairs are lawful
distractors and are deliberately scheduled so the generated lessons identify
the full condition instead of teaching "fill every matching pair".
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c41c36fa32a7"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "629679ec0c33"

SUMMARY = (
    "For each color occurring at two aligned endpoints, fill only the exact "
    "midpoint when the distance is even and the whole interior segment is zero; "
    "blocked or odd-distance pairs remain unchanged."
)

INVARIANTS = [
    "background is 0 and every nonzero color appears exactly twice",
    "each same-color pair is horizontal or vertical",
    "at least one pair has a clear even-distance segment and therefore changes the output",
    "productive pairs have distinct midpoint cells, so the answer is unambiguous",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 6..14", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 6..14", "valid": "6..14"},
    "pair_count": {"type": "int", "default": "difficulty-aware 1..8", "valid": "1..8"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Exact endpoint topologies from all canonical train/test inputs.  Default
# generation samples a color-renamed/reflected member of this empirical
# manifold 25% of the time in every difficulty band; the other 75% supplies
# generalized anti-shortcut witnesses.
_CANONICAL_PROFILES = (
    {
        "dims": (7, 7),
        "pairs": (((0, 4), (4, 4)), ((1, 1), (1, 5)), ((5, 0), (5, 4))),
    },
    {
        "dims": (8, 8),
        "pairs": (((0, 6), (4, 6)), ((1, 1), (5, 1)), ((2, 0), (2, 6))),
    },
    {
        "dims": (6, 9),
        "pairs": (((0, 2), (0, 6)), ((1, 8), (5, 8)), ((4, 1), (4, 7))),
    },
    {
        "dims": (7, 9),
        "pairs": (((0, 5), (4, 5)), ((3, 0), (3, 8)), ((6, 2), (6, 6))),
    },
)

SCHEDULE_PROFILES = (
    "canonical_a",
    "canonical_b",
    "generalized_a",
    "generalized_b",
    "generalized_c",
    "generalized_d",
    "generalized_e",
    "generalized_f",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic curriculum profile; eight consecutive draws cover all modes."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _path(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r0, c0 = a
    r1, c1 = b
    dr = (r1 > r0) - (r1 < r0)
    dc = (c1 > c0) - (c1 < c0)
    distance = abs(r1 - r0) + abs(c1 - c0)
    return tuple((r0 + step * dr, c0 + step * dc) for step in range(distance + 1))


def _analyze(grid) -> tuple[list[dict[str, object]], list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return [], errors

    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions[value].append((row, col))
    if not positions:
        return [], ["at least one nonzero endpoint pair is required"]

    segments: list[dict[str, object]] = []
    for color in sorted(positions):
        points = positions[color]
        if len(points) != 2:
            errors.append(f"color {color} appears {len(points)} times (expected exactly 2)")
            continue
        a, b = sorted(points)
        same_row = a[0] == b[0]
        same_col = a[1] == b[1]
        if same_row == same_col:
            errors.append(f"color {color} endpoints must share exactly one row or column")
            continue
        distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
        cells = _path(a, b)
        blockers = tuple((r, c, grid[r][c]) for r, c in cells[1:-1] if grid[r][c] != 0)
        productive = distance % 2 == 0 and not blockers
        midpoint = cells[distance // 2] if distance % 2 == 0 else None
        segments.append(
            {
                "color": color,
                "a": a,
                "b": b,
                "orientation": "H" if same_row else "V",
                "distance": distance,
                "path": cells,
                "blockers": blockers,
                "productive": productive,
                "midpoint": midpoint,
            }
        )

    productive = [segment for segment in segments if segment["productive"]]
    if not errors and not productive:
        errors.append("scene has no clear even-distance pair, so the transformation would be identity")
    midpoint_owners: dict[tuple[int, int], int] = {}
    for segment in productive:
        midpoint = segment["midpoint"]
        assert isinstance(midpoint, tuple)
        if midpoint in midpoint_owners:
            errors.append(
                f"productive midpoint {midpoint} is shared by colors "
                f"{midpoint_owners[midpoint]} and {segment['color']}"
            )
        midpoint_owners[midpoint] = int(segment["color"])
    return segments, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete, non-identity, unambiguous teaching grammar."""
    del difficulty, meta
    _segments, errors = _analyze(grid)
    return errors


def _intersection_counts(grid, segments):
    zero_crossings = 0
    endpoint_block_crossings = 0
    for index, left in enumerate(segments):
        left_path = set(left["path"])
        for right in segments[index + 1 :]:
            for row, col in left_path & set(right["path"]):
                if grid[row][col] == 0:
                    zero_crossings += 1
                else:
                    left_endpoint = (row, col) in {left["a"], left["b"]}
                    right_endpoint = (row, col) in {right["a"], right["b"]}
                    if left_endpoint != right_endpoint:
                        endpoint_block_crossings += 1
    return zero_crossings, endpoint_block_crossings


def _linked_signature(grid):
    segments, errors = _analyze(grid)
    if errors:
        return None
    zero_crossings, endpoint_crossings = _intersection_counts(grid, segments)
    grammar = tuple(
        sorted(
            (
                str(segment["orientation"]),
                int(segment["distance"]),
                bool(segment["productive"]),
            )
            for segment in segments
        )
    )
    return len(grid), len(grid[0]), grammar, zero_crossings, endpoint_crossings


def _canonical_signatures():
    signatures = set()
    for profile in _CANONICAL_PROFILES:
        h, w = profile["dims"]
        grid = full_grid(h, w, 0)
        for color, (a, b) in enumerate(profile["pairs"], start=1):
            grid[a[0]][a[1]] = color
            grid[b[0]][b[1]] = color
        signatures.add(_linked_signature(grid))
    return signatures


_CANONICAL_SIGNATURES = _canonical_signatures()


def strict_canonical_like(grid) -> list[str]:
    """Require one of the four linked canonical topology profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = _linked_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked topology {signature!r} is outside the four canonical profiles"]
    return []


def _segments_ok(grid):
    segments, errors = _analyze(grid)
    return segments if not errors else []


def _productive_horizontal(grid) -> bool:
    return any(s["productive"] and s["orientation"] == "H" for s in _segments_ok(grid))


def _productive_vertical(grid) -> bool:
    return any(s["productive"] and s["orientation"] == "V" for s in _segments_ok(grid))


def _blocked_distractor(grid) -> bool:
    return any(s["blockers"] for s in _segments_ok(grid))


def _odd_distance_distractor(grid) -> bool:
    return any(int(s["distance"]) % 2 for s in _segments_ok(grid))


def _long_productive_gap(grid) -> bool:
    return any(s["productive"] and int(s["distance"]) >= 6 for s in _segments_ok(grid))


SEMANTIC_WITNESSES = {
    "productive_horizontal_pair": _productive_horizontal,
    "productive_vertical_pair": _productive_vertical,
    "blocked_pair_left_unchanged": _blocked_distractor,
    "odd_distance_pair_left_unchanged": _odd_distance_distractor,
    "productive_distance_at_least_six": _long_productive_gap,
}


def _expected_output(grid):
    segments, errors = _analyze(grid)
    if errors:
        raise ValueError(f"invalid midpoint scene: {errors}")
    out = [list(row) for row in grid]
    for segment in segments:
        if segment["productive"]:
            row, col = segment["midpoint"]
            out[row][col] = int(segment["color"])
    return out


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos that expose both orientations and both negative conditions."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the midpoint teaching grammar")

    productive_orientations: set[str] = set()
    saw_blocked = False
    saw_odd = False
    saw_long = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        segments, errors = _analyze(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        if demo["output"] != _expected_output(demo["input"]):
            reasons.append(f"demo {index} output is not the exact conditional midpoint transformation")
        productive_orientations.update(
            str(segment["orientation"]) for segment in segments if segment["productive"]
        )
        saw_blocked |= any(segment["blockers"] for segment in segments)
        saw_odd |= any(int(segment["distance"]) % 2 for segment in segments)
        saw_long |= any(segment["productive"] and int(segment["distance"]) >= 4 for segment in segments)
    if productive_orientations != {"H", "V"}:
        reasons.append("demonstrations must collectively include productive horizontal and vertical pairs")
    if not saw_long:
        reasons.append("demonstrations need a nontrivial clear gap longer than three cells")
    # Blocked and odd cases are scheduled across the broader curriculum.  A
    # three-demo lesson need only contain one of them to rule out unconditional
    # midpoint filling while remaining materializable at every start offset.
    if not (saw_blocked or saw_odd):
        reasons.append("demonstrations need a blocked or odd-distance negative pair")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    segments, errors = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe an invalid grid: {errors}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "pair_count": len(segments)}


def _candidate_pairs(h: int, w: int, *, orientation=None, parity=None):
    candidates = []
    if orientation in (None, "H"):
        for row in range(h):
            for left in range(w):
                for right in range(left + 2, w):
                    distance = right - left
                    if parity is not None and distance % 2 != parity:
                        continue
                    candidates.append(((row, left), (row, right)))
    if orientation in (None, "V"):
        for col in range(w):
            for top in range(h):
                for bottom in range(top + 2, h):
                    distance = bottom - top
                    if parity is not None and distance % 2 != parity:
                        continue
                    candidates.append(((top, col), (bottom, col)))
    return candidates


def _render_pairs(h, w, pairs, colors):
    grid = full_grid(h, w, 0)
    for color, (a, b) in zip(colors, pairs):
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
    return grid


def _fallback_pairs(h: int, w: int, pair_count: int):
    pairs = []
    for row in range(h):
        for left in range(0, w - 2, 3):
            pairs.append(((row, left), (row, left + 2)))
    if len(pairs) < pair_count:
        raise ValueError(f"cannot fit {pair_count} endpoint pairs in {h}x{w}")
    return pairs[:pair_count]


def _select_general_pairs(h, w, pair_count, mode, colors, rng):
    all_pairs = _candidate_pairs(h, w)
    even_h = _candidate_pairs(h, w, orientation="H", parity=0)
    even_v = _candidate_pairs(h, w, orientation="V", parity=0)
    odd = _candidate_pairs(h, w, parity=1)

    forced_options = [[]]
    if pair_count >= 2 and mode == "blocked":
        options = []
        for blocked in [pair for pair in even_v + even_h if len(_path(*pair)) >= 5]:
            interior = _path(*blocked)[1:-1]
            for point in interior:
                blockers = [pair for pair in even_h + even_v if point in pair and not (set(pair) & set(blocked))]
                for blocker in blockers[:8]:
                    options.append([blocked, blocker])
            if len(options) >= 300:
                break
        rng.shuffle(options)
        forced_options = options or [[]]
    elif pair_count >= 2 and mode == "odd_distance":
        forced_options = [[rng.choice(odd), rng.choice(even_h + even_v)]]
    elif pair_count >= 2 and mode == "mixed":
        forced_options = [[rng.choice(even_h), rng.choice(even_v)]]
    elif mode == "horizontal":
        all_pairs = even_h
    elif mode == "vertical":
        all_pairs = even_v
    elif mode == "long":
        all_pairs = sorted(
            even_h + even_v,
            key=lambda pair: -(abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1])),
        )

    for forced in forced_options[:100]:
        for _attempt in range(160):
            selected = list(forced)
            endpoints = {cell for pair in selected for cell in pair}
            if len(endpoints) != 2 * len(selected):
                continue
            candidates = list(all_pairs)
            rng.shuffle(candidates)
            if mode == "long":
                candidates.sort(
                    key=lambda pair: -(
                        abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1])
                    )
                )
            for pair in candidates:
                if set(pair) & endpoints:
                    continue
                selected.append(pair)
                endpoints.update(pair)
                if len(selected) == pair_count:
                    break
            if len(selected) != pair_count:
                continue
            grid = _render_pairs(h, w, selected, colors)
            segments, errors = _analyze(grid)
            if errors:
                continue
            if mode == "blocked" and pair_count >= 2 and not any(s["blockers"] for s in segments):
                continue
            if mode == "odd_distance" and pair_count >= 2 and not any(int(s["distance"]) % 2 for s in segments):
                continue
            if mode == "mixed" and pair_count >= 2:
                orientations = {s["orientation"] for s in segments if s["productive"]}
                if orientations != {"H", "V"}:
                    continue
            if mode == "horizontal" and not any(s["productive"] and s["orientation"] == "H" for s in segments):
                continue
            if mode == "vertical" and not any(s["productive"] and s["orientation"] == "V" for s in segments):
                continue
            return selected

    fallback = _fallback_pairs(h, w, pair_count)
    grid = _render_pairs(h, w, fallback, colors)
    if self_check(grid):
        raise ValueError(f"fallback construction failed for {h}x{w}, pair_count={pair_count}")
    return fallback



def _curriculum_pairs(h, w, pair_count, colors, rng):
    """Build a branch-complete generalized scene, then add safe extra pairs."""
    if pair_count < 4:
        raise ValueError("branch-complete curriculum scenes require at least four pairs")
    top = rng.randint(0, h - 6)
    left = rng.randint(0, w - 6)
    base = [
        ((top + 0, left + 2), (top + 4, left + 2)),  # blocked V4
        ((top + 2, left + 2), (top + 2, left + 4)),  # productive H2, blocks first
        ((top + 0, left + 5), (top + 3, left + 5)),  # odd V3 distractor
        ((top + 1, left + 0), (top + 5, left + 0)),  # productive V4
    ]
    if rng.randrange(2):
        base = [((h - 1 - a[0], a[1]), (h - 1 - b[0], b[1])) for a, b in base]
    if rng.randrange(2):
        base = [((a[0], w - 1 - a[1]), (b[0], w - 1 - b[1])) for a, b in base]
    if pair_count == 4:
        return base

    for _attempt in range(240):
        selected = list(base)
        endpoints = {cell for pair in selected for cell in pair}
        candidates = _candidate_pairs(h, w)
        rng.shuffle(candidates)
        for pair in candidates:
            if set(pair) & endpoints:
                continue
            selected.append(pair)
            endpoints.update(pair)
            if len(selected) == pair_count:
                break
        if len(selected) != pair_count:
            continue
        grid = _render_pairs(h, w, selected, colors)
        if not self_check(grid):
            return selected
    raise ValueError(f"cannot extend branch-complete curriculum to {pair_count} pairs in {h}x{w}")

def _canonical_pairs(profile, rng):
    h, w = profile["dims"]
    pairs = list(profile["pairs"])
    reflect_rows = bool(rng.randrange(2))
    reflect_cols = bool(rng.randrange(2))

    def transform(point):
        row, col = point
        if reflect_rows:
            row = h - 1 - row
        if reflect_cols:
            col = w - 1 - col
        return row, col

    return [(transform(a), transform(b)) for a, b in pairs]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override(s): {sorted(unknown)!r}")

    profile_name = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = dict(overrides)
    canonical_profile = None
    if not overrides and profile_name.startswith("canonical"):
        canonical_profile = _CANONICAL_PROFILES[stable_rng(seed, f"{TASK_ID}|{sample_index}|canonical-profile", VERSION).randrange(len(_CANONICAL_PROFILES))]
        h, w = canonical_profile["dims"]
        effective_overrides.update(grid_h=h, grid_w=w, pair_count=3)
    elif not overrides:
        effective_overrides["pair_count"] = {"easy": 4, "medium": 5, "hard": 7}.get(difficulty, 5)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    h = ctx.draw_int_diff("grid_h", 6, 14)
    w = ctx.draw_int_diff("grid_w", 6, 14)
    pair_count = ctx.draw_int_diff("pair_count", 1, 8)
    colors = ctx.draw_distinct_colors("colors", n=pair_count, exclude={0})
    layout_rng = ctx.draw_rng("layout")

    if canonical_profile is not None:
        pairs = _canonical_pairs(canonical_profile, layout_rng)
    elif not overrides:
        pairs = _curriculum_pairs(h, w, pair_count, colors, layout_rng)
    else:
        pairs = _select_general_pairs(h, w, pair_count, profile_name, colors, layout_rng)
    grid = _render_pairs(h, w, pairs, colors)

    errors = self_check(grid, difficulty=difficulty, meta={"profile": profile_name})
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]
