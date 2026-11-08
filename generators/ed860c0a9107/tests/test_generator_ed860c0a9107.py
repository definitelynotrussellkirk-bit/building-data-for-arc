from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as _canonical_pairs
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)


def canonical_pairs(task_id):
    return _canonical_pairs(task_id, root=ROOT, labeled_only=True)


def canonical_rule_source(task_id):
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id and row.get("program_solution"):
            return str(row["program_solution"])
    raise AssertionError(f"missing canonical rule source for {task_id}")


def canonical_rule_hash(task_id):
    source = canonical_rule_source(task_id)
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pinned_seed(task_id, band, index):
    payload = f"profile-floor:v1:{task_id}:{band}:{index}".encode()
    return int(hashlib.sha256(payload).hexdigest()[:12], 16)


def _data_path(relative):
    for base in (ROOT / "data", ROOT / "shared" / "data"):
        candidate = base / relative
        if candidate.is_file():
            return candidate
    raise AssertionError(f"missing data file {relative}")


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.ed860c0a9107.generator"
)


EXACT_AXES = {
    "grid_h",
    "grid_w",
    "n_containers",
    "box_h",
    "box_w",
}
BASE_SOLUTIONS = (
    _data_path("base/solutions/augmented/7c9b52a0__096faaeaedad.json"),
    _data_path("base/solutions/training/7c9b52a0__ed860c0a9107.json"),
)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_and_canonical_inputs_are_owned():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) >= 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_public_axis_contract_is_small_observable_and_non_degenerate():
    assert set(gen.AXES) == EXACT_AXES
    assert "texture" not in gen.AXES
    assert "position_bias" not in gen.AXES


@pytest.mark.parametrize(
    "grid_h,grid_w,n_containers,box_h,box_w",
    [
        (14, 14, 4, 5, 5),
        (14, 22, 3, 2, 5),
        (22, 14, 2, 5, 2),
        (22, 22, 4, 2, 2),
    ],
)
def test_boundary_override_combinations_are_constructive_and_exact(
    grid_h: int,
    grid_w: int,
    n_containers: int,
    box_h: int,
    box_w: int,
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_containers": n_containers,
        "box_h": box_h,
        "box_w": box_w,
    }
    grid = gen.generate(4100 + grid_h + grid_w, n_containers, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


def test_invalid_and_unknown_controls_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")
    with pytest.raises((TypeError, ValueError), match="integer"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="integer"):
        gen.generate(1, 0, box_w=5.0)


def test_every_generated_input_contains_a_real_priority_counterexample():
    witness = gen.SEMANTIC_WITNESSES["priority_overlap"]
    rival = gen.SEMANTIC_RIVALS["last_visible"]
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = gen.generate(5200 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert witness(grid) is True
            assert rival(grid) != gen.rule_mirror(grid)


def test_last_visible_is_the_strongest_canonical_fitting_shortcut():
    rival = gen.CANONICAL_SHORTCUTS["last_visible"]
    for pair in canonical_pairs(gen.TASK_ID):
        assert rival(pair["input"]) == pair["output"]


def test_each_rotated_lesson_refutes_the_declared_rival():
    pairs = []
    for index in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(6301, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    rival = gen.LESSON_COMPETITORS["last_visible"]
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in canonical_pairs(gen.TASK_ID)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _pinned_seed(gen.TASK_ID, band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            hits += _profile(grid) in canonical_profiles
        assert hits >= 1, band


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261005)
    state = random.getstate()
    first = gen.generate(701, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(701, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(701, 9, difficulty="hard")


def test_all_selected_rule_authorities_match_canonical_text_exactly():
    selected = canonical_rule_source(gen.TASK_ID)
    for path in BASE_SOLUTIONS:
        payload = json.loads(path.read_text())
        assert payload["racket_target"]["target_code"] == selected
        assert payload["racket_target"]["raw_code"] != ""
