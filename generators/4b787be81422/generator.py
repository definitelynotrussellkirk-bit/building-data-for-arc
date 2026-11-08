"""Generator for ARC task 44f52bb0: classify left-right symmetry.

The Racket oracle returns ``[[1]]`` when the input is symmetric across the
vertical axis and ``[[7]]`` otherwise.  The public examples are ambiguous:
top-bottom symmetry and 180-degree rotational symmetry happen to make the same
classification on every canonical pair.  Ordinary generated lessons therefore
cycle through explicit counterexamples to both rivals, and pair positive and
negative examples with the same foreground count.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b787be81422"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4a60caa6e208"

SUMMARY = (
    "Return 1 for a binary grid with left-right reflection symmetry and 7 "
    "otherwise; generated lessons separate that rule from top-bottom, "
    "rotational, count-only, fixed-label, and color-echo shortcuts."
)

INVARIANTS = [
    "the input is a 3..8 by 3..8 rectangular ARC grid",
    "zero is the background and exactly one nonzero foreground color is present",
    "ordinary four-example windows contain both left-right-symmetric and asymmetric inputs",
    "ordinary windows contain a top-bottom-symmetric but left-right-asymmetric counterexample",
    "ordinary windows contain a 180-degree-symmetric but left-right-asymmetric counterexample",
    "a symmetric/asymmetric pair in every ordinary window has the same foreground count",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
# The authoritative rule is a binary classifier.  Declaring the complete
# finite codomain prevents generic diversity probes from mistaking the lawful
# two-grid output alphabet for constant-output training poison.
EXPECTED_OUTPUT_CODOMAIN = 2
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "paired schedule; periodic canonical 3x3 anchors plus 3..8 variants",
        "valid": "3..8",
    },
    "grid_w": {
        "type": "int",
        "default": "paired schedule; periodic canonical 3x3 anchors plus 3..8 variants",
        "valid": "3..8",
    },
    "symmetric": {
        "type": "bool",
        "default": "alternates by sample_index",
        "valid": "true|false",
    },
    "fg_color": {
        "type": "color",
        "default": "2 on canonical anchors; otherwise one of 3,4,5,6,8,9",
        "valid": "1..9",
    },
}

SCHEDULE_PROFILES = (
    "lr_symmetric_rot_pair",
    "rot180_symmetric_lr_asymmetric",
    "lr_symmetric_tb_pair",
    "top_bottom_symmetric_lr_asymmetric",
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")


def _validate_sample_index(sample_index: Any) -> None:
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the four-residue adversarial lesson schedule."""
    del seed
    _validate_sample_index(sample_index)
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: Any, options: Iterable[Any]) -> Any:
    options = tuple(options)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _is_rectangular_arc_grid(grid: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be literal ARC integers 0..9")
    return errors


def _is_lr_symmetric(grid: Any) -> bool:
    return all(tuple(row) == tuple(reversed(row)) for row in grid)


def _is_tb_symmetric(grid: Any) -> bool:
    return tuple(tuple(row) for row in grid) == tuple(
        tuple(row) for row in reversed(grid)
    )


def _is_rot180_symmetric(grid: Any) -> bool:
    return all(
        grid[r][c] == grid[len(grid) - 1 - r][len(grid[0]) - 1 - c]
        for r in range(len(grid))
        for c in range(len(grid[0]))
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _is_rectangular_arc_grid(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    palette = tuple(sorted({value for row in grid for value in row}))
    if not 3 <= height <= 8:
        errors.append(f"height {height} outside 3..8")
    if not 3 <= width <= 8:
        errors.append(f"width {width} outside 3..8")
    if 0 not in palette:
        errors.append("zero background must be present")
    nonzero = tuple(value for value in palette if value != 0)
    if len(nonzero) != 1:
        errors.append(
            "exactly one nonzero foreground color is required; "
            f"observed {list(nonzero)}"
        )
    foreground = nonzero[0] if len(nonzero) == 1 else None
    foreground_count = (
        sum(value == foreground for row in grid for value in row)
        if foreground is not None
        else 0
    )
    foreground_positions = (
        tuple(
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == foreground
        )
        if foreground is not None
        else ()
    )
    if foreground is not None and foreground_count < 2:
        errors.append("at least two foreground cells are required")
    if foreground_positions:
        occupied_rows = sorted({row for row, _ in foreground_positions})
        occupied_cols = sorted({col for _, col in foreground_positions})
        if (
            len(occupied_rows) == 1
            and occupied_cols
            == list(range(occupied_cols[0], occupied_cols[-1] + 1))
        ):
            errors.append("a single contiguous horizontal line is degenerate")
        if (
            len(foreground_positions) == 4
            and len(occupied_rows) == 2
            and len(occupied_cols) == 2
            and occupied_rows[1] == occupied_rows[0] + 1
            and occupied_cols[1] == occupied_cols[0] + 1
        ):
            errors.append("a solid 2x2 foreground block is degenerate")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "fg_color": foreground,
        "foreground_count": foreground_count,
        "foreground_positions": foreground_positions,
        "symmetric": _is_lr_symmetric(grid),
        "top_bottom_symmetric": _is_tb_symmetric(grid),
        "rot180_symmetric": _is_rot180_symmetric(grid),
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "symmetric": analysis["symmetric"],
        "fg_color": analysis["fg_color"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the canonical-compatible binary-grid input grammar."""
    errors: list[str] = []
    try:
        _band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))
    analysis = _analysis(grid)
    errors.extend(analysis["errors"])
    if analysis["errors"]:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: Any) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid symmetry-classification grid: " + "; ".join(errors))
    return [[1 if _is_lr_symmetric(grid) else 7]]


def _rival_always_symmetric(grid: Any) -> list[list[int]]:
    del grid
    return [[1]]


def _rival_always_asymmetric(grid: Any) -> list[list[int]]:
    del grid
    return [[7]]


def _rival_top_bottom(grid: Any) -> list[list[int]]:
    return [[1 if _is_tb_symmetric(grid) else 7]]


def _rival_rot180(grid: Any) -> list[list[int]]:
    return [[1 if _is_rot180_symmetric(grid) else 7]]


def _rival_even_foreground_count(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for count rival")
    return [[1 if analysis["foreground_count"] % 2 == 0 else 7]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_symmetric": _rival_always_symmetric,
    "always_asymmetric": _rival_always_asymmetric,
    "top_bottom_symmetry": _rival_top_bottom,
    "rot180_symmetry": _rival_rot180,
    "even_foreground_count": _rival_even_foreground_count,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "top_bottom_symmetry": _rival_top_bottom,
    "rot180_symmetry": _rival_rot180,
}


def _witness_lr_not_tb_or_rot(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["symmetric"]
        and not analysis["top_bottom_symmetric"]
        and not analysis["rot180_symmetric"]
    )


def _witness_tb_not_lr(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["top_bottom_symmetric"]
        and not analysis["symmetric"]
    )


def _witness_rot_not_lr(grid: Any) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["rot180_symmetric"]
        and not analysis["symmetric"]
    )


SEMANTIC_WITNESSES = {
    "lr_symmetric_not_tb_or_rot180": _witness_lr_not_tb_or_rot,
    "top_bottom_symmetric_lr_asymmetric": _witness_tb_not_lr,
    "rot180_symmetric_lr_asymmetric": _witness_rot_not_lr,
}
WITNESS_RIVALS = {
    "lr_symmetric_not_tb_or_rot180": [
        "top_bottom_symmetry",
        "rot180_symmetry",
    ],
    "top_bottom_symmetric_lr_asymmetric": ["top_bottom_symmetry"],
    "rot180_symmetric_lr_asymmetric": ["rot180_symmetry"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require every four-demo window to eliminate the named plausible rivals."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    labels: set[int] = set()
    colors: set[int] = set()
    count_to_labels: dict[int, set[int]] = {}
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match left-right symmetry")
            continue
        label = expected[0][0]
        labels.add(label)
        colors.add(analysis["fg_color"])
        count_to_labels.setdefault(analysis["foreground_count"], set()).add(label)
        valid_demos.append(demo)

    if labels != {1, 7}:
        reasons.append("demonstrations must include both output labels 1 and 7")
    if len(colors) < 2:
        reasons.append("demonstrations must vary foreground color")
    if not any(values == {1, 7} for values in count_to_labels.values()):
        reasons.append(
            "demonstrations need equal-foreground-count examples with opposite labels"
        )
    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _lr_orbits(height: int, width: int) -> tuple[frozenset[tuple[int, int]], ...]:
    return tuple(
        frozenset(((row, col), (row, width - 1 - col)))
        for row in range(height)
        for col in range(width // 2)
    )


def _tb_orbits(height: int, width: int) -> tuple[frozenset[tuple[int, int]], ...]:
    return tuple(
        frozenset(((row, col), (height - 1 - row, col)))
        for row in range(height // 2)
        for col in range(width)
    )


def _rot180_orbits(
    height: int, width: int
) -> tuple[frozenset[tuple[int, int]], ...]:
    seen: set[tuple[int, int]] = set()
    orbits: list[frozenset[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen:
                continue
            partner = (height - 1 - row, width - 1 - col)
            orbit = frozenset(((row, col), partner))
            seen.update(orbit)
            if len(orbit) == 2:
                orbits.append(orbit)
    return tuple(orbits)


def _select_orbits(
    orbits: tuple[frozenset[tuple[int, int]], ...],
    *,
    mandatory: frozenset[tuple[int, int]],
    forbidden: frozenset[tuple[int, int]],
    count: int,
    rng,
) -> tuple[frozenset[tuple[int, int]], ...]:
    if mandatory not in orbits or forbidden not in orbits:
        raise ValueError("required adversarial orbit is unavailable")
    candidates = [orbit for orbit in orbits if orbit not in (mandatory, forbidden)]
    if not 1 <= count <= 1 + len(candidates):
        raise ValueError(
            f"cannot select {count} orbits from {len(orbits)} with one forbidden"
        )
    selected = [mandatory]
    if count > 1:
        selected.extend(rng.sample(candidates, count - 1))
    return tuple(selected)


def _paint_orbits(
    height: int,
    width: int,
    color: int,
    orbits: Iterable[frozenset[tuple[int, int]]],
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for orbit in orbits:
        for row, col in orbit:
            grid[row][col] = color
    return grid


def _scheduled_defaults(seed: int, pair_group: int, band: str) -> tuple[int, int, int]:
    """Return paired dimensions/color with periodic canonical-profile anchors."""
    if pair_group % 4 == 1:
        return 3, 3, 2
    rng = stable_rng(seed, f"{TASK_ID}|pair:{pair_group}|defaults:{band}", VERSION)
    ranges = {
        "easy": (3, 5),
        "medium": (4, 7),
        "hard": (5, 8),
    }
    lo, hi = ranges[band]
    height = rng.randint(lo, hi)
    width = rng.randint(lo, hi)
    # Adjacent pair groups draw from disjoint palettes, so every four-demo
    # sliding window varies color without relying on the anchor frequency.
    palette = (3, 4, 5) if pair_group % 2 == 0 else (6, 8, 9)
    color = rng.choice(palette)
    return height, width, color


def _pair_count(seed: int, pair_group: int, band: str, maximum: int) -> int:
    if pair_group % 4 == 1:
        return 1 + ((pair_group // 2) % min(2, maximum))
    rng = stable_rng(seed, f"{TASK_ID}|pair:{pair_group}|count:{band}", VERSION)
    if band == "easy":
        low, high = 1, min(3, maximum)
    elif band == "hard":
        low, high = max(2, maximum // 2), maximum
    else:
        low, high = min(2, maximum), min(6, maximum)
    return rng.randint(low, high)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for name in ("grid_h", "grid_w", "fg_color"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"override {name!r} must be an integer, got {value!r}")
    if "symmetric" in overrides and overrides["symmetric"] is not None:
        if not isinstance(overrides["symmetric"], bool):
            raise TypeError(
                "override 'symmetric' must be a bool, "
                f"got {overrides['symmetric']!r}"
            )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_seed(seed)
    _validate_sample_index(sample_index)
    _validate_overrides(overrides)
    band = _band(difficulty)
    pair_group = sample_index // 2
    scheduled_h, scheduled_w, scheduled_color = _scheduled_defaults(
        seed, pair_group, band
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 3, 8)
    width = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 3, 8)
    color = _draw_scheduled_choice(ctx, "fg_color", scheduled_color, range(1, 10))
    symmetric = bool(
        _draw_scheduled_choice(
            ctx, "symmetric", sample_index % 2 == 0, (True, False)
        )
    )

    lr_orbits = _lr_orbits(height, width)
    relation_orbits = (
        _rot180_orbits(height, width) if pair_group % 2 == 0
        else _tb_orbits(height, width)
    )
    maximum = min(
        min(len(lr_orbits), len(relation_orbits)) - 1,
        (height * width - 1) // 4,
    )
    count = _pair_count(seed, pair_group, band, maximum)

    if symmetric:
        mandatory = frozenset(((0, 0), (0, width - 1)))
        forbidden = frozenset(((height - 1, 0), (height - 1, width - 1)))
        selected = _select_orbits(
            lr_orbits,
            mandatory=mandatory,
            forbidden=forbidden,
            count=count,
            rng=ctx.draw_rng("lr_orbit_selection"),
        )
        # A full contiguous foreground row is a lawful binary grid but a poor
        # teaching example: it collapses object structure to a trivial stripe.
        # Keep multi-orbit positive examples spread over at least two rows so
        # self_check can reject that degenerate grammar without generation
        # retries or hidden fallback behavior.
        selected_cells = set().union(*selected)
        if len(selected) > 1 and len({row for row, _ in selected_cells}) == 1:
            replacement = next(
                orbit
                for orbit in lr_orbits
                if orbit not in selected
                and orbit != forbidden
                and any(row != 0 for row, _ in orbit)
            )
            selected = selected[:-1] + (replacement,)
    elif pair_group % 2 == 0:
        mandatory = frozenset(((0, 0), (height - 1, width - 1)))
        forbidden = frozenset(((0, width - 1), (height - 1, 0)))
        selected = _select_orbits(
            relation_orbits,
            mandatory=mandatory,
            forbidden=forbidden,
            count=count,
            rng=ctx.draw_rng("rot180_orbit_selection"),
        )
    else:
        mandatory = frozenset(((0, 0), (height - 1, 0)))
        forbidden = frozenset(((0, width - 1), (height - 1, width - 1)))
        selected = _select_orbits(
            relation_orbits,
            mandatory=mandatory,
            forbidden=forbidden,
            count=count,
            rng=ctx.draw_rng("tb_orbit_selection"),
        )

    grid = _paint_orbits(height, width, int(color), selected)
    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid grid: " + "; ".join(errors))
    if _is_lr_symmetric(grid) != symmetric:
        raise AssertionError("generated symmetry status does not match requested axis")
    return grid
