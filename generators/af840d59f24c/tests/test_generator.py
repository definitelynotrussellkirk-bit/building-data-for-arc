"""Regression contract for the zero-column rank generator repair."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    first_seen_rank,
    frequency_rank,
    intended_output,
    load_generator,
    modal_nonzero,
    racket_outputs,
    row_local_rank,
    zero_stats,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
TASK_ID = "af840d59f24c"
RULE_HASH = "dbb5a0b9e901"
PROFILES = ("canonical_sparse", "wide_many", "dense_mixed", "scrambled_order")
SCHEDULE = (
    "canonical_sparse", "dense_mixed", "wide_many", "dense_mixed", "canonical_sparse",
    "canonical_sparse", "dense_mixed", "scrambled_order", "dense_mixed", "canonical_sparse",
)



def test_reference_probe_finds_the_nearest_portable_runtime_when_relocated(tmp_path):
    runtime = tmp_path / "portable-runtime"
    (runtime / "shared/runtime").mkdir(parents=True)
    (runtime / "shared/data/canonical").mkdir(parents=True)
    (runtime / "tools").mkdir(parents=True)
    shutil.copy2(
        ROOT / "shared/runtime/reviewer_support.py",
        runtime / "shared/runtime/reviewer_support.py",
    )
    shutil.copy2(
        canonical_path(ROOT),
        runtime / "shared/data/canonical/puzzles.jsonl",
    )
    relocated = runtime / "tools/reference_probe.py"
    shutil.copy2(HOME / "workspace/reference_probe.py", relocated)
    script = f"""
import importlib.util
import sys
sys.path.insert(0, {str(runtime / 'shared/runtime')!r})
from reviewer_support import find_root
spec = importlib.util.spec_from_file_location('relocated_probe', {str(relocated)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.ROOT == find_root(module.__file__)
assert len(module.canonical_pairs()) == 4
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

def test_rule_pin_and_all_canonical_pairs_are_preserved():
    assert gen.RULE_HASH == RULE_HASH
    assert gen.TASK_ID == TASK_ID
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
def test_each_exact_profile_is_lawful_observable_and_deterministic(difficulty, profile):
    for seed in (0, 17, 99173):
        grid = gen.generate(seed, 11, difficulty=difficulty, scene_profile=profile)
        assert grid == gen.generate(seed, 11, difficulty=difficulty, scene_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.rule_mirror(grid) == intended_output(grid)
        stats = zero_stats(grid)
        assert 4 <= len(stats["columns"]) <= 8
        assert sum(stats["counts"].values()) >= 8
        assert len(stats["row_counts"]) >= 3
        assert len(set(stats["counts"].values())) >= 2
        assert any(count >= 2 for count in stats["row_counts"].values())
        if profile == "dense_mixed":
            assert len(stats["row_counts"]) == len(grid)
            assert any(count == 1 for count in stats["row_counts"].values())
        else:
            assert len(stats["row_counts"]) < len(grid)

        palette = set(stats["nonzero_counts"])
        full_columns = [c for c, count in stats["counts"].items() if count == len(grid)]
        if profile == "canonical_sparse":
            assert (len(grid), len(grid[0]), palette, len(stats["columns"])) == (10, 10, {5}, 4)
            assert not full_columns
        elif profile == "wide_many":
            assert len(grid[0]) > 10 and palette == {9}
            assert 6 <= len(stats["columns"]) <= 8
            assert not full_columns
        elif profile == "dense_mixed":
            assert len(grid[0]) > 10 and modal_nonzero(grid) == 8
            assert palette == {8, 9}
            assert full_columns
        else:
            assert len(grid[0]) > 10 and palette == {6}
            assert len(stats["columns"]) == 5
            assert not full_columns


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_cycles_profiles_and_every_grid_refutes_order_shortcuts(difficulty):
    observed = []
    assert gen.SCHEDULE_PROFILES == SCHEDULE
    for sample_index in range(3 * len(SCHEDULE)):
        grid = gen.generate(1234, sample_index, difficulty=difficulty)
        profile = SCHEDULE[sample_index % len(SCHEDULE)]
        observed.append(gen.observe_overrides(grid)["scene_profile"])
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        expected = intended_output(grid)
        assert row_local_rank(grid) != expected
        assert first_seen_rank(grid) != expected
        assert frequency_rank(grid) != expected
    assert observed == list(SCHEDULE) * 3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 1},
        {"scene_profile": True},
    ],
)
def test_invalid_overrides_are_rejected_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[5, 5], [5]],
        [[5] * 10 for _ in range(10)],
        [[0] * 10 for _ in range(10)],
        [[0 if (r, c) == (5, 5) else 5 for c in range(10)] for r in range(10)],
        [[0 if 4 <= r < 6 and 4 <= c < 6 else 5 for c in range(10)] for r in range(10)],
        [[0 if r == 5 and 2 <= c < 8 else 5 for c in range(10)] for r in range(10)],
    ],
)
def test_validator_rejects_malformed_and_minimal_impostors(grid):
    assert gen.self_check(grid)


def test_canonical_shortcuts_are_real_and_generated_lessons_refute_them():
    expected_names = {"base5_only", "ten_by_ten_only", "clamp_after_four", "erase_nonmodal"}
    assert set(gen.CANONICAL_SHORTCUTS) == expected_names
    for pair in canonical_pairs():
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]

    grids = [gen.generate(73, index) for index in range(4)]
    outputs = [intended_output(grid) for grid in grids]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != output for grid, output in zip(grids, outputs)), name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_five_pair_window_is_identifiable_under_all_query_rotations(difficulty):
    assert gen.EXAMPLES_NEEDED == 4
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        pairs = []
        for offset in range(5):
            grid = gen.generate(1009 + start, start + offset, difficulty=difficulty)
            pairs.append({"input": grid, "output": intended_output(grid)})
        for held_out in range(5):
            query = pairs[held_out]
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    start,
                    held_out,
                    name,
                )


def test_generation_is_fresh_and_does_not_touch_global_random_state():
    random.seed(20261008)
    before = random.getstate()
    first = gen.generate(319, 27, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(319, 27, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0 if first[0][0] else 1
    assert first != second


def test_real_racket_reference_matches_independent_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(600 + index, index) for index in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_selected_racket_authority_is_exactly_synchronized_to_canonical_program():
    import json

    authority_path = (
        ROOT / "shared/data/base/solutions/training/575b1a71__af840d59f24c.json"
    )
    authority = json.loads(authority_path.read_text())
    canonical = __import__("reference_probe").canonical_record()
    assert authority["racket_target"]["target_code"] == canonical["program_solution"]
    assert authority["racket_target"]["raw_code"]


def test_difficulty_bands_change_hidden_layout_without_changing_profile():
    for sample_index, profile in enumerate(SCHEDULE):
        grids = [
            gen.generate(808, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({repr(grid) for grid in grids}) >= 2
        assert all(gen.observe_overrides(grid) == {"scene_profile": profile} for grid in grids)
