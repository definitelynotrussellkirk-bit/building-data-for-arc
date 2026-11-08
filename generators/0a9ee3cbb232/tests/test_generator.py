"""Task-local regression tests for the horizontal-run curriculum."""
from __future__ import annotations

from copy import deepcopy
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANVAS_PROFILES,
    canonical_pairs,
    connected_components_output,
    drop_twos_on_overflow_output,
    lesson,
    load_generator,
    normalized,
    observed,
    occupied_rows_output,
    rule_output,
    run_counts,
    selected_rule_sources,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BACKGROUNDS = (0, 1, 4, 5, 6, 7, 8, 9)


def test_rule_pin_and_all_canonical_pairs():
    assert gen.RULE_HASH == "54a0bdf9c500"
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert rule_output(pair["input"]) == pair["output"]
        assert gen._mirror(pair["input"]) == pair["output"]


def test_selected_rule_sources_are_exactly_synchronized():
    sources = selected_rule_sources()
    normalized_sources = {name: normalized(source) for name, source in sources.items()}
    assert len(set(normalized_sources.values())) == 1, normalized_sources.keys()


def test_every_exact_axis_is_constructive_and_observable():
    bands = (None, "easy", "medium", "hard")
    for case_index, (profile, n3, n2, background) in enumerate(
        itertools.product(range(5), range(1, 7), range(1, 7), BACKGROUNDS)
    ):
        options = {
            "canvas_profile": profile,
            "n_3": n3,
            "n_2": n2,
            "background": background,
        }
        band = bands[case_index % len(bands)]
        grid = gen.generate(1701 + case_index, case_index, difficulty=band, **options)
        assert gen.self_check(grid) == []
        assert observed(grid) == options
        assert gen.observe_overrides(grid) == options
        assert rule_output(grid) == gen._mirror(grid)


@pytest.mark.parametrize(
    "options",
    [
        {"typo": 1},
        {"canvas_profile": -1},
        {"canvas_profile": 5},
        {"n_3": 0},
        {"n_3": 7},
        {"n_2": 0},
        {"n_2": 7},
        {"background": 2},
        {"background": 3},
        {"background": 10},
        {"n_3": True},
        {"n_2": 2.5},
        {"background": "5"},
    ],
)
def test_invalid_overrides_are_loud(options):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_invalid_seed_controls_are_loud(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "0", None])
def test_invalid_sample_index_controls_are_loud(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


@pytest.mark.parametrize(
    "difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_invalid_difficulty_controls_are_loud(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_default_distribution_covers_profiles_outputs_and_witnesses():
    outputs = set()
    backgrounds = set()
    profiles = set()
    for band in ("easy", "medium", "hard"):
        band_overflow = 0
        for index in range(60):
            grid = gen.generate(3100 + index, index, difficulty=band)
            assert grid == gen.generate(3100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert (len(grid), len(grid[0])) in CANVAS_PROFILES
            assert len({value for row in grid for value in row}) == 3
            assert gen.SEMANTIC_WITNESSES["multirow_component"](grid)
            assert gen.SEMANTIC_WITNESSES["multiple_runs_same_row"](grid)
            assert connected_components_output(grid) != rule_output(grid)
            assert occupied_rows_output(grid) != rule_output(grid)
            overflow = gen.SEMANTIC_WITNESSES["overflow_truncation"](grid)
            band_overflow += int(overflow)
            assert overflow == (drop_twos_on_overflow_output(grid) != rule_output(grid))
            outputs.add(tuple(map(tuple, rule_output(grid))))
            obs = observed(grid)
            backgrounds.add(obs["background"])
            profiles.add(obs["canvas_profile"])
        assert 20 <= band_overflow <= 40
    assert len(outputs) >= 8
    assert backgrounds == set(BACKGROUNDS)
    assert profiles == set(range(5))
    easy = gen.generate(91, 7, difficulty="easy")
    medium = gen.generate(91, 7, difficulty="medium")
    hard = gen.generate(91, 7, difficulty="hard")
    assert len({str(easy), str(medium), str(hard)}) == 3


def test_every_cyclic_three_of_four_lesson_refutes_all_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = lesson(8800 + start, start, band)
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_declared_rivals_fit_canonical_but_generated_witnesses_refute_them():
    pairs = canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    for index in range(6):
        grid = gen.generate(712, index)
        for witness, names in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != rule_output(grid) for name in names)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)],
        [[2] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(9)] + [[2, 2] + [0] * 8],
    ],
)
def test_self_check_rejects_malformed_and_minimal_impostors(grid):
    assert gen.self_check(grid)


def test_validator_rejects_structure_destroying_mutations():
    grid = gen.generate(41, 5, canvas_profile=1, n_3=3, n_2=3, background=5)
    mutations = []
    missing_three = [[5 if value == 3 else value for value in row] for row in grid]
    mutations.append(missing_three)
    singleton = deepcopy(grid)
    background = observed(grid)["background"]
    for r, row in enumerate(singleton):
        run = [c for c, value in enumerate(row) if value == 3]
        if run:
            # Collapse one whole maximal run to a single cell; merely deleting
            # its endpoint would still be a lawful shorter segment.
            first = run[0]
            end = first
            while end + 1 < len(row) and row[end + 1] == 3:
                end += 1
            for c in range(first + 1, end + 1):
                singleton[r][c] = background
            mutations.append(singleton)
            break
    unknown = deepcopy(grid)
    replacement = next(color for color in (0, 1, 4, 5, 6, 7, 8, 9) if color != background)
    for r, row in enumerate(unknown):
        for c, value in enumerate(row):
            if value == background:
                unknown[r][c] = replacement
                break
        else:
            continue
        break
    mutations.append(unknown)
    mutations.append(grid + [list(grid[0])])
    for mutation in mutations:
        assert gen.self_check(mutation)


def test_reusable_qualification_probe_smoke():
    import qualify

    report = qualify.audit(samples_per_band=12, cyclic_starts=4, full_cartesian=False)
    assert report["status"] == "pass"
    assert report["generator_sha256"]
    assert report["canonical_pairs"] == 5
    assert report["defaults"]["draws"] == 36
    assert report["lessons"]["cyclic_windows"] == 48
