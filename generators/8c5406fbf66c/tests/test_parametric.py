"""Native parametric contract for the 2x2-window count relay family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK = "8c5406fbf66c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native parametric adapter is not implemented"
    name = "_test_8c5406fbf66c_parametric"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).open()
        if (row := json.loads(line)).get("task_id") == TASK
        and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.fixture
def racket_bridge():
    from arc_repl.racket_bridge import RacketBridge

    bridge = RacketBridge()
    try:
        yield bridge
    finally:
        bridge.close()


def test_canonical_default_is_exact_and_alternative_is_distinct():
    adapter = load_adapter()
    assert adapter.program({"window_scope": "all"}) == canonical_program()
    assert adapter.program({"window_scope": "key_count_relay"}) != canonical_program()


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 4)])
def test_counts_are_independent_inputs_are_matched_and_prefixes_are_stable(demos, queries):
    adapter = load_adapter()
    episodes = [
        adapter.generate(17, {"window_scope": scope}, demos, queries)
        for scope in ("all", "key_count_relay")
    ]
    for episode in episodes:
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        pairs = episode["train"] + episode["test"]
        assert len({frozen(pair["input"]) for pair in pairs}) == demos + queries
        assert all(
            type(value) is int and 0 <= value <= 9
            for pair in pairs
            for row in pair["input"]
            for value in row
        )
    assert [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]] == [
        pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]
    ]
    assert episodes[0]["train"] != episodes[1]["train"]

    smaller = adapter.generate(17, {"window_scope": "key_count_relay"}, 2, 1)
    larger = adapter.generate(17, {"window_scope": "key_count_relay"}, 6, 4)
    assert smaller["train"] == larger["train"][:2]
    assert smaller["test"] == larger["test"][:1]


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (2**63, 3, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, False),
        (0, 3, 0),
        (0, 3, 5),
    ],
)
def test_strict_seed_and_count_validation(seed, demos, queries):
    with pytest.raises(ValueError):
        load_adapter().generate(seed, {"window_scope": "all"}, demos, queries)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"window_scope": True},
        {"window_scope": "unknown"},
        {"window_scope": "all", "extra": 1},
    ],
)
def test_strict_setting_validation(settings):
    with pytest.raises(ValueError):
        load_adapter().program(settings)


def test_relay_has_an_input_dependent_a_to_b_dependency():
    adapter = load_adapter()
    episode = adapter.generate(23, {"window_scope": "key_count_relay"}, 3, 4)
    seen = set()
    for pair in episode["train"] + episode["test"]:
        analysis = adapter.prototype.analyze_relay(pair["input"])
        seen.add(analysis["source_window_count"])
        assert analysis["target_rank"] == analysis["source_window_count"]
        assert pair["output"] == adapter.prototype.solve_python(
            pair["input"], "key_count_relay"
        )
    assert seen == {1, 2, 3}

    witness = episode["test"][0]["input"]
    analysis = adapter.prototype.analyze_relay(witness)
    assert analysis["source_window_count"] != 1
    expected = adapter.prototype.solve_python(witness, "key_count_relay")
    wrong = adapter.prototype.solve_relay_with_intermediate(witness, 1)
    assert wrong != expected


def test_two_demos_refute_declared_shortcuts_without_query_answers():
    adapter = load_adapter()
    for scope in ("all", "key_count_relay"):
        episode = adapter.generate(13, {"window_scope": scope}, 2, 4)
        report = adapter.prototype.teaching_check(episode, scope)
        assert report["setting_survivors"] == [scope]
        assert report["rival_survivors"] == []
        assert report["used_query_answers"] is False


def test_teaching_profiles_break_area_vs_window_count_and_position_shortcuts():
    adapter = load_adapter()
    episode = adapter.generate(13, {"window_scope": "key_count_relay"}, 2, 4)
    for pair in episode["train"]:
        analysis = adapter.prototype.analyze_relay(pair["input"])
        by_area = analysis["candidate_colors_by_area"]
        by_windows = analysis["candidate_colors_by_window_count"]
        rank = analysis["source_window_count"] - 1
        assert by_area[rank] != by_windows[rank]
    report = adapter.prototype.teaching_check(episode, "key_count_relay")
    assert {"window_count_rank", "top_left_rank", "bottom_right_rank"} <= set(
        report["refuted_rivals"]
    )


def test_four_queries_include_a_substantive_30x30_stress_scene():
    adapter = load_adapter()
    episode = adapter.generate(5, {"window_scope": "all"}, 2, 4)
    grids = [pair["input"] for pair in episode["test"]]
    assert len({frozen(grid) for grid in grids}) == 4
    stress = grids[3]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 190
    assert any(stress[0]) and any(stress[-1])
    assert any(row[0] for row in stress) and any(row[-1] for row in stress)
    assert load_adapter().prototype.analyze_relay(stress)["source_window_count"] == 2


def test_public_turn_rejects_malformed_visible_grids_but_ignores_private_answers():
    adapter = load_adapter()
    episode = adapter.generate(37, {"window_scope": "key_count_relay"}, 3, 4)

    bad_train_input = deepcopy(episode)
    bad_train_input["train"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="exact ARC integers"):
        adapter.prototype.public_turn(bad_train_input, 0)

    bad_train_output = deepcopy(episode)
    bad_train_output["train"][0]["output"][0].pop()
    with pytest.raises(ValueError, match="rectangular"):
        adapter.prototype.public_turn(bad_train_output, 0)

    bad_query_input = deepcopy(episode)
    bad_query_input["test"][0]["input"] = [[0, 0], [0, False]]
    with pytest.raises(ValueError, match="exact ARC integers"):
        adapter.prototype.public_turn(bad_query_input, 0)

    private_answer_only = deepcopy(episode)
    private_answer_only["test"][0]["output"] = [[True]]
    assert adapter.prototype.public_turn(private_answer_only, 0) == adapter.prototype.public_turn(
        episode, 0
    )


def test_public_turn_masks_private_state_and_is_first_turn_invariant():
    adapter = load_adapter()
    one = adapter.generate(31, {"window_scope": "key_count_relay"}, 3, 1)
    four = adapter.generate(31, {"window_scope": "key_count_relay"}, 3, 4)
    assert adapter.prototype.turn_bytes(one, 0) == adapter.prototype.turn_bytes(four, 0)

    public = adapter.prototype.public_turn(four, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    raw = adapter.prototype.turn_bytes(four, 0)
    assert b"window_scope" not in raw
    assert b"program_solution" not in raw

    changed = deepcopy(four)
    changed["settings"] = {"window_scope": "secret"}
    changed["seed"] = 999
    changed["program_solution"] = "secret"
    changed["test"][0]["output"] = [[True]]
    assert adapter.prototype.turn_bytes(changed, 0) == raw


@pytest.mark.parametrize("scope", ["all", "key_count_relay"])
def test_protected_racket_matches_python_on_ordinary_and_large_inputs(scope, racket_bridge):
    adapter = load_adapter()
    episode = adapter.generate(7, {"window_scope": scope}, 2, 4)
    program = wrap_rule(adapter.program({"window_scope": scope}))
    for pair in (episode["train"][0], episode["test"][3]):
        racket_bridge.define_grid("parametric_grid", pair["input"])
        actual = racket_bridge.eval_text(f"({program} parametric_grid)")
        assert actual == pair["output"]
