"""Canonical-profile generator for ``bee63e6e52bd``.

A single nonzero, non-yellow color forms a rectangular frame with one
contiguous gap in exactly one side.  The two retained pieces of that side are
the mouth arms.  The selected Racket rule pours yellow (4) through the gap,
fills the cavity, paints one cell just outside each arm tip, and continues away
from both tips as 45-degree diagonal spouts.

``generate`` returns inputs only.  The Python transformations below are review
mirrors and declared rival rules; the pinned Racket program remains authority.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bee63e6e52bd"
TASK_ID = GENERATOR_ID
RULE_HASH = "eedba8f59365"
VERSION = "3.0.0"
SUMMARY = (
    "A canonical-size 0-background grid contains one colored rectangular frame "
    "with one contiguous gap on exactly one side. Yellow (4) pours from that "
    "mouth through the cavity and continues diagonally beyond both arm tips. "
    "Arm lengths include canonical 2/2 cases and scheduled 1/1, 1/3, and 3/1 "
    "counterexamples to the strongest canonical-fitting shortcut."
)

INVARIANTS = [
    "the input contains only background 0 and one non-4 shape color",
    "the shape lies on one rectangular perimeter with exactly three full sides",
    "the fourth side has one contiguous nonempty gap and keeps both corners",
    "the open side has at least one outward background cell inside the canvas",
    "ordinary samples use a canonical 6x6, 7x7, 9x9, or 10x10 canvas profile",
]

SCENE_PROFILES = {
    "6x6": (6, 6),
    "7x7": (7, 7),
    "9x9": (9, 9),
    "10x10": (10, 10),
}
OPEN_SIDES = ("left", "right", "top", "bottom")
ARM_LENGTHS = {
    "canonical_2_2": (2, 2),
    "short_1_1": (1, 1),
    "asym_1_3": (1, 3),
    "asym_3_1": (3, 1),
}
SCHEDULE_PROFILES = (
    "canonical_2_2",
    "short_1_1",
    "asym_1_3",
    "asym_3_1",
)
LESSON_SCHEDULE_PERIOD = 4
COLORS = (1, 2, 3, 5, 6, 7, 8, 9)

# Keep this a literal dictionary: static review tooling intentionally parses it.
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "canonical-profile draw",
        "valid": "6x6|7x7|9x9|10x10",
    },
    "open_side": {
        "type": "str",
        "default": "uniform",
        "valid": "left|right|top|bottom",
    },
    "arm_profile": {
        "type": "str",
        "default": "period-4 teaching schedule",
        "valid": "canonical_2_2|short_1_1|asym_1_3|asym_3_1",
    },
    "color": {
        "type": "color",
        "default": "uniform non-0 non-4",
        "valid": "1|2|3|5|6|7|8|9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the period-four arm curriculum.

    There is only one canonical-fitting 2/2 slot per period.  Therefore every
    three consecutive demonstrations, and every three-demo holdout of four
    consecutive pairs, retains at least two counterexamples to the 2/2-only
    shortcut.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _profile_options(difficulty) -> tuple[str, ...]:
    """Preserve every exact profile in every band while shifting density."""
    all_profiles = tuple(SCENE_PROFILES)
    if difficulty == "easy":
        return all_profiles + ("6x6",) * 5 + ("7x7",) * 3
    if difficulty == "medium":
        return all_profiles + ("7x7",) * 2 + ("9x9",) * 5
    if difficulty == "hard":
        return all_profiles + ("9x9",) * 2 + ("10x10",) * 5
    return all_profiles


def _validate_request(difficulty, overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    for name in ("scene_profile", "open_side", "arm_profile"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not str:
            raise TypeError(f"{name} override must be a string")
    if "color" in overrides and overrides["color"] is not None and type(overrides["color"]) is not int:
        raise TypeError("color override must be an integer ARC color (not bool)")


def _choose_dimension(rng, lo: int, hi: int, difficulty) -> int:
    if hi < lo:
        raise ValueError(f"no legal dimension in [{lo}, {hi}]")
    if difficulty == "easy":
        return lo
    if difficulty == "hard":
        return hi
    return rng.randint(lo, hi)


def _draw_frame(
    h: int,
    w: int,
    side: str,
    before: int,
    after: int,
    color: int,
    *,
    difficulty,
    rng,
) -> list[list[int]]:
    """Construct a legal one-gap perimeter with an outward mouth margin."""
    minimum_span = max(5, before + after + 1)
    if side in ("left", "right"):
        bh = _choose_dimension(rng, minimum_span, h, difficulty)
        bw = _choose_dimension(rng, 3, w - 1, difficulty)
        r0 = rng.randint(0, h - bh)
        if side == "left":
            c0 = rng.randint(1, w - bw)
        else:
            c0 = rng.randint(0, w - bw - 1)
    else:
        bw = _choose_dimension(rng, minimum_span, w, difficulty)
        bh = _choose_dimension(rng, 3, h - 1, difficulty)
        c0 = rng.randint(0, w - bw)
        if side == "top":
            r0 = rng.randint(1, h - bh)
        else:
            r0 = rng.randint(0, h - bh - 1)
    r1, c1 = r0 + bh - 1, c0 + bw - 1

    grid = full_grid(h, w, 0)
    for c in range(c0, c1 + 1):
        grid[r0][c] = color
        grid[r1][c] = color
    for r in range(r0, r1 + 1):
        grid[r][c0] = color
        grid[r][c1] = color

    if side == "left":
        for r in range(r0 + before, r1 - after + 1):
            grid[r][c0] = 0
    elif side == "right":
        for r in range(r0 + before, r1 - after + 1):
            grid[r][c1] = 0
    elif side == "top":
        for c in range(c0 + before, c1 - after + 1):
            grid[r0][c] = 0
    else:
        for c in range(c0 + before, c1 - after + 1):
            grid[r1][c] = 0
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)

    # The scheduled arm profile is injected only as the default.  Explicit
    # caller overrides still pass through the same draw_choice validity gate.
    effective_overrides = dict(overrides)
    if effective_overrides.get("arm_profile") is None:
        effective_overrides["arm_profile"] = schedule_profile(
            seed, sample_index, difficulty
        )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", _profile_options(difficulty))
    side = ctx.draw_choice("open_side", OPEN_SIDES)
    arm_profile = ctx.draw_choice("arm_profile", SCHEDULE_PROFILES)
    color = ctx.draw_choice("color", COLORS)
    before, after = ARM_LENGTHS[arm_profile]
    h, w = SCENE_PROFILES[profile]
    return _draw_frame(
        h,
        w,
        side,
        before,
        after,
        color,
        difficulty=difficulty,
        rng=ctx.draw_rng("frame_geometry"),
    )


def _shape_facts(grid) -> tuple[dict | None, list[str]]:
    """Validate and describe a one-gap frame without mutating the input."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid rows must be nonempty and rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9 (not bool)"]

    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 1 or colors[0] == 4:
        return None, [
            f"input must contain exactly one nonzero shape color excluding 4, found {colors}"
        ]
    color = colors[0]
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    if not cells:
        return None, ["shape is empty"]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    rh, rw = r1 - r0 + 1, c1 - c0 + 1
    errors: list[str] = []
    if rh < 3 or rw < 3:
        errors.append(f"frame bbox {rh}x{rw} must be at least 3x3")

    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    missing_corners = sorted(corners - cells)
    if missing_corners:
        errors.append(f"frame is missing bbox corner(s) {missing_corners}")
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    extras = sorted(cells - perimeter)
    if extras:
        errors.append(f"shape color appears inside the frame at {extras[:4]}")

    sequences = {
        "top": [(r0, c) in cells for c in range(c0, c1 + 1)],
        "bottom": [(r1, c) in cells for c in range(c0, c1 + 1)],
        "left": [(r, c0) in cells for r in range(r0, r1 + 1)],
        "right": [(r, c1) in cells for r in range(r0, r1 + 1)],
    }
    incomplete = [side for side, occupied in sequences.items() if not all(occupied)]
    if len(incomplete) != 1:
        errors.append(
            f"expected exactly three full sides and one open side, found incomplete={incomplete}"
        )
        return None, errors
    side = incomplete[0]
    missing = [index for index, occupied in enumerate(sequences[side]) if not occupied]
    if not missing:
        errors.append("open side must have a nonempty gap")
        return None, errors
    if missing != list(range(missing[0], missing[-1] + 1)):
        errors.append("open side must contain exactly one contiguous gap")
    before = missing[0]
    after = len(sequences[side]) - missing[-1] - 1
    if before < 1 or after < 1:
        errors.append("both mouth arms must retain their bbox corner")

    h, w = len(grid), width
    if side == "left" and c0 == 0:
        errors.append("left-facing mouth must have an outward background column")
    elif side == "right" and c1 == w - 1:
        errors.append("right-facing mouth must have an outward background column")
    elif side == "top" and r0 == 0:
        errors.append("top-facing mouth must have an outward background row")
    elif side == "bottom" and r1 == h - 1:
        errors.append("bottom-facing mouth must have an outward background row")
    if errors:
        return None, errors
    return {
        "height": h,
        "width": w,
        "color": color,
        "bbox": (r0, c0, r1, c1),
        "open_side": side,
        "arm_before": before,
        "arm_after": after,
        "gap_start": missing[0],
        "gap_end": missing[-1],
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _shape_facts(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    facts, errors = _shape_facts(grid)
    if errors:
        return list(errors)
    assert facts is not None
    profile = f"{facts['height']}x{facts['width']}"
    if profile not in SCENE_PROFILES:
        return [
            f"canvas profile {profile} is outside the declared canonical-profile manifold"
        ]
    return []


def observe_overrides(grid) -> dict[str, object]:
    facts, errors = _shape_facts(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid input: " + "; ".join(errors))
    assert facts is not None
    arm_lookup = {lengths: name for name, lengths in ARM_LENGTHS.items()}
    lengths = (facts["arm_before"], facts["arm_after"])
    if lengths not in arm_lookup:
        raise ValueError(f"arm lengths {lengths} are outside the declared axis domain")
    return {
        "scene_profile": f"{facts['height']}x{facts['width']}",
        "open_side": facts["open_side"],
        "arm_profile": arm_lookup[lengths],
        "color": facts["color"],
    }


def _paint_zero(out: list[list[int]], r: int, c: int) -> None:
    if 0 <= r < len(out) and 0 <= c < len(out[0]) and out[r][c] == 0:
        out[r][c] = 4


def _apply_with_assumed_arms(grid, before: int, after: int):
    facts, errors = _shape_facts(grid)
    if errors:
        raise ValueError("invalid frame input: " + "; ".join(errors))
    assert facts is not None
    out = deepcopy(grid)
    h, w = facts["height"], facts["width"]
    r0, c0, r1, c1 = facts["bbox"]
    side = facts["open_side"]

    if side in ("left", "right"):
        top_tip = r0 + before - 1
        bottom_tip = r1 - after + 1
        mouth_c = c0 - 1 if side == "left" else c1 + 1
        for r in range(top_tip + 1, bottom_tip):
            columns = range(0, c1 + 1) if side == "left" else range(c0, w)
            for c in columns:
                _paint_zero(out, r, c)
        for r in (top_tip, bottom_tip):
            _paint_zero(out, r, mouth_c)
            interior = range(c0 + 1, c1 + 1) if side == "left" else range(c0, c1)
            for c in interior:
                _paint_zero(out, r, c)
        outward = -1 if side == "left" else 1
        for distance in range(1, max(h, w) + 1):
            _paint_zero(out, top_tip - distance, mouth_c + outward * distance)
            _paint_zero(out, bottom_tip + distance, mouth_c + outward * distance)
    else:
        left_tip = c0 + before - 1
        right_tip = c1 - after + 1
        mouth_r = r0 - 1 if side == "top" else r1 + 1
        for c in range(left_tip + 1, right_tip):
            rows = range(0, r1 + 1) if side == "top" else range(r0, h)
            for r in rows:
                _paint_zero(out, r, c)
        for c in (left_tip, right_tip):
            _paint_zero(out, mouth_r, c)
            interior = range(r0 + 1, r1 + 1) if side == "top" else range(r0, r1)
            for r in interior:
                _paint_zero(out, r, c)
        outward = -1 if side == "top" else 1
        for distance in range(1, max(h, w) + 1):
            _paint_zero(out, mouth_r + outward * distance, left_tip - distance)
            _paint_zero(out, mouth_r + outward * distance, right_tip + distance)
    return out


def _apply_intended(grid):
    """Independent-from-generation Python mirror used only for review hooks."""
    facts, errors = _shape_facts(grid)
    if errors:
        raise ValueError("invalid frame input: " + "; ".join(errors))
    assert facts is not None
    return _apply_with_assumed_arms(
        grid, facts["arm_before"], facts["arm_after"]
    )


def _fixed_two_arms(grid):
    """RIVAL: incorrectly assumes both mouth arms are always length two."""
    return _apply_with_assumed_arms(grid, 2, 2)


def _has_noncanonical_arm_lengths(grid) -> bool:
    facts, errors = _shape_facts(grid)
    return not errors and facts is not None and (
        facts["arm_before"], facts["arm_after"]
    ) != (2, 2)


SEMANTIC_WITNESSES = {
    "noncanonical_arm_lengths": _has_noncanonical_arm_lengths,
}
SEMANTIC_RIVALS = {
    "fixed_two_arms": _fixed_two_arms,
}
WITNESS_RIVALS = {
    "noncanonical_arm_lengths": ["fixed_two_arms"],
}
CANONICAL_SHORTCUTS = {
    "fixed_two_arms": _fixed_two_arms,
}
LESSON_COMPETITORS = {
    "fixed_two_arms": _fixed_two_arms,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that survive all demos but change the query answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        if pair["output"] != _apply_intended(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the frame-pour rule")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
    elif query["output"] != _apply_intended(query["input"]):
        reasons.append("query output disagrees with the frame-pour rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons
