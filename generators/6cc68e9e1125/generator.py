"""Semantic generator for ARC task 6cc68e9e1125.

Five square panels are separated by gray columns.  The first three panels are
an in-grid worked example ``A, B, merge(A, B)``.  The final two panels are the
query operands.  Empty cells pass through, equal nonzero values are preserved,
and unequal nonzero values merge to maroon 9.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6cc68e9e1125"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "da70d4d65006"
SUMMARY = (
    "Split the input at four full-height gray columns. Panels 0 and 1 "
    "demonstrate the cellwise merge and panel 2 is their exact result. "
    "Apply the same merge to query panels 3 and 4: zero passes the other "
    "value through, equal nonzero values remain unchanged, and unequal "
    "nonzero values become maroon 9."
)
EXAMPLES_NEEDED = 3

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "canonical linked morphology or a novel lawful merge lesson",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "four full-height color-5 separators divide five equal square panels",
    "panels 0 and 1 contain nonzero operand colors other than 5 and 9",
    "panel 2 is exactly the cellwise merge of panels 0 and 1",
    "panels 3 and 4 contain nonzero operand colors other than 5 and 9",
    "the worked example includes left-only, right-only, overlap, and empty cells",
    "the output is the cellwise merge of panels 3 and 4",
]


def _grid(*rows):
    return [[int(value) for value in row] for row in rows]


_PUBLIC_INPUTS = (
    _grid(
        "2005000520054005000",
        "0205030509050405060",
        "0005003500350045600",
    ),
    _grid(
        "070050700507005003350003",
        "007050008500785030050300",
        "000050000500005000053000",
        "000050000500005000050000",
    ),
    _grid(
        "220050200522005004450400",
        "020052000522005040054000",
        "000050000500005000050000",
        "000050000500005000050000",
    ),
)


def _panel_width(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return 0
    width = len(first)
    return (width - 4) // 5 if (width - 4) % 5 == 0 else 0


def _panel_left(index, panel_width):
    return index * (panel_width + 1)


def _split_panels(grid):
    panel_width = _panel_width(grid)
    return tuple(
        [
            [
                grid[row][_panel_left(panel, panel_width) + col]
                for col in range(panel_width)
            ]
            for row in range(len(grid))
        ]
        for panel in range(5)
    )


def _assemble(panels):
    height = len(panels[0])
    panel_width = len(panels[0][0])
    grid = full_grid(height, 5 * panel_width + 4, 0)
    for panel, values in enumerate(panels):
        left = _panel_left(panel, panel_width)
        for row in range(height):
            for col in range(panel_width):
                grid[row][left + col] = values[row][col]
    for panel in range(4):
        separator = _panel_left(panel, panel_width) + panel_width
        for row in range(height):
            grid[row][separator] = 5
    return grid


def _merge(left, right):
    if (
        not left
        or not right
        or len(left) != len(right)
        or len(left[0]) != len(right[0])
    ):
        raise ValueError("merge operands must have the same nonempty shape")
    return [
        [
            (
                right[row][col]
                if left[row][col] == 0
                else left[row][col]
                if right[row][col] == 0 or left[row][col] == right[row][col]
                else 9
            )
            for col in range(len(left[0]))
        ]
        for row in range(len(left))
    ]


def _rotate(panel):
    return [list(row) for row in zip(*panel[::-1])]


def _flip_lr(panel):
    return [row[::-1] for row in panel]


def _d4(panel):
    forms = []
    current = [row[:] for row in panel]
    for _ in range(4):
        forms.append([row[:] for row in current])
        forms.append(_flip_lr(current))
        current = _rotate(current)
    return tuple(forms)


def _canonical_pair_values(first, second):
    mapping = {}
    next_value = 1
    canonical = []
    for panel in (first, second):
        encoded = []
        for row in panel:
            encoded_row = []
            for value in row:
                if value == 0:
                    encoded_row.append(0)
                    continue
                if value not in mapping:
                    mapping[value] = next_value
                    next_value += 1
                encoded_row.append(mapping[value])
            encoded.append(tuple(encoded_row))
        canonical.append(tuple(encoded))
    return tuple(canonical)


def _pair_key(first, second):
    candidates = []
    first_forms = _d4(first)
    second_forms = _d4(second)
    for index in range(8):
        a = first_forms[index]
        b = second_forms[index]
        candidates.append(_canonical_pair_values(a, b))
        candidates.append(_canonical_pair_values(b, a))
    return min(candidates)


def _profile_key(panels):
    return (
        len(panels[0]),
        len(panels[0][0]),
        _pair_key(panels[0], panels[1]),
        _pair_key(panels[3], panels[4]),
    )


_PUBLIC_PROFILE_KEYS = tuple(
    _profile_key(_split_panels(grid)) for grid in _PUBLIC_INPUTS
)


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    panel_width = _panel_width(grid)
    if not 3 <= len(grid) <= 5:
        errors.append("panel height must be 3..5")
    if not 3 <= panel_width <= 5:
        errors.append("panel width must be 3..5")
    if len(grid) != panel_width:
        errors.append("all five panels must be square")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors


def _state_counts(left, right):
    counts = {
        "both_zero": 0,
        "left_only": 0,
        "right_only": 0,
        "overlap_equal": 0,
        "overlap_conflict": 0,
    }
    for row in range(len(left)):
        for col in range(len(left[0])):
            a = left[row][col]
            b = right[row][col]
            if a == 0 and b == 0:
                counts["both_zero"] += 1
            elif a != 0 and b == 0:
                counts["left_only"] += 1
            elif a == 0 and b != 0:
                counts["right_only"] += 1
            elif a == b:
                counts["overlap_equal"] += 1
            else:
                counts["overlap_conflict"] += 1
    return counts


def _relation_name(counts):
    equal = counts["overlap_equal"] > 0
    conflict = counts["overlap_conflict"] > 0
    if equal and conflict:
        return "mixed"
    if conflict:
        return "conflict"
    if equal:
        return "equal"
    return "disjoint"


def _analyze(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    height = len(grid)
    panel_width = _panel_width(grid)
    expected_separators = tuple(
        _panel_left(panel, panel_width) + panel_width
        for panel in range(4)
    )
    actual_separators = tuple(
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 5 for row in range(height))
    )
    if actual_separators != expected_separators:
        errors.append("expected exactly four full-height color-5 separators")
    panels = _split_panels(grid)
    operand_palettes = []
    for panel in (0, 1, 3, 4):
        palette = {
            value
            for row in panels[panel]
            for value in row
            if value != 0
        }
        if not palette or palette & {5, 9}:
            errors.append(
                f"operand panel {panel} must contain nonzero role colors "
                "other than 5 or 9"
            )
        operand_palettes.append(tuple(sorted(palette)))
    if panels[2] != _merge(panels[0], panels[1]):
        errors.append("panel 2 must be the exact merge of panels 0 and 1")

    demonstration_states = _state_counts(panels[0], panels[1])
    query_states = _state_counts(panels[3], panels[4])
    for state in ("both_zero", "left_only", "right_only"):
        if demonstration_states[state] == 0:
            errors.append(f"worked example must include {state}")
        if query_states[state] == 0:
            errors.append(f"query pair must include {state}")
    if (
        demonstration_states["overlap_equal"]
        + demonstration_states["overlap_conflict"]
        == 0
    ):
        errors.append("worked example must include a nonzero overlap")

    facts = None
    if not errors:
        profile_key = _profile_key(panels)
        profile_index = next(
            (
                index
                for index, public_key in enumerate(_PUBLIC_PROFILE_KEYS)
                if profile_key == public_key
            ),
            None,
        )
        output = _merge(panels[3], panels[4])
        facts = {
            "panel_size": panel_width,
            "panels": panels,
            "operand_palettes": tuple(operand_palettes),
            "demonstration_states": demonstration_states,
            "query_states": query_states,
            "output": output,
            "profile_index": profile_index,
            "scene_family": "linked" if profile_index is not None else "generalized",
            "relation": _relation_name(demonstration_states),
            "query_relation": _relation_name(query_states),
        }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    if facts["profile_index"] is not None:
        return f"public_profile_{facts['profile_index'] + 1}"
    return (
        f"generalized:{facts['panel_size']}:{facts['relation']}:"
        f"{facts['query_relation']}"
    )


def rule_mirror(grid):
    """Input-pure Python mirror used only for focused parity evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _apply_form(panel, form_index):
    return _d4(panel)[form_index]


def _recolor_panels(rng, panels):
    role_values = sorted(
        {
            value
            for panel in (0, 1, 3, 4)
            for row in panels[panel]
            for value in row
            if value != 0
        }
    )
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8], len(role_values))
    mapping = dict(zip(role_values, palette))
    return tuple(
        [
            [
                9 if value == 9 else mapping.get(value, value)
                for value in row
            ]
            for row in panel
        ]
        for panel in panels
    )


def _build_linked(rng):
    if rng.random() < 0.08:
        return copy.deepcopy(rng.choice(_PUBLIC_INPUTS))
    panels = list(_split_panels(rng.choice(_PUBLIC_INPUTS)))
    demonstration_form = rng.randrange(8)
    query_form = rng.randrange(8)
    for panel in (0, 1, 2):
        panels[panel] = _apply_form(panels[panel], demonstration_form)
    for panel in (3, 4):
        panels[panel] = _apply_form(panels[panel], query_form)
    if rng.random() < 0.5:
        panels[0], panels[1] = panels[1], panels[0]
    if rng.random() < 0.5:
        panels[3], panels[4] = panels[4], panels[3]
    panels = _recolor_panels(rng, tuple(panels))
    return _assemble(panels)


def _pair_masks(rng, size, density):
    positions = [(row, col) for row in range(size) for col in range(size)]
    rng.shuffle(positions)
    overlap, left_only, right_only, reserved_empty = positions[:4]
    left = {overlap, left_only}
    right = {overlap, right_only}
    for position in positions[4:]:
        if position == reserved_empty or rng.random() >= density:
            continue
        mode = rng.choice(("left", "right", "both"))
        if mode in ("left", "both"):
            left.add(position)
        if mode in ("right", "both"):
            right.add(position)
    return left, right


def _paint_mask(size, cells, color):
    panel = full_grid(size, size, 0)
    for row, col in cells:
        panel[row][col] = color
    return panel


def _role_pair(rng, same):
    first = rng.choice([1, 2, 3, 4, 6, 7, 8])
    if same:
        return first, first
    second = rng.choice(
        [color for color in (1, 2, 3, 4, 6, 7, 8) if color != first]
    )
    return first, second


def _build_generalized(rng, band):
    size = {"easy": 3, "medium": 4, "hard": 5}[band]
    density = {"easy": 0.12, "medium": 0.24, "hard": 0.38}[band]
    same_relation = rng.random() < 0.5
    for _ in range(100):
        demo_left, demo_right = _pair_masks(rng, size, density)
        query_left, query_right = _pair_masks(rng, size, density)
        demo_colors = _role_pair(rng, same_relation)
        query_colors = _role_pair(rng, same_relation)
        panel_0 = _paint_mask(size, demo_left, demo_colors[0])
        panel_1 = _paint_mask(size, demo_right, demo_colors[1])
        panel_2 = _merge(panel_0, panel_1)
        panel_3 = _paint_mask(size, query_left, query_colors[0])
        panel_4 = _paint_mask(size, query_right, query_colors[1])
        panels = (panel_0, panel_1, panel_2, panel_3, panel_4)
        if _profile_key(panels) not in _PUBLIC_PROFILE_KEYS:
            return _assemble(panels)
    raise RuntimeError("could not construct a non-canonical generalized scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = context.draw_choice("scene_family", SCENE_FAMILIES)
    rng = context.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
