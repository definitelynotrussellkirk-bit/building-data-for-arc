"""Generator for the Boolean Transform Composer task.

The top-left key chooses union/intersection/xor.  The top-right key chooses
identity/left-right reflection/clockwise rotation for the color-5 shape.  Both
color-4 and color-5 shapes are normalized to their bounding-box top-left before
composition, and the cropped result is emitted in color 9 by the Racket oracle.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "655ca4b10a8c"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "ad20edf43b3d"

SUMMARY = (
    "Read the operation key at (0,0): 1=union, 2=intersection, 3=xor. "
    "Read the transform key at the top-right: 6=identity, 7=horizontal flip, "
    "8=90-degree clockwise rotation. Normalize the color-4 shape A and the "
    "color-5 shape B to their bounding boxes, transform B, combine the two "
    "cell sets using the selected Boolean operation, crop the result, and "
    "paint every result cell color 9. Generated nine-example windows cover "
    "all operation×transform key pairs on informative asymmetric shapes."
)

INVARIANTS = [
    "background is 0; the only non-background colors are both keys and colors 4 and 5",
    "(0,0) is exactly one of 1/2/3 and the top-right cell is exactly one of 6/7/8",
    "colors 4 and 5 each form one 4-connected 4..6-cell shape below the key row",
    "after the selected transform, A and B overlap and each also has an exclusive cell",
    "ordinary nine-sample windows contain all nine operation×transform key combinations",
]

OPS = (1, 2, 3)
TRANSFORMS = (6, 7, 8)
GRID_PROFILES = ((7, 11), (8, 12))
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 9
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "alternates by nine-sample block between canonical heights 7 and 8",
        "valid": "7..8",
    },
    "grid_w": {
        "type": "int",
        "default": "alternates by nine-sample block between canonical widths 11 and 12",
        "valid": "11..12",
    },
    "op": {
        "type": "int",
        "default": "scheduled so every nine consecutive samples contain 1,2,3 × transforms",
        "valid": "1..3",
    },
    "transform": {
        "type": "int",
        "default": "scheduled so every nine consecutive samples contain 6,7,8 × operations",
        "valid": "6..8",
    },
    "shape_size_a": {
        "type": "int",
        "default": "difficulty-banded deterministic choice",
        "valid": "4..6",
    },
    "shape_size_b": {
        "type": "int",
        "default": "difficulty-banded deterministic choice",
        "valid": "4..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, default: int, overrides: dict[str, Any]) -> int:
    """Record a deterministic scheduled default while honoring the full axis domain."""
    if label in overrides:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, [default])


def _normalize(cells: Any) -> tuple[tuple[int, int], ...]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells: Any, code: int) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    if not normalized:
        return ()
    if code == 7:
        max_c = max(c for _, c in normalized)
        return _normalize((r, max_c - c) for r, c in normalized)
    if code == 8:
        max_r = max(r for r, _ in normalized)
        return _normalize((c, max_r - r) for r, c in normalized)
    return normalized


def _compose_cells(a: Any, b: Any, op: int) -> tuple[tuple[int, int], ...]:
    sa, sb = set(_normalize(a)), set(_normalize(b))
    if op == 1:
        result = sa | sb
    elif op == 2:
        result = sa & sb
    elif op == 3:
        result = sa ^ sb
    else:
        raise ValueError(f"unknown operation code: {op!r}")
    return _normalize(result)


def _build_motif(rng, size: int) -> tuple[tuple[int, int], ...]:
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        nxt = (r + dr, c + dc)
        if nxt not in seen:
            seen.add(nxt)
            cells.append(nxt)
    return _normalize(cells)


def _bbox_size(cells: Any) -> tuple[int, int]:
    normalized = _normalize(cells)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _all_key_outputs(a: Any, b: Any) -> dict[tuple[int, int], tuple[tuple[int, int], ...]]:
    return {
        (op, transform): _compose_cells(a, _transform(b, transform), op)
        for op in OPS
        for transform in TRANSFORMS
    }


def _informative_pair(a: Any, b: Any) -> bool:
    """Every transform exposes overlap and both differences; every key answer differs."""
    a_set = set(_normalize(a))
    for transform in TRANSFORMS:
        b_set = set(_transform(b, transform))
        if not (a_set & b_set and a_set - b_set and b_set - a_set):
            return False
    outputs = _all_key_outputs(a, b)
    if not all(outputs.values()) or len(set(outputs.values())) != len(outputs):
        return False
    # Large solid rectangles trigger the generic no-op detector and hide the
    # cell-set geometry. Small intersections (for example 1x1) remain lawful.
    for result in outputs.values():
        height, width = _bbox_size(result)
        if height > 1 and width > 1 and len(result) == height * width and len(result) >= 9:
            return False
    return True


def _legal_positions(h: int, w: int, cells: Any) -> list[tuple[int, int]]:
    shape_h, shape_w = _bbox_size(cells)
    return [
        (r0, c0)
        for r0 in range(1, h - shape_h + 1)
        for c0 in range(0, w - shape_w + 1)
    ]


def _placed(cells: Any, origin: tuple[int, int]) -> set[tuple[int, int]]:
    r0, c0 = origin
    return {(r0 + r, c0 + c) for r, c in _normalize(cells)}


def _choose_layout(rng, h: int, w: int, a: Any, b: Any) -> tuple[set[tuple[int, int]], set[tuple[int, int]]] | None:
    a_positions = _legal_positions(h, w, a)
    b_positions = _legal_positions(h, w, b)
    rng.shuffle(a_positions)
    rng.shuffle(b_positions)
    for a_origin in a_positions:
        a_cells = _placed(a, a_origin)
        for b_origin in b_positions:
            b_cells = _placed(b, b_origin)
            if a_cells.isdisjoint(b_cells):
                return a_cells, b_cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    block = sample_index // 9
    default_h, default_w = GRID_PROFILES[block % len(GRID_PROFILES)]
    h = _draw_scheduled_int(ctx, "grid_h", 7, 8, default_h, overrides)
    w = _draw_scheduled_int(ctx, "grid_w", 11, 12, default_w, overrides)

    phase = sample_index % 9
    default_op = OPS[phase // len(TRANSFORMS)]
    default_transform = TRANSFORMS[phase % len(TRANSFORMS)]
    op = _draw_scheduled_int(ctx, "op", 1, 3, default_op, overrides)
    transform = _draw_scheduled_int(ctx, "transform", 6, 8, default_transform, overrides)

    size_options = {
        "easy": (4,),
        "medium": (4, 5),
        "hard": (5, 6),
    }[band]
    size_rng = stable_rng(seed, f"{TASK_ID}|sizes|block={block}|band={band}", VERSION)
    default_size_a = size_rng.choice(size_options)
    default_size_b = size_rng.choice(size_options)
    size_a = _draw_scheduled_int(ctx, "shape_size_a", 4, 6, default_size_a, overrides)
    size_b = _draw_scheduled_int(ctx, "shape_size_b", 4, 6, default_size_b, overrides)

    motif_rng = stable_rng(
        seed,
        f"{TASK_ID}|motifs|block={block}|{h}x{w}|sizes={size_a},{size_b}",
        VERSION,
    )
    for attempt in range(1200):
        a = _build_motif(motif_rng, size_a)
        b = _build_motif(motif_rng, size_b)
        a_h, a_w = _bbox_size(a)
        b_h, b_w = _bbox_size(b)
        if a_h > h - 1 or b_h > h - 1 or a_w > w or b_w > w:
            continue
        if not _informative_pair(a, b):
            continue
        layout_rng = stable_rng(
            seed,
            f"{TASK_ID}|layout|block={block}|attempt={attempt}|{h}x{w}",
            VERSION,
        )
        layout = _choose_layout(layout_rng, h, w, a, b)
        if layout is None:
            continue
        a_cells, b_cells = layout
        grid = full_grid(h, w, 0)
        grid[0][0] = op
        grid[0][w - 1] = transform
        for r, c in a_cells:
            grid[r][c] = 4
        for r, c in b_cells:
            grid[r][c] = 5
        return grid
    raise ValueError(
        "could not construct an informative Boolean-composer scene after 1200 attempts"
    )


def _shape(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
    if not (7 <= h <= 8 and 11 <= w <= 12):
        errors.append(f"grid dimensions must be within canonical 7..8 by 11..12, got {h}x{w}")
    return h, w, errors


def _components4(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return nested
    return {name: meta[name] for name in AXES if name in meta}


def _analyse(grid: Any, *, meta: Any = None) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _shape(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors

    flat = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 9) for value in flat):
        errors.append("cells must be integer ARC colors 0..9")
        return info, errors

    op = grid[0][0]
    transform = grid[0][w - 1]
    info.update({"op": op, "transform": transform})
    if op not in OPS:
        errors.append(f"(0,0) operation key must be one of {OPS}, got {op!r}")
    if transform not in TRANSFORMS:
        errors.append(f"top-right transform key must be one of {TRANSFORMS}, got {transform!r}")

    allowed = {0, 4, 5, *OPS, *TRANSFORMS}
    stray = sorted(set(flat) - allowed)
    if stray:
        errors.append(f"unexpected colors outside the composer grammar: {stray}")

    for c in range(1, w - 1):
        if grid[0][c] != 0:
            errors.append("the key row must be background except at its two endpoints")
            break

    a_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    b_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    info.update({
        "shape_size_a": len(a_cells),
        "shape_size_b": len(b_cells),
        "a_cells": a_cells,
        "b_cells": b_cells,
    })
    if not (4 <= len(a_cells) <= 6):
        errors.append(f"color-4 shape must contain 4..6 cells, got {len(a_cells)}")
    if not (4 <= len(b_cells) <= 6):
        errors.append(f"color-5 shape must contain 4..6 cells, got {len(b_cells)}")
    if any(r == 0 for r, _ in a_cells | b_cells):
        errors.append("shape cells must stay below the key row")
    if a_cells and len(_components4(a_cells)) != 1:
        errors.append("color-4 cells must form exactly one 4-connected shape")
    if b_cells and len(_components4(b_cells)) != 1:
        errors.append("color-5 cells must form exactly one 4-connected shape")

    if op in OPS and transform in TRANSFORMS and a_cells and b_cells:
        a = set(_normalize(a_cells))
        b_t = set(_transform(b_cells, transform))
        if not (a & b_t):
            errors.append("normalized shapes must overlap after the selected transform")
        if not (a - b_t):
            errors.append("color-4 shape needs a cell outside transformed color-5")
        if not (b_t - a):
            errors.append("transformed color-5 shape needs a cell outside color-4")

    if not errors:
        observed = {name: info[name] for name in AXES}
        for name, requested in _meta_overrides(meta).items():
            if name in AXES and observed[name] != requested:
                errors.append(
                    f"override {name} requested {requested!r}, observed {observed[name]!r}"
                )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting all canonical inputs."""
    return _analyse(grid, meta=meta)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) not in GRID_PROFILES:
        reasons.append("canonical dimensions are 7x11 or 8x12")
    return reasons


def rule_mirror(grid: Any, *, forced_op: int | None = None, forced_transform: int | None = None) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    op = info["op"] if forced_op is None else forced_op
    transform = info["transform"] if forced_transform is None else forced_transform
    result = _compose_cells(info["a_cells"], _transform(info["b_cells"], transform), op)
    if not result:
        return [[0]]
    out_h = max(r for r, _ in result) + 1
    out_w = max(c for _, c in result) + 1
    out = full_grid(out_h, out_w, 0)
    for r, c in result:
        out[r][c] = 9
    return out


def _key_witness(*, op: int | None = None, transform: int | None = None) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and (op is None or info["op"] == op) and (
            transform is None or info["transform"] == transform
        )

    return predicate


SEMANTIC_WITNESSES = {
    "union_branch": _key_witness(op=1),
    "intersection_branch": _key_witness(op=2),
    "xor_branch": _key_witness(op=3),
    "identity_transform": _key_witness(transform=6),
    "horizontal_flip_transform": _key_witness(transform=7),
    "clockwise_rotation_transform": _key_witness(transform=8),
}


def _fixed_op(op: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: rule_mirror(grid, forced_op=op)


def _fixed_transform(transform: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: rule_mirror(grid, forced_transform=transform)


SEMANTIC_RIVALS = {
    "always_union": _fixed_op(1),
    "always_intersection": _fixed_op(2),
    "always_xor": _fixed_op(3),
    "always_identity_transform": _fixed_transform(6),
    "always_horizontal_flip": _fixed_transform(7),
    "always_clockwise_rotation": _fixed_transform(8),
}
WITNESS_RIVALS = {
    "union_branch": ["always_intersection", "always_xor"],
    "intersection_branch": ["always_union", "always_xor"],
    "xor_branch": ["always_union", "always_intersection"],
    "identity_transform": ["always_horizontal_flip", "always_clockwise_rotation"],
    "horizontal_flip_transform": ["always_identity_transform", "always_clockwise_rotation"],
    "clockwise_rotation_transform": ["always_identity_transform", "always_horizontal_flip"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _lesson_signature(grid: Any) -> tuple[Any, ...]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return (
        info["grid_h"],
        info["grid_w"],
        _normalize(info["a_cells"]),
        _normalize(info["b_cells"]),
    )


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    combos: set[tuple[int, int]] = set()
    signatures_by_combo: dict[tuple[int, int], set[tuple[Any, ...]]] = {}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        combo = (info["op"], info["transform"])
        combos.add(combo)
        signatures_by_combo.setdefault(combo, set()).add(_lesson_signature(pair["input"]))
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the Boolean composer rule")

    expected = {(op, transform) for op in OPS for transform in TRANSFORMS}
    missing = expected - combos
    if missing:
        reasons.append(f"demonstrations miss key combinations: {sorted(missing)}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        info, errors = _analyse(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        else:
            combo = (info["op"], info["transform"])
            query_signature = _lesson_signature(query["input"])
            if combo not in combos:
                reasons.append(f"query key combination {combo} was not demonstrated")
            elif all(sig == query_signature for sig in signatures_by_combo.get(combo, set())):
                reasons.append("query repeats its demonstrated shape pair instead of testing transfer")
            if "output" in query and query["output"] != rule_mirror(query["input"]):
                reasons.append("query output disagrees with the Boolean composer rule")
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    phase = sample_index % 9
    return f"op{OPS[phase // 3]}_transform{TRANSFORMS[phase % 3]}"


SCHEDULE_PROFILES = tuple(
    f"op{op}_transform{transform}" for op in OPS for transform in TRANSFORMS
)
