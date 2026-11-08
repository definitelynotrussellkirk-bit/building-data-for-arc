"""Generator for ARC task e84fef15 / content hash 8b320727aa72.

The 29x29 input is a 5x5 array of 5x5 tiles separated by one-cell solid
lines. Exactly 24 tiles are identical. One tile is an erasure-corrupted copy:
1..5 foreground cells have been replaced by the tile background. The Racket
rule reconstructs the consensus tile and writes color 1 at every coordinate
where the 25 copies disagree.

The official examples use separator 3, background 8, 6..8 foreground cells,
3..4 foreground colors, one anomalous tile, and 2..4 erased cells. Default
draws retain that linked profile frequently while also varying lawful nuisance
features such as palette, anomaly location, occupancy layout, and difficulty.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b320727aa72"
RULE_HASH = "065574e7466b"  # normalized canonical program_solution hash
VERSION = "2.2.0"  # strict call contract plus semantic teaching hooks.
TASK_ID = "8b320727aa72"
SUMMARY = (
    "29x29 input containing 25 five-by-five tiles separated by solid lines; "
    "24 tiles are identical and one erases 1..5 consensus foreground cells "
    "to the tile background. Output is the consensus tile with every "
    "disagreement coordinate replaced by color 1."
)
EXAMPLES_NEEDED = 2

INVARIANTS = [
    "input is exactly 29x29 with 5x5 tiles at offsets 0,6,12,18,24",
    "rows and columns 5,11,17,23 form one uniform separator color",
    "exactly one tile differs from the other 24 identical tiles",
    "the anomalous tile only erases consensus foreground cells to background",
    "the consensus tile has 5..12 foreground cells using 1..5 colors",
    "there are exactly 1..5 disagreement coordinates",
    "color 1 is absent from the input and reserved for output markers",
]

TILE_LAYOUTS = (
    "scattered",
    "diagonal",
    "frame",
    "corners",
    "checker",
    "stripes",
)
DISAGREEMENT_DISTRIBUTIONS = ("spread", "center", "edge")
OFFSETS = (0, 6, 12, 18, 24)
GAP_LINES = (5, 11, 17, 23)
_PRIVATE_OVERRIDE_AXES = {"tile_layout", "disagreement_distribution"}
_INTEGER_OVERRIDE_AXES = {
    "n_filled_in_tile",
    "n_disagreements",
    "palette_size",
    "background_color",
    "separator_color",
    "corrupt_tile_index",
}


def _validate_generate_call(seed, sample_index, difficulty, overrides):
    """Reject malformed public calls before RNG or schedule logic sees them."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer (bool is not accepted)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES) - _PRIVATE_OVERRIDE_AXES
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in _INTEGER_OVERRIDE_AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    anchor = overrides.get("anchor_position")
    if anchor is not None and type(anchor) is not bool:
        raise ValueError(f"anchor_position must be a bool, not {type(anchor).__name__}")

    tile_layout = overrides.get("tile_layout")
    if tile_layout is not None and tile_layout not in TILE_LAYOUTS:
        raise ValueError(f"tile_layout must be one of {TILE_LAYOUTS}")
    disagreement_distribution = overrides.get("disagreement_distribution")
    if (
        disagreement_distribution is not None
        and disagreement_distribution not in DISAGREEMENT_DISTRIBUTIONS
    ):
        raise ValueError(
            "disagreement_distribution must be one of "
            f"{DISAGREEMENT_DISTRIBUTIONS}"
        )

AXES = {
    "n_filled_in_tile": {
        "type": "int",
        "default": "weighted 5..12; official-like 6..8 frequent",
        "valid": "5..12",
    },
    "n_disagreements": {
        "type": "int",
        "default": "weighted 1..5; official-like 2..4 frequent",
        "valid": "1..5",
    },
    "palette_size": {
        "type": "int",
        "default": "weighted 1..5; official-like 3..4 frequent",
        "valid": "1..5",
    },
    "background_color": {
        "type": "color",
        "default": "weighted 5..9; official color 8 frequent",
        "valid": "5..9",
    },
    "separator_color": {
        "type": "color",
        "default": "weighted 2..4; official color 3 frequent",
        "valid": "2..4",
    },
    "corrupt_tile_index": {
        "type": "int",
        "default": "sample_index%4==0 -> 0, otherwise keyed rng 0..24",
        "valid": "0..24",
    },
    "anchor_position": {
        "type": "bool",
        "default": "rng true|false",
        "valid": "true|false",
    },
}


def _weighted_options(values, preferred, repeats):
    """Keep every override value legal while biasing ordinary draws."""
    return list(values) + list(preferred) * repeats


def _layout_positions(layout, rng):
    positions = [(r, c) for r in range(5) for c in range(5)]
    if layout == "diagonal":
        diagonal = [(k, k) for k in range(5)]
        rest = [cell for cell in positions if cell not in diagonal]
        rng.shuffle(rest)
        return diagonal + rest
    if layout == "frame":
        border = [
            cell for cell in positions
            if cell[0] in (0, 4) or cell[1] in (0, 4)
        ]
        interior = [cell for cell in positions if cell not in border]
        rng.shuffle(border)
        rng.shuffle(interior)
        return border + interior
    if layout == "corners":
        corners = [(0, 0), (0, 4), (4, 0), (4, 4)]
        rest = [cell for cell in positions if cell not in corners]
        rng.shuffle(rest)
        return corners + rest
    if layout == "checker":
        even = [cell for cell in positions if sum(cell) % 2 == 0]
        odd = [cell for cell in positions if sum(cell) % 2 == 1]
        rng.shuffle(even)
        rng.shuffle(odd)
        return even + odd
    if layout == "stripes":
        stripe = [cell for cell in positions if cell[0] % 2 == 0]
        rest = [cell for cell in positions if cell[0] % 2 == 1]
        rng.shuffle(stripe)
        rng.shuffle(rest)
        return stripe + rest
    rng.shuffle(positions)
    return positions


def _spread_order(cells, rng):
    """Greedy farthest-point ordering with deterministic randomized ties."""
    remaining = list(cells)
    rng.shuffle(remaining)
    if not remaining:
        return []
    chosen = [remaining.pop()]
    while remaining:
        best_index = max(
            range(len(remaining)),
            key=lambda index: min(
                abs(remaining[index][0] - r) + abs(remaining[index][1] - c)
                for r, c in chosen
            ),
        )
        chosen.append(remaining.pop(best_index))
    return chosen


def _disagreement_order(cells, mode, rng):
    cells = list(cells)
    rng.shuffle(cells)  # deterministic tie-breaking for all sorted modes
    if mode == "center":
        return sorted(cells, key=lambda rc: abs(rc[0] - 2) + abs(rc[1] - 2))
    if mode == "edge":
        return sorted(
            cells,
            key=lambda rc: min(rc[0], 4 - rc[0], rc[1], 4 - rc[1]),
        )
    return _spread_order(cells, rng)


def _extract_tiles(grid):
    return [
        tuple(
            tuple(grid[tr + r][tc + c] for c in range(5))
            for r in range(5)
        )
        for tr in OFFSETS
        for tc in OFFSETS
    ]


def _analyze(grid):
    """Recover the exact semantic quantities encoded in a valid input."""
    if not isinstance(grid, list) or len(grid) != 29:
        raise ValueError("grid must have 29 rows")
    if any(not isinstance(row, list) or len(row) != 29 for row in grid):
        raise ValueError("grid must be rectangular 29x29")

    separator_values = {
        grid[r][c]
        for r in range(29)
        for c in range(29)
        if r in GAP_LINES or c in GAP_LINES
    }
    if len(separator_values) != 1:
        raise ValueError("separator rows and columns are not uniform")
    separator_color = next(iter(separator_values))

    tiles = _extract_tiles(grid)
    counts = Counter(tiles)
    if sorted(counts.values()) != [1, 24]:
        raise ValueError("expected one anomalous tile and 24 identical tiles")
    consensus = next(tile for tile, count in counts.items() if count == 24)
    anomaly = next(tile for tile, count in counts.items() if count == 1)
    corrupt_tile_index = next(
        index for index, tile in enumerate(tiles) if tile == anomaly
    )

    consensus_values = [value for row in consensus for value in row]
    value_counts = Counter(consensus_values)
    background_color, background_count = value_counts.most_common(1)[0]
    if list(value_counts.values()).count(background_count) != 1:
        raise ValueError("consensus tile has no unique modal background")

    disagreements = [
        (r, c)
        for r in range(5)
        for c in range(5)
        if consensus[r][c] != anomaly[r][c]
    ]
    foreground_values = [
        value for value in consensus_values if value != background_color
    ]
    return {
        "separator_color": separator_color,
        "background_color": background_color,
        "corrupt_tile_index": corrupt_tile_index,
        "n_filled_in_tile": len(foreground_values),
        "palette_size": len(set(foreground_values)),
        "n_disagreements": len(disagreements),
        "anchor_position": consensus[0][0] != background_color,
        "consensus": consensus,
        "anomaly": anomaly,
        "disagreements": disagreements,
        "tile_counts": counts,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_call(seed, sample_index, difficulty, overrides)

    # These two legacy private controls appear in the retained frozen fixture.
    # They are honored but stay outside AXES because their values are not
    # recoverable exactly from returned pixels.
    tile_layout_override = overrides.get("tile_layout")
    disagreement_distribution_override = overrides.get(
        "disagreement_distribution"
    )

    # Every standard four-pair lesson starts with a top-left anomaly. This
    # falsifies the tempting shortcut "treat the first tile as the answer"
    # while explicit overrides retain full precedence for contract probes.
    effective_overrides = {
        key: value for key, value in overrides.items() if key in AXES
    }
    if (
        effective_overrides.get("corrupt_tile_index") is None
        and sample_index % 4 == 0
    ):
        effective_overrides["corrupt_tile_index"] = 0

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    canonical_profile = ctx.draw_rng("canonical_profile").random() < 0.55
    if canonical_profile:
        filled_preferred = (6, 7, 8)
        disagreement_preferred = (2, 3, 4)
        palette_preferred = (3, 4)
        background_preferred = (8,)
        separator_preferred = (3,)
        repeats = 7
    elif difficulty == "easy":
        filled_preferred = (5, 6, 7)
        disagreement_preferred = (1, 2)
        palette_preferred = (1, 2, 3)
        background_preferred = (8, 5, 6)
        separator_preferred = (3, 2, 4)
        repeats = 3
    elif difficulty == "hard":
        filled_preferred = (10, 11, 12)
        disagreement_preferred = (4, 5)
        palette_preferred = (4, 5)
        background_preferred = (8, 7, 9)
        separator_preferred = (3, 2, 4)
        repeats = 3
    else:
        filled_preferred = (7, 8, 9, 10)
        disagreement_preferred = (2, 3, 4)
        palette_preferred = (2, 3, 4)
        background_preferred = (8, 5, 6, 7, 9)
        separator_preferred = (3, 2, 4)
        repeats = 3

    n_filled = ctx.draw_choice(
        "n_filled_in_tile",
        _weighted_options(range(5, 13), filled_preferred, repeats),
    )
    n_disagreements = ctx.draw_choice(
        "n_disagreements",
        _weighted_options(range(1, 6), disagreement_preferred, repeats),
    )
    palette_size = ctx.draw_choice(
        "palette_size",
        _weighted_options(range(1, 6), palette_preferred, repeats),
    )
    background_color = ctx.draw_choice(
        "background_color",
        _weighted_options(range(5, 10), background_preferred, repeats),
    )
    separator_color = ctx.draw_choice(
        "separator_color",
        _weighted_options(range(2, 5), separator_preferred, repeats),
    )
    corrupt_tile_index = ctx.draw_int("corrupt_tile_index", 0, 24)
    tile_layout = (
        tile_layout_override
        if tile_layout_override is not None
        else ctx.draw_rng("tile_layout_choice").choice(TILE_LAYOUTS)
    )
    disagreement_distribution = (
        disagreement_distribution_override
        if disagreement_distribution_override is not None
        else ctx.draw_rng("disagreement_distribution_choice").choice(
            DISAGREEMENT_DISTRIBUTIONS
        )
    )
    anchor_position = ctx.draw_choice("anchor_position", (False, True))

    layout_rng = ctx.draw_rng("tile_cells")
    candidates = _layout_positions(tile_layout, layout_rng)
    if anchor_position:
        selected = [(0, 0)]
        selected.extend(
            cell for cell in candidates if cell != (0, 0)
        )
    else:
        selected = [cell for cell in candidates if cell != (0, 0)]
    selected = selected[:n_filled]

    legal_colors = [
        color for color in range(10)
        if color not in {1, background_color, separator_color}
    ]
    palette_rng = ctx.draw_rng("foreground_palette")
    palette = palette_rng.sample(legal_colors, palette_size)
    assignment_cells = list(selected)
    palette_rng.shuffle(assignment_cells)

    consensus = full_grid(5, 5, background_color)
    for index, (r, c) in enumerate(assignment_cells):
        color = palette[index] if index < palette_size else palette_rng.choice(palette)
        consensus[r][c] = color

    disagreement_rng = ctx.draw_rng("disagreement_cells")
    disagreement_cells = _disagreement_order(
        selected, disagreement_distribution, disagreement_rng
    )[:n_disagreements]

    grid = full_grid(29, 29, separator_color)
    for tile_index, (tr, tc) in enumerate(
        (tr, tc) for tr in OFFSETS for tc in OFFSETS
    ):
        for r in range(5):
            for c in range(5):
                value = consensus[r][c]
                if (
                    tile_index == corrupt_tile_index
                    and (r, c) in disagreement_cells
                ):
                    value = background_color
                grid[tr + r][tc + c] = value
    return grid


def observe_overrides(grid):
    analysis = _analyze(grid)
    return {
        "n_filled_in_tile": analysis["n_filled_in_tile"],
        "n_disagreements": analysis["n_disagreements"],
        "palette_size": analysis["palette_size"],
        "background_color": analysis["background_color"],
        "separator_color": analysis["separator_color"],
        "corrupt_tile_index": analysis["corrupt_tile_index"],
        "anchor_position": analysis["anchor_position"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]

    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    if any(value == 1 for row in grid for value in row):
        errors.append("input contains reserved output marker color 1")

    separator_color = analysis["separator_color"]
    background_color = analysis["background_color"]
    consensus = analysis["consensus"]
    anomaly = analysis["anomaly"]
    disagreements = analysis["disagreements"]

    tile_values = {value for row in consensus for value in row}
    if separator_color in tile_values:
        errors.append("separator color also appears inside the consensus tile")
    if background_color in {1, separator_color}:
        errors.append("background color conflicts with marker or separator")

    n_filled = analysis["n_filled_in_tile"]
    if not 5 <= n_filled <= 12:
        errors.append(f"consensus foreground count is {n_filled}, expected 5..12")
    palette_size = analysis["palette_size"]
    if not 1 <= palette_size <= 5:
        errors.append(f"foreground palette size is {palette_size}, expected 1..5")
    if not 1 <= len(disagreements) <= 5:
        errors.append(
            f"disagreement count is {len(disagreements)}, expected 1..5"
        )

    for r, c in disagreements:
        if consensus[r][c] == background_color:
            errors.append("anomaly changes a consensus background cell")
            break
        if anomaly[r][c] != background_color:
            errors.append("anomaly replaces a foreground cell with a non-background color")
            break

    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return the exact lawful 24+1 erasure grammar used for teaching."""
    return self_check(grid)


def _canonical_mark_output(grid):
    """Python contract mirror only; canonical Racket remains label authority."""
    analysis = _analyze(grid)
    output = [list(row) for row in analysis["consensus"]]
    for r, c in analysis["disagreements"]:
        output[r][c] = 1
    return output


def _restore_consensus_output(grid):
    """RIVAL/prototype setting: resolve disagreements to the modal copy value."""
    return [list(row) for row in _analyze(grid)["consensus"]]


def _has_disagreement_marker_requirement(grid) -> bool:
    try:
        return bool(_analyze(grid)["disagreements"])
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "disagreement_marker_required": _has_disagreement_marker_requirement,
}
SEMANTIC_RIVALS = {"restore_consensus": _restore_consensus_output}
WITNESS_RIVALS = {
    "disagreement_marker_required": ["restore_consensus"],
}
LESSON_COMPETITORS = {"restore_consensus": _restore_consensus_output}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that survives demos but changes the query."""
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must provide a demo list and one query pair"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # noqa: BLE001 - contract diagnostics must be loud
            reasons.append(f"{name} scoring failed: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(
                f"{name} fits all {len(demos)} demonstrations but changes the query"
            )
    return reasons

