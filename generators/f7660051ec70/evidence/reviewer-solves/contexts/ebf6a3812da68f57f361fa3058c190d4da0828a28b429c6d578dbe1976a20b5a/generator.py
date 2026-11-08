"""Reviewed generator for seeded rectangular-frame interior filling.

The input contains separate closed color-1 rectangular frames.  A frame whose
interior contains one or two color-2 seeds is active: the canonical rule fills
all remaining interior background cells with color 3.  Empty frames are decoys
and remain unchanged.  Outputs are produced only by the canonical Racket rule;
``rule_mirror`` below is a deterministic test oracle for this simple geometry.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "f7660051ec70"
TASK_ID = GENERATOR_ID
RULE_HASH = "3efd212303b7"
VERSION = "4.0.0"
SUMMARY = (
    "Separate closed blue rectangular frames contain zero, one, or two red "
    "interior seeds. Fill every remaining interior background cell green in "
    "each seeded frame; leave empty decoy frames unchanged."
)

INVARIANTS = [
    "the grid uses only colors 0, 1, and 2 before transformation",
    "every color-1 component is exactly one closed rectangular outline",
    "at least one frame is seeded and at least one frame is an empty decoy",
    "every seeded frame has one or two interior seeds and at least one fill target",
    "frames are separate components and every seed lies strictly inside one frame",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors plus banded 9..26", "valid": "9..26"},
    "grid_w": {"type": "int", "default": "canonical anchors plus banded 11..26", "valid": "11..26"},
    "n_seeded_frames": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "n_decoy_frames": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "seed_count": {"type": "int", "default": "alternating lesson schedule 1|2", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Three demonstrations are the packet default.  Alternating seed-count profiles
# guarantee that every three consecutive generated pairs contain both a one-seed
# and a two-seed case, directly refuting the former "exactly one seed" shortcut.
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("one_seed", "two_seed")
MIN_STRICT_FRAC = 1.0

_CANONICAL_SHAPES = ((10, 12), (11, 13), (12, 14))
_AXIS_LIMITS = {
    "grid_h": (9, 26),
    "grid_w": (11, 26),
    "n_seeded_frames": (1, 2),
    "n_decoy_frames": (1, 2),
    "seed_count": (1, 2),
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_LIMITS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_exact_or_default(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _AXIS_LIMITS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # A singleton keyed choice records the scheduled/default axis value without
    # introducing a second source of randomness.  Exact overrides still travel
    # through draw_int_strict with the full declared range above.
    return ctx.draw_choice(name, (default,))


def _broad_shape(ctx, difficulty: Any) -> tuple[int, int]:
    if difficulty == "easy":
        hs, ws = range(9, 15), range(11, 17)
    elif difficulty == "hard":
        hs, ws = range(14, 27), range(16, 27)
    elif difficulty == "medium":
        hs, ws = range(11, 21), range(13, 23)
    else:
        hs, ws = range(9, 27), range(11, 27)
    return (
        ctx.draw_rng("broad_grid_h").choice(tuple(hs)),
        ctx.draw_rng("broad_grid_w").choice(tuple(ws)),
    )


def _draw_canvas(ctx, difficulty: Any, overrides: dict[str, Any]) -> tuple[int, int]:
    h_overridden = overrides.get("grid_h") is not None
    w_overridden = overrides.get("grid_w") is not None

    # Canonical-sized anchors occur in every difficulty band, while one quarter
    # of default draws explores a wider band.  Correlated canonical pairs avoid
    # the false "inside the envelope but never an exact profile" condition.
    mode = ctx.draw_choice(
        "curriculum_canvas",
        ("canonical", "canonical", "canonical", "broad"),
    )
    if mode == "canonical":
        default_h, default_w = ctx.draw_rng("canonical_shape").choice(_CANONICAL_SHAPES)
    else:
        default_h, default_w = _broad_shape(ctx, difficulty)

    h = (
        ctx.draw_int_strict("grid_h", *_AXIS_LIMITS["grid_h"])
        if h_overridden
        else ctx.draw_choice("grid_h", (default_h,))
    )
    w = (
        ctx.draw_int_strict("grid_w", *_AXIS_LIMITS["grid_w"])
        if w_overridden
        else ctx.draw_choice("grid_w", (default_w,))
    )
    return h, w


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return "one_seed" if sample_index % 2 == 0 else "two_seed"


def _slot_grid(height: int, width: int) -> list[tuple[int, int, int, int]]:
    """Four separated slots, each at least 4x4 at the minimum 9x11 canvas."""
    top_h = (height - 1) // 2
    bottom_h = height - 1 - top_h
    left_w = (width - 1) // 2
    right_w = width - 1 - left_w
    slots = [
        (0, 0, top_h, left_w),
        (0, left_w + 1, top_h, right_w),
        (top_h + 1, 0, bottom_h, left_w),
        (top_h + 1, left_w + 1, bottom_h, right_w),
    ]
    if any(slot_h < 4 or slot_w < 4 for _, _, slot_h, slot_w in slots):
        raise ValueError(f"canvas {height}x{width} cannot fit four separated 4x4 slots")
    return slots


def _place_frame(
    grid: list[list[int]],
    slot: tuple[int, int, int, int],
    *,
    seeded: bool,
    seed_count: int,
    rng,
) -> None:
    slot_r, slot_c, slot_h, slot_w = slot
    frame_h = rng.randint(4, slot_h)
    frame_w = rng.randint(4, slot_w)
    top = slot_r + rng.randint(0, slot_h - frame_h)
    left = slot_c + rng.randint(0, slot_w - frame_w)
    bottom = top + frame_h - 1
    right = left + frame_w - 1
    draw_frame(grid, top, left, bottom, right, 1)
    if not seeded:
        return
    interior = [
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    ]
    if len(interior) <= seed_count:
        raise RuntimeError("seeded frame lacks a visible fill target")
    for row, col in rng.sample(interior, seed_count):
        grid[row][col] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        task_id=TASK_ID,
        version=VERSION,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width = _draw_canvas(ctx, difficulty, overrides)

    if overrides.get("n_seeded_frames") is not None:
        n_seeded = ctx.draw_int_strict("n_seeded_frames", 1, 2)
    else:
        seeded_choices = {
            "easy": (1, 1, 1, 2),
            "medium": (1, 1, 2, 2),
            "hard": (1, 2, 2, 2),
        }.get(difficulty, (1, 1, 2, 2))
        n_seeded = ctx.draw_choice("n_seeded_frames", seeded_choices)

    if overrides.get("n_decoy_frames") is not None:
        n_decoys = ctx.draw_int_strict("n_decoy_frames", 1, 2)
    else:
        decoy_choices = {
            "easy": (1, 1, 1, 2),
            "medium": (1, 1, 2, 2),
            "hard": (1, 2, 2, 2),
        }.get(difficulty, (1, 1, 2, 2))
        n_decoys = ctx.draw_choice("n_decoy_frames", decoy_choices)

    scheduled_seed_count = 1 if schedule_profile(seed, sample_index, difficulty) == "one_seed" else 2
    seed_count = _draw_exact_or_default(ctx, overrides, "seed_count", scheduled_seed_count)

    slots = _slot_grid(height, width)
    slot_rng = ctx.draw_rng("slot_order")
    slot_rng.shuffle(slots)
    flags = [True] * n_seeded + [False] * n_decoys
    flag_rng = ctx.draw_rng("frame_roles")
    flag_rng.shuffle(flags)

    grid = full_grid(height, width, 0)
    geometry_rng = ctx.draw_rng("frame_geometry")
    for slot, seeded in zip(slots[: len(flags)], flags, strict=True):
        _place_frame(
            grid,
            slot,
            seeded=seeded,
            seed_count=seed_count,
            rng=geometry_rng,
        )
    return grid


def _grid_rows(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    rows = [list(row) for row in grid]
    if any(type(value) is not int or value not in (0, 1, 2) for row in rows for value in row):
        return None, ["input cells must be integer colors 0, 1, or 2"]
    return rows, []


def _frame_components(grid: list[list[int]]) -> tuple[list[dict[str, int]], list[str]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    parsed: list[dict[str, int]] = []
    errors: list[str] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(row for row, _ in cells)
            r2 = max(row for row, _ in cells)
            c1 = min(col for _, col in cells)
            c2 = max(col for _, col in cells)
            expected = (
                {(r1, col) for col in range(c1, c2 + 1)}
                | {(r2, col) for col in range(c1, c2 + 1)}
                | {(row, c1) for row in range(r1, r2 + 1)}
                | {(row, c2) for row in range(r1, r2 + 1)}
            )
            if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3 or cells != expected:
                errors.append(
                    f"color-1 component at {(start_r, start_c)} is not one closed rectangular frame"
                )
                continue
            parsed.append({"r1": r1, "c1": c1, "r2": r2, "c2": c2})
    return sorted(parsed, key=lambda frame: (frame["r1"], frame["c1"])), errors


def _analyze(grid: Any) -> tuple[list[str], list[dict[str, int]], dict[str, Any] | None]:
    rows, errors = _grid_rows(grid)
    if rows is None:
        return errors, [], None
    height, width = len(rows), len(rows[0])
    if not 9 <= height <= 26:
        errors.append(f"grid height {height} outside 9..26")
    if not 11 <= width <= 26:
        errors.append(f"grid width {width} outside 11..26")

    frames, frame_errors = _frame_components(rows)
    errors.extend(frame_errors)
    if not frames:
        errors.append("expected at least one color-1 rectangular frame")
        return errors, [], None

    for row, line in enumerate(rows):
        for col, value in enumerate(line):
            if value != 2:
                continue
            owners = [
                frame
                for frame in frames
                if frame["r1"] < row < frame["r2"] and frame["c1"] < col < frame["c2"]
            ]
            if len(owners) != 1:
                errors.append(f"seed {(row, col)} must lie strictly inside exactly one frame")

    seeded = 0
    decoys = 0
    seed_counts: set[int] = set()
    enriched: list[dict[str, int]] = []
    for frame in frames:
        interior = [
            (row, col)
            for row in range(frame["r1"] + 1, frame["r2"])
            for col in range(frame["c1"] + 1, frame["c2"])
        ]
        count = sum(rows[row][col] == 2 for row, col in interior)
        empty = sum(rows[row][col] == 0 for row, col in interior)
        item = dict(frame, seed_count=count)
        enriched.append(item)
        if count == 0:
            decoys += 1
        else:
            seeded += 1
            seed_counts.add(count)
            if count not in (1, 2):
                errors.append(
                    f"seeded frame {(frame['r1'], frame['c1'])} has {count} seeds; expected 1 or 2"
                )
            if empty < 1:
                errors.append(
                    f"seeded frame {(frame['r1'], frame['c1'])} has no empty fill target"
                )
    if seeded < 1:
        errors.append("expected at least one seeded frame")
    if decoys < 1:
        errors.append("expected at least one unseeded decoy frame")
    if seeded > 2:
        errors.append(f"expected at most two seeded frames, got {seeded}")
    if decoys > 2:
        errors.append(f"expected at most two decoy frames, got {decoys}")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "n_seeded_frames": seeded,
        "n_decoy_frames": decoys,
        "seed_count": next(iter(seed_counts)) if len(seed_counts) == 1 else "mixed",
    }
    return errors, enriched, facts


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    errors, _, facts = _analyze(grid)
    if errors or facts is None:
        return errors
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        for name, expected in meta["overrides"].items():
            if name in AXES and expected is not None and facts.get(name) != expected:
                errors.append(f"override {name}={expected!r} realized as {facts.get(name)!r}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    errors, _, facts = _analyze(grid)
    if errors or facts is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors[:4]))
    return facts


def _apply_fill(grid, predicate: Callable[[int], bool]) -> list[list[int]]:
    errors, frames, _ = _analyze(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors[:4]))
    out = deepcopy(grid)
    for frame in frames:
        if not predicate(frame["seed_count"]):
            continue
        for row in range(frame["r1"] + 1, frame["r2"]):
            for col in range(frame["c1"] + 1, frame["c2"]):
                if out[row][col] == 0:
                    out[row][col] = 3
    return out


def rule_mirror(grid):
    """Independent Python mirror used by tests; canonical labels remain Racket-owned."""
    return _apply_fill(grid, lambda seed_count: seed_count >= 1)


def _exactly_one_seed(grid):
    return _apply_fill(grid, lambda seed_count: seed_count == 1)


def _fill_all_frames(grid):
    return _apply_fill(grid, lambda seed_count: True)


def _has_two_seed_frame(grid) -> bool:
    try:
        _, frames, _ = _analyze(grid)
        return any(frame["seed_count"] == 2 for frame in frames)
    except Exception:
        return False


def _has_unseeded_decoy(grid) -> bool:
    try:
        _, frames, _ = _analyze(grid)
        return any(frame["seed_count"] == 0 for frame in frames)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "two_seed_frame": _has_two_seed_frame,
    "unseeded_decoy": _has_unseeded_decoy,
}
SEMANTIC_RIVALS = {
    "exactly_one_seed": _exactly_one_seed,
    "fill_all_frames": _fill_all_frames,
}
WITNESS_RIVALS = {
    "two_seed_frame": ["exactly_one_seed"],
    "unseeded_decoy": ["fill_all_frames"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} competitor failed to score: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
