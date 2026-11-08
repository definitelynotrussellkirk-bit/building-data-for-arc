"""Generator for arc_additional_puzzle_bank_volume4:M24.

Rule: red (2) is a source marker and green (3) is a destination marker.  Move
one connected non-marker payload by the red->green vector onto a blank grid,
preserving every payload color and dropping the markers/original payload.

The public ARC examples are narrower than the rule: all use an up-right vector
and a monochrome payload.  The schedule below deliberately keeps regular
canonical-scale anchors while making every two-demo subset of every cyclic
three-sample lesson window include both a non-up-right case and a multicolor
case.  That prevents those two public correlations from becoming curriculum
shortcuts even when any one sample is held out as the query.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a8932958b14"
TASK_ID = "1a8932958b14"
VERSION = "3.1.0"
RULE_HASH = "42869e666344"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains exactly one connected payload (colors other "
    "than 0/2/3), one red source marker (2), and one green destination marker "
    "(3). Translate the entire payload, preserving all of its colors, by the "
    "vector from red to green onto a blank grid; remove both markers and the "
    "original payload. Grid dimensions, payload size/colors, vector direction, "
    "shape, placement, and marker positions vary."
)

INVARIANTS = [
    "exactly one red (2) source marker and one green (3) destination marker",
    "all non-0/2/3 cells form one nonempty 4-connected payload object",
    "the red->green vector is nonzero and keeps every translated payload cell in bounds",
    "the output is a blank grid containing only the color-preserving translated payload",
]

_DIRECTIONS = (
    "up_right",
    "down_left",
    "down_right",
    "up_left",
    "left",
    "right",
    "up",
    "down",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three canonical-scale anchor slots per nine; otherwise difficulty-shaped",
        "valid": "9..20",
    },
    "grid_w": {
        "type": "int",
        "default": "three canonical-scale anchor slots per nine; otherwise difficulty-shaped",
        "valid": "9..20",
    },
    "payload_size": {
        "type": "int",
        "default": "difficulty-shaped, with canonical anchors at size 4",
        "valid": "3..9",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled so every two-demo window contains a multicolor payload",
        "valid": "1..3",
    },
    "vector_direction": {
        "type": "str",
        "default": "nine-slot schedule separating canonical anchors with shortcut-counterexamples",
        "valid": "up_right|down_left|down_right|up_left|left|right|up|down",
    },
}

# Declaring the (empty) incompatibility table opts this generator into the
# strict override contract. Every value in every declared axis is realizable in
# combination with every value of the other axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Slots 0, 3, and 6 intentionally resemble the public examples closely enough
# to keep the canonical profile well represented.  Their spacing is exactly
# three on a nine-slot cycle, so every three-sample cyclic lesson window has at
# most one anchor.  Holding out any one sample therefore leaves a demo pair with
# both a multicolor payload and an orientation that genuinely falsifies the
# public-only "always up-right" shortcut. Exact overrides can still request all
# eight direction branches.
_CANONICAL_ANCHOR_SLOTS = frozenset((0, 3, 6))
_PALETTE_SCHEDULE = (1, 2, 2, 1, 2, 2, 1, 2, 2)
_DIRECTION_SCHEDULE = (
    "up_right",
    "down_left",
    "down_right",
    "up_right",
    "up_left",
    "left",
    "up_right",
    "down_left",
    "down",
)
SCHEDULE_PROFILES = tuple(range(len(_DIRECTION_SCHEDULE)))

_PCOLORS = (1, 4, 5, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SIZE_BANDS = {
    None: (9, 20),
    "easy": (9, 13),
    "medium": (10, 16),
    "hard": (11, 20),
}
_PAYLOAD_BANDS = {
    None: (3, 9),
    "easy": (3, 5),
    "medium": (4, 7),
    "hard": (5, 9),
}

_FALLBACK_SHAPES = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
    7: ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    8: (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
    9: (
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2), (1, 3),
        (2, 0), (2, 1),
    ),
}


@dataclass(frozen=True)
class _Scene:
    h: int
    w: int
    source: tuple[int, int]
    destination: tuple[int, int]
    payload: tuple[tuple[int, int, int], ...]

    @property
    def delta(self) -> tuple[int, int]:
        return (
            self.destination[0] - self.source[0],
            self.destination[1] - self.source[1],
        )

    @property
    def payload_cells(self) -> tuple[tuple[int, int], ...]:
        return tuple((r, c) for r, c, _ in self.payload)

    @property
    def palette_size(self) -> int:
        return len({value for _, _, value in self.payload})


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Pedagogical slot; independent of seed/difficulty by design."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _SIZE_BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "payload_size", "palette_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    direction = overrides.get("vector_direction")
    if direction is not None and not isinstance(direction, str):
        raise ValueError("vector_direction must be a string")


def _normalize(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _random_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Connected, compact, visibly non-rectangular polyomino of exact size."""
    for _attempt in range(96):
        cells = {(0, 0)}
        for _step in range(512):
            if len(cells) >= size:
                break
            row, col = rng.choice(sorted(cells))
            dr, dc = rng.choice(_CARDINAL)
            cells.add((row + dr, col + dc))
        if len(cells) != size:
            continue
        shape = _normalize(cells)
        sh, sw = _shape_dims(shape)
        if 2 <= sh <= 4 and 2 <= sw <= 4 and sh * sw > size:
            return shape
    return _FALLBACK_SHAPES[size]


def _sign(value: int) -> int:
    return 0 if value == 0 else (1 if value > 0 else -1)


def _direction(dr: int, dc: int) -> str:
    key = (_sign(dr), _sign(dc))
    names = {
        (-1, 1): "up_right",
        (1, -1): "down_left",
        (1, 1): "down_right",
        (-1, -1): "up_left",
        (0, -1): "left",
        (0, 1): "right",
        (-1, 0): "up",
        (1, 0): "down",
    }
    if key not in names:
        raise ValueError(f"zero or unsupported vector ({dr}, {dc})")
    return names[key]


def _vector_candidates(direction: str, h: int, w: int, rng) -> list[tuple[int, int]]:
    """Non-unit vectors in the requested direction, canonical magnitudes first."""
    row_mags = list(range(1, min(4, h - 1) + 1))
    col_mags = list(range(1, min(4, w - 1) + 1))
    diag = [(2, 1), (1, 2), (2, 2), (3, 1), (1, 3), (3, 2), (2, 3)]
    diag = [(r, c) for r, c in diag if r in row_mags and c in col_mags]
    rng.shuffle(diag)
    # Preserve the public 2x1/1x2 geometry as frequent cases without fixing it.
    diag.sort(key=lambda pair: 0 if pair in ((2, 1), (1, 2)) else 1)
    cardinal_rows = [m for m in row_mags if m >= 2]
    cardinal_cols = [m for m in col_mags if m >= 2]
    rng.shuffle(cardinal_rows)
    rng.shuffle(cardinal_cols)

    if direction == "up_right":
        return [(-r, c) for r, c in diag]
    if direction == "down_left":
        return [(r, -c) for r, c in diag]
    if direction == "down_right":
        return [(r, c) for r, c in diag]
    if direction == "up_left":
        return [(-r, -c) for r, c in diag]
    if direction == "left":
        return [(0, -m) for m in cardinal_cols]
    if direction == "right":
        return [(0, m) for m in cardinal_cols]
    if direction == "up":
        return [(-m, 0) for m in cardinal_rows]
    if direction == "down":
        return [(m, 0) for m in cardinal_rows]
    raise ValueError(f"unknown vector_direction {direction!r}")


def _placement_range(size: int, span: int, delta: int) -> range:
    low = max(0, -delta)
    high = min(size - span, size - span - delta)
    return range(low, high + 1) if low <= high else range(0)


def _place_payload_and_markers(
    *,
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    direction: str,
    rng,
) -> tuple[list[tuple[int, int]], tuple[int, int], tuple[int, int]]:
    sh, sw = _shape_dims(shape)
    vectors = _vector_candidates(direction, h, w, rng)
    if not vectors:
        raise ValueError(f"grid {h}x{w} cannot realize vector direction {direction}")

    # Prefer vectors that move at least half of the payload to fresh cells, but
    # retain a fallback because overlap is lawful and appears naturally in ARC.
    fallback = None
    for dr, dc in vectors:
        tops = list(_placement_range(h, sh, dr))
        lefts = list(_placement_range(w, sw, dc))
        rng.shuffle(tops)
        rng.shuffle(lefts)
        for top in tops:
            for left in lefts:
                payload = [(top + r, left + c) for r, c in shape]
                occupied = set(payload)
                shifted = {(r + dr, c + dc) for r, c in payload}
                if len(shifted) != len(payload):
                    continue
                starts = []
                blocked = occupied | shifted
                for pr in range(h):
                    for pc in range(w):
                        qr, qc = pr + dr, pc + dc
                        if not (0 <= qr < h and 0 <= qc < w):
                            continue
                        if (pr, pc) in blocked or (qr, qc) in blocked:
                            continue
                        starts.append((pr, pc))
                if not starts:
                    continue
                source = rng.choice(starts)
                destination = (source[0] + dr, source[1] + dc)
                candidate = (payload, source, destination)
                overlap = len(occupied & shifted)
                if overlap <= len(payload) // 2:
                    return candidate
                if fallback is None:
                    fallback = candidate
    if fallback is not None:
        return fallback
    raise ValueError("no lawful payload/marker placement for requested exact axes")


def _draw_int_axis(ctx, name: str, lo: int, hi: int, scheduled: int | None = None) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    if scheduled is not None:
        if not lo <= scheduled <= hi:
            raise ValueError(f"scheduled {name}={scheduled} outside [{lo}, {hi}]")
        return int(ctx.draw_choice(name, (scheduled,)))
    return ctx.draw_int(name, lo, hi)


def _draw_choice_axis(ctx, name: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def _analyze(grid: Any) -> tuple[_Scene | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return None, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be nonempty and rectangular"]
    h, w = len(grid), width
    if h > 30 or w > 30:
        errors.append(f"ARC grid dimensions must be <=30, got {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return None, errors

    red = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    green = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    payload = tuple(
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 2, 3)
    )
    if len(red) != 1:
        errors.append(f"expected exactly 1 red source marker, found {len(red)}")
    if len(green) != 1:
        errors.append(f"expected exactly 1 green destination marker, found {len(green)}")
    if not payload:
        errors.append("expected one nonempty payload object")
    if errors:
        return None, errors

    source, destination = red[0], green[0]
    dr = destination[0] - source[0]
    dc = destination[1] - source[1]
    if dr == 0 and dc == 0:
        errors.append("red and green markers must define a nonzero vector")

    payload_cells = {(r, c) for r, c, _ in payload}
    stack = [next(iter(payload_cells))]
    seen = {stack[0]}
    while stack:
        row, col = stack.pop()
        for drow, dcol in _CARDINAL:
            neighbor = (row + drow, col + dcol)
            if neighbor in payload_cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    if seen != payload_cells:
        errors.append("all payload cells must form one 4-connected object")

    shifted = [(r + dr, c + dc) for r, c, _ in payload]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in shifted):
        errors.append("red->green vector shifts at least one payload cell out of bounds")

    if errors:
        return None, errors
    return _Scene(h, w, source, destination, payload), []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid input grammar; accepts every canonical train/test input."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful manifold for semantic-census purposes."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests only; canonical Racket is authority."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        raise ValueError("rule_mirror expects a lawful scene: " + "; ".join(errors))
    dr, dc = scene.delta
    output = full_grid(scene.h, scene.w, 0)
    for row, col, value in scene.payload:
        output[row + dr][col + dc] = value
    return output


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every exact declared axis from a returned lawful grid."""
    scene, errors = _analyze(grid)
    if errors or scene is None:
        raise ValueError("cannot observe exact axes from malformed grid: " + "; ".join(errors))
    dr, dc = scene.delta
    return {
        "grid_h": scene.h,
        "grid_w": scene.w,
        "payload_size": len(scene.payload),
        "palette_size": scene.palette_size,
        "vector_direction": _direction(dr, dc),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return {"valid": False, "errors": errors}
    dr, dc = scene.delta
    cells = set(scene.payload_cells)
    shifted = {(r + dr, c + dc) for r, c in cells}
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return {
        "valid": True,
        **observe_overrides(grid),
        "delta": (dr, dc),
        "vector_linf": max(abs(dr), abs(dc)),
        "payload_bbox_area": bbox_area,
        "payload_is_bbox_solid": bbox_area == len(cells),
        "payload_shift_overlap": len(cells & shifted),
        "source": scene.source,
        "destination": scene.destination,
    }


def _shift_with_delta(grid, dr: int, dc: int, *, only_color: int | None = None):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    out = full_grid(scene.h, scene.w, 0)
    for row, col, value in scene.payload:
        if only_color is not None and value != only_color:
            continue
        nr, nc = row + dr, col + dc
        if 0 <= nr < scene.h and 0 <= nc < scene.w:
            out[nr][nc] = value
    return out


def _reverse_vector(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    dr, dc = scene.delta
    return _shift_with_delta(grid, -dr, -dc)


def _canonical_up_right(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    dr, dc = scene.delta
    return _shift_with_delta(grid, -abs(dr), abs(dc))


def _modal_color_translate(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    counts = Counter(value for _, _, value in scene.payload)
    first_pos: dict[int, int] = {}
    for index, (_, _, value) in enumerate(scene.payload):
        first_pos.setdefault(value, index)
    modal = max(counts, key=lambda color: (counts[color], -first_pos[color]))
    dr, dc = scene.delta
    return _shift_with_delta(grid, dr, dc, only_color=modal)


def _one_step_vector(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    dr, dc = scene.delta
    return _shift_with_delta(grid, _sign(dr), _sign(dc))


def _filled_bbox(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    counts = Counter(value for _, _, value in scene.payload)
    fill = max(counts, key=counts.get)
    rows = [r for r, _, _ in scene.payload]
    cols = [c for _, c, _ in scene.payload]
    dr, dc = scene.delta
    out = full_grid(scene.h, scene.w, 0)
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            nr, nc = row + dr, col + dc
            if 0 <= nr < scene.h and 0 <= nc < scene.w:
                out[nr][nc] = fill
    return out


def _drop_markers_keep_payload(grid):
    scene, errors = _analyze(grid)
    if errors or scene is None:
        return [list(row) for row in grid]
    out = full_grid(scene.h, scene.w, 0)
    for row, col, value in scene.payload:
        out[row][col] = value
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _witness_up_right(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("vector_direction") == "up_right")


def _witness_noncanonical_direction(grid) -> bool:
    # This witness is specifically for the canonical-only "always up-right"
    # shortcut, so require an input on which that shortcut actually disagrees
    # with the authoritative rule (pure up/right vectors would not refute it).
    scene, errors = _analyze(grid)
    return bool(
        not errors
        and scene is not None
        and _canonical_up_right(grid) != rule_mirror(grid)
    )


def _witness_monochrome(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("palette_size") == 1)


def _witness_multicolor(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and int(profile.get("palette_size", 0)) >= 2)


def _witness_long_vector(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and int(profile.get("vector_linf", 0)) >= 2)


def _witness_irregular_payload(grid) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and not profile.get("payload_is_bbox_solid"))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canonical_up_right_orientation": _witness_up_right,
    "noncanonical_orientation": _witness_noncanonical_direction,
    "monochrome_payload": _witness_monochrome,
    "multicolor_payload": _witness_multicolor,
    "non_unit_vector": _witness_long_vector,
    "irregular_payload_shape": _witness_irregular_payload,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reverse_red_green_vector": _reverse_vector,
    "canonical_up_right": _canonical_up_right,
    "translate_modal_payload_color": _modal_color_translate,
    "one_step_toward_green": _one_step_vector,
    "translate_filled_payload_bbox": _filled_bbox,
    "drop_markers_without_moving": _drop_markers_keep_payload,
    "identity": _identity,
}

WITNESS_RIVALS = {
    "canonical_up_right_orientation": ["reverse_red_green_vector"],
    "noncanonical_orientation": ["canonical_up_right"],
    "monochrome_payload": ["reverse_red_green_vector"],
    "multicolor_payload": ["translate_modal_payload_color"],
    "non_unit_vector": ["one_step_toward_green"],
    "irregular_payload_shape": ["translate_filled_payload_bbox"],
}

# Both shortcuts reproduce every public canonical pair: all public vectors are
# up-right and every public payload is monochrome. Generated witnesses must kill
# them, and every lesson window is scheduled to do so.
CANONICAL_SHORTCUTS = {
    "canonical_up_right": _canonical_up_right,
    "translate_modal_payload_color": _modal_color_translate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut fits all demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not lawful: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the red->green translation rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed scenes that structural self_check must reject."""
    missing_red = full_grid(7, 7, 0)
    missing_red[2][2] = 4
    missing_red[2][3] = 4
    missing_red[3][2] = 4
    missing_red[5][5] = 3

    duplicate_green = full_grid(7, 7, 0)
    duplicate_green[2][2] = 4
    duplicate_green[2][3] = 4
    duplicate_green[3][2] = 4
    duplicate_green[5][1] = 2
    duplicate_green[3][3] = 3
    duplicate_green[4][3] = 3

    disconnected_payload = full_grid(8, 8, 0)
    disconnected_payload[2][2] = 4
    disconnected_payload[2][3] = 4
    disconnected_payload[3][2] = 4
    disconnected_payload[5][5] = 7
    disconnected_payload[6][1] = 2
    disconnected_payload[4][2] = 3

    out_of_bounds = full_grid(7, 7, 0)
    out_of_bounds[1][1] = 4
    out_of_bounds[1][2] = 4
    out_of_bounds[2][1] = 4
    out_of_bounds[6][5] = 2
    out_of_bounds[0][5] = 3

    no_payload = full_grid(7, 7, 0)
    no_payload[5][1] = 2
    no_payload[3][3] = 3

    return [
        ("missing_red_source_marker", missing_red),
        ("duplicate_green_destination_marker", duplicate_green),
        ("disconnected_second_payload_piece", disconnected_payload),
        ("marker_vector_pushes_payload_out_of_bounds", out_of_bounds),
        ("markers_without_payload", no_payload),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)

    canonical_anchor = slot in _CANONICAL_ANCHOR_SLOTS
    canonical_size = 9 + ctx.draw_rng("canonical_size").randrange(3)
    size_lo, size_hi = _SIZE_BANDS[difficulty]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", 9, 20)
    elif canonical_anchor:
        h = int(ctx.draw_choice("grid_h", (canonical_size,)))
    else:
        h = ctx.draw_int("grid_h", size_lo, size_hi)

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", 9, 20)
    elif canonical_anchor:
        w = int(ctx.draw_choice("grid_w", (canonical_size,)))
    else:
        w = ctx.draw_int("grid_w", size_lo, size_hi)

    payload_lo, payload_hi = _PAYLOAD_BANDS[difficulty]
    if overrides.get("payload_size") is not None:
        payload_size = ctx.draw_int("payload_size", 3, 9)
    elif canonical_anchor:
        payload_size = int(ctx.draw_choice("payload_size", (4,)))
    else:
        payload_size = ctx.draw_int("payload_size", payload_lo, payload_hi)

    palette_size = _draw_int_axis(
        ctx,
        "palette_size",
        1,
        3,
        _PALETTE_SCHEDULE[slot] if overrides.get("palette_size") is None else None,
    )
    vector_direction = _draw_choice_axis(
        ctx,
        "vector_direction",
        _DIRECTIONS,
        _DIRECTION_SCHEDULE[slot],
    )

    shape_rng = ctx.draw_rng("shape")
    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")

    last_error = None
    for _attempt in range(64):
        shape = _random_shape(shape_rng, payload_size)
        try:
            cells, source, destination = _place_payload_and_markers(
                h=h,
                w=w,
                shape=shape,
                direction=vector_direction,
                rng=layout_rng,
            )
        except ValueError as exc:
            last_error = exc
            continue

        palette = list(color_rng.sample(_PCOLORS, palette_size))
        order = list(range(len(cells)))
        color_rng.shuffle(order)
        colors = [palette[0]] * len(cells)
        # Guarantee that the observed palette cardinality equals the exact axis.
        for index, color in zip(order[:palette_size], palette):
            colors[index] = color
        for index in order[palette_size:]:
            colors[index] = color_rng.choice(palette)

        grid = full_grid(h, w, 0)
        for (row, col), color in zip(cells, colors):
            grid[row][col] = color
        grid[source[0]][source[1]] = 2
        grid[destination[0]][destination[1]] = 3

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            last_error = ValueError("; ".join(errors))
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": h,
            "grid_w": w,
            "payload_size": payload_size,
            "palette_size": palette_size,
            "vector_direction": vector_direction,
        }
        if observed != expected:
            raise AssertionError(f"exact-axis round trip failed: {expected=} {observed=}")
        return grid

    raise ValueError(f"could not realize requested exact axes: {last_error}")
