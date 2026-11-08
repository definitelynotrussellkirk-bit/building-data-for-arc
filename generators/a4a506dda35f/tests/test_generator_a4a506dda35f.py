"""Focused regression contract for the repaired a4a506dda35f generator."""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from itertools import permutations
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a4a506dda35f"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def oracle(grid):
    """Independent transcription of the selected Racket rule."""
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    output = []
    for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        output.extend([color] * count)
    return [output]


def component_count_rival(grid):
    """Count 4-connected same-color components instead of painted cells."""
    height, width = len(grid), len(grid[0])
    seen = set()
    counts = Counter()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            counts[color] += 1
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    output = []
    for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        output.extend([color] * count)
    return [output]


def first_seen_tie_rival(grid):
    counts = Counter()
    first = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            counts[color] += 1
            first.setdefault(color, row * len(values) + col)
    output = []
    for color in sorted(counts, key=lambda value: (-counts[value], first[value])):
        output.extend([color] * counts[color])
    return [output]


def test_canonical_pairs_match_authority_and_are_accepted():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        before = deepcopy(pair["input"])
        assert oracle(pair["input"]) == pair["output"]
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert pair["input"] == before


def test_rule_hash_version_axes_and_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "639443b5cb4a"
    assert gen.VERSION == "3.1.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"layout_profile", "palette_profile"}
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "component_count_sort",
        "first_seen_tie_break",
    }
    assert gen.CANONICAL_SHORTCUTS == gen.SEMANTIC_RIVALS
    assert gen.CANONICAL_SHORTCUTS == gen.LESSON_COMPETITORS
    assert set(gen.SEMANTIC_WITNESSES) == {
        "cell_count_not_component_count",
        "numeric_tie_break_not_first_seen",
    }


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("layout_profile", [
    "canonical_7x9_tie",
    "canonical_7x10_distinct",
    "canonical_7x11_tie",
    "canonical_8x10_distinct",
    "expanded_10x14_four_tie",
    "expanded_9x12_four_distinct",
])
@pytest.mark.parametrize("palette_profile", ["low", "warm", "cool", "mixed"])
def test_joint_exact_overrides_are_observable_and_lawful(
    difficulty, layout_profile, palette_profile
):
    requested = {
        "layout_profile": layout_profile,
        "palette_profile": palette_profile,
    }
    grid = gen.generate(711, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert len(oracle(grid)) == 1
    assert len(oracle(grid)[0]) <= len(grid[0])
    assert gen.SEMANTIC_RIVALS["component_count_sort"](grid) == component_count_rival(grid)
    assert component_count_rival(grid) != oracle(grid)
    if "_tie" in layout_profile:
        assert gen.SEMANTIC_RIVALS["first_seen_tie_break"](grid) == first_seen_tie_rival(grid)
        assert first_seen_tie_rival(grid) != oracle(grid)
    else:
        assert first_seen_tie_rival(grid) == oracle(grid)


@pytest.mark.parametrize("kwargs", [
    {"unknown_axis": 1},
    {"layout_profile": "unknown"},
    {"layout_profile": 3},
    {"palette_profile": "unknown"},
    {"palette_profile": True},
])
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize("seed,sample_index", [
    (True, 0),
    (1.0, 0),
    ("1", 0),
    (1, True),
    (1, 1.0),
    (1, "1"),
    (1, -1),
])
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_unknown_difficulty_is_rejected():
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_schedule_covers_profiles_and_is_deterministic(difficulty):
    layouts = []
    global_state = random.getstate()
    for index in range(24):
        first = gen.generate(2026, index, difficulty=difficulty)
        second = gen.generate(2026, index, difficulty=difficulty)
        assert random.getstate() == global_state
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first) == []
        assert gen.strict_canonical_like(first) == []
        observed = gen.observe_overrides(first)
        layouts.append(observed["layout_profile"])
        assert component_count_rival(first) != oracle(first)
        assert (first_seen_tie_rival(first) != oracle(first)) == (index % 2 == 0)
        first[0][0] = 9 if first[0][0] != 9 else 8
        assert first != second
    assert set(layouts) == set(gen.SCHEDULE_PROFILES)
    assert {
        (7, 9, 4),
        (7, 10, 4),
        (7, 11, 4),
        (8, 10, 4),
    } <= {
        (len(gen.generate(2026, i, difficulty=difficulty)),
         len(gen.generate(2026, i, difficulty=difficulty)[0]),
         len({cell for row in gen.generate(2026, i, difficulty=difficulty) for cell in row}))
        for i in range(24)
    }


def test_declared_shortcuts_fit_every_canonical_pair_and_generated_witnesses_refute_them():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name
    component_witness = gen.generate(31337, 1, layout_profile="canonical_7x10_distinct")
    tie_witness = gen.generate(31337, 0, layout_profile="canonical_7x9_tie")
    assert gen.SEMANTIC_WITNESSES["cell_count_not_component_count"](component_witness)
    assert gen.SEMANTIC_WITNESSES["numeric_tie_break_not_first_seen"](tie_witness)


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_four_pair_window_is_identifiable_under_all_query_rotations(difficulty):
    pairs = []
    for index in range(14):
        grid = gen.generate(919, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": oracle(grid)})
    for start in range(11):
        window = pairs[start:start + 4]
        for query_index in range(4):
            query = window[query_index]
            demos = [pair for index, pair in enumerate(window) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    assert rival(query["input"]) == query["output"], (
                        difficulty,
                        start,
                        query_index,
                        name,
                    )


@pytest.mark.parametrize("bad", [
    None,
    [],
    [[]],
    [[0, 0], [0]],
    [[0, True], [0, 1]],
    [[0, 10], [0, 1]],
    [[0] * 9 for _ in range(7)],
])
def test_self_check_rejects_malformed_or_degenerate_inputs(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_unsupported_count_and_shape_profiles():
    lawful = gen.generate(77, 3, layout_profile="canonical_8x10_distinct")

    wrong_shape = deepcopy(lawful) + [[0] * len(lawful[0])]
    assert gen.self_check(wrong_shape)

    too_many = deepcopy(lawful)
    color = next(cell for row in lawful for cell in row if cell != 0)
    for row in range(len(too_many)):
        for col in range(len(too_many[0])):
            if too_many[row][col] == 0:
                too_many[row][col] = color
                if Counter(cell for values in too_many for cell in values)[color] > 4:
                    break
        else:
            continue
        break
    assert gen.self_check(too_many)


def test_declared_output_codomain_is_exact_for_supported_frequency_assignments():
    outputs = set()
    for palette_name in gen.PALETTE_PROFILES:
        palette = gen._PALETTES[palette_name]
        for n_colors in (3, 4):
            colors = tuple(sorted(palette[:n_colors]))
            for mode in ("tie", "distinct"):
                for signature in gen._COUNT_SIGNATURES[(n_colors, mode)]:
                    for counts in set(permutations(signature)):
                        row = []
                        for color, count in sorted(
                            zip(colors, counts), key=lambda item: (-item[1], item[0])
                        ):
                            row.extend([color] * count)
                        outputs.add(tuple(row))
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN == 552


def test_difficulty_bands_use_distinct_deterministic_placement_streams():
    grids = [gen.generate(314159, 4, difficulty=band) for band in BANDS]
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) == len(BANDS)


@pytest.mark.parametrize("filename", [
    "component_count_sort.json",
    "first_seen_tie_break.json",
])
def test_retained_counterexamples_replay_exactly(filename):
    import json

    path = HOME / "counterexamples" / filename
    case = json.loads(path.read_text())
    call = case["generator_call"]
    grid = gen.generate(
        call["seed"],
        call["sample_index"],
        difficulty=call["difficulty"],
        **call["overrides"],
    )
    assert grid == case["input"]
    assert gen.self_check(grid) == case["self_check"] == []
    assert gen.rule_mirror(grid) == case["intended_output"]
    assert gen.CANONICAL_SHORTCUTS[case["rival_name"]](grid) == case["rival_output"]
    assert case["rival_output"] != case["intended_output"]


def test_shape_palette_and_total_do_not_determine_the_output():
    """Same observable envelope must require counting, not a profile lookup."""
    outputs_by_envelope = {}
    for seed in range(128):
        grid = gen.generate(
            seed,
            0,
            layout_profile="canonical_7x9_tie",
            palette_profile="low",
        )
        colors = frozenset(cell for row in grid for cell in row if cell != 0)
        total = sum(cell != 0 for row in grid for cell in row)
        envelope = (len(grid), len(grid[0]), colors, total)
        outputs_by_envelope.setdefault(envelope, set()).add(
            tuple(oracle(grid)[0])
        )
    assert max(map(len, outputs_by_envelope.values())) >= 4


def test_numeric_color_rank_does_not_fix_frequency_assignment():
    counts_by_color = {color: set() for color in (1, 2, 3)}
    for seed in range(128):
        grid = gen.generate(
            seed,
            1,
            layout_profile="canonical_7x10_distinct",
            palette_profile="low",
        )
        counts = Counter(cell for row in grid for cell in row if cell != 0)
        for color in counts_by_color:
            counts_by_color[color].add(counts[color])
    assert all(len(values) >= 3 for values in counts_by_color.values())
