"""Generator for task 97c9b7818f99 — Manhattan Voronoi frame fill.

Every nonzero, non-cyan interior cell is a seed.  Empty interior cells inherit
whichever seed color is nearest in Manhattan distance; a nearest-distance tie
is colored gray (5).  Gray is therefore allowed to be an input seed as well as
the output tie marker.  The cyan border and all seed cells remain unchanged.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97c9b7818f99"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "af2297af758f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "A cyan (8) rectangular frame encloses 2-4 distinct single-cell seeds. "
    "A seed may use any nonzero color except cyan, including gray (5). For "
    "each empty interior cell, copy the color of its nearest seed by Manhattan "
    "distance; when two or more seeds are tied for nearest, paint gray (5). "
    "The frame and the original seeds stay unchanged."
)

INVARIANTS = [
    "the complete outer border is cyan (8)",
    "the interior contains 2-4 seeds at distinct cells with distinct colors from 1..7 or 9",
    "gray (5) is a lawful seed color and is also the output marker for nearest-distance ties",
    "at least one interior cell is empty in every input",
    "ordinary generated scenes contain both uniquely owned cells and true Manhattan tie cells",
    "ordinary generated scenes visibly distinguish Manhattan from squared-Euclidean nearest seeds",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical-linked schedule plus one generalized profile",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical-linked schedule plus one generalized profile",
        "valid": "8..15",
    },
    "n_seeds": {
        "type": "int",
        "default": "four-slot schedule covers 2, 3, and 4",
        "valid": "2..4",
    },
    "include_gray_seed": {
        "type": "bool",
        "default": "one slot in every four",
        "valid": "false|true",
    },
}

# Joint (height, width, seed count) profiles from all four train inputs and the
# held-out test input.  Palette size is seed count + {background, frame} because
# canonical seeds are distinct.
_CANONICAL_PROFILES: tuple[tuple[int, int, int], ...] = (
    (7, 9, 3),
    (8, 8, 2),
    (9, 10, 3),
    (8, 9, 3),
    (9, 9, 3),
)
_CANONICAL_PROFILE_KEYS = set(_CANONICAL_PROFILES)
_GENERALIZED_PROFILE = {
    None: (10, 12, 4),
    "easy": (7, 8, 4),
    "medium": (10, 12, 4),
    "hard": (13, 15, 4),
}
_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_NON_GRAY_SEED_COLORS = tuple(color for color in _SEED_COLORS if color != 5)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lower, upper in (
        ("grid_h", 7, 13),
        ("grid_w", 8, 15),
        ("n_seeds", 2, 4),
    ):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")
    gray = overrides.get("include_gray_seed")
    if gray is not None and type(gray) is not bool:
        raise ValueError("include_gray_seed must be a boolean")


def _draw_int_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Record a scheduled exact axis while preserving its whole override range."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_bool_axis(ctx, overrides, name: str, default: bool) -> bool:
    if overrides.get(name) is not None:
        return bool(ctx.draw_choice(name, (False, True)))
    return bool(ctx.draw_choice(name, (default,)))


def _scheduled_profile(sample_index: int, difficulty: str | None) -> tuple[int, int, int, bool]:
    """Every four-example window covers gray-seed, 2-seed, and 4-seed cases."""
    index = int(sample_index)
    slot = index % EXAMPLES_NEEDED
    block = index // EXAMPLES_NEEDED
    if slot == 0:
        # Rotate through all canonical linked profiles over successive lessons.
        h, w, n_seeds = _CANONICAL_PROFILES[block % len(_CANONICAL_PROFILES)]
        include_gray = False
    elif slot == 1:
        # Canonical gray-seed profile: this kills the tempting "5 is never a seed" shortcut.
        h, w, n_seeds = _CANONICAL_PROFILES[2]
        include_gray = True
    elif slot == 2:
        h, w, n_seeds = _CANONICAL_PROFILES[1]
        include_gray = False
    else:
        h, w, n_seeds = _GENERALIZED_PROFILE[difficulty]
        include_gray = False
    return h, w, n_seeds, include_gray


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty list or tuple")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row:
                raise ValueError("grid rows must be non-empty")
            try:
                result.append([int(value) for value in row])
            except ValueError as exc:
                raise ValueError("string rows must contain ARC digits") from exc
        elif isinstance(row, (list, tuple)) and row:
            result.append(list(row))
        else:
            raise ValueError("grid rows must be non-empty lists, tuples, or digit strings")
    return result


def _distance(seed: tuple[int, int, int], row: int, col: int) -> int:
    return abs(row - seed[0]) + abs(col - seed[1])


def _ownership_metrics(
    height: int,
    width: int,
    seeds: Iterable[tuple[int, int, int]],
) -> dict[str, Any]:
    seed_list = tuple(seeds)
    seed_positions = {(row, col) for row, col, _color in seed_list}
    tie_cells: list[tuple[int, int]] = []
    unique_cells: list[tuple[int, int, int]] = []
    owner_counts = [0] * len(seed_list)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if (row, col) in seed_positions:
                continue
            distances = [_distance(seed, row, col) for seed in seed_list]
            minimum = min(distances)
            owners = [index for index, value in enumerate(distances) if value == minimum]
            if len(owners) >= 2:
                tie_cells.append((row, col))
            else:
                owner = owners[0]
                owner_counts[owner] += 1
                unique_cells.append((row, col, owner))
    return {
        "tie_cells": tuple(tie_cells),
        "unique_cells": tuple(unique_cells),
        "owner_counts": tuple(owner_counts),
    }


def _distance_model_disagreement_count(
    height: int,
    width: int,
    seeds: Iterable[tuple[int, int, int]],
) -> int:
    """Count empty cells whose visible Manhattan and Euclidean colors differ."""
    seed_list = tuple(seeds)
    seed_positions = {(row, col) for row, col, _color in seed_list}
    disagreement_count = 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if (row, col) in seed_positions:
                continue
            manhattan_distances = [_distance(seed, row, col) for seed in seed_list]
            euclidean_distances = [
                (row - seed[0]) ** 2 + (col - seed[1]) ** 2
                for seed in seed_list
            ]
            manhattan_minimum = min(manhattan_distances)
            euclidean_minimum = min(euclidean_distances)
            manhattan_owners = [
                index
                for index, value in enumerate(manhattan_distances)
                if value == manhattan_minimum
            ]
            euclidean_owners = [
                index
                for index, value in enumerate(euclidean_distances)
                if value == euclidean_minimum
            ]
            manhattan_color = (
                5
                if len(manhattan_owners) >= 2
                else seed_list[manhattan_owners[0]][2]
            )
            euclidean_color = (
                5
                if len(euclidean_owners) >= 2
                else seed_list[euclidean_owners[0]][2]
            )
            disagreement_count += manhattan_color != euclidean_color
    return disagreement_count


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"], "grid": values}
    height = len(values)
    if not 7 <= height <= 13:
        errors.append(f"grid height must be in 7..13, got {height}")
    if not 8 <= width <= 15:
        errors.append(f"grid width must be in 8..15, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}

    for row in range(height):
        for col in range(width):
            if row in (0, height - 1) or col in (0, width - 1):
                if values[row][col] != 8:
                    errors.append(f"border cell ({row},{col}) must be cyan (8)")
                    # One structural finding is sufficient and keeps mutation logs concise.
                    break
        if errors and errors[-1].startswith("border cell"):
            break

    interior_eights = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if values[row][col] == 8
    ]
    if interior_eights:
        errors.append("cyan (8) may appear only on the outer frame")

    seeds = [
        (row, col, values[row][col])
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if values[row][col] not in (0, 8)
    ]
    if not 2 <= len(seeds) <= 4:
        errors.append(f"expected 2-4 interior seeds, got {len(seeds)}")
    seed_colors = [color for _row, _col, color in seeds]
    if len(set(seed_colors)) != len(seed_colors):
        errors.append("seed colors must be distinct")
    zero_count = sum(
        values[row][col] == 0
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    )
    if zero_count == 0:
        errors.append("the interior must contain at least one empty zero cell")

    metrics = {
        "tie_cells": (),
        "unique_cells": (),
        "owner_counts": (),
    }
    if 2 <= len(seeds) <= 4:
        metrics = _ownership_metrics(height, width, seeds)
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "seeds": tuple(seeds),
        "seed_colors": tuple(seed_colors),
        "zero_count": zero_count,
        **metrics,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_seeds": len(analysis["seeds"]),
        "include_gray_seed": 5 in analysis["seed_colors"],
    }
    for name, actual in observed.items():
        value = requested.get(name)
        if value is not None and value != actual:
            errors.append(f"meta {name} requested {value!r}, observed {actual!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_seeds": len(analysis["seeds"]),
        "include_gray_seed": 5 in analysis["seed_colors"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    signature = (analysis["height"], analysis["width"], len(analysis["seeds"]))
    if signature not in _CANONICAL_PROFILE_KEYS:
        return [f"joint canonical profile not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    return (analysis["height"], analysis["width"], len(analysis["seeds"]))


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror of the pinned canonical Racket rule."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid Voronoi input: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in analysis["grid"]]
    seeds = analysis["seeds"]
    for row in range(1, analysis["height"] - 1):
        for col in range(1, analysis["width"] - 1):
            if output[row][col] != 0:
                continue
            distances = [_distance(seed, row, col) for seed in seeds]
            minimum = min(distances)
            nearest = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            output[row][col] = 5 if len(nearest) >= 2 else nearest[0][2]
    return output


def _euclidean_rival_output(grid) -> list[list[int]]:
    """Squared-Euclidean nearest-seed rival used only for adversarial checks."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid Voronoi input")
    output = [list(row) for row in analysis["grid"]]
    seeds = analysis["seeds"]
    for row in range(1, analysis["height"] - 1):
        for col in range(1, analysis["width"] - 1):
            if output[row][col] != 0:
                continue
            distances = [
                (row - seed[0]) ** 2 + (col - seed[1]) ** 2
                for seed in seeds
            ]
            minimum = min(distances)
            nearest = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            output[row][col] = 5 if len(nearest) >= 2 else nearest[0][2]
    return output


def _identity_rival_output(grid) -> list[list[int]]:
    return _coerce_grid(grid)


def _ignore_gray_seed_rival_output(grid) -> list[list[int]]:
    """Tempting false rule: reserve 5 for ties and ignore a gray input seed."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid Voronoi input")
    seeds = tuple(seed for seed in analysis["seeds"] if seed[2] != 5)
    if not seeds:
        return _coerce_grid(grid)
    output = [list(row) for row in analysis["grid"]]
    for row in range(1, analysis["height"] - 1):
        for col in range(1, analysis["width"] - 1):
            if output[row][col] != 0:
                continue
            distances = [_distance(seed, row, col) for seed in seeds]
            minimum = min(distances)
            nearest = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            output[row][col] = 5 if len(nearest) >= 2 else nearest[0][2]
    return output


def _no_tie_marker_rival_output(grid) -> list[list[int]]:
    """False rule: break nearest-distance ties instead of writing gray."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid Voronoi input")
    output = [list(row) for row in analysis["grid"]]
    seeds = analysis["seeds"]
    for row in range(1, analysis["height"] - 1):
        for col in range(1, analysis["width"] - 1):
            if output[row][col] != 0:
                continue
            distances = [_distance(seed, row, col) for seed in seeds]
            minimum = min(distances)
            nearest = [seed for seed, distance in zip(seeds, distances) if distance == minimum]
            if len(nearest) >= 2:
                output[row][col] = next(seed[2] for seed in nearest if seed[2] != 5)
            else:
                output[row][col] = nearest[0][2]
    return output


SEMANTIC_RIVALS = {
    "identity": _identity_rival_output,
    "ignore_gray_seed": _ignore_gray_seed_rival_output,
    "no_tie_marker": _no_tie_marker_rival_output,
    "euclidean_distance": _euclidean_rival_output,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "seed_count": len(analysis["seeds"]),
        "includes_gray_seed": 5 in analysis["seed_colors"],
        "tie_cell_count": len(analysis["tie_cells"]),
        "unique_cell_count": len(analysis["unique_cells"]),
        "min_owned_cells": min(analysis["owner_counts"]),
        "euclidean_disagreement_cells": sum(
            left != right
            for left_row, right_row in zip(rule_mirror(grid), _euclidean_rival_output(grid))
            for left, right in zip(left_row, right_row)
        ),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _candidate_positions(
    height: int,
    width: int,
    seed_colors: tuple[int, ...],
    rng,
):
    n_seeds = len(seed_colors)
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    best = None
    best_score = None
    for _attempt in range(96):
        positions = tuple(rng.sample(interior, n_seeds))
        seeds = tuple(
            (row, col, color)
            for (row, col), color in zip(positions, seed_colors)
        )
        metrics = _ownership_metrics(height, width, seeds)
        if not metrics["tie_cells"] or not metrics["unique_cells"]:
            continue
        if min(metrics["owner_counts"]) < 1:
            continue
        disagreement_cells = _distance_model_disagreement_count(
            height, width, seeds
        )
        if disagreement_cells < 1:
            continue
        # Prefer scenes with substantial ownership regions and nontrivial tie geometry.
        score = (
            min(metrics["owner_counts"]),
            min(disagreement_cells, 8),
            min(len(metrics["tie_cells"]), 8),
            len({row for row, _col in positions}) + len({col for _row, col in positions}),
        )
        if best_score is None or score > best_score:
            best = positions
            best_score = score
    if best is None:  # pragma: no cover - domains are exhaustively exercised by tests
        raise RuntimeError(
            f"could not place {n_seeds} seeds in {height}x{width} with tie, ownership, and distance-model witnesses"
        )
    return best


def _draw_seed_colors(n_seeds: int, include_gray: bool, rng) -> tuple[int, ...]:
    if include_gray:
        colors = [5, *rng.sample(_NON_GRAY_SEED_COLORS, n_seeds - 1)]
        rng.shuffle(colors)
        return tuple(colors)
    return tuple(rng.sample(_NON_GRAY_SEED_COLORS, n_seeds))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n, default_gray = _scheduled_profile(
        sample_index, difficulty
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", default_h, 7, 13)
    width = _draw_int_axis(ctx, overrides, "grid_w", default_w, 8, 15)
    n_seeds = _draw_int_axis(ctx, overrides, "n_seeds", default_n, 2, 4)
    include_gray = _draw_bool_axis(
        ctx, overrides, "include_gray_seed", default_gray
    )

    color_rng = ctx.draw_rng(f"colors|n={n_seeds}|gray={int(include_gray)}")
    colors = _draw_seed_colors(n_seeds, include_gray, color_rng)
    layout_rng = ctx.draw_rng(
        f"layout|{height}x{width}|n={n_seeds}|gray={int(include_gray)}"
    )
    positions = _candidate_positions(height, width, colors, layout_rng)

    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[0][col] = 8
        grid[height - 1][col] = 8
    for row in range(height):
        grid[row][0] = 8
        grid[row][width - 1] = 8
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color

    errors = self_check(
        grid,
        meta={
            "grid_h": height,
            "grid_w": width,
            "n_seeds": n_seeds,
            "include_gray_seed": include_gray,
        },
    )
    if errors:
        raise AssertionError("generated invalid Voronoi scene: " + "; ".join(errors))
    analysis = _analyze(grid)
    if not analysis["tie_cells"]:
        raise AssertionError("generated scene hides the tie branch")
    if min(analysis["owner_counts"]) < 1:
        raise AssertionError("generated scene contains a seed with no owned empty cell")
    if _distance_model_disagreement_count(
        analysis["height"], analysis["width"], analysis["seeds"]
    ) < 1:
        raise AssertionError("generated scene hides the Manhattan-vs-Euclidean distinction")
    return grid


def _witness(predicate):
    def wrapped(grid):
        analysis = _analyze(grid)
        return not analysis.get("errors") and bool(predicate(analysis))

    return wrapped


SEMANTIC_WITNESSES = {
    "true_manhattan_tie_cells": _witness(lambda analysis: bool(analysis["tie_cells"])),
    "euclidean_nearest_disagrees": lambda grid: (
        not _analyze(grid).get("errors")
        and _euclidean_rival_output(grid) != rule_mirror(grid)
    ),
    "unique_nearest_cells": _witness(lambda analysis: bool(analysis["unique_cells"])),
    "every_seed_owns_empty_cells": _witness(
        lambda analysis: bool(analysis["owner_counts"]) and min(analysis["owner_counts"]) >= 1
    ),
    "gray_seed_is_present": _witness(lambda analysis: 5 in analysis["seed_colors"]),
    "gray_seed_is_absent": _witness(lambda analysis: 5 not in analysis["seed_colors"]),
    "two_seed_case": _witness(lambda analysis: len(analysis["seeds"]) == 2),
    "four_seed_case": _witness(lambda analysis: len(analysis["seeds"]) == 4),
    "canonical_linked_profile": _witness(
        lambda analysis: (
            analysis["height"], analysis["width"], len(analysis["seeds"])
        ) in _CANONICAL_PROFILE_KEYS
    ),
}

WITNESS_RIVALS = {
    "true_manhattan_tie_cells": ["no_tie_marker"],
    "euclidean_nearest_disagrees": ["euclidean_distance"],
    "unique_nearest_cells": ["identity"],
    "every_seed_owns_empty_cells": ["identity"],
    "gray_seed_is_present": ["ignore_gray_seed"],
    "gray_seed_is_absent": ["identity"],
    "two_seed_case": ["identity"],
    "four_seed_case": ["identity"],
    "canonical_linked_profile": ["identity"],
}

SCHEDULE_PROFILES = (
    "canonical_rotating",
    "gray_seed",
    "two_seed",
    "generalized_four_seed",
)

def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    analysis = _analyze(pair["input"])
    if analysis.get("errors"):
        return None, [f"{label}: {error}" for error in analysis["errors"]]
    try:
        output = _coerce_grid(pair["output"])
    except ValueError as exc:
        return None, [f"{label} output: {exc}"]
    if output != rule_mirror(pair["input"]):
        return None, [f"{label} output does not implement Manhattan nearest-seed fill"]
    return analysis, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that preserve common geometry, marker, or color shortcuts."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    analyses: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, pair in enumerate(demos):
        analysis, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if analysis is not None:
            analyses.append((pair, analysis))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_analysis = _analyze(query["input"])
        reasons.extend(f"query: {error}" for error in query_analysis.get("errors", []))
    if reasons:
        return reasons

    if not any(5 in analysis["seed_colors"] for _pair, analysis in analyses):
        reasons.append("demonstrations permit the false shortcut that gray (5) is never a seed")
    if not any(analysis["tie_cells"] for _pair, analysis in analyses):
        reasons.append("demonstrations omit the nearest-distance tie branch")
    if not all(analysis["unique_cells"] for _pair, analysis in analyses):
        reasons.append("a demonstration lacks uniquely nearest cells")
    if not all(min(analysis["owner_counts"]) >= 1 for _pair, analysis in analyses):
        reasons.append("a demonstration contains a seed whose color never expands")

    seed_counts = {len(analysis["seeds"]) for _pair, analysis in analyses}
    if 2 not in seed_counts or 4 not in seed_counts:
        reasons.append("demonstrations do not span both the two-seed and four-seed cases")
    dimensions = {(analysis["height"], analysis["width"]) for _pair, analysis in analyses}
    if len(dimensions) < 3:
        reasons.append("demonstrations vary fewer than three grid dimensions")

    by_count: dict[int, set[tuple[tuple[int, ...], ...]]] = {}
    for pair, analysis in analyses:
        output = tuple(tuple(row) for row in _coerce_grid(pair["output"]))
        by_count.setdefault(len(analysis["seeds"]), set()).add(output)
    if not any(len(outputs) >= 2 for outputs in by_count.values()):
        reasons.append("count-only output prediction is not contradicted at a fixed seed count")

    if all(
        _euclidean_rival_output(pair["input"]) == _coerce_grid(pair["output"])
        for pair, _analysis in analyses
    ):
        reasons.append("Euclidean-nearest coloring remains consistent with every demonstration")
    if all(pair["input"] == _coerce_grid(pair["output"]) for pair, _analysis in analyses):
        reasons.append("the identity rule remains consistent with every demonstration")
    if all(
        sum(value != 0 for row in _coerce_grid(pair["output"]) for value in row)
        == len(analysis["seeds"]) + 2 * analysis["height"] + 2 * analysis["width"] - 4
        for pair, analysis in analyses
    ):
        reasons.append("marker-as-answer shortcut remains consistent with every demonstration")
    return reasons
