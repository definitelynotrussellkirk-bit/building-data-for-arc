from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "9c26c4b2c305"
TASK_DIR = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
POLICIES = (
    "aligned",
    "reflect_bottom",
    "top_heavier_reflect_bottom",
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load_module(PROTOTYPE_PATH, "parametric_alignment_prototype")


def _canonical_source() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _top_heavy_fixture() -> list[list[int]]:
    return [
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [4, 4, 4, 4],
        [2, 0, 0, 0],
        [0, 0, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]


def _bottom_heavy_fixture() -> list[list[int]]:
    return [
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [4, 4, 4, 4],
        [2, 2, 0, 0],
        [0, 2, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]


def test_prototype_exports_required_interface():
    prototype = _prototype()

    for name in (
        "canonical_program",
        "program_for",
        "episode_inputs",
        "apply_policy",
        "generate_episode",
    ):
        assert callable(getattr(prototype, name))


def test_programs_preserve_exact_default_and_are_three_distinct_rules():
    prototype = _prototype()
    canonical = _canonical_source()

    assert prototype.POLICIES == POLICIES
    assert prototype.DEFAULT_POLICY == "aligned"
    assert prototype.canonical_program() == canonical
    assert prototype.program_for("aligned") == canonical
    programs = {policy: prototype.program_for(policy) for policy in POLICIES}
    assert len(set(programs.values())) == 3
    assert "(- w c 1)" in programs["reflect_bottom"]
    assert "top-count" in programs["top_heavier_reflect_bottom"]
    assert "bottom-count" in programs["top_heavier_reflect_bottom"]
    assert "reflect?" in programs["top_heavier_reflect_bottom"]

    for bad in (None, True, "", "palette_reflect", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)


def test_apply_policy_matches_two_hand_derived_gate_branches():
    prototype = _prototype()
    top_heavy = _top_heavy_fixture()
    bottom_heavy = _bottom_heavy_fixture()

    aligned_top = [
        [3, 3, 0, 0],
        [0, 3, 3, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    reflected_top = [
        [3, 3, 0, 3],
        [0, 3, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    aligned_bottom = [
        [3, 3, 0, 0],
        [0, 3, 3, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    reflected_bottom = [
        [3, 0, 3, 3],
        [0, 0, 3, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]

    assert prototype.apply_policy(top_heavy, "aligned") == aligned_top
    assert prototype.apply_policy(top_heavy, "reflect_bottom") == reflected_top
    assert prototype.apply_policy(top_heavy, "top_heavier_reflect_bottom") == reflected_top
    assert prototype.apply_policy(bottom_heavy, "aligned") == aligned_bottom
    assert prototype.apply_policy(bottom_heavy, "reflect_bottom") == reflected_bottom
    assert prototype.apply_policy(bottom_heavy, "top_heavier_reflect_bottom") == aligned_bottom


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _occupancy_counts(grid: list[list[int]]) -> tuple[int, int]:
    width = len(grid[0])
    top = sum(grid[row][col] != 0 for row in range(4) for col in range(width))
    bottom = sum(grid[5 + row][col] != 0 for row in range(4) for col in range(width))
    return top, bottom


def test_episode_inputs_are_deterministic_distinct_sensitive_and_stress_width_30():
    prototype = _prototype()
    generator = load_selected_generator(TASK_ID, root=ROOT)[0]

    first = prototype.episode_inputs(17, demos=2, queries=4)
    second = prototype.episode_inputs(17, demos=2, queries=4)
    assert first == second
    assert first is not second
    assert [len(grid[0]) for grid in first] == [4, 4, 18, 21, 27, 30]
    assert [_occupancy_counts(grid)[0] > _occupancy_counts(grid)[1] for grid in first] == [
        True,
        False,
        False,
        True,
        False,
        True,
    ]
    assert len({_freeze(grid) for grid in first}) == 6

    for grid in first:
        assert len(grid) == 9
        assert generator.self_check(grid) == []
        assert all(type(cell) is int for row in grid for cell in row)
        assert prototype.apply_policy(grid, "aligned") != prototype.apply_policy(
            grid, "reflect_bottom"
        )

    maximum = prototype.episode_inputs(23, demos=6, queries=8)
    assert len(maximum) == 14
    assert len({_freeze(grid) for grid in maximum}) == 14
    assert 30 in [len(grid[0]) for grid in maximum]


def test_two_demos_identify_every_selected_policy_and_inputs_are_matched():
    prototype = _prototype()
    episodes = {
        policy: prototype.generate_episode(29, policy, demos=2, queries=4)
        for policy in POLICIES
    }

    input_sets = [
        [pair["input"] for pair in episode["train"] + episode["test"]]
        for episode in episodes.values()
    ]
    assert input_sets[1:] == input_sets[:-1]

    for selected, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(selected)
        assert all(set(pair) == {"input", "output"} for pair in episode["train"])
        assert all(set(pair) == {"input", "output"} for pair in episode["test"])
        survivors = [
            candidate
            for candidate in POLICIES
            if all(
                prototype.apply_policy(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        assert survivors == [selected]
        assert all(
            pair["output"] == prototype.apply_policy(pair["input"], selected)
            for pair in episode["train"] + episode["test"]
        )


def test_seed_policy_and_pair_count_validation_is_strict():
    prototype = _prototype()

    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(bad_seed, demos=2, queries=4)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, "aligned", demos=2, queries=4)

    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=bad_demos, queries=4)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, "aligned", demos=bad_demos, queries=4)

    for bad_queries in (False, 0, 9, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.episode_inputs(0, demos=2, queries=bad_queries)
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, "aligned", demos=2, queries=bad_queries)

    for bad_policy in (None, True, "", "palette_reflect", 0):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, bad_policy, demos=2, queries=4)


def test_protected_racket_matches_python_at_width_4_and_width_30():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    prototype = _prototype()
    inputs = prototype.episode_inputs(41, demos=2, queries=4)
    witnesses = (inputs[0], inputs[-1])
    assert [len(grid[0]) for grid in witnesses] == [4, 30]

    with RacketBridge(timeout=20, max_calls_before_restart=16) as bridge:
        for grid_index, grid in enumerate(witnesses):
            name = f"g{grid_index}"
            bridge.define_grid(name, grid)
            for policy in POLICIES:
                callable_source = wrap_rule(prototype.program_for(policy))
                actual = bridge.eval_text(f"({callable_source} {name})")
                assert actual == prototype.apply_policy(grid, policy)
        assert bridge.runtime_identity["protected"] is True


ADAPTER_PATH = TASK_DIR / "workspace" / "parametric" / "adapter.py"
PROMOTION_PATH = TASK_DIR / "workspace" / "parametric" / "promotion.json"


def test_native_adapter_and_contract_have_exact_bounded_surface():
    prototype = _prototype()
    adapter = _load_module(ADAPTER_PATH, "parametric_alignment_adapter")
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/9c26c4b2c305/workspace/parametric/adapter.py",
        "parameters": {"alignment_policy": list(POLICIES)},
        "default": {"alignment_policy": "aligned"},
        "limits": {"demos": [2, 6], "queries": [1, 8]},
    }
    for policy in POLICIES:
        settings = {"alignment_policy": policy}
        assert adapter.program(settings) == prototype.program_for(policy)
        assert adapter.generate(53, settings, 2, 4) == prototype.generate_episode(
            53, policy, 2, 4
        )


def test_adapter_rejects_wrong_setting_shapes_and_values():
    adapter = _load_module(ADAPTER_PATH, "parametric_alignment_adapter_validation")

    for bad in (
        None,
        [],
        {},
        {"alignment_policy": "aligned", "extra": 1},
        {"policy": "aligned"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, bad, 2, 4)

    for bad_value in (None, True, "", "palette_reflect", 0):
        settings = {"alignment_policy": bad_value}
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 4)


def _palette_tuple(grid: list[list[int]]) -> tuple[int, int, int]:
    top = {cell for row in grid[:4] for cell in row if cell}
    bottom = {cell for row in grid[5:] for cell in row if cell}
    assert len(top) == len(bottom) == 1
    return next(iter(top)), next(iter(bottom)), grid[4][0]


def test_minimum_demos_break_palette_conditioned_reflection_shortcuts():
    prototype = _prototype()
    episode = prototype.generate_episode(
        71, "top_heavier_reflect_bottom", demos=2, queries=4
    )
    first, second = episode["train"]
    first_palette = _palette_tuple(first["input"])
    assert _palette_tuple(second["input"]) == first_palette

    def palette_equal_reflects(pair):
        policy = (
            "reflect_bottom"
            if _palette_tuple(pair["input"]) == first_palette
            else "aligned"
        )
        return prototype.apply_policy(pair["input"], policy)

    def palette_unequal_reflects(pair):
        policy = (
            "reflect_bottom"
            if _palette_tuple(pair["input"]) != first_palette
            else "aligned"
        )
        return prototype.apply_policy(pair["input"], policy)

    assert any(palette_equal_reflects(pair) != pair["output"] for pair in episode["train"])
    assert any(palette_unequal_reflects(pair) != pair["output"] for pair in episode["train"])


def test_minimum_demos_break_width_parity_reflection_shortcuts():
    prototype = _prototype()
    episode = prototype.generate_episode(
        71, "top_heavier_reflect_bottom", demos=2, queries=4
    )

    def even_width_reflects(pair):
        policy = "reflect_bottom" if len(pair["input"][0]) % 2 == 0 else "aligned"
        return prototype.apply_policy(pair["input"], policy)

    def odd_width_reflects(pair):
        policy = "reflect_bottom" if len(pair["input"][0]) % 2 == 1 else "aligned"
        return prototype.apply_policy(pair["input"], policy)

    assert any(even_width_reflects(pair) != pair["output"] for pair in episode["train"])
    assert any(odd_width_reflects(pair) != pair["output"] for pair in episode["train"])


def test_minimum_demos_match_width_and_palette_while_requiring_opposite_actions():
    prototype = _prototype()
    episode = prototype.generate_episode(
        71, "top_heavier_reflect_bottom", demos=2, queries=4
    )
    first, second = episode["train"]
    assert len(first["input"][0]) == len(second["input"][0])
    assert _palette_tuple(first["input"]) == _palette_tuple(second["input"])
    assert _occupancy_counts(first["input"])[0] > _occupancy_counts(first["input"])[1]
    assert _occupancy_counts(second["input"])[0] < _occupancy_counts(second["input"])[1]
    assert first["output"] == prototype.apply_policy(first["input"], "reflect_bottom")
    assert second["output"] == prototype.apply_policy(second["input"], "aligned")


def test_public_projection_hides_setting_program_and_query_answers():
    prototype = _prototype()
    episode = prototype.generate_episode(83, "top_heavier_reflect_bottom", 2, 4)
    public = json.loads(public_challenge_bytes(episode))

    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "alignment_policy" not in serialized
    assert "top_heavier_reflect_bottom" not in serialized
    assert "program_solution" not in serialized
    assert len(public_challenge_id(episode)) == 64
