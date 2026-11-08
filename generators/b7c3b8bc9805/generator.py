"""Generator for ARC task b7c3b8bc9805.

A complete gray frame surrounds a blank interior.  Two distinct singleton
markers sit in corner regions outside the frame.  Read the markers in row-major
order.  The first marker chooses the phase of a two-color quadrant
checkerboard: interior quadrants with the same UL/LR-vs-UR/LL parity as that
marker receive its color, and the other quadrants receive the second color.
"""
from __future__ import annotations

import copy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b7c3b8bc9805"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a17b11ed3aa1"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A 0-background grid contains one complete gray(5) rectangular frame with "
    "a blank interior and exactly two distinct singleton colored markers in "
    "corner regions outside it. Read markers row-major. Split the frame "
    "interior into four quadrants. Quadrants with the same parity as the first "
    "marker's corner receive its color; the other two receive the second "
    "marker color. The frame, markers, and all exterior cells are preserved."
)

INVARIANTS = [
    "one complete gray frame, 5 or 6 cells high and wide, with blank interior",
    "exactly two distinct singleton non-gray markers in outside corner regions",
    "row-major first marker selects the checkerboard phase",
    "only the frame interior changes and it uses exactly the two marker colors",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "10..22"},
    "grid_w": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "10..24"},
    "frame_h": {"type": "int", "default": "four-slot schedule", "valid": "5..6"},
    "frame_w": {"type": "int", "default": "four-slot schedule", "valid": "5..6"},
    "m1_quadrant": {"type": "str", "default": "four-slot schedule", "valid": "UL|UR|LL|LR"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_QUADRANTS = ("UL", "UR", "LL", "LR")
_PHASE = {"UL": 0, "LR": 0, "UR": 1, "LL": 1}
_DIFFICULTIES = {None, "easy", "medium", "hard"}
_SLOT_PROFILE = {
    0: {"m1_quadrant": "UL", "frame_h": 6, "frame_w": 6,
        "marker_relation": "opposite", "m1_color_rank": "lower"},
    1: {"m1_quadrant": "UR", "frame_h": 5, "frame_w": 5,
        "marker_relation": "same", "m1_color_rank": "lower"},
    2: {"m1_quadrant": "LL", "frame_h": 6, "frame_w": 5,
        "marker_relation": "same", "m1_color_rank": "lower"},
    3: {"m1_quadrant": "LR", "frame_h": 5, "frame_w": 6,
        "marker_relation": "same", "m1_color_rank": "higher"},
}
SCHEDULE_PROFILES = tuple(f"slot_{i}" for i in range(4))


def _validate_call_scalars(seed, sample_index) -> None:
    """Keep deterministic call identity literal instead of coercible."""
    if type(seed) is not int:
        raise TypeError("seed must be a Python integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be a Python integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _validate_request(seed, sample_index, difficulty, overrides: dict) -> None:
    _validate_call_scalars(seed, sample_index)
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")


def _record_int(ctx, label: str, value: int, lo: int, hi: int) -> int:
    """Record a scheduled exact axis while retaining its full legal domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    ctx.draw_bounds_store[label] = (lo, hi)
    return ctx._record(label, int(value), from_override=False)


def _record_choice(ctx, label: str, value: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    ctx.draw_options_store[label] = tuple(options)
    return str(ctx._record(label, value, from_override=False))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    _validate_call_scalars(seed, sample_index)
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return f"slot_{sample_index % 4}"


def _scheduled_size(ctx, slot: int, difficulty) -> tuple[int, int]:
    if slot == 0:
        return (
            _record_int(ctx, "grid_h", 10, 10, 22),
            _record_int(ctx, "grid_w", 10, 10, 24),
        )
    # Keep every ordinary band broad but deterministic and observable.
    ranges = {
        None: ((10, 22), (10, 24)),
        "easy": ((10, 15), (10, 16)),
        "medium": ((13, 18), (14, 20)),
        "hard": ((17, 22), (18, 24)),
    }
    (hlo, hhi), (wlo, whi) = ranges[difficulty]
    if "grid_h" in ctx.overrides:
        h = ctx.draw_int_strict("grid_h", 10, 22)
    else:
        rng = ctx.draw_rng("grid_h_default")
        h = _record_int(ctx, "grid_h", rng.randint(hlo, hhi), 10, 22)
    if "grid_w" in ctx.overrides:
        w = ctx.draw_int_strict("grid_w", 10, 24)
    else:
        rng = ctx.draw_rng("grid_w_default")
        w = _record_int(ctx, "grid_w", rng.randint(wlo, whi), 10, 24)
    return h, w


def _corner_cells(h: int, w: int, top: int, left: int, fh: int, fw: int,
                  quadrant: str) -> list[tuple[int, int]]:
    bottom, right = top + fh - 1, left + fw - 1
    rows = range(0, top) if quadrant[0] == "U" else range(bottom + 1, h)
    cols = range(0, left) if quadrant[1] == "L" else range(right + 1, w)
    return [(r, c) for r in rows for c in cols]


def _choose_frame_position(ctx, h: int, w: int, fh: int, fw: int) -> tuple[int, int]:
    # Two cells of margin on every side makes every corner region large enough
    # for a same-quadrant counterexample, even at the 10x10 boundary.
    max_top = h - fh - 2
    max_left = w - fw - 2
    if max_top < 2 or max_left < 2:
        raise ValueError(f"grid {h}x{w} cannot hold {fh}x{fw} frame plus cue margins")
    if h == 10 and w == 10 and fh == 6 and fw == 6:
        return 2, 2
    rng = ctx.draw_rng("frame_position")
    return rng.randint(2, max_top), rng.randint(2, max_left)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    slot = sample_index % 4
    profile = _SLOT_PROFILE[slot]

    h, w = _scheduled_size(ctx, slot, difficulty)
    fh = _record_int(ctx, "frame_h", profile["frame_h"], 5, 6)
    fw = _record_int(ctx, "frame_w", profile["frame_w"], 5, 6)
    m1q = _record_choice(ctx, "m1_quadrant", profile["m1_quadrant"], _QUADRANTS)
    top, left = _choose_frame_position(ctx, h, w, fh, fw)

    grid = full_grid(h, w, 0)
    draw_frame(grid, top, left, top + fh - 1, left + fw - 1, 5)

    colors = sorted(ctx.draw_distinct_colors("marker_colors", n=2, exclude={0, 5}))
    if profile["m1_color_rank"] == "higher":
        m1_color, m2_color = colors[1], colors[0]
    else:
        m1_color, m2_color = colors[0], colors[1]

    # Exact quadrant overrides take precedence over curriculum relations.  The
    # ordinary four-slot stream carries the rival-killing same/opposite cases.
    relation = profile["marker_relation"] if "m1_quadrant" not in overrides else "same"
    if relation == "same":
        m2q = m1q
    else:
        # Slot 0 is the canonical anchor: UL first, then the opposite-phase
        # lower-left corner, which is always later in row-major order.
        m2q = "LL" if m1q == "UL" else "LR"

    cells1 = _corner_cells(h, w, top, left, fh, fw, m1q)
    cells2 = _corner_cells(h, w, top, left, fh, fw, m2q)
    if relation == "same":
        if len(cells1) < 2:
            raise ValueError("selected corner region cannot hold two markers")
        rng = ctx.draw_rng("marker_positions")
        picked = sorted(rng.sample(cells1, 2))
        p1, p2 = picked[0], picked[1]
    else:
        rng1 = ctx.draw_rng("marker1_position")
        rng2 = ctx.draw_rng("marker2_position")
        p1, p2 = rng1.choice(cells1), rng2.choice(cells2)
        if not p1 < p2:
            # This branch is only ordinary UL->LR; keep the assertion loud.
            raise ValueError("first-marker schedule failed row-major ordering")

    grid[p1[0]][p1[1]] = m1_color
    grid[p2[0]][p2[1]] = m2_color
    return grid


def _shape_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list"
    if not isinstance(grid[0], list) or not grid[0]:
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _analyze(grid) -> dict:
    error = _shape_error(grid)
    if error:
        return {"errors": [error], "facts": {}}
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                return {"errors": ["grid contains a non-integer or ARC color outside 0..9"], "facts": {}}
    if not 10 <= h <= 22:
        errors.append(f"height {h} must be in 10..22")
    if not 10 <= w <= 24:
        errors.append(f"width {w} must be in 10..24")

    gray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not gray:
        errors.append("missing gray frame")
        return {"errors": errors, "facts": {"height": h, "width": w}}
    top = min(r for r, _ in gray); bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray); right = max(c for _, c in gray)
    fh, fw = bottom - top + 1, right - left + 1
    if fh not in (5, 6):
        errors.append(f"frame height {fh} must be 5 or 6")
    if fw not in (5, 6):
        errors.append(f"frame width {fw} must be 5 or 6")
    expected = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    actual = set(gray)
    missing = expected - actual
    extra = actual - expected
    if missing:
        errors.append(f"gray frame has {len(missing)} missing border cell(s)")
    if extra:
        errors.append(f"gray frame has {len(extra)} gray cell(s) off the border")

    dirty = [
        (r, c, grid[r][c])
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] != 0
    ]
    if dirty:
        errors.append(f"frame interior must start blank; first dirty cell is {dirty[0]}")

    markers = sorted(
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 5)
    )
    if len(markers) != 2:
        errors.append(f"expected exactly two singleton markers, found {len(markers)}")
    if len(markers) >= 2 and markers[0][2] == markers[1][2]:
        errors.append("marker colors must be distinct")
    if len(markers) == 2:
        for r, c, color in markers:
            vertical = "U" if r < top else ("L" if r > bottom else "")
            horizontal = "L" if c < left else ("R" if c > right else "")
            if not vertical or not horizontal:
                errors.append(
                    f"marker color {color} at {(r, c)} must lie in an outside corner region"
                )
    facts = {
        "height": h, "width": w,
        "frame_top": top, "frame_left": left,
        "frame_bottom": bottom, "frame_right": right,
        "frame_h": fh, "frame_w": fw,
        "markers": markers,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyze(grid)["errors"]


def _marker_quadrant(marker: tuple[int, int, int], facts: dict) -> str:
    r, c, _ = marker
    return ("U" if r < facts["frame_top"] else "L") + (
        "L" if c < facts["frame_left"] else "R"
    )


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "frame_h": facts["frame_h"],
        "frame_w": facts["frame_w"],
        "m1_quadrant": _marker_quadrant(facts["markers"][0], facts),
    }


def semantic_signature(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("malformed grid: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    m1, m2 = facts["markers"]
    q1, q2 = _marker_quadrant(m1, facts), _marker_quadrant(m2, facts)
    strict = (
        (facts["height"], facts["width"]) == (10, 10)
        and (facts["frame_top"], facts["frame_left"], facts["frame_h"], facts["frame_w"])
        == (2, 2, 6, 6)
        and _PHASE[q1] != _PHASE[q2]
    )
    return {
        "m1_quadrant": q1,
        "m1_phase": "diagonal" if _PHASE[q1] == 0 else "off_diagonal",
        "marker_phase_relation": "same" if _PHASE[q1] == _PHASE[q2] else "opposite",
        "m1_color_rank": "lower" if m1[2] < m2[2] else "higher",
        "frame_parity": (facts["frame_h"] % 2, facts["frame_w"] % 2),
        "strict_canonical_like": strict,
    }


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("grid is outside rule domain: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    m1, m2 = facts["markers"]
    m1q = _marker_quadrant(m1, facts)
    phase = _PHASE[m1q]
    output = copy.deepcopy(grid)
    ir1, ir2 = facts["frame_top"] + 1, facts["frame_bottom"] - 1
    ic1, ic2 = facts["frame_left"] + 1, facts["frame_right"] - 1
    hmid = (ir1 + ir2) // 2
    wmid = (ic1 + ic2) // 2
    for r in range(ir1, ir2 + 1):
        for c in range(ic1, ic2 + 1):
            qr = 0 if r < hmid + 1 else 1
            qc = 0 if c < wmid + 1 else 1
            output[r][c] = m1[2] if (qr + qc) % 2 == phase else m2[2]
    return output


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze(grid)["facts"]
    m1, m2 = facts["markers"]
    q1, q2 = _marker_quadrant(m1, facts), _marker_quadrant(m2, facts)
    strict_errors: list[str] = []
    if (facts["height"], facts["width"]) != (10, 10):
        strict_errors.append("canonical profile requires 10x10")
    if (facts["frame_top"], facts["frame_left"], facts["frame_h"], facts["frame_w"]) != (2, 2, 6, 6):
        strict_errors.append("canonical profile requires the 6x6 frame at (2,2)")
    if _PHASE[q1] == _PHASE[q2]:
        strict_errors.append("canonical profile requires opposite marker parity")
    return strict_errors


def _rival_fill(grid, first_phase: int, first_color: int, second_color: int):
    facts = _analyze(grid)["facts"]
    output = copy.deepcopy(grid)
    ir1, ir2 = facts["frame_top"] + 1, facts["frame_bottom"] - 1
    ic1, ic2 = facts["frame_left"] + 1, facts["frame_right"] - 1
    hmid, wmid = (ir1 + ir2) // 2, (ic1 + ic2) // 2
    for r in range(ir1, ir2 + 1):
        for c in range(ic1, ic2 + 1):
            p = ((0 if r < hmid + 1 else 1) + (0 if c < wmid + 1 else 1)) % 2
            output[r][c] = first_color if p == first_phase else second_color
    return output


def _rival_marker_position_symmetric(grid):
    if self_check(grid):
        return None
    facts = _analyze(grid)["facts"]
    m1, m2 = facts["markers"]
    p1 = _PHASE[_marker_quadrant(m1, facts)]
    p2 = _PHASE[_marker_quadrant(m2, facts)]
    if p1 == p2:
        return _rival_fill(grid, p1, m2[2], m1[2])
    return _rival_fill(grid, p1, m1[2], m2[2])


def _rival_always_diagonal(grid):
    if self_check(grid):
        return None
    m1, m2 = _analyze(grid)["facts"]["markers"]
    return _rival_fill(grid, 0, m1[2], m2[2])


def _rival_always_off_diagonal(grid):
    if self_check(grid):
        return None
    m1, m2 = _analyze(grid)["facts"]["markers"]
    return _rival_fill(grid, 1, m1[2], m2[2])


def _rival_lower_color_primary(grid):
    if self_check(grid):
        return None
    facts = _analyze(grid)["facts"]
    m1, m2 = facts["markers"]
    p1 = _PHASE[_marker_quadrant(m1, facts)]
    lo, hi = sorted((m1[2], m2[2]))
    return _rival_fill(grid, p1, lo, hi)


SEMANTIC_RIVALS = {
    "marker_position_symmetric": _rival_marker_position_symmetric,
    "always_diagonal": _rival_always_diagonal,
    "always_off_diagonal": _rival_always_off_diagonal,
    "lower_color_primary": _rival_lower_color_primary,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "marker_position_symmetric": _rival_marker_position_symmetric,
}


def _sig_is(**expected) -> Callable[[list[list[int]]], bool]:
    def predicate(grid) -> bool:
        if self_check(grid):
            return False
        sig = semantic_signature(grid)
        return all(sig.get(key) == value for key, value in expected.items())
    return predicate


SEMANTIC_WITNESSES = {
    "m1_upper_right": _sig_is(m1_quadrant="UR"),
    "m1_lower_left": _sig_is(m1_quadrant="LL"),
    "m1_lower_right": _sig_is(m1_quadrant="LR"),
    "diagonal_phase": _sig_is(m1_phase="diagonal"),
    "off_diagonal_phase": _sig_is(m1_phase="off_diagonal"),
    "same_phase_markers": _sig_is(marker_phase_relation="same"),
    "same_phase_m1_lower": _sig_is(marker_phase_relation="same", m1_color_rank="lower"),
    "same_phase_m1_higher": _sig_is(marker_phase_relation="same", m1_color_rank="higher"),
}
WITNESS_RIVALS = {
    "m1_upper_right": ["marker_position_symmetric", "always_diagonal"],
    "m1_lower_left": ["marker_position_symmetric", "always_diagonal"],
    "m1_lower_right": ["marker_position_symmetric", "always_off_diagonal", "lower_color_primary"],
    "diagonal_phase": ["always_off_diagonal"],
    "off_diagonal_phase": ["always_diagonal"],
    "same_phase_markers": ["marker_position_symmetric"],
    "same_phase_m1_lower": ["marker_position_symmetric"],
    "same_phase_m1_higher": ["marker_position_symmetric", "lower_color_primary"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    signatures = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
            signatures.append(semantic_signature(demo["input"]))
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output does not match the quadrant-phase rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    quadrants = {s["m1_quadrant"] for s in signatures}
    phases = {s["m1_phase"] for s in signatures}
    relations = {s["marker_phase_relation"] for s in signatures}
    ranks = {s["m1_color_rank"] for s in signatures}
    if quadrants != set(_QUADRANTS):
        reasons.append(f"demos must cover all first-marker quadrants, got {sorted(quadrants)}")
    if phases != {"diagonal", "off_diagonal"}:
        reasons.append(f"demos must cover both phases, got {sorted(phases)}")
    if relations != {"same", "opposite"}:
        reasons.append(f"demos must cover same and opposite marker parity, got {sorted(relations)}")
    if ranks != {"lower", "higher"}:
        reasons.append(f"demos must make first-marker color order vary, got {sorted(ranks)}")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    base = generate(811, 0, difficulty="easy")
    facts = _analyze(base)["facts"]
    fixtures: list[tuple[str, list[list[int]]]] = []
    fixtures.append(("all_background", full_grid(len(base), len(base[0]), 0)))

    broken = copy.deepcopy(base)
    broken[facts["frame_top"]][facts["frame_left"] + 1] = 0
    fixtures.append(("missing_frame_cell", broken))

    one_marker = copy.deepcopy(base)
    r, c, _ = facts["markers"][1]
    one_marker[r][c] = 0
    fixtures.append(("one_marker", one_marker))

    dirty = copy.deepcopy(base)
    dirty[facts["frame_top"] + 1][facts["frame_left"] + 1] = 4
    fixtures.append(("dirty_interior", dirty))

    edge_marker = copy.deepcopy(base)
    r, c, color = facts["markers"][0]
    edge_marker[r][c] = 0
    edge_marker[0][facts["frame_left"] + 1] = color
    fixtures.append(("marker_not_in_corner_region", edge_marker))

    extra = copy.deepcopy(base)
    top, bottom = facts["frame_top"], facts["frame_bottom"]
    left, right = facts["frame_left"], facts["frame_right"]
    blank_corner = next(
        (r, c)
        for r in range(len(extra))
        for c in range(len(extra[0]))
        if extra[r][c] == 0
        and (r < top or r > bottom)
        and (c < left or c > right)
    )
    extra[blank_corner[0]][blank_corner[1]] = next(
        color for color in range(1, 10)
        if color not in {5, facts["markers"][0][2], facts["markers"][1][2]}
    )
    fixtures.append(("third_marker", extra))

    painted = rule_mirror(base)
    fixtures.append(("already_transformed", painted))
    return fixtures
