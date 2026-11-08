"""Focused regressions for repaired base and parametric turn-after-smear family."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "69dbf44065e2"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _canonical_row():
    path = canonical_path(ROOT)
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row not found")


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("_test_69db_parametric_adapter", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _all_pairs(row):
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def test_rule_pin_and_all_canonical_labels():
    row = _canonical_row()
    program = row["program_solution"]
    expected = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "b6021aa25bf4"
    for pair in _all_pairs(row):
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_base_axis_boundaries_round_trip_in_every_band():
    boundaries = (
        {"grid_h": 5, "grid_w": 5, "n_color": 2, "n_walls": 0},
        {"grid_h": 30, "grid_w": 30, "n_color": 8, "n_walls": 4},
    )
    for difficulty in (None, "easy", "medium", "hard"):
        for index, requested in enumerate(boundaries):
            grid = GEN.generate(1100 + index, 17 + index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid, meta={"overrides": requested}) == []
            assert GEN.observe_overrides(grid) == requested
            assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": True},
        {"grid_w": 5.5},
        {"n_color": "3"},
        {"n_walls": False},
        {"grid_h": 4},
        {"grid_w": 31},
        {"n_color": 1},
        {"n_walls": 5},
        {"palette_size": 4},
    ],
)
def test_base_rejects_malformed_or_unknown_overrides(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="not-a-band")


def test_three_step_base_lesson_refutes_relevant_shortcuts():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            pairs = []
            profiles = []
            witnesses = set()
            for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(6000 + start, index, difficulty=difficulty)
                assert GEN.self_check(grid) == []
                pair = {"input": grid, "output": GEN.rule_mirror(grid)}
                pairs.append(pair)
                profiles.append(GEN.schedule_profile(6000 + start, index, difficulty))
                witnesses.update(
                    name for name, predicate in GEN.SEMANTIC_WITNESSES.items() if predicate(grid)
                )
            assert set(profiles[: GEN.EXAMPLES_NEEDED]) == set(GEN.SCHEDULE_PROFILES)
            assert set(GEN.WITNESS_RIVALS) <= witnesses
            assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_parametric_contract_default_is_byte_exact_and_settings_are_strict():
    adapter = _load_adapter()
    canonical = (PARAMETRIC / "canonical.rkt").read_text()
    assert adapter.program({"turn": "none"}) == canonical == _canonical_row()["program_solution"]
    left = adapter.program({"turn": "left"})
    right = adapter.program({"turn": "right"})
    assert len({canonical, left, right}) == 3
    for bad in ({}, {"turn": "up"}, {"turn": 1}, {"turn": "none", "extra": 1}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)

    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["parameters"] == {"turn": ["none", "left", "right"]}
    assert contract["default"] == {"turn": "none"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2


def test_parametric_inputs_are_matched_distinct_and_include_real_30x30_stress():
    adapter = _load_adapter()
    for seed in (0, 17, 991):
        episodes = {
            turn: adapter.generate(seed, {"turn": turn}, demos=2, queries=4)
            for turn in ("none", "left", "right")
        }
        visible_inputs = {
            turn: [pair["input"] for split in ("train", "test") for pair in episode[split]]
            for turn, episode in episodes.items()
        }
        assert visible_inputs["none"] == visible_inputs["left"] == visible_inputs["right"]
        serialized = [json.dumps(grid) for grid in visible_inputs["none"]]
        assert len(serialized) == len(set(serialized)) == 6
        assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in visible_inputs["none"])

        for index, grid in enumerate(visible_inputs["none"]):
            outputs = []
            for turn in ("none", "left", "right"):
                split = "train" if index < 2 else "test"
                offset = index if split == "train" else index - 2
                output = episodes[turn][split][offset]["output"]
                assert output == adapter.solve(grid, turn)
                assert output != grid
                outputs.append(output)
            assert len({json.dumps(output) for output in outputs}) == 3

        stress = next(grid for grid in visible_inputs["none"] if len(grid) == 30)
        nonzero = sum(cell != 0 for row in stress for cell in row)
        assert nonzero >= 18
        for turn in ("left", "right"):
            out = adapter.solve(stress, turn)
            changed = sum(a != b for ra, rb in zip(stress, out) for a, b in zip(ra, rb))
            assert changed >= 80


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_parametric_count_boundaries(demos, queries):
    adapter = _load_adapter()
    episode = adapter.generate(44, {"turn": "right"}, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert len({json.dumps(pair["input"]) for split in ("train", "test") for pair in episode[split]}) == demos + queries


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2, False)],
)
def test_parametric_count_rejection(demos, queries):
    adapter = _load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"turn": "left"}, demos=demos, queries=queries)


def test_two_stage_dependency_is_not_cosmetic_or_order_independent():
    adapter = _load_adapter()
    for seed in (0, 17, 23):
        episode = adapter.generate(seed, {"turn": "left"}, demos=2, queries=4)
        for pair in [*episode["train"], *episode["test"]]:
            grid = pair["input"]
            actual = adapter.solve(grid, "left")
            assert actual != adapter.skip_stage_a(grid, "left")
            assert actual != adapter.wrong_order(grid, "left")
            facts = adapter.dependency_facts(grid, "left")
            assert facts["active_endpoints"]
            assert facts["stage_a_changed_cells"] >= 1
            assert facts["stage_b_changed_cells"] >= 1


def test_parametric_scene_and_solver_reject_malformed_numeric_types():
    adapter = _load_adapter()
    valid = adapter.generate(9, {"turn": "right"}, demos=2, queries=1)["test"][0]["input"]
    malformed = copy.deepcopy(valid)
    malformed[0][0] = True
    with pytest.raises((TypeError, ValueError)):
        adapter.solve(malformed, "right")
    malformed = copy.deepcopy(valid)
    malformed[0] = malformed[0][:-1]
    with pytest.raises((TypeError, ValueError)):
        adapter.solve(malformed, "right")


def test_thin_scene_reserves_both_turn_corridors_from_extra_vertical_trails():
    """Regression: seed 53/pair 4 used to make right-turn equal canonical."""
    adapter = _load_adapter()
    episode_by_turn = {
        turn: adapter.generate(53, {"turn": turn}, demos=2, queries=4)
        for turn in ("none", "left", "right")
    }
    outputs = [episode_by_turn[turn]["test"][2]["output"] for turn in ("none", "left", "right")]
    assert len({json.dumps(output) for output in outputs}) == 3
    grid = episode_by_turn["none"]["test"][2]["input"]
    assert adapter.dependency_facts(grid, "left")["stage_b_changed_cells"] >= 1
    assert adapter.dependency_facts(grid, "right")["stage_b_changed_cells"] >= 1
