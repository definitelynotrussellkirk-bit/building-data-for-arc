"""Generator for ARC task 6d1d5c90 / content hash 6d06c5b96c19.

Column 0 is an instruction strip.  Exactly one cell in that column is red (2).
After removing the instruction column, rotate the payload rows DOWN by the
red cell's zero-based row index.  Thus a red marker in row 0 means no rotation,
row 1 means a one-row downward rotation, and so on with cyclic wraparound.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "6d06c5b96c19"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "9b7b9cf11c40"

SUMMARY = (
    "Remove column 0, read the red marker's zero-based row index, and cyclically "
    "rotate the remaining rows downward by that many rows."
)

INVARIANTS = [
    "column 0 contains exactly one red(2) cell",
    "all other instruction-column cells share one non-red marker color",
    "the non-red instruction color never appears in the payload",
    "payload rows use 3..6 colors and have full cyclic period",
    "one scheduled profile includes an adjacent duplicate payload row",
    "ordinary schedules cover zero shift, one-row shift, middle shift, and bottom-row wraparound",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 6 or difficulty-banded 5..14",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 7 or difficulty-banded 6..15",
        "valid": "6..15",
    },
    "red_row_index": {
        "type": "int",
        "default": "scheduled top|row1|middle|bottom",
        "valid": "0..h-1",
    },
    "payload_palette_size": {
        "type": "int",
        "default": "6 on canonical profiles, otherwise keyed 3..6",
        "valid": "3..6",
    },
}

# A requested marker row can be incompatible with a simultaneously requested
# smaller grid height.  The raised ValueError also names these axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (("grid_h", "red_row_index"),)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

_PROFILE_NAMES = (
    "canonical_top",
    "broad_high_a",
    "canonical_row1",
    "broad_high_b",
    "canonical_middle",
    "broad_high_c",
    "canonical_bottom",
    "broad_high_d",
)
SCHEDULE_PROFILES = _PROFILE_NAMES


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _require_literal_int(name: str, value: Any, *, minimum: int | None = None) -> int:
    """Reject booleans and values that only happen to be coercible to ``int``."""
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    _require_literal_int("seed", seed)
    sample_index = _require_literal_int("sample_index", sample_index, minimum=0)
    _band(difficulty)
    return _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]


def _draw_scheduled_int(ctx, overrides: dict[str, Any], label: str, lo: int, hi: int, default: int) -> int:
    """Honor the full declared override domain while pinning a scheduled default."""
    if label in overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _raise_incompatible(message: str, *axes: str) -> None:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)  # type: ignore[attr-defined]
    raise exc


def _default_dimensions(ctx, phase: int, band: str) -> tuple[int, int]:
    if phase % 2 == 0:
        return 6, 7
    rng = ctx.draw_rng("profile_dimensions")
    options = {
        "easy": ((5, 6), (7, 8)),
        "medium": ((8, 9), (10, 11)),
        "hard": ((12, 13), (14, 15)),
    }[band]
    return rng.choice(options)


def _default_red_row(phase: int, h: int) -> int:
    # Every broad (odd) profile places the cue on its bottom row.  This
    # interleaves a decisive extrapolation witness between all canonical-size
    # profiles, so every consecutive three-example lesson refutes both the
    # canonical-fitting four-row-code shortcut and the opposite-direction rule.
    # Using a fixed row 4 was insufficient: on an 8-row grid it is a half-turn,
    # where upward and downward rotation coincide.
    if phase % 2:
        return h - 1
    role = phase // 2
    if role == 0:
        return 0
    if role == 1:
        return 1
    if role == 2:
        return h // 2
    return h - 1


def _cyclic_row_period(rows: list[list[int]]) -> int:
    frozen = [tuple(row) for row in rows]
    for shift in range(1, len(frozen) + 1):
        if all(frozen[index] == frozen[(index + shift) % len(frozen)] for index in range(len(frozen))):
            return shift
    raise RuntimeError("row sequence has no cyclic period")


def _pattern_payload(
    h: int,
    pw: int,
    palette: tuple[int, ...],
    rng,
    *,
    repeat_adjacent_row: bool = False,
) -> list[list[int]]:
    """Create exact-palette, low-component payloads with full cyclic period.

    Ordinary profiles have ``h == pw``.  A monotone two-color staircase keeps
    the canonical object-count scale (roughly one connected region per payload
    color) while making every cyclic row shift observable.  Full-domain
    overrides with ``h > pw`` use compact binary row codes.  The canonical-row1
    schedule deliberately repeats one adjacent row to cover a pattern present
    in the canonical demonstrations without making the row sequence periodic.
    """
    if len(palette) < 2:
        raise ValueError("payload palette must contain at least two colors")

    left_to_right = bool(rng.randrange(2))
    top_to_bottom = bool(rng.randrange(2))
    primary_a, primary_b = palette[0], palette[1]

    if h <= pw:
        levels = list(range(1, h + 1))
        if not top_to_bottom:
            levels.reverse()
        payload: list[list[int]] = []
        for level in levels:
            row = [primary_a] * level + [primary_b] * (pw - level)
            if not left_to_right:
                row.reverse()
            payload.append(row)
    else:
        # The smallest declared width has five payload columns, enough to code
        # all fourteen possible row indices without duplicate rows.
        payload = []
        for r in range(h):
            bits = [primary_a if ((r >> c) & 1) == 0 else primary_b for c in range(pw)]
            if not left_to_right:
                bits.reverse()
            payload.append(bits)
        if not top_to_bottom:
            payload.reverse()

    if repeat_adjacent_row:
        repeat_top = max(0, min(h - 2, h // 2 - 1))
        payload[repeat_top + 1] = payload[repeat_top][:]

        # Paint every extra color as a vertical domino across the repeated
        # pair, preserving the duplicate while avoiding singleton accents.
        candidate_cols = list(range(pw))
        if not left_to_right:
            candidate_cols.reverse()
        for offset, color in enumerate(palette[2:]):
            c = candidate_cols[offset]
            payload[repeat_top][c] = color
            payload[repeat_top + 1][c] = color
    else:
        # Paint each extra color as a vertical domino across two adjacent,
        # already-distinct rows.  Reserve one column where those rows differ;
        # this guarantees that they remain distinct after receiving identical
        # accent columns.  Keeping accents in one row pair also avoids cutting
        # the staircase's thin edge into singleton primary-color components.
        pairs = [
            (r, next(c for c in range(pw) if payload[r][c] != payload[r + 1][c]))
            for r in range(h - 1)
            if payload[r] != payload[r + 1]
        ]
        if not pairs:
            raise RuntimeError("ordinary payload needs an adjacent distinct row pair")
        if h <= pw:
            accent_top, reserve_col = max(
                pairs,
                key=lambda item: min(levels[item[0]], levels[item[0] + 1]),
            )
        else:
            accent_top, reserve_col = pairs[0]
        column_order = list(range(pw))
        if not left_to_right:
            column_order.reverse()
        accent_cols = [c for c in column_order if c != reserve_col]
        for offset, color in enumerate(palette[2:]):
            c = accent_cols[offset]
            payload[accent_top][c] = color
            payload[accent_top + 1][c] = color

    if {value for row in payload for value in row} != set(palette):
        raise RuntimeError("payload failed exact palette construction")
    if _cyclic_row_period(payload) != h:
        raise RuntimeError("payload rows must retain full cyclic period")
    duplicate_count = h - len({tuple(row) for row in payload})
    if repeat_adjacent_row and duplicate_count != 1:
        raise RuntimeError("repeated-row schedule must contain exactly one duplicate row")
    if not repeat_adjacent_row and duplicate_count != 0:
        raise RuntimeError("ordinary schedules must retain distinct payload rows")
    return payload


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _require_literal_int("seed", seed)
    sample_index = _require_literal_int("sample_index", sample_index, minimum=0)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        _require_literal_int(name, value)
    band = _band(difficulty)
    phase = sample_index % len(_PROFILE_NAMES)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    default_h, default_w = _default_dimensions(ctx, phase, band)
    requested_red = overrides.get("red_row_index")
    if requested_red is not None:
        if not (0 <= requested_red <= 13):
            raise ValueError("red_row_index must be within the declared 0..13 envelope")
        if "grid_h" not in overrides:
            default_h = max(default_h, requested_red + 1)
        elif requested_red >= overrides["grid_h"]:
            _raise_incompatible(
                f"red_row_index={requested_red} does not fit grid_h={overrides['grid_h']}",
                "grid_h",
                "red_row_index",
            )

    h = _draw_scheduled_int(ctx, overrides, "grid_h", 5, 14, default_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 6, 15, default_w)
    red_default = _default_red_row(phase, h)
    red_row = _draw_scheduled_int(ctx, overrides, "red_row_index", 0, h - 1, red_default)

    palette_rng = ctx.draw_rng("palette_default")
    default_palette_size = 6 if phase % 2 == 0 else palette_rng.randint(3, 6)
    n_payload = _draw_scheduled_int(
        ctx, overrides, "payload_palette_size", 3, 6, default_palette_size
    )

    colors = ctx.draw_distinct_colors("instruction_and_payload_colors", n=n_payload + 1, exclude={2})
    instruction_color = colors[0]
    payload_palette = tuple(colors[1:])
    payload = _pattern_payload(
        h,
        w - 1,
        payload_palette,
        ctx.draw_rng("payload"),
        repeat_adjacent_row=(phase == 2),
    )

    grid = []
    for r in range(h):
        marker = 2 if r == red_row else instruction_color
        grid.append([marker, *payload[r]])
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return nested
    return {name: meta[name] for name in AXES if name in meta}


def _analyse(grid: Any, *, meta: Any = None) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty sequences"]
    h, w = len(grid), len(grid[0])
    info.update({"grid_h": h, "grid_w": w})
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    flat = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for value in flat):
        return info, ["cells must be integer ARC colors 0..9"]
    if not (3 <= h <= 18):
        errors.append(f"grid height must be 3..18, got {h}")
    if not (2 <= w <= 18):
        errors.append(f"grid width must be 2..18, got {w}")

    red_rows = [r for r, row in enumerate(grid) if row[0] == 2]
    if len(red_rows) != 1:
        errors.append(f"column 0 must contain exactly one red(2), found {len(red_rows)}")
        red_row = -1
    else:
        red_row = red_rows[0]
        info["red_row_index"] = red_row

    other_markers = [row[0] for r, row in enumerate(grid) if r != red_row]
    instruction_color = other_markers[0] if other_markers else None
    if not other_markers or len(set(other_markers)) != 1 or instruction_color == 2:
        errors.append("all non-red cells in column 0 must share one non-red instruction color")
    info["instruction_color"] = instruction_color

    payload = [list(row[1:]) for row in grid]
    payload_colors = {value for row in payload for value in row}
    info["payload"] = payload
    info["payload_palette_size"] = len(payload_colors)
    info["payload_rows_distinct"] = len({tuple(row) for row in payload}) == h
    info["payload_row_period"] = _cyclic_row_period(payload)
    if instruction_color in payload_colors:
        errors.append("the non-red instruction color must not appear in the payload")
    if len(payload_colors) < 2:
        errors.append("payload must use at least two colors")

    observed = {
        "grid_h": h,
        "grid_w": w,
        "red_row_index": red_row,
        "payload_palette_size": len(payload_colors),
    }
    for name, requested in _meta_overrides(meta).items():
        if name in observed and observed[name] != requested:
            errors.append(f"override {name} requested {requested!r}, observed {observed[name]!r}")
    info["observed"] = observed
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return dict(info["observed"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the instruction-column grammar and observable axis claims."""
    _band(difficulty)
    return _analyse(grid, meta=meta)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) != (6, 7):
        reasons.append("canonical dimensions are 6x7")
    if info["payload_palette_size"] != 6:
        reasons.append("canonical payload uses exactly six colors")
    if len({value for row in grid for value in row}) != 8:
        reasons.append("canonical inputs use eight total colors")
    return reasons


def rule_mirror(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    payload = [row[:] for row in info["payload"]]
    shift = info["red_row_index"] % len(payload)
    if shift == 0:
        return payload
    return payload[-shift:] + payload[:-shift]


def _rival_drop_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [row[:] for row in info["payload"]]


def _rival_rotate_up_by_marker(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    payload = [row[:] for row in info["payload"]]
    shift = info["red_row_index"] % len(payload)
    return payload[shift:] + payload[:shift]


def _rival_move_marker_row_to_bottom(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    payload = [row[:] for row in info["payload"]]
    shift_up = (info["red_row_index"] + 1) % len(payload)
    return payload[shift_up:] + payload[:shift_up]


def _rival_always_down_one(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    payload = [row[:] for row in info["payload"]]
    return payload[-1:] + payload[:-1]


def _rival_reverse_rows(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return list(reversed([row[:] for row in info["payload"]]))


def _rival_four_row_instruction_code(grid: Any) -> list[list[int]]:
    """Canonical-fitting shortcut: interpret the cue as a four-row code.

    Canonical demonstrations use marker rows 0..3 only, so reducing the row
    index modulo four agrees with every labeled pair.  Generated bottom-marker
    cases with heights above four refute it.
    """
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    payload = [row[:] for row in info["payload"]]
    shift = (info["red_row_index"] % 4) % len(payload)
    if shift == 0:
        return payload
    return payload[-shift:] + payload[:-shift]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "drop_column_only": _rival_drop_only,
    "rotate_up_by_marker_index": _rival_rotate_up_by_marker,
    "move_marker_row_to_bottom": _rival_move_marker_row_to_bottom,
    "always_rotate_down_one": _rival_always_down_one,
    "reverse_payload_rows": _rival_reverse_rows,
    "four_row_instruction_code": _rival_four_row_instruction_code,
}
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {
    "four_row_instruction_code": _rival_four_row_instruction_code,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _info_if_generated_witness(grid: Any) -> dict[str, Any] | None:
    info, errors = _analyse(grid)
    if errors or info["payload_row_period"] != info["grid_h"]:
        return None
    return info


def _witness_top(grid: Any) -> bool:
    info = _info_if_generated_witness(grid)
    return bool(info and info["red_row_index"] == 0)


def _witness_nonzero(grid: Any) -> bool:
    info = _info_if_generated_witness(grid)
    return bool(info and info["red_row_index"] > 0)


def _witness_direction(grid: Any) -> bool:
    info = _info_if_generated_witness(grid)
    if not info:
        return False
    h, marker = info["grid_h"], info["red_row_index"]
    return marker > 0 and (2 * marker) % h != 0


def _witness_bottom(grid: Any) -> bool:
    info = _info_if_generated_witness(grid)
    return bool(info and info["red_row_index"] == info["grid_h"] - 1)


SEMANTIC_WITNESSES = {
    "top_marker_means_zero_shift": _witness_top,
    "nonzero_marker_changes_row_order": _witness_nonzero,
    "downward_direction_is_distinguishable": _witness_direction,
    "bottom_marker_wraps_cyclically": _witness_bottom,
}
WITNESS_RIVALS = {
    "top_marker_means_zero_shift": ["always_rotate_down_one"],
    "nonzero_marker_changes_row_order": ["drop_column_only"],
    "downward_direction_is_distinguishable": ["rotate_up_by_marker_index"],
    "bottom_marker_wraps_cyclically": [
        "move_marker_row_to_bottom",
        "four_row_instruction_code",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    valid_demos: list[dict[str, Any]] = []
    marker_rows: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with downward rotation rule")
            continue
        marker_rows.add(info["red_row_index"])
        valid_demos.append(pair)

    if len(marker_rows) < 2:
        reasons.append("demonstrations need at least two distinct marker-row indices")
    if not any(row > 0 for row in marker_rows):
        reasons.append("demonstrations need a nonzero rotation")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"named rival {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, errors = _analyse(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with downward rotation rule")
    return reasons
