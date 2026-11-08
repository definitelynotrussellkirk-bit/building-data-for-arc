"""Constructive curriculum for periodic recoloring by row-transition groups.

The selected Racket authority is unchanged.  Inputs are built from maximal runs
of identical rows.  The running run index starts at zero; every run whose index
is divisible by three has all nonzero cells recolored to 2.

The five profile IDs are the five canonical (height, width, group-count)
profiles.  Row contents and run-height allocations remain independently random,
so this anchors morphology without replaying canonical grids.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "be5d9fa6fec1"
TASK_ID = GENERATOR_ID
RULE_HASH = "0ff6975f3e81"
VERSION = "3.0.0"
SUMMARY = (
    "A narrow grid is partitioned into 8..16 maximal groups of 1..3 identical "
    "rows. Groups alternate between nonempty 0/1 rows and nonempty 0/8 rows. "
    "Scan groups from zero: in groups 0,3,6,... recolor every nonzero cell to "
    "2; preserve all cells in the other groups."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "shape and row-group count match one of the five canonical profiles",
    "each maximal row group has height 1..3 and adjacent groups alternate 0/1 versus 0/8",
    "every row has foreground and no row mixes colors 1 and 8",
    "generated group 0 has height at least 2, separating group counting from row-index shortcuts",
]

PROFILE_SPECS = {
    0: (20, 4, 14),
    1: (19, 5, 12),
    2: (14, 5, 11),
    3: (15, 3, 8),
    4: (22, 4, 16),
}
_SHAPE_TO_PROFILE = {(height, width): profile for profile, (height, width, _) in PROFILE_SPECS.items()}
KINDS = ("mix", "eight")

AXES = {
    "profile_id": {
        "type": "int",
        "default": "difficulty-weighted choice 0..4",
        "valid": "0..4",
    },
    "start_kind": {
        "type": "str",
        "default": "uniform mix|eight",
        "valid": "mix|eight",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

_PROFILE_CHOICES = {
    "easy": (3, 3, 3, 2, 2, 1, 0, 4),
    "medium": (2, 1, 0, 3, 4),
    "hard": (4, 4, 4, 0, 0, 1, 2, 3),
    None: (0, 1, 2, 3, 4),
}


def _validate_override_types(overrides) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "profile_id" in overrides:
        value = overrides["profile_id"]
        if type(value) is not int:
            raise TypeError("profile_id must be an integer (not bool, float, string, or None)")
        if value not in PROFILE_SPECS:
            raise ValueError(f"profile_id must be one of {sorted(PROFILE_SPECS)}")
    if "start_kind" in overrides:
        value = overrides["start_kind"]
        if type(value) is not str:
            raise TypeError("start_kind must be a string")
        if value not in KINDS:
            raise ValueError(f"start_kind must be one of {KINDS}")


def _run_heights(total_height: int, group_count: int, rng) -> list[int]:
    """Allocate exactly total_height with 1..3 rows/group, constructively.

    Group zero receives a second row before the remaining capacity is sampled.
    This guarantees a direct witness against both row-index and first-row-only
    interpretations without post-hoc row mutation.
    """
    heights = [1] * group_count
    heights[0] = 2
    remaining = total_height - sum(heights)
    capacity_tokens = [
        (group, slot)
        for group, height in enumerate(heights)
        for slot in range(3 - height)
    ]
    if not 0 <= remaining <= len(capacity_tokens):
        raise ValueError("profile cannot be represented with run heights 1..3")
    for group, _slot in rng.sample(capacity_tokens, remaining):
        heights[group] += 1
    return heights


@lru_cache(maxsize=16)
def _row_candidates(kind: str, width: int) -> tuple[tuple[int, ...], ...]:
    if kind == "mix":
        # Both 0 and 1 are present. Canonical all-1 rows remain accepted by
        # self_check, but generated rows retain explicit background evidence.
        return tuple(
            tuple(1 if mask & (1 << column) else 0 for column in range(width))
            for mask in range(1, (1 << width) - 1)
        )
    if kind == "eight":
        rows = []
        for mask in range(1, 1 << width):
            row = tuple(8 if mask & (1 << column) else 0 for column in range(width))
            # Duplicate denser rows in the choice population while preserving
            # sparse canonical-like possibilities.
            rows.extend([row] * (1 + sum(value == 8 for value in row)))
        return tuple(rows)
    raise ValueError(f"unknown row kind {kind!r}")


def _choose_row(kind: str, width: int, previous_same_kind, rng) -> tuple[int, ...]:
    candidates = [row for row in _row_candidates(kind, width) if row != previous_same_kind]
    if not candidates:
        raise RuntimeError("row candidate domain unexpectedly exhausted")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _PROFILE_CHOICES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    choices = _PROFILE_CHOICES.get(difficulty, _PROFILE_CHOICES[None])
    profile_id = ctx.draw_choice("profile_id", choices)
    start_kind = ctx.draw_choice("start_kind", KINDS)
    height, width, group_count = PROFILE_SPECS[profile_id]
    rng = ctx.draw_rng("layout")
    heights = _run_heights(height, group_count, rng)

    rows: list[list[int]] = []
    previous_by_kind = {"mix": None, "eight": None}
    for group, run_height in enumerate(heights):
        kind = start_kind if group % 2 == 0 else ("eight" if start_kind == "mix" else "mix")
        row = _choose_row(kind, width, previous_by_kind[kind], rng)
        previous_by_kind[kind] = row
        rows.extend([list(row) for _ in range(run_height)])
    return rows


def _validate_rectangular(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("ragged grid")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("cells must be integer ARC colors 0..9")
    return len(grid), width


def _row_kind(row) -> str:
    values = set(row)
    if values <= {0, 1} and 1 in values:
        return "mix"
    if values <= {0, 8} and 8 in values:
        return "eight"
    if values == {0}:
        return "zero"
    if 1 in values and 8 in values:
        return "mixed_foregrounds"
    return "other"


def _groups(grid) -> list[dict]:
    _validate_rectangular(grid)
    groups: list[dict] = []
    start = 0
    for stop in range(1, len(grid) + 1):
        if stop == len(grid) or list(grid[stop]) != list(grid[stop - 1]):
            row = tuple(grid[start])
            groups.append({
                "start": start,
                "stop": stop,
                "height": stop - start,
                "row": row,
                "kind": _row_kind(row),
            })
            start = stop
    return groups


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        height, width = _validate_rectangular(grid)
        groups = _groups(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    profile_id = _SHAPE_TO_PROFILE.get((height, width))
    if profile_id is None:
        errors.append(f"shape {(height, width)} is outside the five canonical profiles")
    else:
        expected_groups = PROFILE_SPECS[profile_id][2]
        if len(groups) != expected_groups:
            errors.append(f"expected {expected_groups} maximal row groups, got {len(groups)}")

    palette = {value for row in grid for value in row}
    if palette != {0, 1, 8}:
        errors.append(f"input palette must be exactly [0, 1, 8], got {sorted(palette)}")

    for index, group in enumerate(groups):
        if not 1 <= group["height"] <= 3:
            errors.append(f"group {index} height {group['height']} outside 1..3")
        if group["kind"] not in KINDS:
            errors.append(f"group {index} row is neither a nonempty 0/1 nor 0/8 pattern")
        if index and group["kind"] == groups[index - 1]["kind"]:
            errors.append(f"groups {index - 1} and {index} do not alternate row kind")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The complete selected input grammar; generated support is exactly strict."""
    return self_check(grid)


def observe_overrides(grid) -> dict:
    issues = self_check(grid)
    if issues:
        raise ValueError("; ".join(issues))
    profile_id = _SHAPE_TO_PROFILE[(len(grid), len(grid[0]))]
    return {"profile_id": profile_id, "start_kind": _groups(grid)[0]["kind"]}


def _group_indices(grid) -> list[int]:
    _validate_rectangular(grid)
    indices: list[int] = []
    group = -1
    previous = None
    for index, row in enumerate(grid):
        current = tuple(row)
        if index == 0 or current != previous:
            group += 1
        indices.append(group)
        previous = current
    return indices


def _render(grid, selector, cell_selector=lambda value: value != 0):
    _validate_rectangular(grid)
    indices = _group_indices(grid)
    output = deepcopy([list(row) for row in grid])
    seen: set[int] = set()
    for row_index, row in enumerate(grid):
        group = indices[row_index]
        first = group not in seen
        seen.add(group)
        if selector(row_index, group, first):
            for column, value in enumerate(row):
                if cell_selector(value):
                    output[row_index][column] = 2
    return output


def rule_mirror(grid):
    """Independent executable mirror for contracts; Racket remains authority."""
    return _render(grid, lambda _row, group, _first: group % 3 == 0)


def _rival_row_index_mod3(grid):
    return _render(grid, lambda row, _group, _first: row % 3 == 0)


def _rival_one_based_groups(grid):
    return _render(grid, lambda _row, group, _first: (group + 1) % 3 == 0)


def _rival_first_row_only(grid):
    return _render(grid, lambda _row, group, first: group % 3 == 0 and first)


def _rival_color8_only(grid):
    return _render(
        grid,
        lambda _row, group, _first: group % 3 == 0,
        lambda value: value == 8,
    )


def _rival_color1_only(grid):
    return _render(
        grid,
        lambda _row, group, _first: group % 3 == 0,
        lambda value: value == 1,
    )


def _rival_all_nonzero(grid):
    return _render(grid, lambda _row, _group, _first: True)


SEMANTIC_RIVALS = {
    "row_index_mod3": _rival_row_index_mod3,
    "one_based_groups": _rival_one_based_groups,
    "first_row_only": _rival_first_row_only,
    "color8_only": _rival_color8_only,
    "color1_only": _rival_color1_only,
    "all_nonzero": _rival_all_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}


def _differs_from(name):
    def witness(grid):
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    return witness


SEMANTIC_WITNESSES = {
    "transition_count_not_row_index": _differs_from("row_index_mod3"),
    "zero_based_group_phase": _differs_from("one_based_groups"),
    "whole_target_group": _differs_from("first_row_only"),
    "target_mix_rows": _differs_from("color8_only"),
    "target_eight_rows": _differs_from("color1_only"),
    "periodic_not_all_nonzero": _differs_from("all_nonzero"),
}
WITNESS_RIVALS = {
    "transition_count_not_row_index": ["row_index_mod3"],
    "zero_based_group_phase": ["one_based_groups"],
    "whole_target_group": ["first_row_only"],
    "target_mix_rows": ["color8_only"],
    "target_eight_rows": ["color1_only"],
    "periodic_not_all_nonzero": ["all_nonzero"],
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query) -> list[str]:
    del query
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
                return ["demonstrations must contain input/output grids"]
            try:
                survived = rival(demo["input"]) == demo["output"]
            except (TypeError, ValueError) as exc:
                return [f"{name} evaluation failed: {exc}"]
            if not survived:
                break
        if survived:
            reasons.append(f"{name} fits every demonstration")
    return reasons
