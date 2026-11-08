"""Semantic generator for ``13d2544b2b64`` — agreement across panel triples.

Two all-zero rows and two all-zero columns partition an input into a 3x3 array
of equal-sized panels.  For every local coordinate, a cell in a middle-column
panel takes the shared non-background color of its left/right counterparts; a
cell in a middle-row panel analogously takes the shared top/bottom color.  At
the center panel, a horizontal mark has priority when both rules fire.

The four-profile curriculum is deliberately source-bound to canonical 8x8,
four-color examples.  Every four-example window contains the three strongest
canonical blind spots (missing color-equality negatives, missing crossing
priority, and missing overwrite evidence) plus ordinary positive and one-sided
controls.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "13d2544b2b64"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "301b331591ad"

SUMMARY = (
    "Two zero rows and two zero columns split an 8x8 input into nine 2x2 "
    "panels.  At each local coordinate, equal non-1 colors on the left and "
    "right paint the intervening middle-column cell; equal non-1 colors on "
    "the top and bottom paint the intervening middle-row cell.  Horizontal "
    "wins at a center-cell conflict.  A four-profile schedule explicitly "
    "teaches unequal-color near misses, crossing priority, target overwrite, "
    "outer-middle fills, and one-sided controls."
)

INVARIANTS = [
    "exactly two full-zero separator rows and two full-zero separator columns",
    "the separators form three equal-height and three equal-width nonzero panels",
    "panel background is 1 and marker colors are ARC colors 2..9",
    "all generated inputs have canonical signature (height=8, width=8, palette-size=4)",
    "every generated input has at least one visible rule application",
    "every four-example schedule window contains all four semantic profiles",
]

COUNTER_HYPOTHESES = [
    "fill whenever both opposite cells are non-background, even if their colors differ",
    "give vertical agreement priority at center crossings",
    "write only into background-1 targets",
    "modify only the center panel",
    "use only horizontal or only vertical agreement",
    "copy a lone non-background source without requiring an opposite mate",
]

SCENE_PROFILES = (
    "canonical_controls",
    "equality_mismatch",
    "horizontal_precedence",
    "target_overwrite",
)
SCHEDULE_PROFILES = SCENE_PROFILES
# Solve preparation reads this teaching minimum without executing source.
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = len(SCENE_PROFILES)
MIN_STRICT_FRAC = 1.0

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic semantic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_GENERATED_SHAPE = (8, 8)
_GENERATED_PANEL_SIZE = (2, 2)
_PANEL_STARTS = (0, 3, 6)
_MARKER_COLORS = tuple(range(2, 10))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_sample_identity(seed: int, sample_index: int) -> None:
    """Keep reproducible request identities literal, without implicit coercion."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle every semantic contrast through every four-example window."""
    _validate_sample_identity(seed, sample_index)
    _band(difficulty)
    return SCENE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid dimensions must not exceed 30x30, found {len(grid)}x{width}"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be a literal ARC integer color 0..9"]
    return []


def _layout(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "valid": False}

    height, width = len(grid), len(grid[0])
    zero_rows = [r for r in range(height) if all(value == 0 for value in grid[r])]
    zero_cols = [c for c in range(width) if all(grid[r][c] == 0 for r in range(height))]
    if len(zero_rows) != 2:
        errors.append(f"expected exactly 2 full-zero separator rows, found {len(zero_rows)}")
    if len(zero_cols) != 2:
        errors.append(f"expected exactly 2 full-zero separator columns, found {len(zero_cols)}")
    if errors:
        return {
            "errors": errors,
            "valid": False,
            "height": height,
            "width": width,
            "zero_rows": zero_rows,
            "zero_cols": zero_cols,
        }

    sr0, sr1 = zero_rows
    sc0, sc1 = zero_cols
    row_sizes = (sr0, sr1 - sr0 - 1, height - sr1 - 1)
    col_sizes = (sc0, sc1 - sc0 - 1, width - sc1 - 1)
    if min(row_sizes) < 1 or len(set(row_sizes)) != 1:
        errors.append(f"separator rows must form three equal positive panel heights, found {row_sizes}")
    if min(col_sizes) < 1 or len(set(col_sizes)) != 1:
        errors.append(f"separator columns must form three equal positive panel widths, found {col_sizes}")

    separator_rows = set(zero_rows)
    separator_cols = set(zero_cols)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            on_separator = r in separator_rows or c in separator_cols
            if on_separator and value != 0:
                errors.append(f"separator cell ({r},{c}) must be 0")
                break
            if not on_separator and value == 0:
                errors.append(f"panel cell ({r},{c}) must be nonzero")
                break
        if errors:
            break

    return {
        "errors": errors,
        "valid": not errors,
        "height": height,
        "width": width,
        "zero_rows": zero_rows,
        "zero_cols": zero_cols,
        "row_sizes": row_sizes,
        "col_sizes": col_sizes,
        "cell_h": row_sizes[0],
        "cell_w": col_sizes[0],
        "row_starts": (0, sr0 + 1, sr1 + 1),
        "col_starts": (0, sc0 + 1, sc1 + 1),
    }


def _panel_index(position: int, first_separator: int, second_separator: int) -> int:
    if position < first_separator:
        return 0
    if position > second_separator:
        return 2
    return 1


def _equal_candidate(first: int, second: int) -> int:
    return first if first == second and first != 1 else 0


def _both_nonbackground_candidate(first: int, second: int) -> int:
    return first if first != 1 and second != 1 else 0


def _single_source_candidate(first: int, second: int) -> int:
    if first != 1:
        return first
    if second != 1:
        return second
    return 0


def _apply_variant(
    grid: Sequence[Sequence[int]],
    *,
    horizontal_mode: str = "equal",
    vertical_mode: str = "equal",
    priority: str = "horizontal",
    background_only: bool = False,
    center_only: bool = False,
    horizontal_enabled: bool = True,
    vertical_enabled: bool = True,
) -> list[list[int]]:
    layout = _layout(grid)
    if layout["errors"]:
        raise ValueError("invalid panel grid: " + "; ".join(layout["errors"]))

    candidate_functions = {
        "equal": _equal_candidate,
        "both_nonbackground": _both_nonbackground_candidate,
        "single_source": _single_source_candidate,
    }
    try:
        horizontal_candidate = candidate_functions[horizontal_mode]
        vertical_candidate = candidate_functions[vertical_mode]
    except KeyError as exc:
        raise ValueError(f"unknown candidate mode: {exc.args[0]}") from exc
    if priority not in {"horizontal", "vertical"}:
        raise ValueError(f"unknown priority: {priority!r}")

    output = [list(row) for row in grid]
    sr0, sr1 = layout["zero_rows"]
    sc0, sc1 = layout["zero_cols"]
    row_starts = layout["row_starts"]
    col_starts = layout["col_starts"]

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            gr = _panel_index(r, sr0, sr1)
            gc = _panel_index(c, sc0, sc1)
            if center_only and (gr, gc) != (1, 1):
                continue
            if background_only and value != 1:
                continue
            local_r = r - row_starts[gr]
            local_c = c - col_starts[gc]

            h_mark = 0
            if horizontal_enabled and gc == 1:
                left = grid[r][col_starts[0] + local_c]
                right = grid[r][col_starts[2] + local_c]
                h_mark = horizontal_candidate(left, right)

            v_mark = 0
            if vertical_enabled and gr == 1:
                top = grid[row_starts[0] + local_r][c]
                bottom = grid[row_starts[2] + local_r][c]
                v_mark = vertical_candidate(top, bottom)

            marks = (h_mark, v_mark) if priority == "horizontal" else (v_mark, h_mark)
            selected = next((mark for mark in marks if mark != 0), 0)
            if selected != 0:
                output[r][c] = selected
    return output


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return structural and semantic facts used by checks and review tooling."""
    layout = _layout(grid)
    base = {
        "valid": False,
        "errors": list(layout.get("errors", [])),
        "height": layout.get("height"),
        "width": layout.get("width"),
        "cell_h": layout.get("cell_h"),
        "cell_w": layout.get("cell_w"),
        "palette_size": 0,
        "marker_count": 0,
        "horizontal_match_count": 0,
        "vertical_match_count": 0,
        "horizontal_change_count": 0,
        "vertical_change_count": 0,
        "different_nonbackground_pair_count": 0,
        "one_sided_pair_count": 0,
        "one_sided_counterexample_count": 0,
        "priority_conflict_count": 0,
        "same_color_crossing_count": 0,
        "target_overwrite_count": 0,
        "outer_change_count": 0,
        "center_change_count": 0,
        "changed_count": 0,
        "output": None,
    }
    if layout["errors"]:
        return base

    output = [list(row) for row in grid]
    sr0, sr1 = layout["zero_rows"]
    sc0, sc1 = layout["zero_cols"]
    row_starts = layout["row_starts"]
    col_starts = layout["col_starts"]

    horizontal_matches = 0
    vertical_matches = 0
    horizontal_changes = 0
    vertical_changes = 0
    mismatches = 0
    one_sided = 0
    one_sided_counterexamples = 0
    conflicts = 0
    same_crossings = 0
    overwrites = 0
    outer_changes = 0
    center_changes = 0
    changed = 0

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            gr = _panel_index(r, sr0, sr1)
            gc = _panel_index(c, sc0, sc1)
            local_r = r - row_starts[gr]
            local_c = c - col_starts[gc]

            h_mark = 0
            h_loose = 0
            h_one = False
            if gc == 1:
                left = grid[r][col_starts[0] + local_c]
                right = grid[r][col_starts[2] + local_c]
                h_mark = _equal_candidate(left, right)
                h_loose = _single_source_candidate(left, right)
                h_one = (left != 1) ^ (right != 1)
                if h_mark:
                    horizontal_matches += 1
                if left != 1 and right != 1 and left != right:
                    mismatches += 1
                if h_one:
                    one_sided += 1

            v_mark = 0
            v_loose = 0
            v_one = False
            if gr == 1:
                top = grid[row_starts[0] + local_r][c]
                bottom = grid[row_starts[2] + local_r][c]
                v_mark = _equal_candidate(top, bottom)
                v_loose = _single_source_candidate(top, bottom)
                v_one = (top != 1) ^ (bottom != 1)
                if v_mark:
                    vertical_matches += 1
                if top != 1 and bottom != 1 and top != bottom:
                    mismatches += 1
                if v_one:
                    one_sided += 1

            if h_mark and v_mark:
                if h_mark == v_mark:
                    same_crossings += 1
                else:
                    conflicts += 1

            selected = h_mark or v_mark
            new_value = selected or value
            output[r][c] = new_value
            if new_value != value:
                changed += 1
                if h_mark:
                    horizontal_changes += 1
                elif v_mark:
                    vertical_changes += 1
                if value != 1:
                    overwrites += 1
                if (gr, gc) == (1, 1):
                    center_changes += 1
                else:
                    outer_changes += 1

            loose_selected = h_loose or v_loose
            loose_value = loose_selected or value
            if (h_one or v_one) and loose_value != new_value:
                one_sided_counterexamples += 1

    palette = {value for row in grid for value in row}
    base.update(
        {
            "valid": True,
            "errors": [],
            "palette_size": len(palette),
            "marker_count": sum(value not in (0, 1) for row in grid for value in row),
            "horizontal_match_count": horizontal_matches,
            "vertical_match_count": vertical_matches,
            "horizontal_change_count": horizontal_changes,
            "vertical_change_count": vertical_changes,
            "different_nonbackground_pair_count": mismatches,
            "one_sided_pair_count": one_sided,
            "one_sided_counterexample_count": one_sided_counterexamples,
            "priority_conflict_count": conflicts,
            "same_color_crossing_count": same_crossings,
            "target_overwrite_count": overwrites,
            "outer_change_count": outer_changes,
            "center_change_count": center_changes,
            "changed_count": changed,
            "output": output,
        }
    )
    return base


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact generated scene profile from the input alone."""
    facts = analyze_grid(grid)
    if not facts["valid"]:
        return {"scene_profile": None}
    if (facts["height"], facts["width"], facts["cell_h"], facts["cell_w"]) != (8, 8, 2, 2):
        return {"scene_profile": None}
    if facts["palette_size"] != 4:
        return {"scene_profile": None}

    profile: str | None = None
    if (
        facts["priority_conflict_count"] >= 1
        and facts["different_nonbackground_pair_count"] == 0
        and facts["target_overwrite_count"] == 0
    ):
        profile = "horizontal_precedence"
    elif (
        facts["target_overwrite_count"] >= 1
        and facts["priority_conflict_count"] == 0
        and facts["different_nonbackground_pair_count"] == 0
    ):
        profile = "target_overwrite"
    elif (
        facts["different_nonbackground_pair_count"] >= 2
        and facts["priority_conflict_count"] == 0
        and facts["target_overwrite_count"] == 0
        and facts["horizontal_change_count"] >= 1
        and facts["vertical_change_count"] >= 1
    ):
        profile = "equality_mismatch"
    elif (
        facts["different_nonbackground_pair_count"] == 0
        and facts["priority_conflict_count"] == 0
        and facts["target_overwrite_count"] == 0
        and facts["horizontal_change_count"] >= 1
        and facts["vertical_change_count"] >= 1
        and facts["outer_change_count"] >= 1
        and facts["one_sided_counterexample_count"] >= 1
    ):
        profile = "canonical_controls"
    return {"scene_profile": profile}


def _blank_grid() -> list[list[int]]:
    grid = full_grid(8, 8, 1)
    for c in range(8):
        grid[2][c] = 0
        grid[5][c] = 0
    for r in range(8):
        grid[r][2] = 0
        grid[r][5] = 0
    return grid


def _put(
    grid: list[list[int]],
    local: tuple[int, int],
    panel: tuple[int, int],
    color: int,
) -> None:
    local_r, local_c = local
    panel_r, panel_c = panel
    grid[_PANEL_STARTS[panel_r] + local_r][_PANEL_STARTS[panel_c] + local_c] = color


def _horizontal(
    grid: list[list[int]],
    local: tuple[int, int],
    panel_row: int,
    color: int,
    *,
    target: int = 1,
) -> None:
    _put(grid, local, (panel_row, 0), color)
    _put(grid, local, (panel_row, 1), target)
    _put(grid, local, (panel_row, 2), color)


def _vertical(
    grid: list[list[int]],
    local: tuple[int, int],
    panel_col: int,
    color: int,
    *,
    target: int = 1,
) -> None:
    _put(grid, local, (0, panel_col), color)
    _put(grid, local, (1, panel_col), target)
    _put(grid, local, (2, panel_col), color)


def _one_sided_controls(
    grid: list[list[int]],
    local: tuple[int, int],
    horizontal_color: int,
    vertical_color: int,
) -> None:
    _put(grid, local, (1, 0), horizontal_color)
    _put(grid, local, (0, 1), vertical_color)


def _render_profile(profile: str, rng) -> list[list[int]]:
    grid = _blank_grid()
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    rng.shuffle(positions)
    color_a, color_b = rng.sample(_MARKER_COLORS, 2)

    if profile == "canonical_controls":
        if rng.choice(("corner_l", "independent")) == "corner_l":
            # Canonical shared-source topology: a corner L supplies two
            # perpendicular outer fills and two one-sided negatives.
            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            for panel in rng.sample(corners, 3):
                _put(grid, positions[0], panel, color_a)
            if rng.choice(("horizontal", "vertical")) == "horizontal":
                _horizontal(grid, positions[1], 1, color_b)
            else:
                _vertical(grid, positions[1], 1, color_b)
        else:
            # Independent pairs retain simpler controls without imposing a
            # fixed three-fill count on every ordinary example.
            if rng.choice(("horizontal", "vertical")) == "horizontal":
                _horizontal(grid, positions[0], 1, color_a)
                _vertical(grid, positions[1], rng.choice((0, 2)), color_b)
            else:
                _vertical(grid, positions[0], 1, color_a)
                _horizontal(grid, positions[1], rng.choice((0, 2)), color_b)
            _put(
                grid, positions[2],
                rng.choice(((1, 0), (1, 2), (0, 1), (2, 1))),
                rng.choice((color_a, color_b)),
            )

    elif profile == "equality_mismatch":
        _put(grid, positions[0], (1, 0), color_a)
        _put(grid, positions[0], (1, 2), color_b)
        _put(grid, positions[1], (0, 1), color_a)
        _put(grid, positions[1], (2, 1), color_b)
        _horizontal(grid, positions[2], 1, color_a)
        _vertical(grid, positions[3], rng.choice((0, 2)), color_b)

    elif profile == "horizontal_precedence":
        _horizontal(grid, positions[0], 1, color_a)
        _vertical(grid, positions[0], 1, color_b)
        _horizontal(grid, positions[1], rng.choice((0, 2)), color_b)
        _vertical(grid, positions[2], rng.choice((0, 2)), color_a)
        _one_sided_controls(grid, positions[3], color_a, color_b)

    elif profile == "target_overwrite":
        _horizontal(grid, positions[0], 1, color_a, target=color_b)
        _vertical(
            grid,
            positions[1],
            rng.choice((0, 2)),
            color_a,
            target=color_b,
        )
        _vertical(grid, positions[2], 1, color_b)
        _one_sided_controls(grid, positions[3], color_a, color_b)

    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_sample_identity(seed, sample_index)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    rng = ctx.draw_rng(f"layout_{profile}_{band}")
    grid = _render_profile(profile, rng)

    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise RuntimeError(f"rendered profile {profile!r} observed as {observed!r}")
    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError(f"rendered profile {profile!r} failed self_check: {errors}")
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority grammar and reject structure-free impostors."""
    if difficulty is not None:
        try:
            _band(difficulty)
        except ValueError as exc:
            return [str(exc)]
    facts = analyze_grid(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    palette = {value for row in grid for value in row}
    if 1 not in palette:
        errors.append("panel background color 1 must be present")
    if not any(value not in (0, 1) for value in palette):
        errors.append("at least one non-background marker color is required")
    if facts["cell_h"] < 2 or facts["cell_w"] < 2:
        errors.append("panel height and width must each be at least 2")
    if facts["changed_count"] == 0:
        errors.append("the selected rule is an identity transformation on this input")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the literal shape/palette support observed in canonical pairs."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = analyze_grid(grid)
    if (facts["height"], facts["width"]) != _GENERATED_SHAPE:
        errors.append(f"strict profile requires shape 8x8, found {facts['height']}x{facts['width']}")
    if (facts["cell_h"], facts["cell_w"]) != _GENERATED_PANEL_SIZE:
        errors.append(
            "strict profile requires 2x2 panels, found "
            f"{facts['cell_h']}x{facts['cell_w']}"
        )
    if facts["palette_size"] not in (3, 4):
        errors.append(
            f"strict profile requires canonical palette size 3 or 4, found {facts['palette_size']}"
        )
    return errors


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected canonical Racket authority."""
    return _apply_variant(grid)


def _rival_ignore_color_equality(grid):
    return _apply_variant(
        grid,
        horizontal_mode="both_nonbackground",
        vertical_mode="both_nonbackground",
    )


def _rival_vertical_priority(grid):
    return _apply_variant(grid, priority="vertical")


def _rival_background_only(grid):
    return _apply_variant(grid, background_only=True)


def _rival_center_panel_only(grid):
    return _apply_variant(grid, center_only=True)


def _rival_horizontal_only(grid):
    return _apply_variant(grid, vertical_enabled=False)


def _rival_vertical_only(grid):
    return _apply_variant(grid, horizontal_enabled=False)


def _rival_copy_single_source(grid):
    return _apply_variant(
        grid,
        horizontal_mode="single_source",
        vertical_mode="single_source",
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_color_equality": _rival_ignore_color_equality,
    "vertical_priority": _rival_vertical_priority,
    "background_only": _rival_background_only,
    "center_panel_only": _rival_center_panel_only,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "copy_single_source": _rival_copy_single_source,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_color_equality": _rival_ignore_color_equality,
    "vertical_priority": _rival_vertical_priority,
    "background_only": _rival_background_only,
}


def _fact(grid, name: str) -> int:
    value = analyze_grid(grid).get(name, 0)
    return int(value) if isinstance(value, (int, bool)) else 0


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "different_nonbackground_pair_stays_unfilled": lambda grid: (
        _fact(grid, "different_nonbackground_pair_count") > 0
    ),
    "horizontal_priority_conflict": lambda grid: (
        _fact(grid, "priority_conflict_count") > 0
    ),
    "matching_pair_overwrites_nonbackground_target": lambda grid: (
        _fact(grid, "target_overwrite_count") > 0
    ),
    "outer_middle_panel_transforms": lambda grid: (
        _fact(grid, "outer_change_count") > 0
    ),
    "horizontal_branch_changes_output": lambda grid: (
        _fact(grid, "horizontal_change_count") > 0
    ),
    "vertical_branch_changes_output": lambda grid: (
        _fact(grid, "vertical_change_count") > 0
    ),
    "one_sided_source_stays_unfilled": lambda grid: (
        _fact(grid, "one_sided_counterexample_count") > 0
    ),
}
BRANCH_WITNESSES = (
    "horizontal_branch_changes_output",
    "vertical_branch_changes_output",
)
WITNESS_RIVALS = {
    "different_nonbackground_pair_stays_unfilled": [
        "ignore_color_equality",
        "copy_single_source",
    ],
    "horizontal_priority_conflict": ["vertical_priority"],
    "matching_pair_overwrites_nonbackground_target": ["background_only"],
    "outer_middle_panel_transforms": ["center_panel_only"],
    "horizontal_branch_changes_output": ["vertical_only"],
    "vertical_branch_changes_output": ["horizontal_only"],
    "one_sided_source_stays_unfilled": ["copy_single_source"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson unless all profiles occur and every named rival loses."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    profiles: set[str] = set()
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        grid = pair["input"]
        errors = strict_canonical_like(grid)
        if errors:
            reasons.append(f"pair {index} is outside the strict task grammar: {errors[0]}")
            continue
        expected = rule_mirror(grid)
        if expected != pair["output"]:
            reasons.append(f"pair {index} disagrees with the selected agreement rule")
        if index < len(demos):
            observed = observe_overrides(grid)["scene_profile"]
            if observed is not None:
                profiles.add(observed)

    if reasons:
        return reasons
    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        reasons.append(f"demonstrations are missing scheduled profiles: {missing}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named malformed or semantically empty scenes self_check must reject."""
    valid = generate(7011, 0, difficulty="medium", scene_profile="canonical_controls")

    unequal_panels = [row[:] for row in valid[:-1]]

    internal_zero = [row[:] for row in valid]
    internal_zero[0][0] = 0

    broken_separator = [row[:] for row in valid]
    broken_separator[2][0] = 1

    identity = _blank_grid()

    missing_background = [row[:] for row in valid]
    for r, row in enumerate(missing_background):
        for c, value in enumerate(row):
            if value == 1:
                missing_background[r][c] = 2

    return [
        ("unequal_panel_heights", unequal_panels),
        ("zero_inside_panel", internal_zero),
        ("broken_full_separator", broken_separator),
        ("identity_without_matches", identity),
        ("missing_background_one", missing_background),
    ]
