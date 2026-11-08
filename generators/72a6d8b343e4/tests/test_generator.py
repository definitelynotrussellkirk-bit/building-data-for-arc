"""Source-bound regression tests for the Endpoint Bridge generator repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    extra_occurrence_witness,
    load_generator,
    misaligned_witness,
    observed,
    profile,
    racket_outputs,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(8, 9, 3), (8, 10, 3), (8, 11, 3)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


def test_rule_hash_and_executable_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "3650a4704dc3"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.SEMANTIC_WITNESSES) == {
        "misaligned_pair_ignored",
        "extra_occurrence_blocks_line",
    }
    assert set(gen.SEMANTIC_RIVALS) == {
        "connect_misaligned_by_l_path",
        "connect_aligned_subsets",
    }
    assert gen.WITNESS_RIVALS == {
        "misaligned_pair_ignored": ["connect_misaligned_by_l_path"],
        "extra_occurrence_blocks_line": ["connect_aligned_subsets"],
    }
    assert set(gen.CANONICAL_SHORTCUTS) == set(gen.SEMANTIC_RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_axis_round_trips_at_the_minimum_canvas(band):
    requested = {
        "grid_h": 8,
        "grid_w": 9,
        "n_lines": 3,
        "n_adjacent": 1,
        "n_misaligned": 1,
        "n_triplets": 1,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    assert {key: observed(grid)[key] for key in requested} == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 13),
        ("grid_w", 8),
        ("grid_w", 16),
        ("n_lines", 0),
        ("n_lines", 4),
        ("n_adjacent", -1),
        ("n_adjacent", 2),
        ("n_misaligned", -1),
        ("n_misaligned", 2),
        ("n_triplets", -1),
        ("n_triplets", 2),
        ("grid_h", True),
        ("grid_w", 9.5),
        ("n_lines", "2"),
    ],
)
def test_unknown_out_of_domain_and_wrong_type_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_curriculum_has_canonical_support_and_both_guards(band):
    profiles = set()
    strict = 0
    misaligned = 0
    triplets = 0
    horizontal = 0
    vertical = 0
    inputs = set()
    for index in range(120):
        grid = gen.generate(8000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(8000 + index, index, difficulty=band)
        facts = observed(grid)
        profiles.add(profile(grid))
        strict += not gen.strict_canonical_like(grid)
        misaligned += facts["n_misaligned"] > 0
        triplets += facts["n_triplets"] > 0
        horizontal += facts["horizontal"] > 0
        vertical += facts["vertical"] > 0
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert CANONICAL_PROFILES <= profiles
    assert strict >= 50
    assert misaligned >= 50
    assert triplets >= 50
    assert horizontal >= 30 and vertical >= 30
    assert len(inputs) >= 105


def test_declared_shortcuts_fit_all_canonical_pairs_and_witnesses_refute_them():
    pairs = canonical_pairs()
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    misaligned = misaligned_witness()
    triplet = extra_occurrence_witness()
    assert gen.self_check(misaligned) == []
    assert gen.self_check(triplet) == []
    assert reference_output(misaligned) != gen.SEMANTIC_RIVALS["connect_misaligned_by_l_path"](misaligned)
    assert reference_output(triplet) != gen.SEMANTIC_RIVALS["connect_aligned_subsets"](triplet)
    assert gen.SEMANTIC_WITNESSES["misaligned_pair_ignored"](misaligned)
    assert gen.SEMANTIC_WITNESSES["extra_occurrence_blocks_line"](triplet)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demo_lessons_and_all_cyclic_query_rotations_refute_every_rival(band):
    for start in range(24):
        seed = 12000 + start
        pairs = []
        for offset in range(4):
            grid = gen.generate(seed, start * 11 + offset, difficulty=band)
            pairs.append({"input": grid, "output": reference_output(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert len(demos) == gen.EXAMPLES_NEEDED
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert not all(rival(pair["input"]) == pair["output"] for pair in demos)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)], [[10] * 9 for _ in range(8)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_singletons_and_unsupported_fourth_occurrences():
    grid = gen.generate(4, 2, n_lines=2, n_adjacent=0, n_misaligned=1, n_triplets=1)
    singleton = deepcopy(grid)
    color = next(value for row in singleton for value in row if value)
    hit = next((r, c) for r, row in enumerate(singleton) for c, value in enumerate(row) if value == color)
    singleton[hit[0]][hit[1]] = 0
    assert gen.self_check(singleton)

    fourth = deepcopy(grid)
    triplet_color = next(
        color for color, points in _positions(fourth).items() if len(points) == 3
    )
    empty = next((r, c) for r, row in enumerate(fourth) for c, value in enumerate(row) if value == 0)
    fourth[empty[0]][empty[1]] = triplet_color
    assert gen.self_check(fourth)


def _positions(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result.setdefault(value, []).append((r, c))
    return result


def test_fresh_return_and_python_hash_independence():
    first = gen.generate(412, 111, difficulty="hard")
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second and first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(412, 111, difficulty="hard") == second

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_authority_matches_oracle_on_canonical_witness_and_generated_inputs():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [misaligned_witness(), extra_occurrence_witness()]
    grids += [gen.generate(1900 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(30)]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
