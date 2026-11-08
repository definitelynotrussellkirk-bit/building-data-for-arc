"""Generator for filling axis-aligned spans between equal-color endpoints.

Each active color occurs exactly twice.  Its two cells share one row or one
column and are separated by at least one blank cell.  The Racket rule paints
the inclusive segment between the two cells.  When perpendicular spans cross,
colors are processed by row-major first appearance, so the later color
repaints the blank intersection.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cea99cea0238"
TASK_ID = "cea99cea0238"
RULE_HASH = "7e8b9ba56afa"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

SUMMARY = (
    "On a sparse 0-background grid, every nonzero color appears at exactly "
    "two axis-aligned endpoints. Fill the inclusive horizontal or vertical "
    "span between each pair with its endpoint color. Perpendicular spans may "
    "cross; row-major first-appearance order determines which later color "
    "occupies a blank crossing cell."
)

INVARIANTS = [
    "background is 0 and every active color appears exactly twice",
    "the two cells of each color share a row or a column",
    "each endpoint pair has at least one blank cell between its endpoints",
    "different colors never place an endpoint on another color's span",
    "ordinary lessons include horizontal, vertical, and crossing witnesses",
]

ORIENTATION_PROFILES = ("horizontal", "vertical", "mixed")
CROSSING_PROFILES = ("separated", "crossing")
HELPFUL_TEXTURES = ("horizontal", "vertical", "mixed", "crossing")
DEGENERATE_TEXTURES = (
    "no_pairs",
    "adjacent_pair",
    "no_shared_axis",
    "triplicate_color",
)
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..16",
        "valid": "9..16",
    },
    "spans": {
        "type": "int",
        "default": "difficulty-aware 2..7",
        "valid": "2..7",
    },
    "orientation_profile": {
        "type": "str",
        "default": "sample_index lesson schedule",
        "valid": "horizontal|vertical|mixed",
    },
    "crossing_profile": {
        "type": "str",
        "default": "sample_index lesson schedule",
        "valid": "separated|crossing",
    },
    "texture": {
        "type": "str",
        "default": "optional alias for a lesson profile",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class Segment:
    orientation: str
    start: tuple[int, int]
    end: tuple[int, int]
    cells: tuple[tuple[int, int], ...]
    interior: frozenset[tuple[int, int]]

    @property
    def endpoints(self) -> frozenset[tuple[int, int]]:
        return frozenset((self.start, self.end))


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], 0, 0
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if bad:
        errors.append(f"grid colors must be integer values 0..9; got {bad}")
    return errors, h, w


def _color_order(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                ordered.append(value)
    return ordered


def _segment_from_cells(cells: list[tuple[int, int]]) -> Segment | None:
    if len(cells) != 2:
        return None
    p0, p1 = sorted(cells)
    r0, c0 = p0
    r1, c1 = p1
    if r0 == r1 and abs(c1 - c0) >= 2:
        lo, hi = sorted((c0, c1))
        line = tuple((r0, col) for col in range(lo, hi + 1))
        return Segment("horizontal", (r0, lo), (r0, hi), line, frozenset(line[1:-1]))
    if c0 == c1 and abs(r1 - r0) >= 2:
        lo, hi = sorted((r0, r1))
        line = tuple((row, c0) for row in range(lo, hi + 1))
        return Segment("vertical", (lo, c0), (hi, c0), line, frozenset(line[1:-1]))
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_errors(grid)
    facts: dict[str, Any] = {
        "grid_h": h,
        "grid_w": w,
        "spans": 0,
        "palette_size": 0,
        "segments": [],
        "horizontal_count": 0,
        "vertical_count": 0,
        "orientation_profile": None,
        "crossing_count": 0,
        "crossing_profile": None,
        "changed_cells": 0,
        "output": None,
    }
    if errors:
        return {"errors": errors, "facts": facts}

    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))

    if len(positions) < 2:
        errors.append(f"expected at least two active colors; found {len(positions)}")

    segments: list[tuple[int, Segment]] = []
    for color in _color_order(grid):
        cells = positions[color]
        if len(cells) != 2:
            errors.append(f"color {color} must appear exactly twice; found {len(cells)}")
            continue
        segment = _segment_from_cells(cells)
        if segment is None:
            errors.append(
                f"color {color} endpoints must share a row or column with a blank gap"
            )
            continue
        blocked = [cell for cell in segment.interior if grid[cell[0]][cell[1]] != 0]
        if blocked:
            errors.append(
                f"color {color} span interior contains nonzero endpoint cell(s): {blocked[:3]}"
            )
        segments.append((color, segment))

    endpoint_owner: dict[tuple[int, int], int] = {}
    for color, segment in segments:
        for endpoint in segment.endpoints:
            other = endpoint_owner.get(endpoint)
            if other is not None and other != color:
                errors.append(f"colors {other} and {color} share endpoint {endpoint}")
            endpoint_owner[endpoint] = color

    crossing_count = 0
    for index, (_, first) in enumerate(segments):
        for _, second in segments[index + 1 :]:
            shared = set(first.cells) & set(second.cells)
            if not shared:
                continue
            lawful = first.orientation != second.orientation and shared <= (
                first.interior & second.interior
            )
            if not lawful:
                errors.append(
                    "spans may intersect only at perpendicular interior cells; "
                    f"found {sorted(shared)[:3]}"
                )
            else:
                crossing_count += len(shared)

    horizontal = sum(segment.orientation == "horizontal" for _, segment in segments)
    vertical = sum(segment.orientation == "vertical" for _, segment in segments)
    orientation_profile = (
        "horizontal" if horizontal and not vertical else
        "vertical" if vertical and not horizontal else
        "mixed" if horizontal and vertical else None
    )

    output = None
    changed = 0
    if not errors:
        output = _apply_segments(grid, segments, mode="official")
        changed = sum(
            grid[r][c] != output[r][c]
            for r in range(h)
            for c in range(w)
        )
        if changed == 0:
            errors.append("rule would be an identity transformation")

    facts.update(
        {
            "spans": len(segments),
            "palette_size": len(positions) + 1,
            "segments": segments,
            "horizontal_count": horizontal,
            "vertical_count": vertical,
            "orientation_profile": orientation_profile,
            "crossing_count": crossing_count,
            "crossing_profile": "crossing" if crossing_count else "separated",
            "changed_cells": changed,
            "output": output,
        }
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, identity, diagonal, adjacent, and blocked-span scenes."""
    del difficulty, meta
    return _analyze(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold: three mixed-orientation spans at public scale."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    facts = analysis["facts"]
    if reasons:
        return reasons
    if facts["spans"] != 3:
        reasons.append(f"canonical examples have exactly 3 spans; found {facts['spans']}")
    if facts["orientation_profile"] != "mixed":
        reasons.append("canonical examples contain both horizontal and vertical spans")
    if not 8 <= facts["grid_h"] <= 10 or not 9 <= facts["grid_w"] <= 11:
        reasons.append(
            f"canonical dimensions are 8..10 by 9..11; found "
            f"{facts['grid_h']}x{facts['grid_w']}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover all exact semantic axes from a returned valid grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "spans": facts["spans"],
        "orientation_profile": facts["orientation_profile"],
        "crossing_profile": facts["crossing_profile"],
    }


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    lengths = sorted(len(segment.cells) for _, segment in facts["segments"])
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "spans": facts["spans"],
        "orientation_profile": facts["orientation_profile"],
        "crossing_profile": facts["crossing_profile"],
        "crossing_count": facts["crossing_count"],
        "span_lengths": lengths,
        "changed_cells": facts["changed_cells"],
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (facts["grid_h"], facts["grid_w"], facts["palette_size"])


def _witness(grid, key: str) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    facts = analysis["facts"]
    if key == "horizontal_span":
        return facts["horizontal_count"] > 0
    if key == "vertical_span":
        return facts["vertical_count"] > 0
    if key == "crossing_spans":
        return facts["crossing_count"] > 0
    if key == "separated_spans":
        return facts["crossing_count"] == 0
    raise KeyError(key)


SEMANTIC_WITNESSES = {
    "horizontal_span": lambda grid: _witness(grid, "horizontal_span"),
    "vertical_span": lambda grid: _witness(grid, "vertical_span"),
    "crossing_spans": lambda grid: _witness(grid, "crossing_spans"),
    "separated_spans": lambda grid: _witness(grid, "separated_spans"),
}


def _apply_segments(grid, segments, *, mode: str) -> list[list[int]]:
    out = [list(row) for row in grid]
    if mode == "identity":
        return out
    selected = list(segments)
    if mode == "horizontal_only":
        selected = [(c, s) for c, s in selected if s.orientation == "horizontal"]
    elif mode == "vertical_only":
        selected = [(c, s) for c, s in selected if s.orientation == "vertical"]
    elif mode == "first_span_only":
        selected = selected[:1]
    elif mode == "last_span_only":
        selected = selected[-1:]

    first_color = selected[0][0] if selected else 0
    for color, segment in selected:
        if mode == "extend_to_borders":
            if segment.orientation == "horizontal":
                cells = [(segment.start[0], c) for c in range(len(out[0]))]
            else:
                cells = [(r, segment.start[1]) for r in range(len(out))]
        else:
            cells = segment.cells
        paint_color = first_color if mode == "constant_first_color" else color
        for r, c in cells:
            if mode == "first_wins" and grid[r][c] == 0 and out[r][c] != 0:
                continue
            out[r][c] = paint_color
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python mirror used for focused evidence; Racket is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["facts"]["output"]]


_CANDIDATE_RULES = (
    "official",
    "identity",
    "horizontal_only",
    "vertical_only",
    "first_span_only",
    "last_span_only",
    "extend_to_borders",
    "constant_first_color",
    "first_wins",
)


def _candidate_output(name: str, grid) -> list[list[int]] | None:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    mode = "official" if name == "official" else name
    return _apply_segments(grid, analysis["facts"]["segments"], mode=mode)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible shortcut changes the query answer."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    consistent: list[str] = []
    for name in _CANDIDATE_RULES:
        if all(
            _candidate_output(name, pair.get("input")) == pair.get("output")
            for pair in demos
            if isinstance(pair, dict)
        ) and all(isinstance(pair, dict) for pair in demos):
            consistent.append(name)
    if "official" not in consistent:
        return ["official span-fill rule is not consistent with every demonstration"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]
    official = _candidate_output("official", query.get("input"))
    if official != query.get("output"):
        return ["query output disagrees with the official span-fill rule"]
    differing = [
        name
        for name in consistent
        if _candidate_output(name, query.get("input")) != official
    ]
    if differing:
        return [
            "demonstrations admit shortcut rule(s) with a different query answer: "
            + ", ".join(differing)
        ]
    return []


def _draw_int_axis(ctx, overrides, name, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _default_ranges(difficulty):
    if difficulty == "easy":
        return (8, 10), (9, 11), (2, 3)
    if difficulty == "hard":
        return (9, 11), (10, 13), (3, 6)
    return (8, 11), (9, 12), (3, 5)


def _effective_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    effective = dict(overrides)
    texture = effective.get("texture")
    mapped = {
        "horizontal": ("horizontal", "separated"),
        "vertical": ("vertical", "separated"),
        "mixed": ("mixed", "separated"),
        "crossing": ("mixed", "crossing"),
    }
    if texture in mapped:
        orientation, crossing = mapped[texture]
        if effective.get("orientation_profile") not in (None, orientation):
            raise ValueError(
                f"texture={texture!r} conflicts with "
                f"orientation_profile={effective['orientation_profile']!r}"
            )
        if effective.get("crossing_profile") not in (None, crossing):
            raise ValueError(
                f"texture={texture!r} conflicts with "
                f"crossing_profile={effective['crossing_profile']!r}"
            )
        effective["orientation_profile"] = orientation
        effective["crossing_profile"] = crossing
    if (
        effective.get("crossing_profile") == "crossing"
        and effective.get("orientation_profile") not in (None, "mixed")
    ):
        raise ValueError(
            "crossing_profile='crossing' requires orientation_profile='mixed'"
        )
    return effective


def _scheduled_profiles(ctx, sample_index: int, effective: dict[str, Any]):
    explicit_orientation = effective.get("orientation_profile") is not None
    explicit_crossing = effective.get("crossing_profile") is not None

    if explicit_crossing and effective["crossing_profile"] == "crossing":
        default_orientation = ("mixed",)
    elif explicit_orientation:
        default_orientation = ORIENTATION_PROFILES
    else:
        slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
        if slot == 0:
            default_orientation = ("horizontal",)
        elif slot == 1:
            default_orientation = ("vertical",)
        elif slot == 2:
            default_orientation = ("mixed",)
        else:
            default_orientation = ORIENTATION_PROFILES

    orientation = ctx.draw_choice("orientation_profile", default_orientation)

    if orientation != "mixed":
        default_crossing = ("separated",)
    elif explicit_crossing:
        default_crossing = CROSSING_PROFILES
    else:
        slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
        default_crossing = ("crossing",) if slot == 2 else CROSSING_PROFILES
    crossing = ctx.draw_choice("crossing_profile", default_crossing)

    if crossing == "crossing" and orientation != "mixed":
        raise ValueError("crossing_profile='crossing' requires orientation_profile='mixed'")
    return orientation, crossing


@lru_cache(maxsize=None)
def _candidate_segments(h: int, w: int, orientation: str) -> tuple[Segment, ...]:
    result: list[Segment] = []
    if orientation == "horizontal":
        for r in range(h):
            for length in range(3, min(w, 7) + 1):
                for c0 in range(0, w - length + 1):
                    cells = tuple((r, c) for c in range(c0, c0 + length))
                    result.append(
                        Segment(
                            orientation,
                            cells[0],
                            cells[-1],
                            cells,
                            frozenset(cells[1:-1]),
                        )
                    )
    else:
        for c in range(w):
            for length in range(3, min(h, 7) + 1):
                for r0 in range(0, h - length + 1):
                    cells = tuple((r, c) for r in range(r0, r0 + length))
                    result.append(
                        Segment(
                            orientation,
                            cells[0],
                            cells[-1],
                            cells,
                            frozenset(cells[1:-1]),
                        )
                    )
    return tuple(result)


def _compatible(candidate: Segment, chosen: list[Segment], allow_crossings: bool) -> bool:
    candidate_cells = set(candidate.cells)
    for other in chosen:
        other_cells = set(other.cells)
        if candidate.endpoints & other_cells or other.endpoints & candidate_cells:
            return False
        shared = candidate_cells & other_cells
        if not shared:
            continue
        if not allow_crossings:
            return False
        if candidate.orientation == other.orientation:
            return False
        if not shared <= (candidate.interior & other.interior):
            return False
    return True


def _initial_crossing_pair(h: int, w: int, rng) -> tuple[Segment, Segment]:
    """Construct one perpendicular interior crossing without a quadratic scan."""
    cross_r = rng.randint(1, h - 2)
    cross_c = rng.randint(1, w - 2)
    left = rng.randint(1, min(3, cross_c))
    right = rng.randint(1, min(3, w - 1 - cross_c))
    up = rng.randint(1, min(3, cross_r))
    down = rng.randint(1, min(3, h - 1 - cross_r))
    h_cells = tuple((cross_r, c) for c in range(cross_c - left, cross_c + right + 1))
    v_cells = tuple((r, cross_c) for r in range(cross_r - up, cross_r + down + 1))
    horizontal = Segment(
        "horizontal", h_cells[0], h_cells[-1], h_cells, frozenset(h_cells[1:-1])
    )
    vertical = Segment(
        "vertical", v_cells[0], v_cells[-1], v_cells, frozenset(v_cells[1:-1])
    )
    return horizontal, vertical


def _orientation_plan(profile: str, spans: int, rng) -> list[str]:
    if profile == "horizontal":
        return ["horizontal"] * spans
    if profile == "vertical":
        return ["vertical"] * spans
    horizontal = max(1, spans // 2)
    vertical = spans - horizontal
    if vertical == 0:
        vertical, horizontal = 1, spans - 1
    plan = ["horizontal"] * horizontal + ["vertical"] * vertical
    rng.shuffle(plan)
    return plan


def _place_segments(h, w, spans, orientation_profile, crossing_profile, rng):
    candidates = {
        orientation: _candidate_segments(h, w, orientation)
        for orientation in ("horizontal", "vertical")
    }
    plan = _orientation_plan(orientation_profile, spans, rng)
    require_crossing = crossing_profile == "crossing"

    for _attempt in range(400):
        chosen: list[Segment] = []
        remaining = list(plan)
        if require_crossing:
            first, second = _initial_crossing_pair(h, w, rng)
            chosen.extend((first, second))
            remaining.remove("horizontal")
            remaining.remove("vertical")
            rng.shuffle(remaining)
        success = True
        for orientation in remaining:
            options = list(candidates[orientation])
            rng.shuffle(options)
            selected = next(
                (
                    candidate
                    for candidate in options
                    if _compatible(candidate, chosen, allow_crossings=require_crossing)
                ),
                None,
            )
            if selected is None:
                success = False
                break
            chosen.append(selected)
        if not success:
            continue
        crossings = sum(
            bool(set(first.interior) & set(second.interior))
            for index, first in enumerate(chosen)
            for second in chosen[index + 1 :]
            if first.orientation != second.orientation
        )
        if require_crossing and crossings == 0:
            continue
        if not require_crossing and crossings:
            continue
        rng.shuffle(chosen)
        return chosen
    raise AssertionError(
        f"could not place {spans} {orientation_profile}/{crossing_profile} spans "
        f"on {h}x{w}"
    )


def _draw_from_degenerate(name: str):
    g = full_grid(8, 10, 0)
    if name == "no_pairs":
        return g
    if name == "adjacent_pair":
        g[3][2] = 4
        g[3][3] = 4
        g[6][1] = 7
        g[6][4] = 7
        return g
    if name == "no_shared_axis":
        g[2][3] = 4
        g[5][7] = 4
        g[6][1] = 7
        g[6][4] = 7
        return g
    if name == "triplicate_color":
        g[2][2] = g[2][5] = g[5][2] = 4
        g[6][1] = 7
        g[6][4] = 7
        return g
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    effective = _effective_overrides(overrides)
    texture = effective.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    (h_lo, h_hi), (w_lo, w_hi), (s_lo, s_hi) = _default_ranges(difficulty)
    slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
    scheduled_crossing_demo = slot == 2 and all(
        effective.get(name) is None
        for name in ("texture", "orientation_profile", "crossing_profile")
    )
    if scheduled_crossing_demo:
        # Anchor the decisive crossing demonstration to the public scale and
        # three-span structure while the other lesson slots retain broad
        # difficulty variation. Explicit overrides always keep precedence.
        if effective.get("grid_h") is None:
            h_lo, h_hi = max(h_lo, 8), min(h_hi, 10)
        if effective.get("grid_w") is None:
            w_lo, w_hi = max(w_lo, 9), min(w_hi, 11)
        if effective.get("spans") is None:
            s_lo = s_hi = 3
    h = _draw_int_axis(ctx, effective, "grid_h", h_lo, h_hi, 8, 14)
    w = _draw_int_axis(ctx, effective, "grid_w", w_lo, w_hi, 9, 16)
    spans = _draw_int_axis(ctx, effective, "spans", s_lo, s_hi, 2, 7)
    orientation_profile, crossing_profile = _scheduled_profiles(
        ctx, sample_index, effective
    )

    rng = ctx.draw_rng("layout")
    segments = _place_segments(
        h, w, spans, orientation_profile, crossing_profile, rng
    )
    colors = list(ctx.draw_distinct_colors("colors", n=spans, exclude=(0,)))
    rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for color, segment in zip(colors, segments):
        for r, c in segment.endpoints:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid span lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "spans": spans,
        "orientation_profile": orientation_profile,
        "crossing_profile": crossing_profile,
    }
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid
