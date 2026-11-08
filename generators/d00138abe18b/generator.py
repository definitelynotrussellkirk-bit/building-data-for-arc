"""Semantic curriculum for reading the first non-zero value of each row.

Selected rule authority: scan rows from top to bottom.  Empty rows disappear;
for every non-empty row, emit the FIRST non-zero value (left-to-right) as one
cell of a vertical output column.  The selected Racket rule also defines the
all-empty edge case as ``[[0]]``, but that edge case is deliberately outside
the task-like training grammar here.

The public examples happen to make every non-empty row monochrome.  That makes
"row color", "last non-zero", and "modal row color" indistinguishable from the
selected first-non-zero rule on canonical alone.  The mixed-row curriculum
profile is therefore load-bearing: its first non-zero differs from both the
row mode and the last non-zero.  A second witness profile repeats a head color
in two different rows, ruling out deduplication of the output column.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d00138abe18b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7ed0d39bdf69"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Scan rows top-to-bottom. Skip empty rows; from each non-empty row take "
    "the first non-zero cell from the left and append that color as one row "
    "of a one-column output. Mixed-row witnesses distinguish first non-zero "
    "from modal/last-row-color shortcuts, and repeated heads prove duplicate "
    "output values are preserved."
)

INVARIANTS = [
    "background is 0",
    "task-like inputs are 6..10 rows by 7..12 columns",
    "there are 3..8 non-empty rows and at least one empty row",
    "each non-empty row contains one contiguous run of 2..4 non-zero cells",
    "a row run may use one or two colors; the selected answer is its leftmost non-zero color",
    "output order is the original top-to-bottom row order, with duplicates preserved",
]

SCENE_PROFILES = (
    "canonical_uniform",
    "mixed_first_witness",
    "duplicate_heads_witness",
)
SCHEDULE_PROFILES = SCENE_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "three-slot cyclic semantic curriculum",
        "valid": "canonical_uniform|mixed_first_witness|duplicate_heads_witness",
        "doc": (
            "Exact observable profile: uniform distinct row heads; one mixed "
            "row whose first value differs from mode/last; or uniform rows "
            "with exactly one repeated head color."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Every band retains canonical-size support while harder bands also widen the
# canvas.  The profile schedule is independent, so any three consecutive
# examples still cover every semantic witness.
_SIZE_SCHEDULES = {
    "easy": ((6, 7), (7, 9), (8, 8), (7, 9)),
    "medium": ((7, 9), (8, 8), (9, 10), (8, 8)),
    "hard": ((8, 8), (9, 11), (10, 12), (7, 9)),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and type(profile) is not str:
        raise ValueError("scene_profile must be a string")


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return None, ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be non-empty and rectangular"]
    out: list[list[int]] = []
    for row in grid:
        cooked: list[int] = []
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return None, ["grid cells must be literal ARC integers 0..9"]
            cooked.append(value)
        out.append(cooked)
    return out, []


def _row_run(row: list[int]) -> tuple[int, int, list[int]] | None:
    occupied = [index for index, value in enumerate(row) if value != 0]
    if not occupied:
        return None
    left, right = occupied[0], occupied[-1]
    if occupied != list(range(left, right + 1)):
        return None
    return left, right, row[left : right + 1]


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    cooked, errors = _coerce_grid(grid)
    if errors:
        return None, errors
    assert cooked is not None
    height, width = len(cooked), len(cooked[0])
    if not 6 <= height <= 10 or not 7 <= width <= 12:
        errors.append(f"grid dimensions must be 6..10 by 7..12; found {height}x{width}")

    rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(cooked):
        if not any(row):
            continue
        run = _row_run(row)
        if run is None:
            errors.append(f"row {row_index} non-zero cells must form one contiguous run")
            continue
        left, right, values = run
        if not 2 <= len(values) <= 4:
            errors.append(
                f"row {row_index} run length must be 2..4; found {len(values)}"
            )
        colors = set(values)
        if len(colors) > 2:
            errors.append(f"row {row_index} run may use at most two non-zero colors")
        rows.append(
            {
                "row": row_index,
                "left": left,
                "right": right,
                "values": tuple(values),
                "head": values[0],
                "mixed": len(colors) > 1,
            }
        )

    if not 3 <= len(rows) <= 8:
        errors.append(f"expected 3..8 non-empty rows; found {len(rows)}")
    if len(rows) == height:
        errors.append("task-like grammar requires at least one empty row")
    if errors:
        return None, errors
    return {
        "grid": cooked,
        "height": height,
        "width": width,
        "rows": rows,
        "heads": tuple(item["head"] for item in rows),
        "mixed_rows": tuple(item for item in rows if item["mixed"]),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize task morphology, while leaving curriculum witnesses to hooks."""
    del difficulty, meta
    _analysis_result, errors = _analyze(grid)
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected Racket rule for semantic rival audits."""
    heads = []
    for row in grid:
        first = next((value for value in row if value != 0), None)
        if first is not None:
            heads.append([first])
    return heads or [[0]]


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact declared scene profile from the returned grid."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe profile on invalid grid: " + "; ".join(errors))
    assert analysis is not None
    if analysis["mixed_rows"]:
        profile = "mixed_first_witness"
    elif len(set(analysis["heads"])) < len(analysis["heads"]):
        profile = "duplicate_heads_witness"
    else:
        profile = "canonical_uniform"
    return {"scene_profile": profile}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every three consecutive samples cover all semantic profiles."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _head_count(height: int, width: int, profile: str, sample_index: int, difficulty) -> int:
    # Match a canonical (height, width, palette-size) profile regularly.  For
    # uniform scenes palette-size is background + distinct row-head colors.
    canonical = {
        (6, 7): (4,),       # palette 5
        (7, 9): (4, 5),    # palette 5 or 6
        (8, 8): (3, 5),    # palette 4 or 6
    }
    if profile == "canonical_uniform" and (height, width) in canonical:
        options = canonical[(height, width)]
        return min(options[int(sample_index) % len(options)], height - 1)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    ranges = {"easy": (3, 4), "medium": (4, 5), "hard": (5, 6)}
    lo, hi = ranges[band]
    span = hi - lo + 1
    return min(lo + (int(sample_index) % span), height - 1)


def _unsort(values: list[int]) -> list[int]:
    if len(values) >= 2 and values == sorted(values):
        values = values[1:] + values[:1]
    return values


def _build_profile(ctx, profile: str, sample_index: int, difficulty) -> list[list[int]]:
    band = difficulty if difficulty in _SIZE_SCHEDULES else "medium"
    sizes = _SIZE_SCHEDULES[band]
    height, width = sizes[int(sample_index) % len(sizes)]
    count = _head_count(height, width, profile, sample_index, difficulty)

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    nonempty_rows = sorted(layout_rng.sample(range(height), count))
    colors = list(range(1, 10))
    palette_rng.shuffle(colors)

    if profile == "duplicate_heads_witness":
        distinct = colors[: max(2, count - 1)]
        heads = distinct[:]
        while len(heads) < count:
            heads.append(distinct[0])
        palette_rng.shuffle(heads)
        # Exactly one value should repeat; put its two occurrences apart when
        # possible so the witness is not a trivial adjacent-run artifact.
        repeated = distinct[0]
        positions = [i for i, value in enumerate(heads) if value == repeated]
        if len(positions) >= 2 and positions[1] == positions[0] + 1 and count >= 3:
            swap = next((i for i, value in enumerate(heads) if value != repeated), None)
            if swap is not None and swap not in positions:
                heads[positions[1]], heads[swap] = heads[swap], heads[positions[1]]
        heads = _unsort(heads)
        decoy = None
    else:
        heads = _unsort(colors[:count])
        decoy = colors[count] if profile == "mixed_first_witness" else None

    grid = full_grid(height, width, 0)
    mixed_row_index = count // 2 if profile == "mixed_first_witness" else None
    for index, row_index in enumerate(nonempty_rows):
        run_len = layout_rng.randint(2, min(4, width))
        if index == mixed_row_index:
            run_len = max(3, run_len)
        start = layout_rng.randint(0, width - run_len)
        head = heads[index]
        values = [head] * run_len
        if index == mixed_row_index:
            assert decoy is not None
            # The selected answer is head, while both last-value and row-mode
            # rivals answer decoy.  This is the decisive canonical ambiguity
            # counterexample the public monochrome rows cannot supply.
            values = [head] + [decoy] * (run_len - 1)
        for offset, value in enumerate(values):
            grid[row_index][start + offset] = value

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise ValueError(f"constructed profile {profile!r} but observed {observed!r}")
    return [row[:] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task-like input; the selected Racket rule owns output."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    return _build_profile(ctx, profile, int(sample_index), difficulty)


def _rival_last_nonzero(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        values = [value for value in row if value != 0]
        if values:
            out.append([values[-1]])
    return out or [[0]]


def _rival_modal_row_color(grid: list[list[int]]) -> list[list[int]]:
    out = []
    for row in grid:
        values = [value for value in row if value != 0]
        if not values:
            continue
        counts = Counter(values)
        best = max(counts.values())
        mode = next(value for value in values if counts[value] == best)
        out.append([mode])
    return out or [[0]]


def _rival_deduplicate_heads(grid: list[list[int]]) -> list[list[int]]:
    seen: set[int] = set()
    out = []
    for value, in rule_mirror(grid):
        if value not in seen:
            seen.add(value)
            out.append([value])
    return out or [[0]]


def _rival_sort_heads(grid: list[list[int]]) -> list[list[int]]:
    return [[value] for value in sorted(value for value, in rule_mirror(grid))]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "last_nonzero": _rival_last_nonzero,
    "modal_row_color": _rival_modal_row_color,
    "deduplicate_heads": _rival_deduplicate_heads,
    "sort_heads": _rival_sort_heads,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These three wrong rules fit all five canonical pairs because every published
# non-empty row is monochrome and every output color is unique within a pair.
CANONICAL_SHORTCUTS = {
    "last_nonzero": _rival_last_nonzero,
    "modal_row_color": _rival_modal_row_color,
    "deduplicate_heads": _rival_deduplicate_heads,
}


def _profile_is(name: str):
    def predicate(grid) -> bool:
        try:
            return not self_check(grid) and observe_overrides(grid)["scene_profile"] == name
        except Exception:
            return False
    return predicate


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    def predicate(grid) -> bool:
        return not self_check(grid) and rule_mirror(grid) != rival(grid)
    return predicate


SEMANTIC_WITNESSES = {
    "first_nonzero_not_last": lambda grid: _profile_is("mixed_first_witness")(grid)
    and _differs_from(_rival_last_nonzero)(grid),
    "first_nonzero_not_mode": lambda grid: _profile_is("mixed_first_witness")(grid)
    and _differs_from(_rival_modal_row_color)(grid),
    "duplicates_are_preserved": lambda grid: _profile_is("duplicate_heads_witness")(grid)
    and _differs_from(_rival_deduplicate_heads)(grid),
    "row_order_is_preserved": _differs_from(_rival_sort_heads),
}
WITNESS_RIVALS = {
    "first_nonzero_not_last": ["last_nonzero"],
    "first_nonzero_not_mode": ["modal_row_color"],
    "duplicates_are_preserved": ["deduplicate_heads"],
    "row_order_is_preserved": ["sort_heads"],
}


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic predicate used for count-backed strict censuses."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = observe_overrides(grid)["scene_profile"]
    answer = rule_mirror(grid)
    if profile == "mixed_first_witness":
        if _rival_last_nonzero(grid) == answer:
            errors.append("mixed witness does not distinguish first from last non-zero")
        if _rival_modal_row_color(grid) == answer:
            errors.append("mixed witness does not distinguish first from modal row color")
    elif profile == "duplicate_heads_witness":
        if _rival_deduplicate_heads(grid) == answer:
            errors.append("duplicate-head witness does not require duplicate preservation")
    if _rival_sort_heads(grid) == answer:
        errors.append("row-head order is accidentally sorted, hiding top-to-bottom order")
    return errors


def lesson_identifiable(demos, query) -> list[str]:
    """Require a three-example lesson that kills every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match first-nonzero row scan")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append("query input is malformed: " + query_errors[0])
        elif query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match first-nonzero row scan")
    if reasons:
        return reasons

    profiles = {
        observe_overrides(pair["input"])["scene_profile"] for pair in valid_demos
    }
    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        reasons.append("demonstrations omit semantic profile(s): " + ", ".join(missing))

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
