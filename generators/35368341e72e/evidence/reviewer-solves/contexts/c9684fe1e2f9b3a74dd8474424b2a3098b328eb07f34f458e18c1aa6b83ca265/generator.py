"""Constructive generator for prototype lookup by a bottom-row query.

The top row contains distinct key colors.  The three rows beneath each key
store a fixed-width 3x3 prototype.  Reading the nonzero values in the final
row from left to right gives the query; the output concatenates the selected
prototypes with one background column between copies.
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "35368341e72e"
VERSION = "3.0.0"
RULE_HASH = "dfe1312c69fd"

SUMMARY = (
    "Distinct keys in row 0 label 3x3 prototypes in rows 1-3.  The nonzero "
    "keys in the final row form an ordered query, and the answer galleries "
    "the corresponding prototypes with one zero column between copies."
)

INVARIANTS = [
    "row 0 contains one to three distinct keys whose 3-column bands do not overlap",
    "each key labels a fixed 3x3 prototype in rows 1-3 (which may be all background)",
    "all rows between the prototypes and final query row are background",
    "the final row contains two or three query entries, each naming a declared key",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "difficulty-weighted", "valid": "11..20"},
    "n_keys": {"type": "int", "default": "difficulty-weighted", "valid": "1..3"},
    "query_len": {"type": "int", "default": "difficulty-weighted", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical_anchor", "exploration")

_AXIS_VALUES = {
    "grid_h": tuple(range(5, 13)),
    "grid_w": tuple(range(11, 21)),
    "n_keys": (1, 2, 3),
    "query_len": (2, 3),
}


def _band_name(difficulty) -> str:
    if difficulty in {"easy", "medium", "hard"}:
        return difficulty
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        if difficulty < 0.34:
            return "easy"
        if difficulty < 0.67:
            return "medium"
        return "hard"
    return "medium"


def _weighted_options(axis: str, difficulty) -> tuple[int, ...]:
    """Return a full-domain choice list whose multiplicities encode difficulty."""
    band = _band_name(difficulty)
    base = _AXIS_VALUES[axis]
    weights = {
        "easy": {
            "grid_h": (6, 6, 6, 6, 6, 6),
            "grid_w": (11, 11, 11, 11, 11, 11),
            "n_keys": (3, 3, 3, 3, 3),
            "query_len": (2, 2, 2, 3),
        },
        "medium": {
            "grid_h": (6, 6, 6, 6, 7, 8),
            "grid_w": (11, 11, 11, 11, 13, 15),
            "n_keys": (3, 3, 3, 3, 2),
            "query_len": (3, 3, 3, 2),
        },
        "hard": {
            "grid_h": (6, 6, 6, 9, 10, 11, 12),
            "grid_w": (11, 11, 11, 14, 16, 18, 20),
            "n_keys": (3, 3, 3, 3, 3, 2),
            "query_len": (3, 3, 3, 2),
        },
    }
    return base + weights[band][axis]


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Reserve a small deterministic slice for exact canonical-scale anchors."""
    return "canonical_anchor" if seed % 3 == 0 else "exploration"


def _axis_options(axis: str, seed: int, sample_index: int, difficulty, overrides: dict):
    anchor_values = {"grid_h": 6, "grid_w": 11, "n_keys": 3, "query_len": 3}
    if schedule_profile(seed, sample_index, difficulty) == "canonical_anchor" and overrides.get(axis) is None:
        return (anchor_values[axis],)
    return _weighted_options(axis, difficulty)


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if value not in _AXIS_VALUES[name]:
            lo, hi = _AXIS_VALUES[name][0], _AXIS_VALUES[name][-1]
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _key_column_choices(width: int, count: int) -> tuple[tuple[int, ...], ...]:
    choices = tuple(
        cols
        for cols in combinations(range(1, width - 1), count)
        if all(right - left >= 3 for left, right in zip(cols, cols[1:]))
    )
    if not choices:  # Defensive: current public ranges always have choices.
        raise ValueError(f"cannot place {count} non-overlapping key bands in width {width}")
    return choices


def _prototype_masks(rng, count: int) -> list[int]:
    candidates = [mask for mask in range(1, 1 << 9) if 3 <= mask.bit_count() <= 7]
    return rng.sample(candidates, count)


def _query_sequence(rng, keys: list[int], length: int) -> list[int]:
    """Make the repeated-key branch explicit so lessons refute deduplication."""
    repeated = rng.choice(keys)
    query = [repeated, repeated]
    for key in keys:
        if len(query) >= length:
            break
        if key != repeated:
            query.append(key)
    while len(query) < length:
        query.append(rng.choice(keys))
    rng.shuffle(query)
    return query


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_choice(
        "grid_h", _axis_options("grid_h", seed, sample_index, difficulty, overrides)
    )
    width = ctx.draw_choice(
        "grid_w", _axis_options("grid_w", seed, sample_index, difficulty, overrides)
    )
    n_keys = ctx.draw_choice(
        "n_keys", _axis_options("n_keys", seed, sample_index, difficulty, overrides)
    )
    query_len = ctx.draw_choice(
        "query_len", _axis_options("query_len", seed, sample_index, difficulty, overrides)
    )

    layout_rng = ctx.draw_rng("layout")
    key_cols = list(layout_rng.choice(_key_column_choices(width, n_keys)))

    # Use one or two prototype colors in addition to the key colors.  With the
    # canonical 6x11 / three-key branch this yields the canonical 5/6-color
    # profiles while retaining shape and color diversity elsewhere.
    prototype_palette_size = 1 + layout_rng.randrange(2)
    palette = layout_rng.sample(range(1, 10), n_keys + prototype_palette_size)
    keys = palette[:n_keys]
    prototype_colors = palette[n_keys:]
    masks = _prototype_masks(layout_rng, n_keys)

    grid = full_grid(height, width, 0)
    for index, (col, key, mask) in enumerate(zip(key_cols, keys, masks)):
        grid[0][col] = key
        selected = [position for position in range(9) if mask & (1 << position)]
        for local_index, position in enumerate(selected):
            row = 1 + position // 3
            cell_col = col - 1 + position % 3
            color = prototype_colors[(local_index + index) % len(prototype_colors)]
            grid[row][cell_col] = color

    query = _query_sequence(layout_rng, keys, query_len)
    query_cols = sorted(layout_rng.sample(range(width), query_len))
    for col, key in zip(query_cols, query):
        grid[-1][col] = key
    return grid


def _grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], 0, 0
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"], 0, 0
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width
    errors = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer color 0..9"
                )
                return errors, len(grid), width
    return errors, len(grid), width


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete prototype-dictionary input grammar."""
    errors, height, width = _grid_errors(grid)
    if errors:
        return errors
    if height < 5:
        errors.append(f"grid has {height} rows; need row 0, three prototype rows, and query")
    if width < 3:
        errors.append(f"grid has {width} columns; 3x3 prototypes cannot fit")
    if errors:
        return errors

    key_entries = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if not 1 <= len(key_entries) <= 3:
        errors.append(f"row 0 must contain 1..3 keys, found {len(key_entries)}")
        return errors
    key_cols = [col for col, _ in key_entries]
    keys = [value for _, value in key_entries]
    if len(set(keys)) != len(keys):
        errors.append("row-0 key colors must be distinct")
    if any(col == 0 or col == width - 1 for col in key_cols):
        errors.append("each key must have one prototype column on both sides")
    if any(right - left < 3 for left, right in zip(key_cols, key_cols[1:])):
        errors.append("key prototype bands overlap")

    legal_proto_cols = {
        col + delta for col in key_cols for delta in (-1, 0, 1) if 0 <= col + delta < width
    }
    for row in range(1, 4):
        for col, value in enumerate(grid[row]):
            if value != 0 and col not in legal_proto_cols:
                errors.append(f"prototype cell ({row},{col}) lies outside every key band")
                break
    for row in range(4, height - 1):
        if any(value != 0 for value in grid[row]):
            errors.append(f"intermediate row {row} must be all background")
            break

    query = [value for value in grid[-1] if value != 0]
    if not query:
        errors.append("last row must contain at least one query key")
    elif len(query) > 5:
        errors.append(f"last row contains {len(query)} query keys; expected at most 5")
    unknown = sorted(set(query) - set(keys))
    if unknown:
        errors.append(f"query contains undeclared key color(s): {unknown}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _prototype_lookup(grid) -> dict[int, list[list[int]]]:
    return {
        value: [row[col - 1 : col + 2] for row in grid[1:4]]
        for col, value in enumerate(grid[0])
        if value != 0
    }


def _gallery(parts: list[list[list[int]]]) -> list[list[int]]:
    if not parts:
        return [[0]]
    output = full_grid(3, 4 * len(parts) - 1, 0)
    for index, part in enumerate(parts):
        left = 4 * index
        for row in range(3):
            for col in range(3):
                if part[row][col] != 0:
                    output[row][left + col] = part[row][col]
    return output


def rule_mirror(grid) -> list[list[int]]:
    prototypes = _prototype_lookup(grid)
    query = [value for value in grid[-1] if value != 0]
    return _gallery([prototypes[value] for value in query])


def _deduplicate_query(grid) -> list[list[int]]:
    prototypes = _prototype_lookup(grid)
    seen: set[int] = set()
    query = []
    for value in grid[-1]:
        if value != 0 and value not in seen:
            seen.add(value)
            query.append(value)
    return _gallery([prototypes[value] for value in query])


def _has_repeated_query(grid) -> bool:
    if self_check(grid):
        return False
    query = [value for value in grid[-1] if value != 0]
    return len(query) > len(set(query))


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "repeated_query": _has_repeated_query,
}
SEMANTIC_RIVALS: dict[str, Callable] = {
    "deduplicate_query": _deduplicate_query,
}
WITNESS_RIVALS = {
    "repeated_query": ["deduplicate_query"],
}
CANONICAL_SHORTCUTS: dict[str, Callable] = {
    "deduplicate_query": _deduplicate_query,
}
LESSON_COMPETITORS: dict[str, Callable] = {
    "deduplicate_query": _deduplicate_query,
}


def lesson_identifiable(demos, query) -> list[str]:
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            findings.append(f"competitor {name!r} fits every demonstration but changes the query")
    return findings


def observe_overrides(grid) -> dict[str, int]:
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe malformed grid: " + "; ".join(findings[:3]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_keys": sum(value != 0 for value in grid[0]),
        "query_len": sum(value != 0 for value in grid[-1]),
    }
