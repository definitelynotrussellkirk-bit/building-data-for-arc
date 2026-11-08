"""Generator for ARC task 662c240a — select the first asymmetric panel.

The input is exactly three vertically stacked 3x3 panels.  Every panel uses
its own pair of nonzero colors.  The output is the first panel, reading from
top to bottom, that is not symmetric across the main diagonal.

Two of every three ordinary draws stay on the linked canonical morphology
profiles.  Every third draw contains two asymmetric panels, so a lesson cannot
silently teach the canonical-compatible shortcuts "the unique asymmetric
panel" or "the last asymmetric panel" instead of the true first-match rule.
"""
from __future__ import annotations

from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8d97c22b1360"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d302c29f3c63"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.60
SCHEDULE_PROFILES = ("canonical_single", "two_asymmetric_rebuttal")

SUMMARY = (
    "Split the 9x3 input into three stacked 3x3 panels. Return the first "
    "panel from top to bottom that differs from its main-diagonal transpose. "
    "Ordinary lessons include two-asymmetric-panel counterexamples so first "
    "match, rather than unique or last match, is identifiable."
)

INVARIANTS = [
    "input is exactly three vertically stacked 3x3 panels (overall 9x3)",
    "each panel is fully colored with exactly two nonzero colors",
    "the three panel palettes are pairwise disjoint (six colors total)",
    "one or two panels are main-diagonal asymmetric, never zero or three",
    "the output is the first asymmetric panel from top to bottom",
]

ASYMMETRIC_POSITIONS = ("top", "middle", "bottom")
_POSITION_TO_INDEX = {name: index for index, name in enumerate(ASYMMETRIC_POSITIONS)}
_INDEX_TO_POSITION = {index: name for name, index in _POSITION_TO_INDEX.items()}

# Only exact, answer-bearing, grid-observable controls are declared.  Panel
# size is fixed by the task and palette relabeling is a nuisance variable, not
# an exact semantic override axis.
AXES = {
    "asymmetric_position": {
        "type": "str",
        "default": "scheduled top|middle|bottom first asymmetric panel",
        "valid": "top|middle|bottom",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Linked signatures extracted from all four train inputs and the held-out test
# input with the same executable feature extractor used below.  Each panel
# signature is (is_symmetric, mismatched_off_diagonal_pairs, sorted_histogram).
_CANONICAL_SIGNATURES = (
    ((True, 0, (3, 6)), (True, 0, (4, 5)), (False, 2, (4, 5))),
    ((True, 0, (4, 5)), (False, 1, (3, 6)), (True, 0, (4, 5))),
    ((False, 1, (3, 6)), (True, 0, (4, 5)), (True, 0, (2, 7))),
    ((True, 0, (2, 7)), (True, 0, (4, 5)), (False, 1, (4, 5))),
    ((False, 1, (3, 6)), (True, 0, (4, 5)), (True, 0, (4, 5))),
)
_CANONICAL_SIGNATURE_SET = set(_CANONICAL_SIGNATURES)


def _pattern_signature(bits: tuple[int, ...]) -> tuple[bool, int, tuple[int, int]]:
    panel = [bits[row * 3:(row + 1) * 3] for row in range(3)]
    mismatches = sum(
        panel[row][col] != panel[col][row]
        for row in range(3)
        for col in range(row + 1, 3)
    )
    ones = sum(bits)
    return mismatches == 0, mismatches, tuple(sorted((ones, 9 - ones)))


# Exhaustive two-color 3x3 motif bank.  Building from all 2^9 bitmaps avoids
# hidden hand-authored texture leakage while letting generation pin exact linked
# canonical signatures and exact shortcut-rebuttal signatures.
_PATTERN_BANK: dict[tuple[bool, int, tuple[int, int]], tuple[tuple[int, ...], ...]] = {}
for _bits in product((0, 1), repeat=9):
    if len(set(_bits)) != 2:
        continue
    _key = _pattern_signature(_bits)
    _PATTERN_BANK.setdefault(_key, tuple())
    _PATTERN_BANK[_key] = _PATTERN_BANK[_key] + (tuple(_bits),)


def _panel_signature(panel: list[list[int]]) -> tuple[bool, int, tuple[int, int]]:
    mismatches = sum(
        panel[row][col] != panel[col][row]
        for row in range(3)
        for col in range(row + 1, 3)
    )
    counts: dict[int, int] = {}
    for row in panel:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    return mismatches == 0, mismatches, tuple(sorted(counts.values()))


def _analyze(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"], None
    if (len(grid), width) != (9, 3):
        return [f"expected 9x3 stacked panels, got {len(grid)}x{width}"], None
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-integer or color outside 0..9"], None

    panels = [
        [list(row) for row in grid[index * 3:(index + 1) * 3]]
        for index in range(3)
    ]
    panel_colors: list[set[int]] = []
    signatures = []
    for index, panel in enumerate(panels):
        colors = {value for row in panel for value in row}
        panel_colors.append(colors)
        if 0 in colors:
            errors.append(f"panel {index} contains background color 0")
        if len(colors) != 2:
            errors.append(
                f"panel {index} must use exactly two colors, got {sorted(colors)}"
            )
        signatures.append(_panel_signature(panel))

    union = set().union(*panel_colors)
    if len(union) != 6 or any(
        panel_colors[left] & panel_colors[right]
        for left in range(3)
        for right in range(left + 1, 3)
    ):
        errors.append("panel palettes must be pairwise disjoint (six colors total)")

    asymmetric = [index for index, signature in enumerate(signatures) if not signature[0]]
    if not (1 <= len(asymmetric) <= 2):
        errors.append(
            f"expected one or two asymmetric panels, found {len(asymmetric)}"
        )

    analysis = {
        "panels": panels,
        "panel_colors": panel_colors,
        "signatures": tuple(signatures),
        "asymmetric_indices": tuple(asymmetric),
        "first_asymmetric": asymmetric[0] if asymmetric else None,
    }
    return errors, analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, answerless, all-asymmetric, or palette-leaking scenes."""
    del difficulty, meta
    errors, _analysis = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require one of the five linked empirical train/test morphology profiles."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        return errors
    if len(analysis["asymmetric_indices"]) != 1:
        errors.append("canonical inputs have exactly one asymmetric panel")
    if analysis["signatures"] not in _CANONICAL_SIGNATURE_SET:
        errors.append(
            "linked panel symmetry/mismatch/histogram profile is absent from canonical train/test"
        )
    return errors


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact first-asymmetric-position axis from the returned grid."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None or analysis["first_asymmetric"] is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {"asymmetric_position": _INDEX_TO_POSITION[analysis["first_asymmetric"]]}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure test/rival mirror; the canonical Racket program remains authoritative."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None or analysis["first_asymmetric"] is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    return [list(row) for row in analysis["panels"][analysis["first_asymmetric"]]]


def _draw_panel(
    rng,
    colors: tuple[int, int],
    signature: tuple[bool, int, tuple[int, int]],
) -> list[list[int]]:
    choices = _PATTERN_BANK.get(signature, ())
    if not choices:
        raise RuntimeError(f"no 3x3 motif for signature {signature!r}")
    bits = rng.choice(choices)
    # Randomly swap the two color roles so the less frequent color is not tied
    # to palette ordering.
    first, second = colors if rng.randrange(2) == 0 else colors[::-1]
    return [
        [first if bits[row * 3 + col] == 0 else second for col in range(3)]
        for row in range(3)
    ]


def _scheduled_profile(sample_index: int) -> tuple[tuple[bool, int, tuple[int, int]], ...] | None:
    """Two canonical profiles, then one multi-asymmetric rebuttal, forever."""
    if sample_index % 3 == 2:
        return None
    canonical_rank = sample_index - (sample_index + 1) // 3
    return _CANONICAL_SIGNATURES[canonical_rank % len(_CANONICAL_SIGNATURES)]


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Expose the three-draw lesson schedule to the semantic gate."""
    del seed, difficulty
    if sample_index % 3 == 2:
        return "two_asymmetric_rebuttal"
    return "canonical_single"


def _multi_asymmetric_profile(sample_index: int) -> tuple[tuple[bool, int, tuple[int, int]], ...]:
    # All panels share the same 4/5 histogram, actively removing histogram
    # odd-one-out as a selector.  Alternate first-match position while keeping
    # a later asymmetric panel that separates first from last/unique rules.
    if (sample_index // 3) % 2 == 0:
        return (
            (False, 1, (4, 5)),
            (True, 0, (4, 5)),
            (False, 2, (4, 5)),
        )
    return (
        (True, 0, (4, 5)),
        (False, 2, (4, 5)),
        (False, 1, (4, 5)),
    )


def _profile_for_override(position: str, sample_index: int):
    index = _POSITION_TO_INDEX[position]
    matching = [
        profile
        for profile in _CANONICAL_SIGNATURES
        if next(i for i, signature in enumerate(profile) if not signature[0]) == index
    ]
    return matching[sample_index % len(matching)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if "asymmetric_position" in overrides and overrides["asymmetric_position"] is not None:
        position = ctx.draw_choice("asymmetric_position", ASYMMETRIC_POSITIONS)
        profile = _profile_for_override(position, sample_index)
    else:
        profile = _scheduled_profile(sample_index)
        if profile is None:
            profile = _multi_asymmetric_profile(sample_index)
        first_index = next(index for index, signature in enumerate(profile) if not signature[0])
        position = ctx.draw_choice("asymmetric_position", (_INDEX_TO_POSITION[first_index],))

    band_tag = "medium" if difficulty is None else difficulty
    palette_rng = ctx.draw_rng(f"panel_palettes_{band_tag}")
    colors = palette_rng.sample(list(range(1, 10)), 6)
    palettes = ((colors[0], colors[1]), (colors[2], colors[3]), (colors[4], colors[5]))
    motif_rng = ctx.draw_rng(f"panel_motifs_{band_tag}")
    panels = [
        _draw_panel(motif_rng, palettes[index], profile[index])
        for index in range(3)
    ]

    grid = full_grid(9, 3, 0)
    for panel_index, panel in enumerate(panels):
        for row in range(3):
            grid[panel_index * 3 + row][:] = panel[row]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)["asymmetric_position"]
    if observed != position:
        raise RuntimeError(
            f"scheduled asymmetric_position {position!r} became {observed!r}"
        )
    return grid


def _analysis_if_valid(grid):
    errors, analysis = _analyze(grid)
    return None if errors else analysis


def _witness_first(index: int):
    def witness(grid):
        analysis = _analysis_if_valid(grid)
        return analysis is not None and analysis["first_asymmetric"] == index
    return witness


def _witness_multiple_asymmetric(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and len(analysis["asymmetric_indices"]) == 2


def _witness_histogram_not_unique(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    histograms = [signature[2] for signature in analysis["signatures"]]
    target = histograms[analysis["first_asymmetric"]]
    return histograms.count(target) > 1


SEMANTIC_WITNESSES = {
    "first_asymmetric_top": _witness_first(0),
    "first_asymmetric_middle": _witness_first(1),
    "first_asymmetric_bottom": _witness_first(2),
    "two_asymmetric_panels_refute_unique_or_last": _witness_multiple_asymmetric,
    "target_histogram_is_not_unique": _witness_histogram_not_unique,
}


def _competitor_fixed(index: int):
    def solve(grid):
        analysis = _analysis_if_valid(grid)
        return None if analysis is None else [list(row) for row in analysis["panels"][index]]
    return solve


def _competitor_last_asymmetric(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None or not analysis["asymmetric_indices"]:
        return None
    return [list(row) for row in analysis["panels"][analysis["asymmetric_indices"][-1]]]


def _competitor_unique_asymmetric(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None or len(analysis["asymmetric_indices"]) != 1:
        return None
    return [list(row) for row in analysis["panels"][analysis["asymmetric_indices"][0]]]


def _competitor_unique_histogram(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    histograms = [signature[2] for signature in analysis["signatures"]]
    candidates = [index for index, value in enumerate(histograms) if histograms.count(value) == 1]
    if len(candidates) != 1:
        return None
    return [list(row) for row in analysis["panels"][candidates[0]]]


SEMANTIC_RIVALS = {
    "last_asymmetric": _competitor_last_asymmetric,
    "unique_asymmetric": _competitor_unique_asymmetric,
    "unique_color_histogram": _competitor_unique_histogram,
    "always_top": _competitor_fixed(0),
    "always_middle": _competitor_fixed(1),
    "always_bottom": _competitor_fixed(2),
}
WITNESS_RIVALS = {
    "first_asymmetric_top": "always_middle",
    "first_asymmetric_middle": "always_top",
    "first_asymmetric_bottom": "always_top",
    "two_asymmetric_panels_refute_unique_or_last": [
        "last_asymmetric",
        "unique_asymmetric",
    ],
    "target_histogram_is_not_unique": "unique_color_histogram",
}

# Both shortcuts fit every official pair because canonical has exactly one
# asymmetric panel.  The generated two-asymmetric witness is therefore the
# required counterexample rather than an optional diversity flourish.
CANONICAL_SHORTCUTS = {
    "last_asymmetric": _competitor_last_asymmetric,
    "unique_asymmetric": _competitor_unique_asymmetric,
}

LESSON_COMPETITORS = {
    "last_asymmetric": _competitor_last_asymmetric,
    "unique_asymmetric": _competitor_unique_asymmetric,
    "unique_color_histogram": _competitor_unique_histogram,
    "always_top": _competitor_fixed(0),
    "always_middle": _competitor_fixed(1),
    "always_bottom": _competitor_fixed(2),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible rival survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} outside rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with first-asymmetric rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query outside rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but answers query differently"
            )
    return reasons
