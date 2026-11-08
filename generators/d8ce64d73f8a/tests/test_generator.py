"""Focused regression suite for d8ce64d73f8a.

The independent oracle lives in workspace/reference_probe.py so future agents
can rerun structural, semantic, and real-Racket checks without trusting the
production generator's own helpers.
"""
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
    canonical_row,
    flood_output,
    load_generator,
    normalized_rule_hash,
    observed,
    racket_outputs,
    selected_base_path,
    top_left_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {(10, 12, 3), (11, 13, 3), (12, 12, 3), (10, 14, 3), (12, 10, 3)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_canonical_pairs_are_owned_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert flood_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_selected_authority_are_exactly_synchronized():
    row = canonical_row()
    source = row["program_solution"]
    assert gen.RULE_HASH == normalized_rule_hash(source) == "2a17285ed2a7"
    selected = selected_base_path()
    if selected is not None:
        payload = json.loads(selected.read_text(encoding="utf-8"))
        assert payload["racket_target"]["target_code"] == source


def test_declared_canonical_shortcuts_really_fit_all_public_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == {"eight_connected", "top_left"}
    for pair in canonical_pairs():
        for shortcut in gen.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("room_count", (2, 3, 4))
@pytest.mark.parametrize("seed_role", ("largest", "nonlargest"))
def test_exact_override_cross_product_in_every_band(band, room_count, seed_role):
    grid = gen.generate(177, 19, difficulty=band, room_count=room_count, seed_role=seed_role)
    expected = {"room_count": room_count, "seed_role": seed_role}
    assert gen.self_check(grid) == []
    assert observed(grid) | expected == observed(grid)  # expected keys/values are present
    assert {key: observed(grid)[key] for key in expected} == expected
    assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"room_count": 1},
        {"room_count": 5},
        {"room_count": True},
        {"room_count": 2.0},
        {"room_count": "2"},
        {"seed_role": "middle"},
        {"seed_role": 1},
    ],
)
def test_invalid_overrides_are_rejected_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", BANDS)
def test_every_generated_example_refutes_both_publicly_ambiguous_shortcuts(band):
    names = set(gen.SEMANTIC_RIVALS)
    assert names == {"eight_connected", "top_left"}
    assert set(gen.LESSON_COMPETITORS) == names
    for index in range(80):
        grid = gen.generate(9000 + index, index, difficulty=band)
        expected = flood_output(grid)
        facts = observed(grid)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == expected
        assert facts["diagonal_leak"]
        assert facts["seed_not_top_left"]
        assert gen.SEMANTIC_WITNESSES["diagonal_separation"](grid)
        assert gen.SEMANTIC_WITNESSES["seed_not_top_left"](grid)
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


@pytest.mark.parametrize("band", BANDS)
def test_three_demo_lessons_and_all_query_rotations_are_identifiable(band):
    pairs = []
    for index in range(4):
        grid = gen.generate(2300 + index, 40 + index, difficulty=band)
        pairs.append({"input": grid, "output": flood_output(grid)})
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", BANDS)
def test_profile_anchors_distribution_and_determinism(band):
    shapes = set()
    room_counts = set()
    roles = set()
    inputs = set()
    for index in range(180):
        seed = 5100 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        if index % 3 == 0:
            assert profile in CANONICAL_PROFILES
        facts = observed(grid)
        shapes.add((len(grid), len(grid[0])))
        room_counts.add(facts["room_count"])
        roles.add(facts["seed_role"])
        inputs.add(json.dumps(grid, separators=(",", ":")))
    assert room_counts == {2, 3, 4}
    assert roles == {"largest", "nonlargest"}
    assert len(shapes) >= 8
    assert len(inputs) >= 160


def test_generation_is_independent_of_global_random_and_python_hash_seed():
    script = (
        "import json,random,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "random.seed(int(sys.argv[2]));"
        "[random.random() for _ in range(50)];"
        "print(json.dumps(load_generator().generate(817,61,difficulty='hard')))"
    )
    results = []
    for hash_seed, random_seed in (("1", "7"), ("901", "997")):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace"), random_seed],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[5, 5], [5]],
        [[True, 5, 5], [5, 2, 5], [5, 5, 5]],
        [[5, 5, 5], [5, 2, 5], [5, 5, 5]],
    ],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_validator_rejects_destructive_mutations():
    base = gen.generate(44, 8, room_count=3, seed_role="nonlargest")
    mutations = []

    bad_color = deepcopy(base)
    bad_color[1][1] = 9
    mutations.append(bad_color)

    open_border = deepcopy(base)
    open_border[0][1] = 0
    mutations.append(open_border)

    no_seed = deepcopy(base)
    for row in no_seed:
        for index, value in enumerate(row):
            if value == 2:
                row[index] = 0
    mutations.append(no_seed)

    extra_seed = deepcopy(base)
    placed = False
    for r, row in enumerate(extra_seed):
        for c, value in enumerate(row):
            if value == 0:
                extra_seed[r][c] = 2
                placed = True
                break
        if placed:
            break
    mutations.append(extra_seed)

    one_room = [[5] * 8]
    one_room += [[5] + [0] * 6 + [5] for _ in range(6)]
    one_room += [[5] * 8]
    one_room[2][2] = 2
    mutations.append(one_room)

    for grid in mutations:
        assert gen.self_check(grid)


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319 + index, index, room_count=2 + index % 3, seed_role=("largest", "nonlargest")[index % 2]) for index in range(24)]
    assert racket_outputs(grids) == [flood_output(grid) for grid in grids]


def test_independent_shortcut_implementations_match_declared_rivals():
    for index in range(40):
        grid = gen.generate(771 + index, index)
        assert gen.SEMANTIC_RIVALS["eight_connected"](grid) == flood_output(grid, diagonal=True)
        assert gen.SEMANTIC_RIVALS["top_left"](grid) == top_left_output(grid)
