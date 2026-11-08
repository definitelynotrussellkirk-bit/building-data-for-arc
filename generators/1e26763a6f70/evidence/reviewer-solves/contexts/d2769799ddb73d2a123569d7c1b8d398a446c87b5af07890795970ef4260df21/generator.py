"""Generator for ``1e26763a6f70`` — mark each lawful pair's midpoint.

The authoritative rule treats every non-zero color independently.  When a color
appears exactly twice, its cells share a row or column, their separation is even,
and the integer midpoint is zero in the original input, that midpoint is painted
with the endpoint color.  Everything else is preserved.

Ordinary draws alternate ``canonical-anchor, rich`` profiles.  Every rich
scene contains four distinct pairs spanning both orientations and both short
and long separations.  Thus any four consecutive examples contain exactly two
scenes that refute horizontal-only, vertical-only, fixed-span, first-pair-only,
identity, and fill-the-whole-gap shortcuts, while the median object count stays
inside the canonical distribution gate.  Anchor scenes keep all three canonical
shape/palette profiles in every difficulty band.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1e26763a6f70"
TASK_ID = GENERATOR_ID
VERSION = "2.0.2"
RULE_HASH = "dffe1ada0168"

SUMMARY = (
    "For each non-zero color appearing exactly twice in one row or column at an "
    "even separation, fill its empty integer midpoint with that same color. "
    "Rich draws mix horizontal/vertical and short/long pairs; canonical anchors "
    "retain the source task's three shape and palette profiles."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0 and every foreground color appears exactly twice",
    "each same-color pair is horizontal or vertical with an even span of at least 2",
    "every pair midpoint is initially 0 and pair midpoints are distinct",
    "ordinary rich scenes contain three colors, both orientations, and spans 2 and >=4",
]

COUNTER_HYPOTHESES = [
    "leave the input unchanged",
    "mark only horizontal pairs",
    "mark only vertical pairs",
    "mark only pairs at the canonical four-cell separation",
    "mark only the first color pair",
    "fill every cell between endpoints rather than only the midpoint",
    "paint every midpoint with a fixed color",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled profile",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled profile",
        "valid": "5..12",
    },
    "pairs": {
        "type": "int",
        "default": "1 for anchors, 3 for rich profiles",
        "valid": "1..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_BOUNDS = {"grid_h": (5, 12), "grid_w": (5, 12), "pairs": (1, 4)}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

# Alternating anchor/rich profiles give every four-example window exactly two
# rich counterexamples while keeping the default stream's median pair/object
# count near the canonical one-pair tasks.  The cycle includes every canonical
# shape and both canonical orientations.
_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "name": "anchor_5x7_horizontal",
        "kind": "anchor",
        "grid_h": 5,
        "grid_w": 7,
        "pairs": 1,
        "specs": (("horizontal", 4),),
    },
    {
        "name": "rich_7x7_balanced",
        "kind": "rich",
        "grid_h": 7,
        "grid_w": 7,
        "pairs": 3,
        "specs": (("horizontal", 2), ("vertical", 2), ("horizontal", 4)),
    },
    {
        "name": "anchor_7x6_vertical",
        "kind": "anchor",
        "grid_h": 7,
        "grid_w": 6,
        "pairs": 1,
        "specs": (("vertical", 4),),
    },
    {
        "name": "rich_8x9_horizontal_long",
        "kind": "rich",
        "grid_h": 8,
        "grid_w": 9,
        "pairs": 3,
        "specs": (("horizontal", 2), ("vertical", 4), ("horizontal", 6)),
    },
    {
        "name": "anchor_7x7_horizontal",
        "kind": "anchor",
        "grid_h": 7,
        "grid_w": 7,
        "pairs": 1,
        "specs": (("horizontal", 4),),
    },
    {
        "name": "rich_9x8_vertical_long",
        "kind": "rich",
        "grid_h": 9,
        "grid_w": 8,
        "pairs": 3,
        "specs": (("vertical", 2), ("horizontal", 4), ("vertical", 6)),
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_PROFILE_BY_NAME = {profile["name"]: profile for profile in _PROFILES}


@dataclass(frozen=True)
class PairRecord:
    color: int
    a: tuple[int, int]
    b: tuple[int, int]
    midpoint: tuple[int, int]
    orientation: str
    span: int


@dataclass(frozen=True)
class _Candidate:
    a: tuple[int, int]
    b: tuple[int, int]
    midpoint: tuple[int, int]
    orientation: str
    span: int

    @property
    def critical(self) -> frozenset[tuple[int, int]]:
        return frozenset((self.a, self.b, self.midpoint))


def _validate_sample_index(sample_index: Any) -> int:
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    return sample_index


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _BOUNDS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching profile for a draw."""
    del seed
    index = _validate_sample_index(sample_index)
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    # Even offsets preserve the anchor/rich phase while rotating which canonical
    # shape and rich geometry each difficulty band sees first.
    offset = {None: 0, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    return SCHEDULE_PROFILES[(index + offset) % len(_PROFILES)]


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    return _PROFILE_BY_NAME[schedule_profile(0, sample_index, difficulty)]


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if not isinstance(row, list) or not row:
            raise ValueError("grid rows must be non-empty lists")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("grid must be rectangular")
        clean: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid colors must be integers in 0..9")
            clean.append(value)
        rows.append(clean)
    return rows


def _records_from_grid(grid: Any, *, lawful_only: bool = False) -> list[PairRecord]:
    values = _coerce_grid(grid)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(values):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))

    records: list[PairRecord] = []
    for color, cells in by_color.items():
        if len(cells) != 2:
            continue
        a, b = cells
        r1, c1 = a
        r2, c2 = b
        if r1 == r2:
            orientation = "horizontal"
            span = abs(c2 - c1)
        elif c1 == c2:
            orientation = "vertical"
            span = abs(r2 - r1)
        else:
            if lawful_only:
                continue
            orientation = "diagonal"
            span = -1
        if orientation == "diagonal":
            midpoint = ((r1 + r2) // 2, (c1 + c2) // 2)
            records.append(PairRecord(color, a, b, midpoint, orientation, span))
            continue
        midpoint = ((r1 + r2) // 2, (c1 + c2) // 2)
        if lawful_only and (
            span < 2
            or span % 2 != 0
            or values[midpoint[0]][midpoint[1]] != 0
        ):
            continue
        records.append(PairRecord(color, a, b, midpoint, orientation, span))
    return records


def _analysis(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(values):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))

    if not by_color:
        errors.append("expected at least one non-zero color pair")

    records: list[PairRecord] = []
    midpoint_owner: dict[tuple[int, int], int] = {}
    for color, cells in by_color.items():
        if len(cells) != 2:
            errors.append(f"color {color} must appear exactly twice; found {len(cells)}")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            orientation = "horizontal"
            span = abs(c2 - c1)
        elif c1 == c2:
            orientation = "vertical"
            span = abs(r2 - r1)
        else:
            errors.append(f"color {color} endpoints must share one row or one column")
            continue
        if span < 2 or span % 2:
            errors.append(f"color {color} span must be even and at least 2; found {span}")
            continue
        midpoint = ((r1 + r2) // 2, (c1 + c2) // 2)
        if values[midpoint[0]][midpoint[1]] != 0:
            errors.append(f"color {color} midpoint {midpoint} must be 0 in the input")
            continue
        previous = midpoint_owner.get(midpoint)
        if previous is not None:
            errors.append(
                f"colors {previous} and {color} share midpoint {midpoint}; output order would be ambiguous"
            )
            continue
        midpoint_owner[midpoint] = color
        records.append(
            PairRecord(color, (r1, c1), (r2, c2), midpoint, orientation, span)
        )

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "by_color": by_color,
        "records": records,
        "orientations": {record.orientation for record in records},
        "spans": {record.span for record in records},
    }


def _candidate_positions(h: int, w: int, orientation: str, span: int) -> list[_Candidate]:
    result: list[_Candidate] = []
    if orientation == "horizontal":
        if span >= w:
            return result
        for r in range(h):
            for c in range(w - span):
                result.append(
                    _Candidate(
                        (r, c),
                        (r, c + span),
                        (r, c + span // 2),
                        orientation,
                        span,
                    )
                )
    elif orientation == "vertical":
        if span >= h:
            return result
        for r in range(h - span):
            for c in range(w):
                result.append(
                    _Candidate(
                        (r, c),
                        (r + span, c),
                        (r + span // 2, c),
                        orientation,
                        span,
                    )
                )
    else:
        raise ValueError(f"unknown orientation {orientation!r}")
    return result


def _override_specs(h: int, w: int, pairs: int, rng) -> tuple[tuple[str, int], ...]:
    # All declared shapes are at least 5x5, so these four semantic motifs are
    # realizable.  Rotate the order to keep overridden scenes from becoming a
    # fixed-position template without changing the exact requested controls.
    base = [
        ("horizontal", 2),
        ("vertical", 2),
        ("horizontal", min(4, (w - 1) // 2 * 2)),
        ("vertical", min(4, (h - 1) // 2 * 2)),
    ]
    if pairs == 1:
        orientation = "horizontal" if rng.randrange(2) == 0 else "vertical"
        max_span = (w - 1) // 2 * 2 if orientation == "horizontal" else (h - 1) // 2 * 2
        return ((orientation, min(4, max_span)),)
    shift = rng.randrange(len(base))
    rotated = base[shift:] + base[:shift]
    return tuple(rotated[:pairs])


def _place_specs(
    h: int,
    w: int,
    specs: tuple[tuple[str, int], ...],
    rng,
) -> list[_Candidate]:
    candidate_lists: list[list[_Candidate]] = []
    for orientation, span in specs:
        candidates = _candidate_positions(h, w, orientation, span)
        rng.shuffle(candidates)
        if not candidates:
            raise ValueError(
                f"cannot place {orientation} span {span} on a {h}x{w} grid"
            )
        candidate_lists.append(candidates)

    chosen: list[_Candidate] = []

    def search(index: int, used: frozenset[tuple[int, int]]) -> bool:
        if index == len(candidate_lists):
            return True
        for candidate in candidate_lists[index]:
            if candidate.critical & used:
                continue
            chosen.append(candidate)
            if search(index + 1, used | candidate.critical):
                return True
            chosen.pop()
        return False

    if not search(0, frozenset()):
        raise ValueError(f"could not place requested pair specification on {h}x{w}")
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    index = _validate_sample_index(sample_index)
    _validate_call(difficulty, overrides)
    profile = _profile_for(index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", profile["grid_h"])
    w = _draw_exact_int(ctx, overrides, "grid_w", profile["grid_w"])
    pair_count = _draw_exact_int(ctx, overrides, "pairs", profile["pairs"])
    colors = ctx.draw_distinct_colors("colors", n=pair_count, exclude={0})
    rng = ctx.draw_rng("layout")

    if overrides:
        specs = _override_specs(h, w, pair_count, rng)
    else:
        specs = tuple(profile["specs"])
    if len(specs) != pair_count:
        raise AssertionError(
            f"profile/spec mismatch: pairs={pair_count}, specs={len(specs)}"
        )

    selected = _place_specs(h, w, specs, rng)
    grid = full_grid(h, w, 0)
    for color, candidate in zip(colors, selected):
        for r, c in (candidate.a, candidate.b):
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {"grid_h": h, "grid_w": w, "pairs": pair_count}
    if observed != requested:
        raise AssertionError(f"exact-axis mismatch: requested={requested}, observed={observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    records: list[PairRecord] = analysis["records"]
    if not _BOUNDS["grid_h"][0] <= h <= _BOUNDS["grid_h"][1]:
        errors.append(f"grid height {h} must be in 5..12")
    if not _BOUNDS["grid_w"][0] <= w <= _BOUNDS["grid_w"][1]:
        errors.append(f"grid width {w} must be in 5..12")
    if not _BOUNDS["pairs"][0] <= len(records) <= _BOUNDS["pairs"][1]:
        errors.append(f"pair count {len(records)} must be in 1..4")

    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(analysis["grid"]) if not errors else {}
        for axis, requested in meta["overrides"].items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"meta {axis} requested {requested!r}, observed {observed[axis]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "pairs": len(analysis["records"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Accept the source task's lawful input manifold, including all canonicals."""
    return self_check(grid)


def _apply_records(grid: Any, predicate: Callable[[PairRecord], bool]) -> list[list[int]]:
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    for record in _records_from_grid(values, lawful_only=True):
        if predicate(record):
            r, c = record.midpoint
            out[r][c] = record.color
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror used only for tests/rivals; Racket remains authority."""
    return _apply_records(grid, lambda record: True)


def _rival_identity(grid):
    return [row[:] for row in _coerce_grid(grid)]


def _rival_horizontal_only(grid):
    return _apply_records(grid, lambda record: record.orientation == "horizontal")


def _rival_vertical_only(grid):
    return _apply_records(grid, lambda record: record.orientation == "vertical")


def _rival_span_two_only(grid):
    return _apply_records(grid, lambda record: record.span == 2)


def _rival_span_four_only(grid):
    return _apply_records(grid, lambda record: record.span == 4)


def _rival_first_pair_only(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    records = _records_from_grid(values, lawful_only=True)
    if records:
        record = records[0]
        r, c = record.midpoint
        out[r][c] = record.color
    return out


def _rival_fill_all_between(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    for record in _records_from_grid(values, lawful_only=True):
        r1, c1 = record.a
        r2, c2 = record.b
        if record.orientation == "horizontal":
            lo, hi = sorted((c1, c2))
            for c in range(lo + 1, hi):
                out[r1][c] = record.color
        else:
            lo, hi = sorted((r1, r2))
            for r in range(lo + 1, hi):
                out[r][c1] = record.color
    return out


def _rival_fixed_color_nine(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    for record in _records_from_grid(values, lawful_only=True):
        r, c = record.midpoint
        out[r][c] = 9
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "span_two_only": _rival_span_two_only,
    "span_four_only": _rival_span_four_only,
    "first_pair_only": _rival_first_pair_only,
    "fill_all_between": _rival_fill_all_between,
    "fixed_color_nine": _rival_fixed_color_nine,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every labeled canonical pair contains exactly one span-four pair, so these two
# shortcuts fit the full canonical train+test inventory.  Rich generated scenes
# provide source-bound counterexamples to both.
CANONICAL_SHORTCUTS = {
    "first_pair_only": _rival_first_pair_only,
    "span_four_only": _rival_span_four_only,
}


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return None if analysis.get("errors") else analysis


SEMANTIC_WITNESSES = {
    "task_manifold": lambda grid: strict_canonical_like(grid) == [],
    "horizontal_pair": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and "horizontal" in analysis["orientations"]
    ),
    "vertical_pair": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and "vertical" in analysis["orientations"]
    ),
    "short_span": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None and 2 in analysis["spans"]
    ),
    "long_span": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and any(span >= 4 for span in analysis["spans"])
    ),
    "multiple_pairs": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and len(analysis["records"]) >= 2
    ),
    "mixed_orientation": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["orientations"] == {"horizontal", "vertical"}
    ),
    "mixed_span": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and 2 in analysis["spans"]
        and any(span >= 4 for span in analysis["spans"])
    ),
}

BRANCH_WITNESSES = (
    "horizontal_pair",
    "vertical_pair",
    "short_span",
    "long_span",
)

WITNESS_RIVALS = {
    "task_manifold": ["identity"],
    "horizontal_pair": ["vertical_only"],
    "vertical_pair": ["horizontal_only"],
    "short_span": ["span_four_only"],
    "long_span": ["span_two_only", "fill_all_between"],
    "multiple_pairs": ["first_pair_only"],
    "mixed_orientation": ["horizontal_only", "vertical_only"],
    "mixed_span": ["span_two_only", "span_four_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check labels and declared rivals for one materialized lesson."""
    reasons: list[str] = []
    pairs = [*demos, query]
    normalized: list[dict[str, list[list[int]]]] = []
    for index, item in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"{label} is not an input/output pair")
            continue
        try:
            inp = _coerce_grid(item["input"])
            out = _coerce_grid(item["output"])
        except ValueError as exc:
            reasons.append(f"{label} is malformed: {exc}")
            continue
        grammar_errors = self_check(inp)
        if grammar_errors:
            reasons.append(f"{label} input violates task grammar: {grammar_errors[0]}")
            continue
        expected = rule_mirror(inp)
        if out != expected:
            reasons.append(f"{label} output disagrees with the midpoint rule")
            continue
        normalized.append({"input": inp, "output": out})
    if reasons:
        return reasons
    if len(normalized) != len(pairs):
        return ["lesson normalization failed"]

    normalized_demos = normalized[:-1]
    normalized_query = normalized[-1]
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(item["input"]) == item["output"]
            for item in normalized_demos
        ):
            prediction = competitor(normalized_query["input"])
            if prediction != normalized_query["output"]:
                reasons.append(
                    f"competing rule {name!r} fits every demo but answers the query differently"
                )
            else:
                reasons.append(f"competing rule {name!r} survives every demo and query")
    return reasons
