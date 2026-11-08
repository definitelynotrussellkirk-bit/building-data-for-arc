"""Semantic generator for ARC task 997c17fd6870 (source 8ee62060).

Partition every row into adjacent two-column tiles.  Reverse the horizontal
order of those tiles while preserving the left/right order inside each tile.
The calibrated curriculum uses repeated 2x2 motifs on a macro-grid, matching
the four published diagonal families and three controlled extrapolations.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "997c17fd6870"
TASK_ID = "997c17fd6870"
VERSION = "3.0.0"
RULE_HASH = "7ac779229e5e"
SUMMARY = "Reverse the order of adjacent two-column tiles without reflecting the contents inside each tile."
INVARIANTS = [
    "the calibrated input is an even square macro-grid of 2x2 cells on black",
    "every occupied macro-cell contains one of the demonstrated asymmetric two-color motifs",
    "official-family scenes repeat one motif down the main macro diagonal",
    "general scenes vary motifs, permute their columns, or add extra occupied macro-cells",
    "the output reverses macro columns and preserves every 2x2 motif byte-exactly",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = ("diagonal_varied", "permuted_tiles", "multi_tiles")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four official diagonal families plus three controlled extrapolations",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_KIND_TO_PUBLIC = {
    "hook": "public_1",
    "corner": "public_2",
    "gap": "public_3",
    "checker": "public_4",
}
_PUBLIC_TO_KIND = {value: key for key, value in _KIND_TO_PUBLIC.items()}


def _motif(kind, first, second):
    if kind == "hook":
        return [[first, first], [second, first]]
    if kind == "corner":
        return [[first, 0], [second, second]]
    if kind == "gap":
        return [[first, second], [second, 0]]
    if kind == "checker":
        return [[first, second], [second, first]]
    raise ValueError(f"unknown motif kind: {kind!r}")


def _macro_grid(n_pairs, placements):
    """Render ``(macro_row, macro_col, 2x2 motif)`` placements."""
    grid = [[0] * (2 * n_pairs) for _ in range(2 * n_pairs)]
    for macro_row, macro_col, motif in placements:
        row0, col0 = 2 * macro_row, 2 * macro_col
        for dr in range(2):
            for dc in range(2):
                grid[row0 + dr][col0 + dc] = motif[dr][dc]
    return grid


def _diagonal_grid(n_pairs, motifs, *, row0=0, col0=0, step=1):
    return _macro_grid(
        n_pairs,
        [(row0 + index, col0 + step * index, motifs[index]) for index in range(len(motifs))],
    )


_PUBLIC_SPECS = {
    "public_1": (6, _motif("hook", 2, 3), -1),
    "public_2": (6, _motif("corner", 8, 2), 1),
    "public_3": (5, _motif("gap", 2, 1), 1),
    "public_4": (7, _motif("checker", 1, 8), -1),
}
_PUBLIC_INPUTS = {
    profile: _diagonal_grid(
        n_pairs,
        [[row[:] for row in motif] for _ in range(n_pairs)],
        col0=0 if step == 1 else n_pairs - 1,
        step=step,
    )
    for profile, (n_pairs, motif, step) in _PUBLIC_SPECS.items()
}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 2 <= len(grid[0]) <= 30:
        return ["input must contain two through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    if width % 2:
        return ["the executable rule requires an even number of columns"]
    return []


def rule_mirror(grid):
    """Exact Python mirror of the broad executable Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = len(grid[0])
    return [
        [value for start in range(width - 2, -1, -2) for value in row[start:start + 2]]
        for row in grid
    ]


def _tile_kind(tile):
    values = [value for row in tile for value in row]
    colors = sorted({value for value in values if value})
    if len(colors) != 2:
        return None
    for first in colors:
        second = colors[1] if first == colors[0] else colors[0]
        for kind in _KIND_TO_PUBLIC:
            if tile == _motif(kind, first, second):
                return kind
    return None


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def _strict_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return errors, None
    height, width = len(grid), len(grid[0])
    if height != width or height % 2 or not 6 <= height <= 20:
        errors.append("calibrated scenes must be even square grids from 6x6 through 20x20")
        return errors, None
    n_pairs = height // 2
    occupied = {}
    kinds = {}
    for macro_row in range(n_pairs):
        for macro_col in range(n_pairs):
            tile = [
                grid[2 * macro_row][2 * macro_col:2 * macro_col + 2],
                grid[2 * macro_row + 1][2 * macro_col:2 * macro_col + 2],
            ]
            if all(value == 0 for row in tile for value in row):
                continue
            kind = _tile_kind(tile)
            if kind is None:
                errors.append("every occupied macro-cell must be a demonstrated asymmetric two-color motif")
                return errors, None
            occupied[(macro_row, macro_col)] = tile
            kinds[(macro_row, macro_col)] = kind
    if len(occupied) < 3:
        errors.append("calibrated scenes require at least three occupied motifs")
    colors = {value for row in grid for value in row if value}
    if len(colors) != 2:
        errors.append("calibrated scenes must use exactly two nonzero motif colors")
    output = rule_mirror(grid)
    if output == [list(row) for row in grid]:
        errors.append("the two-column tile reversal must visibly change the lesson")
    changed_cells = sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    )
    if changed_cells * 20 < height * width:
        errors.append("the tile reversal must alter at least five percent of the calibrated canvas")
    facts = {
        "n_pairs": n_pairs,
        "occupied": occupied,
        "kinds": kinds,
        "occupied_count": len(occupied),
        "colors": colors,
        "changed_cells": changed_cells,
        "output": output,
    }
    return errors, facts


def _diagonal_run(positions):
    if len(positions) < 3:
        return False
    ordered = sorted(positions)
    rows = [row for row, _ in ordered]
    cols = [col for _, col in ordered]
    return rows == list(range(rows[0], rows[0] + len(rows))) and (
        cols == list(range(cols[0], cols[0] + len(cols)))
        or cols == list(range(cols[0], cols[0] - len(cols), -1))
    )


def _recover_profile(grid, facts):
    literal = canonical_profile_signature(grid)
    if literal is not None:
        return literal
    n_pairs = facts["n_pairs"]
    positions = sorted(facts["occupied"])
    if _diagonal_run(positions):
        tiles = [facts["occupied"][position] for position in positions]
        kinds = [facts["kinds"][position] for position in positions]
        if all(tile == tiles[0] for tile in tiles):
            return _KIND_TO_PUBLIC[kinds[0]]
        if len({tuple(map(tuple, tile)) for tile in tiles}) >= 2:
            return "diagonal_varied"
    row_counts = [sum(row == macro_row for row, _ in positions) for macro_row in range(n_pairs)]
    col_counts = [sum(col == macro_col for _, col in positions) for macro_col in range(n_pairs)]
    if all(count == 1 for count in row_counts + col_counts):
        return "permuted_tiles"
    if len(positions) > n_pairs and max(row_counts + col_counts) >= 2:
        return "multi_tiles"
    return None


def _analysis(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": facts, "output": None}
    profile = _recover_profile(grid, facts)
    if profile not in SCENE_PROFILES:
        errors.append("macro-grid does not match a declared official or generalized scene profile")
    return {
        "errors": errors,
        "scene_profile": profile,
        "facts": facts,
        "output": None if errors else facts["output"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Every selected training draw stays on the calibrated task manifold."""
    return self_check(grid)


def _identity_rival(grid):
    return [list(row) for row in grid]


def _whole_row_reflection_rival(grid):
    return [list(reversed(row)) for row in grid]


def _tile_order_changes(grid):
    return not self_check(grid) and rule_mirror(grid) != _identity_rival(grid)


def _internal_tile_order_is_preserved(grid):
    return (
        not self_check(grid)
        and rule_mirror(grid) != _whole_row_reflection_rival(grid)
    )


SEMANTIC_RIVALS = {
    "identity": _identity_rival,
    "whole_row_reflection": _whole_row_reflection_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {}
SEMANTIC_WITNESSES = {
    "tile_order_changes": _tile_order_changes,
    "internal_tile_order_is_preserved": _internal_tile_order_is_preserved,
}
WITNESS_RIVALS = {
    "tile_order_changes": ["identity"],
    "internal_tile_order_is_preserved": ["whole_row_reflection"],
}


def lesson_identifiable(demos, query):
    """Reject malformed labels and any finite rival surviving the demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input violates teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output differs from the selected rule")
        valid_demos.append(demo)

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input violates teaching grammar: {query_errors[0]}")
        return reasons
    expected_query = rule_mirror(query["input"])
    if query["output"] != expected_query:
        reasons.append("query output differs from the selected rule")

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            try:
                if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                    if rival(query["input"]) != query["output"]:
                        reasons.append(
                            f"competitor {name} fits every demo and changes the query answer"
                        )
            except Exception as exc:
                reasons.append(f"competitor {name} errored: {type(exc).__name__}: {exc}")
    return reasons


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES else None


def _limits(difficulty):
    if difficulty == "easy":
        return 3, 6
    if difficulty == "medium":
        return 5, 8
    if difficulty == "hard":
        return 7, 10
    return 4, 8


def _colors(rng):
    return rng.sample(range(1, 10), 2)


def _public_nuisance(profile, difficulty, rng):
    low, high = _limits(difficulty)
    kind = _PUBLIC_TO_KIND[profile]
    for _ in range(80):
        n_pairs = rng.randint(low, high)
        run_length = rng.randint(3, n_pairs)
        row0 = rng.randint(0, n_pairs - run_length)
        step = rng.choice((-1, 1))
        col0 = rng.randint(0, n_pairs - run_length)
        if step == -1:
            col0 += run_length - 1
        first, second = _colors(rng)
        motif = _motif(kind, first, second)
        grid = _diagonal_grid(
            n_pairs,
            [[row[:] for row in motif] for _ in range(run_length)],
            row0=row0,
            col0=col0,
            step=step,
        )
        analysis = _analysis(grid)
        if analysis["errors"] or analysis["scene_profile"] != profile:
            continue
        if canonical_profile_signature(grid) is None:
            return grid
    raise AssertionError(f"could not construct nonliteral official-family profile {profile!r}")


def _diagonal_varied(n_pairs, first, second, rng):
    kinds = list(_KIND_TO_PUBLIC)
    rng.shuffle(kinds)
    chosen = [kinds[index % len(kinds)] for index in range(n_pairs)]
    rng.shuffle(chosen)
    if len(set(chosen)) < 2:
        chosen[-1] = kinds[1]
    return _diagonal_grid(n_pairs, [_motif(kind, first, second) for kind in chosen])


def _permuted_tiles(n_pairs, first, second, rng):
    columns = list(range(n_pairs))
    for _ in range(80):
        rng.shuffle(columns)
        if columns != list(range(n_pairs)):
            break
    kinds = list(_KIND_TO_PUBLIC)
    placements = [
        (row, columns[row], _motif(rng.choice(kinds), first, second))
        for row in range(n_pairs)
    ]
    return _macro_grid(n_pairs, placements)


def _multi_tiles(n_pairs, first, second, rng):
    kinds = list(_KIND_TO_PUBLIC)
    positions = {(index, index) for index in range(n_pairs)}
    target = n_pairs + rng.randint(max(1, n_pairs // 2), n_pairs)
    while len(positions) < target:
        positions.add((rng.randrange(n_pairs), rng.randrange(n_pairs)))
    placements = [
        (row, col, _motif(rng.choice(kinds), first, second))
        for row, col in sorted(positions)
    ]
    return _macro_grid(n_pairs, placements)


def _general_scene(profile, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(120):
        n_pairs = rng.randint(low, high)
        first, second = _colors(rng)
        if profile == "diagonal_varied":
            grid = _diagonal_varied(n_pairs, first, second, rng)
        elif profile == "permuted_tiles":
            grid = _permuted_tiles(n_pairs, first, second, rng)
        elif profile == "multi_tiles":
            grid = _multi_tiles(n_pairs, first, second, rng)
        else:
            raise ValueError(f"unknown scene_profile: {profile!r}")
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct tile-reversal profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 2 + list(GENERAL_PROFILES) * 3)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, difficulty, ctx.draw_rng("public_nuisance"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid tile-reversal lesson: " + "; ".join(errors))
    return grid
