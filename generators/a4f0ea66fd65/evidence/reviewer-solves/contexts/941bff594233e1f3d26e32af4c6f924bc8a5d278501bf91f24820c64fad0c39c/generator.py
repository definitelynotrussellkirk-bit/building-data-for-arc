"""Generator for ARC task a4f0ea66fd65 — vector-copy the cyan object.

The input contains one red marker, one green marker, one connected cyan object,
and one connected color-6/7 decoy.  The red-to-green displacement is applied to
every cyan cell; the translated cells are painted blue.  Existing cells in the
destination are overwritten, as witnessed by the canonical test example.

Consecutive sample indices deliberately teach both canonical directions,
clear-destination and decoy-overwrite branches, then generalized vectors.  The
Racket rule remains the output authority; ``rule_mirror`` is only a pure test
and audit mirror.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4f0ea66fd65"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"  # exact-vector curriculum + executable shortcut contract
# sha256[:12] of whitespace-normalized canonical program_solution.
RULE_HASH = "a5767619a475"

SUMMARY = (
    "Find the displacement from the single red(2) marker to the single green(3) "
    "marker. Copy every cell of the connected cyan(8) object by that vector and "
    "paint the translated cells blue(1). Keep the source and markers. A connected "
    "color-6/7 decoy is irrelevant; when it occupies translated destinations, the "
    "blue copy overwrites it."
)

INVARIANTS = [
    "rectangular 8..18 grid with background color 0",
    "exactly one red(2) marker and one green(3) marker",
    "one connected cyan(8) source object with 3..8 cells",
    "the red-to-green vector is non-zero and translates every cyan cell in bounds",
    "source and translated copy are disjoint; translated cells contain only 0 or decoy color",
    "exactly one connected decoy object, colored uniformly 6 or 7",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.55

SCENE_PROFILES = (
    "canonical_right_clear",
    "general_overwrite",
    "canonical_left_clear",
    "canonical_right_overwrite",
    "general_clear",
    "canonical_left_overwrite",
)
SCHEDULE_PROFILES = SCENE_PROFILES
DECOY_COLORS = (6, 7)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-slot schedule with canonical 8x10/11/12 and 9x12 anchors",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "six-slot schedule with canonical 8x10/11/12 and 9x12 anchors",
        "valid": "8..18",
    },
    "object_size": {
        "type": "int",
        "default": "six-slot lesson schedule",
        "valid": "3..8",
    },
    "scene_profile": {
        "type": "str",
        "default": "six-slot lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "decoy_color": {
        "type": "color",
        "default": "alternating 6/7 schedule",
        "valid": "6|7",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILE_VECTORS = {
    "canonical_right_clear": (2, 3),
    "canonical_left_clear": (2, -3),
    "canonical_right_overwrite": (2, 3),
    "canonical_left_overwrite": (2, -3),
}
# Every generalized vector intentionally falls outside the canonical {2,3}
# magnitudes.  Axis-aligned cases make it impossible to infer a diagonal-only
# copy rule, while the (1,4)/(4,1) cases require reading exact marker distance.
_GENERAL_VECTORS = {
    "easy": ((0, 4), (4, 0), (1, 4), (4, 1)),
    "medium": ((0, -4), (-4, 0), (-1, 4), (4, -1)),
    "hard": ((0, 4), (-4, 0), (-4, -1), (1, -4)),
}
_PROFILE_DIMS = {
    "canonical_right_clear": (8, 12),
    "canonical_left_clear": (9, 12),
    "canonical_right_overwrite": (8, 11),
    "canonical_left_overwrite": (8, 10),
}
_PROFILE_OBJECT_SIZES = {
    "canonical_right_clear": 5,
    "general_overwrite": 8,
    "canonical_left_clear": 5,
    "canonical_right_overwrite": 4,
    "general_clear": 6,
    "canonical_left_overwrite": 3,
}
_GENERAL_DIMS = {
    "general_clear": {
        "easy": (10, 10), "medium": (13, 14), "hard": (17, 18),
    },
    "general_overwrite": {
        "easy": (11, 12), "medium": (15, 14), "hard": (18, 17),
    },
}


def _band_name(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if value < 0.34:
            return "easy"
        if value < 0.67:
            return "medium"
        return "hard"
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w"):
        if overrides.get(name) is not None:
            value = int(overrides[name])
            if not 8 <= value <= 18:
                raise ValueError(f"{name}={value} outside 8..18")
    if overrides.get("object_size") is not None:
        value = int(overrides["object_size"])
        if not 3 <= value <= 8:
            raise ValueError(f"object_size={value} outside 3..8")
    if (
        overrides.get("scene_profile") is not None
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError(f"unknown scene_profile {overrides['scene_profile']!r}")
    if (
        overrides.get("decoy_color") is not None
        and int(overrides["decoy_color"]) not in DECOY_COLORS
    ):
        raise ValueError("decoy_color must be 6 or 7")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic teaching profile used by the six-slot cycle."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _default_dimensions(profile: str, band: str) -> tuple[int, int]:
    if profile in _PROFILE_DIMS:
        return _PROFILE_DIMS[profile]
    return _GENERAL_DIMS[profile][band]


def _prepare_ctx(seed: int, sample_index: int, difficulty: Any, overrides: dict[str, Any]):
    band = _band_name(difficulty)
    slot = int(sample_index) % len(SCENE_PROFILES)
    effective = dict(overrides)
    profile = str(effective.setdefault("scene_profile", schedule_profile(seed, sample_index, difficulty)))
    effective.setdefault("object_size", _PROFILE_OBJECT_SIZES[profile])
    effective.setdefault("decoy_color", DECOY_COLORS[slot % 2])
    default_h, default_w = _default_dimensions(profile, band)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    return ctx, band, slot


def _neighbors(cell: tuple[int, int], h: int, w: int) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        comp = {seed}
        stack = [seed]
        while stack:
            cell = stack.pop()
            for nb in _neighbors(cell, 10**6, 10**6):
                if nb in remaining:
                    remaining.remove(nb)
                    comp.add(nb)
                    stack.append(nb)
        result.append(comp)
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _grow_local_shape(size: int, rng) -> tuple[tuple[int, int], ...]:
    """Connected 3x3 polyomino with deterministic sorted-frontier choices."""
    domain = [(r, c) for r in range(3) for c in range(3)]
    cells = {rng.choice(domain)}
    while len(cells) < size:
        frontier = sorted(
            {
                nb
                for cell in cells
                for nb in _neighbors(cell, 3, 3)
                if nb not in cells
            }
        )
        if not frontier:
            raise ValueError("local shape frontier exhausted")
        cells.add(rng.choice(frontier))
    normalized = _normalize(cells)
    transform = rng.randrange(8)

    def xf(r: int, c: int) -> tuple[int, int]:
        if transform == 0:
            return r, c
        if transform == 1:
            return c, -r
        if transform == 2:
            return -r, -c
        if transform == 3:
            return -c, r
        if transform == 4:
            return r, -c
        if transform == 5:
            return -r, c
        if transform == 6:
            return c, r
        return -c, -r

    return _normalize(xf(r, c) for r, c in normalized)


def _shuffled(items: Iterable[Any], rng) -> list[Any]:
    values = list(items)
    rng.shuffle(values)
    return values


def _profile_vector(profile: str, band: str, rng) -> tuple[int, int]:
    if profile in _PROFILE_VECTORS:
        return _PROFILE_VECTORS[profile]
    return rng.choice(_GENERAL_VECTORS[band])


def _decoy_clear_cells(
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    size: int,
    rng,
) -> set[tuple[int, int]] | None:
    starts = _shuffled(
        ((r, c) for r in range(h) for c in range(w) if (r, c) not in forbidden),
        rng,
    )
    for start in starts:
        cells = {start}
        while len(cells) < size:
            frontier = sorted(
                {
                    nb
                    for cell in cells
                    for nb in _neighbors(cell, h, w)
                    if nb not in cells and nb not in forbidden
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == size:
            return cells
    return None


def _decoy_overwrite_cells(
    h: int,
    w: int,
    target: set[tuple[int, int]],
    forbidden: set[tuple[int, int]],
    size: int,
    rng,
) -> set[tuple[int, int]] | None:
    """Connected decoy with target overlap and at least one surviving off-target cell."""
    target_order = _shuffled(target, rng)
    for overlap in target_order:
        outside_neighbors = _shuffled(
            (
                nb
                for nb in _neighbors(overlap, h, w)
                if nb not in target and nb not in forbidden
            ),
            rng,
        )
        for outside in outside_neighbors:
            cells = {overlap, outside}
            while len(cells) < size:
                frontier = sorted(
                    {
                        nb
                        for cell in cells
                        for nb in _neighbors(cell, h, w)
                        if nb not in cells and nb not in forbidden
                    }
                )
                if not frontier:
                    break
                # Prefer one additional target cell, then grow away from the target.
                target_frontier = [nb for nb in frontier if nb in target]
                if len(cells & target) < min(2, len(target) - 1) and target_frontier:
                    chosen = rng.choice(target_frontier)
                else:
                    off_target = [nb for nb in frontier if nb not in target]
                    chosen = rng.choice(off_target or frontier)
                cells.add(chosen)
            if len(cells) == size and cells & target and cells - target:
                return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx, band, _slot = _prepare_ctx(seed, sample_index, difficulty, overrides)
    h = ctx.draw_int("grid_h", 8, 18)
    w = ctx.draw_int("grid_w", 8, 18)
    object_size = ctx.draw_int("object_size", 3, 8)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    decoy_color = ctx.draw_color("decoy_color", exclude={0, 1, 2, 3, 4, 5, 8, 9})

    shape_rng = ctx.draw_rng("source_shape")
    placement_rng = ctx.draw_rng("placement")
    vector_rng = ctx.draw_rng("vector")
    decoy_rng = ctx.draw_rng("decoy")
    local = _grow_local_shape(object_size, shape_rng)
    sh = max(r for r, _ in local) + 1
    sw = max(c for _, c in local) + 1
    dr, dc = _profile_vector(profile, band, vector_rng)

    r_lo = max(0, -dr)
    r_hi = min(h - sh, h - sh - dr)
    c_lo = max(0, -dc)
    c_hi = min(w - sw, w - sw - dc)
    if r_lo > r_hi or c_lo > c_hi:
        raise ValueError(
            f"incompatible grid/object/vector: {h}x{w}, size={object_size}, vector={(dr, dc)}"
        )

    origins = _shuffled(
        ((r, c) for r in range(r_lo, r_hi + 1) for c in range(c_lo, c_hi + 1)),
        placement_rng,
    )
    overwrite = profile.endswith("overwrite")
    decoy_size = 3 + (int(sample_index) + int(seed)) % 2

    for r0, c0 in origins:
        source = {(r0 + r, c0 + c) for r, c in local}
        target = {(r + dr, c + dc) for r, c in source}
        if source & target:
            continue
        marker_candidates = _shuffled(
            (
                (r, c)
                for r in range(h)
                for c in range(w)
                if 0 <= r + dr < h
                and 0 <= c + dc < w
                and (r, c) not in source
                and (r, c) not in target
                and (r + dr, c + dc) not in source
                and (r + dr, c + dc) not in target
            ),
            placement_rng,
        )
        for red in marker_candidates:
            green = (red[0] + dr, red[1] + dc)
            marker_set = {red, green}
            forbidden = source | marker_set
            if overwrite:
                decoy = _decoy_overwrite_cells(
                    h, w, target, forbidden, decoy_size, decoy_rng
                )
            else:
                decoy = _decoy_clear_cells(
                    h, w, source | target | marker_set, decoy_size, decoy_rng
                )
            if decoy is None:
                continue
            grid = full_grid(h, w, 0)
            for r, c in source:
                grid[r][c] = 8
            grid[red[0]][red[1]] = 2
            grid[green[0]][green[1]] = 3
            for r, c in decoy:
                grid[r][c] = decoy_color
            findings = self_check(grid, difficulty=difficulty)
            if not findings:
                return grid
    raise ValueError(
        f"could not realize profile={profile} on {h}x{w} with object_size={object_size}"
    )


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"], 0, 0
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    errors: list[str] = []
    if w == 0 or any(len(row) != w for row in grid):
        errors.append("grid must be non-empty and rectangular")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be ARC color integers 0..9")
    return errors, h, w


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in range(10)
    }
    red = positions[2]
    green = positions[3]
    cyan = positions[8]
    decoy_colors = [color for color in DECOY_COLORS if positions[color]]
    facts: dict[str, Any] = {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "red": tuple(red),
        "green": tuple(green),
        "cyan": tuple(cyan),
        "object_size": len(cyan),
        "decoy_colors": tuple(decoy_colors),
        "decoy_color": decoy_colors[0] if len(decoy_colors) == 1 else None,
    }
    if len(red) == 1 and len(green) == 1:
        vector = (green[0][0] - red[0][0], green[0][1] - red[0][1])
        target = {(r + vector[0], c + vector[1]) for r, c in cyan}
        collision_count = sum(
            1
            for r, c in target
            if 0 <= r < h and 0 <= c < w and grid[r][c] in DECOY_COLORS
        )
        if vector == (2, 3):
            prefix = "canonical_right"
        elif vector == (2, -3):
            prefix = "canonical_left"
        else:
            prefix = "general"
        facts.update(
            {
                "vector": vector,
                "target": tuple(sorted(target)),
                "collision_count": collision_count,
                "scene_profile": prefix + ("_overwrite" if collision_count else "_clear"),
            }
        )
    return facts


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("scene_profile") not in SCENE_PROFILES:
        raise ValueError("grid does not realize a declared scene profile")
    if facts.get("decoy_color") not in DECOY_COLORS:
        raise ValueError("grid does not have one declared decoy color")
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "object_size": int(facts["object_size"]),
        "scene_profile": str(facts["scene_profile"]),
        "decoy_color": int(facts["decoy_color"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize lawful teaching scenes, including canonical decoy overwrites."""
    errors, h, w = _grid_errors(grid)
    if errors:
        return errors
    if not 8 <= h <= 18 or not 8 <= w <= 18:
        errors.append(f"expected dimensions 8..18, got {h}x{w}")
    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 2, 3, 6, 7, 8})
    if unexpected:
        errors.append(f"unexpected input colors {unexpected}; blue belongs only in output")

    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (2, 3, 6, 7, 8)
    }
    red, green, cyan = positions[2], positions[3], positions[8]
    if len(red) != 1:
        errors.append(f"expected exactly 1 red(2) marker; found {len(red)}")
    if len(green) != 1:
        errors.append(f"expected exactly 1 green(3) marker; found {len(green)}")
    if not 3 <= len(cyan) <= 8:
        errors.append(f"expected 3..8 cyan source cells; found {len(cyan)}")
    if cyan and len(_components(cyan)) != 1:
        errors.append("cyan source must be one 4-connected object")

    decoy_colors = [color for color in DECOY_COLORS if positions[color]]
    if len(decoy_colors) != 1:
        errors.append(f"expected exactly one decoy color from 6/7; found {decoy_colors}")
    else:
        decoy = positions[decoy_colors[0]]
        if not 3 <= len(decoy) <= 4:
            errors.append(f"expected 3..4 decoy cells; found {len(decoy)}")
        if len(_components(decoy)) != 1:
            errors.append("decoy must be one 4-connected object")

    if len(red) == 1 and len(green) == 1 and cyan:
        dr = green[0][0] - red[0][0]
        dc = green[0][1] - red[0][1]
        if (dr, dc) == (0, 0):
            errors.append("red-to-green vector must be non-zero")
        target = {(r + dr, c + dc) for r, c in cyan}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in target):
            errors.append("translated cyan destination leaves grid")
        else:
            source = set(cyan)
            if source & target:
                errors.append("cyan source and translated copy must be disjoint")
            blocked = sorted((r, c, grid[r][c]) for r, c in target if grid[r][c] in (2, 3, 8))
            if blocked:
                errors.append(
                    "translated cells may contain only background or decoy; "
                    f"found protected colors at {blocked[:3]}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    if facts.get("vector") not in ((2, 3), (2, -3)):
        return [f"canonical vector must be (2,3) or (2,-3), got {facts.get('vector')}"]
    if not 3 <= facts.get("object_size", 0) <= 5:
        return [f"canonical cyan size must be 3..5, got {facts.get('object_size')}"]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; the Racket rule remains authoritative."""
    out = deepcopy(grid)
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    green = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    dr, dc = green[0] - red[0], green[1] - red[1]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = 1
    return out


def _tuple_grid(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _fixed_vector_output(grid: list[list[int]], vector: tuple[int, int]) -> list[list[int]]:
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                nr, nc = r + vector[0], c + vector[1]
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = 1
    return out


def _sign(value: int) -> int:
    return -1 if value < 0 else (1 if value > 0 else 0)


def _quantized_2x3_vector(vector: tuple[int, int]) -> tuple[int, int]:
    """Plausible wrong rule: retain direction, but memorize 2/3 distances."""
    dr, dc = vector
    sr, sc = _sign(dr), _sign(dc)
    if dr == 0:
        return 0, 3 * sc
    if dc == 0:
        return 3 * sr, 0
    if abs(dr) <= abs(dc):
        return 2 * sr, 3 * sc
    return 3 * sr, 2 * sc


def _canonical_sign_vector(vector: tuple[int, int]) -> tuple[int, int]:
    """Plausible wrong rule: use canonical (2,3) magnitudes and marker signs."""
    dr, dc = vector
    return 2 * _sign(dr), 3 * _sign(dc)


def _rival_quantized_2x3(grid: list[list[int]]) -> list[list[int]]:
    vector = tuple(semantic_observables(grid)["vector"])
    return _fixed_vector_output(grid, _quantized_2x3_vector(vector))


def _rival_canonical_sign_only(grid: list[list[int]]) -> list[list[int]]:
    vector = tuple(semantic_observables(grid)["vector"])
    return _fixed_vector_output(grid, _canonical_sign_vector(vector))


def _rival_dynamic_empty_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    vector = tuple(semantic_observables(grid)["vector"])
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            nr, nc = r + vector[0], c + vector[1]
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0:
                out[nr][nc] = 1
    return out


def _rival_move_instead_of_copy(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    vector = tuple(semantic_observables(grid)["vector"])
    h, w = len(grid), len(grid[0])
    source = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    for r, c in source:
        out[r][c] = 0
    for r, c in source:
        nr, nc = r + vector[0], c + vector[1]
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = 1
    return out


def _rival_recolor_source_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                out[r][c] = 1
    return out


SEMANTIC_RIVALS = {
    "quantized_2x3": _rival_quantized_2x3,
    "canonical_sign_only": _rival_canonical_sign_only,
    "dynamic_empty_only": _rival_dynamic_empty_only,
    "fixed_right": lambda grid: _fixed_vector_output(grid, (2, 3)),
    "fixed_left": lambda grid: _fixed_vector_output(grid, (2, -3)),
    "move_instead_of_copy": _rival_move_instead_of_copy,
    "recolor_source_only": _rival_recolor_source_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "quantized_2x3": SEMANTIC_RIVALS["quantized_2x3"],
    "canonical_sign_only": SEMANTIC_RIVALS["canonical_sign_only"],
}


def _candidate_outputs(grid: list[list[int]]) -> dict[str, tuple[tuple[int, ...], ...]]:
    outputs = {"dynamic_overwrite": _tuple_grid(rule_mirror(grid))}
    outputs.update(
        (name, _tuple_grid(solver(grid)))
        for name, solver in SEMANTIC_RIVALS.items()
    )
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to refute each declared shortcut."""
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    seen_vectors: set[tuple[int, int]] = set()
    saw_clear = False
    saw_overwrite = False
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        if self_check(pair["input"]):
            return [f"demo {index} input fails self_check"]
        if _tuple_grid(rule_mirror(pair["input"])) != _tuple_grid(pair["output"]):
            reasons.append(f"demo {index} output disagrees with the intended rule")
        facts = semantic_observables(pair["input"])
        seen_vectors.add(tuple(facts["vector"]))
        saw_overwrite |= facts.get("collision_count", 0) > 0
        saw_clear |= facts.get("collision_count", 0) == 0

    if len(seen_vectors) < 2:
        reasons.append("demos do not vary the red-to-green vector")
    if not saw_clear:
        reasons.append("demos never show a clear translated destination")
    if not saw_overwrite:
        reasons.append("demos never prove that blue overwrites a decoy destination")

    for name, rival in LESSON_COMPETITORS.items():
        if all(
            _tuple_grid(rival(pair["input"])) == _tuple_grid(pair["output"])
            for pair in demos
        ):
            reasons.append(f"demos do not refute shortcut {name}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
    elif _tuple_grid(rule_mirror(query["input"])) != _tuple_grid(query["output"]):
        reasons.append("query output disagrees with the intended rule")
    return reasons


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    return semantic_observables(grid)


SEMANTIC_WITNESSES = {
    "canonical_right_vector": lambda grid: _facts(grid).get("vector") == (2, 3),
    "canonical_left_vector": lambda grid: _facts(grid).get("vector") == (2, -3),
    "exact_marker_distance": lambda grid: (
        tuple(_facts(grid).get("vector", (0, 0)))
        != _quantized_2x3_vector(tuple(_facts(grid).get("vector", (0, 0))))
    ),
    "overwrites_decoy": lambda grid: _facts(grid).get("collision_count", 0) > 0,
    "disjoint_source_target": lambda grid: not (
        set(_facts(grid).get("cyan", ())) & set(_facts(grid).get("target", ()))
    ),
    "axis_aligned_vector": lambda grid: (
        0 in tuple(_facts(grid).get("vector", (1, 1)))
    ),
    "clear_destination": lambda grid: _facts(grid).get("collision_count") == 0,
    "source_size_three": lambda grid: _facts(grid).get("object_size") == 3,
    "source_size_eight": lambda grid: _facts(grid).get("object_size") == 8,
    "decoy_color_6": lambda grid: _facts(grid).get("decoy_color") == 6,
    "decoy_color_7": lambda grid: _facts(grid).get("decoy_color") == 7,
}
WITNESS_RIVALS = {
    "canonical_right_vector": ["fixed_left"],
    "canonical_left_vector": ["fixed_right"],
    "exact_marker_distance": ["quantized_2x3", "canonical_sign_only"],
    "overwrites_decoy": ["dynamic_empty_only"],
    "disjoint_source_target": ["move_instead_of_copy", "recolor_source_only"],
}
BRANCH_WITNESSES = {
    "axis_aligned_vector",
    "clear_destination",
    "source_size_three",
    "source_size_eight",
    "decoy_color_6",
    "decoy_color_7",
}


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed near-misses that self_check must reject."""
    base = generate(99173, 2, difficulty="medium")

    missing_green = deepcopy(base)
    for r, row in enumerate(missing_green):
        for c, value in enumerate(row):
            if value == 3:
                missing_green[r][c] = 0

    disconnected_source = deepcopy(base)
    cyan = [(r, c) for r, row in enumerate(disconnected_source) for c, value in enumerate(row) if value == 8]
    disconnected_source[cyan[-1][0]][cyan[-1][1]] = 0
    # Put the removed cyan far from the remaining component and all occupied cells.
    for r in range(len(disconnected_source) - 1, -1, -1):
        for c in range(len(disconnected_source[0]) - 1, -1, -1):
            if disconnected_source[r][c] == 0 and all(abs(r-r0)+abs(c-c0) > 1 for r0,c0 in cyan[:-1]):
                disconnected_source[r][c] = 8
                break
        else:
            continue
        break

    extra_red = deepcopy(base)
    for r, row in enumerate(extra_red):
        for c, value in enumerate(row):
            if value == 0:
                extra_red[r][c] = 2
                break
        else:
            continue
        break

    blue_in_input = deepcopy(base)
    for r, row in enumerate(blue_in_input):
        for c, value in enumerate(row):
            if value == 0:
                blue_in_input[r][c] = 1
                break
        else:
            continue
        break

    target_hits_marker = deepcopy(base)
    facts = semantic_observables(target_hits_marker)
    target_cell = tuple(facts["target"])[0]
    # Keep the marker vector fixed and put protected cyan directly in one of the
    # translated destinations.  This remains invalid even if profile ordering
    # changes, unlike relocating a marker (which also changes the vector).
    target_hits_marker[target_cell[0]][target_cell[1]] = 8

    return [
        ("missing_green_marker", missing_green),
        ("disconnected_cyan_source", disconnected_source),
        ("extra_red_marker", extra_red),
        ("blue_present_in_input", blue_in_input),
        ("translated_target_contains_marker", target_hits_marker),
    ]
