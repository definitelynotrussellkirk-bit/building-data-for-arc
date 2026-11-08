"""Lawful sampler for ARC task d2f8cb1c91b2.

The input is four 3x3 panels separated by full color-5 columns.  Panels A and
B demonstrate a D4 transform.  The same transform is applied to X, then the
transformed X is merged cellwise with Y: empty cells yield to nonempty cells,
matching nonzero cells stay unchanged, and different nonzero cells become 9.

The executable helpers below are mirrors used for validation, curriculum
checks, and source-bound regression probes.  The selected Racket program
remains the authority.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2f8cb1c91b2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a401bcfe7b0a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Infer a unique nonidentity D4 transform from two 3x3 panels, apply it "
    "to a query panel, then merge with a fourth panel using color 9 exactly "
    "for unequal nonzero overlaps."
)
INVARIANTS = [
    "the input is exactly four 3x3 panels separated by full color-5 columns",
    "generated A->B demonstrations identify one requested nonidentity D4 transform",
    "every generated query contains x-only, y-only, matching, and conflicting overlaps",
    "the output preserves lone or matching cells and marks unequal nonzero overlaps with 9",
]

TRANSFORMS = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
GENERATED_TRANSFORMS = tuple(code for code in TRANSFORMS if code != "id")
LEGAL_DATA_COLORS = (1, 2, 3, 4, 6, 7, 8)
SEPARATOR_COLUMNS = (3, 7, 11)
PANEL_LEFTS = (0, 4, 8, 12)

AXES = {
    "transform": {
        "type": "enum",
        "default": "twelve-step teaching schedule",
        "valid": "r1|r2|r3|fh|fv|tr|atr",
    },
    "palette_size": {
        "type": "int",
        "default": "alternating 3,4 schedule",
        "valid": "3..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# Every four consecutive samples contain at least two r3/atr items.  Therefore,
# after any one item is rotated into the query, the remaining three demos still
# refute the historical shortcut that aliases r3 and atr to transpose.
_TRANSFORM_SCHEDULE = (
    "r3", "r1", "atr", "r2", "r3", "fh",
    "atr", "fv", "r3", "tr", "atr", "r1",
)
_PALETTE_SCHEDULE = (3, 4)
_DEMO_COUNTS = {
    None: (3, 4, 5, 6),
    "easy": (3, 3, 4, 3),
    "medium": (4, 5, 4, 5),
    "hard": (5, 6, 6, 5),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    if "transform" in overrides and overrides["transform"] is not None:
        value = overrides["transform"]
        if type(value) is not str:
            raise TypeError("transform override must be a string")
        if value not in GENERATED_TRANSFORMS:
            raise ValueError(
                f"transform override must be one of {GENERATED_TRANSFORMS}, got {value!r}"
            )

    if "palette_size" in overrides and overrides["palette_size"] is not None:
        value = overrides["palette_size"]
        if type(value) is not int:
            raise TypeError("palette_size override must be an integer (not bool)")
        if value not in (3, 4):
            raise ValueError("palette_size override must be 3 or 4")


def _draw_exact(ctx: Any, name: str, domain: Sequence[Any], default: Any) -> Any:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, tuple(domain))
    return ctx.draw_choice(name, (default,))


def _transform_coord(row: int, col: int, n: int, code: str) -> tuple[int, int]:
    if code == "id":
        return row, col
    if code == "r1":
        return col, n - 1 - row
    if code == "r2":
        return n - 1 - row, n - 1 - col
    if code == "r3":
        return n - 1 - col, row
    if code == "fh":
        return row, n - 1 - col
    if code == "fv":
        return n - 1 - row, col
    if code == "tr":
        return col, row
    if code == "atr":
        return n - 1 - col, n - 1 - row
    raise ValueError(f"unknown transform {code!r}")


def _transform_grid(grid: Sequence[Sequence[int]], code: str) -> list[list[int]]:
    if not isinstance(code, str) or code not in TRANSFORMS:
        raise ValueError(f"unknown transform {code!r}")
    if not grid or any(not isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("transform expects a nonempty square grid")
    n = len(grid)
    if any(len(row) != n for row in grid):
        raise ValueError("transform expects a nonempty square grid")
    out = [[0] * n for _ in range(n)]
    for row in range(n):
        for col in range(n):
            target_row, target_col = _transform_coord(row, col, n, code)
            out[target_row][target_col] = int(grid[row][col])
    return out


# Backward-compatible local name used by retained audit snippets.
_xform_grid = _transform_grid


def _transform_cells(
    cells: Iterable[tuple[int, int]], code: str, n: int = 3
) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(_transform_coord(row, col, n, code) for row, col in cells))


def _inverse_transform(code: str) -> str:
    return {
        "id": "id",
        "r1": "r3",
        "r2": "r2",
        "r3": "r1",
        "fh": "fh",
        "fv": "fv",
        "tr": "tr",
        "atr": "atr",
    }[code]


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [min(remaining)]
    seen = {stack[0]}
    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == remaining


def _shape_candidates(count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    cells = tuple((row, col) for row in range(3) for col in range(3))
    candidates: list[tuple[tuple[int, int], ...]] = []
    for candidate in combinations(cells, count):
        if not _is_connected(candidate):
            continue
        images = {_transform_cells(candidate, code) for code in TRANSFORMS}
        if len(images) == 8:
            candidates.append(tuple(candidate))
    if not candidates:
        raise RuntimeError(f"no connected asymmetric 3x3 shapes with {count} cells")
    return tuple(candidates)


_ASYMMETRIC_SHAPES = {count: _shape_candidates(count) for count in range(3, 7)}


def _paint_panel(
    grid: list[list[int]], left: int, cells: Iterable[tuple[int, int]], color: int
) -> None:
    for row, col in sorted(cells):
        grid[row][left + col] = color


def _paint_matrix(grid: list[list[int]], left: int, panel: Sequence[Sequence[int]]) -> None:
    for row in range(3):
        for col in range(3):
            grid[row][left + col] = int(panel[row][col])


def _split_panels(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], ...]:
    return tuple(
        [list(row[left : left + 3]) for row in grid]
        for left in PANEL_LEFTS
    )


def _transform_matches(panel_a: list[list[int]], panel_b: list[list[int]]) -> list[str]:
    return [code for code in TRANSFORMS if _transform_grid(panel_a, code) == panel_b]


def _merge_layers(
    transformed_x: Sequence[Sequence[int]],
    panel_y: Sequence[Sequence[int]],
    *,
    conflict: str = "marker",
) -> list[list[int]]:
    out = [[0] * 3 for _ in range(3)]
    for row in range(3):
        for col in range(3):
            x_value = int(transformed_x[row][col])
            y_value = int(panel_y[row][col])
            if x_value == 0:
                value = y_value
            elif y_value == 0 or x_value == y_value:
                value = x_value
            elif conflict == "marker":
                value = 9
            elif conflict == "keep_x":
                value = x_value
            elif conflict == "keep_y":
                value = y_value
            else:
                raise ValueError(f"unknown conflict mode {conflict!r}")
            out[row][col] = value
    return out


def _merge_stats(
    transformed_x: Sequence[Sequence[int]], panel_y: Sequence[Sequence[int]]
) -> dict[str, int]:
    stats = {"both_zero": 0, "x_only": 0, "y_only": 0, "match": 0, "conflict": 0}
    for row in range(3):
        for col in range(3):
            x_value = int(transformed_x[row][col])
            y_value = int(panel_y[row][col])
            if x_value == 0 and y_value == 0:
                stats["both_zero"] += 1
            elif y_value == 0:
                stats["x_only"] += 1
            elif x_value == 0:
                stats["y_only"] += 1
            elif x_value == y_value:
                stats["match"] += 1
            else:
                stats["conflict"] += 1
    return stats


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    if not isinstance(grid, (list, tuple)) or len(grid) != 3:
        return ["expected exactly 3 rows"], None
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be lists or tuples"], None
    if any(len(row) != 15 for row in grid):
        return ["expected a rectangular 3x15 grid"], None
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({row_index},{col_index}) must be an integer ARC color 0..9"], None

    errors: list[str] = []
    actual_full_dividers = tuple(
        col for col in range(15) if all(grid[row][col] == 5 for row in range(3))
    )
    if actual_full_dividers != SEPARATOR_COLUMNS:
        errors.append(
            f"expected full color-5 separators at {SEPARATOR_COLUMNS}, got {actual_full_dividers}"
        )
    for row in range(3):
        for col in range(15):
            if grid[row][col] == 5 and col not in SEPARATOR_COLUMNS:
                errors.append(f"color 5 is reserved for separators; found at ({row},{col})")
                break
        if errors and errors[-1].startswith("color 5"):
            break
    if errors:
        return errors, None

    panels = _split_panels(grid)
    panel_a, panel_b, panel_x, panel_y = panels
    if panel_a == panel_b:
        errors.append("A and B must demonstrate a nonidentity transform")
    matches = _transform_matches(panel_a, panel_b)
    if not matches:
        errors.append("no D4 transform maps A exactly to B")
    nonzero_counts = [sum(value != 0 for row in panel for value in row) for panel in panels]
    for index, count in enumerate(nonzero_counts):
        if count == 0:
            errors.append(f"panel {index} must contain at least one nonzero cell")
    if errors:
        return errors, None

    transform = matches[0]  # canonical Racket order; canonical test is intentionally ambiguous.
    if transform == "id":
        return ["the first inferred transform must be nonidentity"], None
    transformed_x = _transform_grid(panel_x, transform)
    stats = _merge_stats(transformed_x, panel_y)
    if stats["conflict"] < 1:
        errors.append("query must contain at least one unequal nonzero overlap")
    if errors:
        return errors, None

    colors = {
        int(value)
        for row in grid
        for value in row
        if value not in (0, 5)
    }
    return [], {
        "panels": panels,
        "matches": matches,
        "transform": transform,
        "transformed_x": transformed_x,
        "stats": stats,
        "palette_size": len(colors),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Return exact reasons an input is outside the selected rule's lawful domain."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    if len(analysis["matches"]) != 1:
        raise ValueError(f"cannot observe a unique transform: {analysis['matches']}")
    return {
        "transform": analysis["transform"],
        "palette_size": analysis["palette_size"],
    }


def reference_output(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    return _merge_layers(analysis["transformed_x"], analysis["panels"][3])


rule_mirror = reference_output


def _transpose_alias_rival(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    code = analysis["transform"]
    if code in {"r3", "atr"}:
        code = "tr"
    panel_x, panel_y = analysis["panels"][2:]
    return _merge_layers(_transform_grid(panel_x, code), panel_y)


def _no_transform_rival(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    panel_x, panel_y = analysis["panels"][2:]
    return _merge_layers(panel_x, panel_y)


def _keep_y_on_conflict_rival(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    return _merge_layers(
        analysis["transformed_x"], analysis["panels"][3], conflict="keep_y"
    )


def _matching_is_conflict_rival(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    panel_y = analysis["panels"][3]
    output = _merge_layers(analysis["transformed_x"], panel_y)
    for row in range(3):
        for col in range(3):
            value = analysis["transformed_x"][row][col]
            if value != 0 and value == panel_y[row][col]:
                output[row][col] = 9
    return output


def _safe_witness(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    errors, analysis = _analyze_grid(grid)
    return not errors and analysis is not None and bool(predicate(analysis))


def _witness_transpose_alias(grid: Any) -> bool:
    return _safe_witness(
        grid,
        lambda analysis: analysis["transform"] in {"r3", "atr"}
        and _transpose_alias_rival(grid) != reference_output(grid),
    )


def _witness_transform_required(grid: Any) -> bool:
    return _safe_witness(grid, lambda analysis: _no_transform_rival(grid) != reference_output(grid))


def _witness_conflict(grid: Any) -> bool:
    return _safe_witness(grid, lambda analysis: analysis["stats"]["conflict"] > 0)


def _witness_match(grid: Any) -> bool:
    return _safe_witness(grid, lambda analysis: analysis["stats"]["match"] > 0)


def _branch(name: str) -> Callable[[Any], bool]:
    return lambda grid: _safe_witness(grid, lambda analysis: analysis["stats"][name] > 0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "transpose_aliases": _transpose_alias_rival,
    "no_transform": _no_transform_rival,
    "keep_y_on_conflict": _keep_y_on_conflict_rival,
    "matching_is_conflict": _matching_is_conflict_rival,
}
CANONICAL_SHORTCUTS = {"transpose_aliases": _transpose_alias_rival}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "transpose_alias_counterexample": _witness_transpose_alias,
    "transform_required": _witness_transform_required,
    "different_color_conflict": _witness_conflict,
    "matching_overlap": _witness_match,
    "x_only": _branch("x_only"),
    "y_only": _branch("y_only"),
    "both_zero": _branch("both_zero"),
}
WITNESS_RIVALS = {
    "transpose_alias_counterexample": ["transpose_aliases"],
    "transform_required": ["no_transform"],
    "different_color_conflict": ["keep_y_on_conflict"],
    "matching_overlap": ["matching_is_conflict"],
}
BRANCH_WITNESSES = {"x_only", "y_only", "both_zero"}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require labels to be correct and demos to rule out query-changing rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    episodes = list(demos) + [query]
    for index, episode in enumerate(episodes):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{label} must contain input and output")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{label} is outside the rule domain: {errors[0]}")
            continue
        if episode["output"] != reference_output(episode["input"]):
            reasons.append(f"{label} output disagrees with the selected rule")
    if reasons:
        return reasons

    truth = reference_output(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != truth:
            reasons.append(f"named competitor {name!r} fits every demo but changes the query")
    return reasons


def _query_panels(
    transform: str,
    colors: tuple[int, ...],
    layout_code: str,
) -> tuple[list[list[int]], list[list[int]]]:
    demo_color, x_color, y_color = colors[:3]
    match_color = colors[3] if len(colors) == 4 else demo_color

    transformed_x = [[0] * 3 for _ in range(3)]
    panel_y = [[0] * 3 for _ in range(3)]
    transformed_x[1][1] = x_color       # unequal overlap
    transformed_x[0][1] = x_color       # x-only, connected to conflict
    transformed_x[1][2] = match_color   # matching overlap
    panel_y[1][1] = y_color
    panel_y[2][1] = y_color              # y-only, connected to conflict
    panel_y[1][2] = match_color

    transformed_x = _transform_grid(transformed_x, layout_code)
    panel_y = _transform_grid(panel_y, layout_code)
    panel_x = _transform_grid(transformed_x, _inverse_transform(transform))
    return panel_x, panel_y


def _build_grid(
    shape_a: tuple[tuple[int, int], ...],
    transform: str,
    colors: tuple[int, ...],
    layout_code: str,
) -> list[list[int]]:
    panel_x, panel_y = _query_panels(transform, colors, layout_code)
    grid = full_grid(3, 15, 0)
    for row in range(3):
        for col in SEPARATOR_COLUMNS:
            grid[row][col] = 5
    _paint_panel(grid, 0, shape_a, colors[0])
    _paint_panel(grid, 4, _transform_cells(shape_a, transform), colors[0])
    _paint_matrix(grid, 8, panel_x)
    _paint_matrix(grid, 12, panel_y)
    return grid


def _candidate_is_teaching(grid: list[list[int]], transform: str) -> bool:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["matches"] != [transform]:
        return False
    required = ("x_only", "y_only", "match", "conflict")
    if any(analysis["stats"][name] < 1 for name in required):
        return False
    truth = reference_output(grid)
    if _no_transform_rival(grid) == truth:
        return False
    if _keep_y_on_conflict_rival(grid) == truth:
        return False
    if _matching_is_conflict_rival(grid) == truth:
        return False
    if transform in {"r3", "atr"} and _transpose_alias_rival(grid) == truth:
        return False
    return True


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    transform_default = _TRANSFORM_SCHEDULE[sample_index % len(_TRANSFORM_SCHEDULE)]
    transform = str(_draw_exact(ctx, "transform", GENERATED_TRANSFORMS, transform_default))
    palette_default = _PALETTE_SCHEDULE[sample_index % len(_PALETTE_SCHEDULE)]
    palette_size = int(_draw_exact(ctx, "palette_size", (3, 4), palette_default))

    count_options = _DEMO_COUNTS[difficulty]
    demo_count = count_options[sample_index % len(count_options)]
    shape_rng = ctx.draw_rng("demo_shape")
    shape_a = shape_rng.choice(list(_ASYMMETRIC_SHAPES[demo_count]))

    palette_rng = ctx.draw_rng("palette")
    colors = tuple(palette_rng.sample(list(LEGAL_DATA_COLORS), palette_size))

    layout_rng = ctx.draw_rng("query_layout")
    layouts = list(TRANSFORMS)
    layout_rng.shuffle(layouts)
    grid: list[list[int]] | None = None
    for layout_code in layouts:
        candidate = _build_grid(shape_a, transform, colors, layout_code)
        if _candidate_is_teaching(candidate, transform):
            grid = candidate
            break
    if grid is None:
        raise RuntimeError(
            f"unable to construct a rival-separating query for transform {transform!r}"
        )

    observed = observe_overrides(grid)
    expected = {"transform": transform, "palette_size": palette_size}
    if observed != expected:
        raise RuntimeError(f"internal axis mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Near-miss inputs that the validator must reject."""
    base = generate(99, 14, difficulty="medium", transform="r3", palette_size=4)
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_separator = deepcopy(base)
    missing_separator[0][3] = 0
    fixtures.append(("missing_separator", missing_separator))

    extra_separator = deepcopy(base)
    extra_separator[0][0] = 5
    fixtures.append(("extra_separator", extra_separator))

    identity_demo = deepcopy(base)
    panel_a = _split_panels(identity_demo)[0]
    for row in range(3):
        identity_demo[row][4:7] = panel_a[row]
    fixtures.append(("identity_demo", identity_demo))

    no_conflict = deepcopy(base)
    for row in range(3):
        no_conflict[row][12:15] = [0, 0, 0]
    fixtures.append(("no_conflict", no_conflict))
    return fixtures
