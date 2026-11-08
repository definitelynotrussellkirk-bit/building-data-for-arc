"""Generator for ARC task 907bb29fbac5 — pairwise XOR gallery.

The input is a fixed row of three 4x4 binary masks, separated by one black
column.  The output is the ordered 3x3 relation matrix of those masks: every
4x4 tile is the cellwise XOR of one ordered panel pair, painted red (7), and
tiles are separated by one black row/column.

Ordinary lessons deliberately expose the complete XOR truth table for every
unordered panel pair.  Official inputs are accepted exactly even where a
single pair omits overlap or one exclusive direction; the lesson generator
does not repeat those locally ambiguous cases.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "907bb29fbac5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "edb7f73552a9"
SUMMARY = (
    "Split the fixed 4x14 input into three 4x4 color-6 masks. Build a 3x3 "
    "ordered gallery whose tile (i,j) is panel_i XOR panel_j in color 7, "
    "with one-cell black separators; diagonal tiles are blank and opposite "
    "off-diagonal tiles are equal."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is exactly 4x14 with black separator columns 4 and 9",
    "panel cells use only black 0 and foreground 6",
    "ordinary draws contain three distinct masks with one shared cell and both exclusive directions for every pair",
    "ordinary draws use equal panel counts 4..7 and an observable balanced or shared_core overlap profile",
    "the 14x14 output is a symmetric 3x3 XOR relation matrix with blank diagonal tiles and black separator rows/columns",
]

AXES = {
    "grid_h": {"type": "int", "default": "4", "valid": "4..4"},
    "grid_w": {"type": "int", "default": "14", "valid": "14..14"},
    "panel_cell_count": {
        "type": "int",
        "default": "easy 4; medium 5..6; hard 7",
        "valid": "4..7",
        "doc": "Exact number of foreground cells in each of the three panels.",
    },
    "overlap_profile": {
        "type": "str",
        "default": "keyed balanced|shared_core",
        "valid": "balanced|shared_core",
        "doc": "Exact seven-region Venn profile of the three panel masks.",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_PANEL_STARTS = (0, 5, 10)
_PANEL_SIZE = 4

# Compact exact signatures of the five official inputs.  Each integer is the
# row-major 16-bit mask of one 4x4 panel.  Canonical exceptions are explicit:
# train_0 has a disjoint panel pair and train_2 has a subset pair, yet both are
# official and must remain accepted by self_check.
_CANONICAL_MASK_TRIPLES = {
    (0x088E, 0xE440, 0x0623): "train_0",
    (0x6C80, 0x0AAE, 0x4210): "train_1",
    (0xCC80, 0x4E40, 0x0E00): "train_2",
    (0xC620, 0x6230, 0x0AAE): "train_3",
    (0x88E0, 0x6C80, 0x4E40): "test_0",
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _validate_grid(grid) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                return errors, height, width
    return errors, height, width


def _panel_sets(grid) -> tuple[frozenset[tuple[int, int]], ...]:
    return tuple(
        frozenset(
            (row, col)
            for row in range(_PANEL_SIZE)
            for col in range(_PANEL_SIZE)
            if grid[row][start + col] == 6
        )
        for start in _PANEL_STARTS
    )


def _mask_int(cells: frozenset[tuple[int, int]]) -> int:
    value = 0
    for row in range(_PANEL_SIZE):
        for col in range(_PANEL_SIZE):
            value = (value << 1) | int((row, col) in cells)
    return value


def canonical_profile_signature(grid) -> str | None:
    errors, height, width = _validate_grid(grid)
    if errors or (height, width) != (4, 14):
        return None
    if any(grid[row][gap] != 0 for row in range(4) for gap in (4, 9)):
        return None
    if any(value not in (0, 6) for row in grid for value in row):
        return None
    triple = tuple(_mask_int(panel) for panel in _panel_sets(grid))
    return _CANONICAL_MASK_TRIPLES.get(triple)


def _pair_truth_counts(left, right) -> dict[str, int]:
    return {
        "both": len(left & right),
        "left_only": len(left - right),
        "right_only": len(right - left),
        "neither": 16 - len(left | right),
    }


def semantic_observables(grid) -> dict[str, object]:
    """Return task-linked facts used by tests and semantic censuses."""
    errors, height, width = _validate_grid(grid)
    if errors or (height, width) != (4, 14):
        return {"errors": errors or [f"expected 4x14, got {height}x{width}"]}
    panels = _panel_sets(grid)
    pair_counts = {
        f"{left}-{right}": _pair_truth_counts(panels[left], panels[right])
        for left, right in combinations(range(3), 2)
    }
    triple = len(panels[0] & panels[1] & panels[2])
    pair_only = (
        len((panels[0] & panels[1]) - panels[2]),
        len((panels[0] & panels[2]) - panels[1]),
        len((panels[1] & panels[2]) - panels[0]),
    )
    singles = (
        len(panels[0] - panels[1] - panels[2]),
        len(panels[1] - panels[0] - panels[2]),
        len(panels[2] - panels[0] - panels[1]),
    )
    counts = tuple(len(panel) for panel in panels)
    profile = None
    if len(set(counts)) == 1 and 4 <= counts[0] <= 7:
        n = counts[0]
        if triple == 1 and pair_only == (1, 1, 1) and singles == (n - 3,) * 3:
            profile = "balanced"
        elif triple == n - 2 and pair_only == (0, 0, 0) and singles == (2, 2, 2):
            profile = "shared_core"
    return {
        "errors": [],
        "panel_counts": counts,
        "panel_masks": tuple(_mask_int(panel) for panel in panels),
        "pair_truth_counts": pair_counts,
        "triple_intersection": triple,
        "pair_only_counts": pair_only,
        "single_only_counts": singles,
        "overlap_profile": profile,
        "canonical_signature": _CANONICAL_MASK_TRIPLES.get(
            tuple(_mask_int(panel) for panel in panels)
        ),
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid itself."""
    errors, height, width = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    observed: dict[str, int | str] = {"grid_h": height, "grid_w": width}
    if (height, width) != (4, 14):
        return observed
    facts = semantic_observables(grid)
    counts = facts.get("panel_counts")
    if isinstance(counts, tuple) and len(set(counts)) == 1:
        observed["panel_cell_count"] = counts[0]
    profile = facts.get("overlap_profile")
    if isinstance(profile, str):
        observed["overlap_profile"] = profile
    return observed


def _membership_labels(panel_cell_count: int, profile: str) -> list[str]:
    n = panel_cell_count
    if profile == "balanced":
        return (
            ["ABC", "AB", "AC", "BC"]
            + ["A"] * (n - 3)
            + ["B"] * (n - 3)
            + ["C"] * (n - 3)
        )
    if profile == "shared_core":
        return ["ABC"] * (n - 2) + ["A"] * 2 + ["B"] * 2 + ["C"] * 2
    raise ValueError(f"unknown overlap_profile: {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, XOR-identifying lesson input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 4, 4)
    width = ctx.draw_int("grid_w", 14, 14)

    if "panel_cell_count" in overrides:
        count_lo, count_hi = 4, 7
    elif difficulty == "easy":
        count_lo, count_hi = 4, 4
    elif difficulty == "medium":
        count_lo, count_hi = 5, 6
    elif difficulty == "hard":
        count_lo, count_hi = 7, 7
    else:
        count_lo, count_hi = 4, 7
    panel_cell_count = ctx.draw_int("panel_cell_count", count_lo, count_hi)
    overlap_profile = ctx.draw_choice(
        "overlap_profile", ("balanced", "shared_core")
    )

    labels = _membership_labels(panel_cell_count, overlap_profile)
    positions = [(row, col) for row in range(4) for col in range(4)]
    ctx.draw_rng("membership_layout").shuffle(positions)
    panels = [set(), set(), set()]
    for label, position in zip(labels, positions):
        for panel_index, marker in enumerate("ABC"):
            if marker in label:
                panels[panel_index].add(position)

    grid = full_grid(height, width, 0)
    for panel_index, start in enumerate(_PANEL_STARTS):
        for row, col in panels[panel_index]:
            grid[row][start + col] = 6

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid XOR lesson: {errors}")
    expected = {
        "grid_h": height,
        "grid_w": width,
        "panel_cell_count": panel_cell_count,
        "overlap_profile": overlap_profile,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed grid does not realize keyed axes: {expected} -> {observed}")
    return _copy_grid(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize official inputs plus the stronger generated teaching domain."""
    errors, height, width = _validate_grid(grid)
    if errors:
        return errors
    if (height, width) != (4, 14):
        return [f"expected fixed 4x14 input, got {height}x{width}"]

    for gap in (4, 9):
        if any(grid[row][gap] != 0 for row in range(4)):
            errors.append(f"separator column {gap} must be all 0")
    illegal = [
        (row, col, grid[row][col])
        for row in range(4)
        for col in range(14)
        if col not in (4, 9) and grid[row][col] not in (0, 6)
    ]
    if illegal:
        errors.append("panel cells must use only colors 0 and 6")
    if errors:
        return errors

    facts = semantic_observables(grid)
    counts = facts["panel_counts"]
    masks = facts["panel_masks"]
    if any(count == 0 for count in counts):
        errors.append("all three panels must be nonempty")
    if len(set(masks)) != 3:
        errors.append("three panel masks must be mutually distinct")
    if errors:
        return errors

    # Official examples are the authority, including two locally incomplete
    # truth-table pairs.  Generated non-canonical scenes must satisfy the
    # stronger lesson grammar below.
    if facts["canonical_signature"] is not None:
        return []

    if len(set(counts)) != 1 or not 4 <= counts[0] <= 7:
        errors.append("non-canonical lessons require equal panel counts in 4..7")
    if facts["overlap_profile"] not in ("balanced", "shared_core"):
        errors.append("non-canonical lesson does not match a declared overlap profile")
    for pair, truth in facts["pair_truth_counts"].items():
        missing = [name for name, count in truth.items() if count == 0]
        if missing:
            errors.append(f"panel pair {pair} hides XOR truth branch(es): {missing}")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Exact Python mirror used only for focused tests and evidence."""
    panels = []
    for start in _PANEL_STARTS:
        panels.append([
            [1 if grid[row][start + col] == 6 else 0 for col in range(4)]
            for row in range(4)
        ])
    output = full_grid(14, 14, 0)
    for panel_row in range(3):
        for panel_col in range(3):
            top = panel_row * 5
            left = panel_col * 5
            for row in range(4):
                for col in range(4):
                    if panels[panel_row][row][col] != panels[panel_col][row][col]:
                        output[top + row][left + col] = 7
    return output


def mutation_fixtures():
    """Task-specific must-reject impostors for strict defect lint."""
    base = generate(99173, 11, difficulty="medium", panel_cell_count=5,
                    overlap_profile="balanced")

    separator = _copy_grid(base)
    separator[0][4] = 6

    wrong_color = _copy_grid(base)
    for row in range(4):
        for col in range(4):
            if wrong_color[row][col] == 6:
                wrong_color[row][col] = 5
                break
        else:
            continue
        break

    duplicate_panel = _copy_grid(base)
    for row in range(4):
        duplicate_panel[row][10:14] = duplicate_panel[row][0:4]

    missing_panel = _copy_grid(base)
    for row in range(4):
        missing_panel[row][5:9] = [0, 0, 0, 0]

    hidden_branch = _copy_grid(base)
    # Make panel B a subset of panel A.  The Racket rule can execute this, but
    # it is not an XOR-identifying generated lesson because A/B lacks B-only.
    for row in range(4):
        for col in range(4):
            hidden_branch[row][5 + col] = 6 if hidden_branch[row][col] == 6 else 0
    # Keep the three masks distinct while preserving the missing B-only branch.
    for row in range(4):
        for col in range(4):
            if hidden_branch[row][col] == 6:
                hidden_branch[row][5 + col] = 0
                break
        else:
            continue
        break

    return [
        ("separator_contamination", separator),
        ("wrong_foreground_color", wrong_color),
        ("duplicate_panel", duplicate_panel),
        ("missing_panel", missing_panel),
        ("hidden_xor_direction", hidden_branch),
    ]
