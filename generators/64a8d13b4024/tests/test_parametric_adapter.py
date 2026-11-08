"""Behavioral tests for the native 64a8d13b4024 parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"

CANONICAL_PROGRAM = """(rule!
  (let ((totals (map (lambda (color) (length (find-color g color))) (list 1 2 3))))
    (grid-from-fn 6 3
      (lambda (r c)
        (let ((color (+ c 1))
              (hgt (list-ref totals c)))
          (if (>= r (- 6 hgt)) color 0))))))"""


def adapter():
    assert ADAPTER_PATH.is_file(), "native parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("parametric_64a8d13b4024_test", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_grid_4_4_6():
    grid = [[0] * 8 for _ in range(8)]
    for row, col in ((0, 0), (1, 2), (5, 5), (7, 7)):
        grid[row][col] = 1
    for row, col in ((0, 7), (2, 2), (4, 4), (7, 0)):
        grid[row][col] = 2
    for row, col in ((0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3)):
        grid[row][col] = 3
    return grid


def visible_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_byte_exact_selected_canonical():
    mod = adapter()
    assert (PARAMETRIC / "canonical.rkt").read_text() == CANONICAL_PROGRAM
    assert mod.program({"column_order": "color_order"}) == CANONICAL_PROGRAM


def test_count_ranked_transform_uses_counts_and_low_color_tie_break():
    mod = adapter()
    grid = literal_grid_4_4_6()
    assert mod.counts(grid) == (4, 4, 6)
    assert mod.ordered_bars(grid, "count_descending") == ((3, 6), (1, 4), (2, 4))
    assert mod.transform(grid, {"column_order": "color_order"}) == [
        [0, 0, 3],
        [0, 0, 3],
        [1, 2, 3],
        [1, 2, 3],
        [1, 2, 3],
        [1, 2, 3],
    ]
    assert mod.transform(grid, {"column_order": "count_descending"}) == [
        [3, 0, 0],
        [3, 0, 0],
        [3, 1, 2],
        [3, 1, 2],
        [3, 1, 2],
        [3, 1, 2],
    ]


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"column_order": "unknown"},
        {"column_order": 1},
        {"column_order": "color_order", "extra": True},
    ],
)
def test_settings_fail_closed(bad):
    mod = adapter()
    with pytest.raises(ValueError):
        mod.program(bad)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": True},
        {"queries": 0},
        {"queries": 5},
        {"queries": False},
    ],
)
def test_request_bounds_reject_invalid_typed_values(kwargs):
    mod = adapter()
    values = {
        "seed": 0,
        "settings": {"column_order": "color_order"},
        "demos": 3,
        "queries": 4,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        mod.generate(**values)


@pytest.mark.parametrize("setting", ["color_order", "count_descending"])
def test_generation_is_deterministic_and_does_not_mutate_settings(setting):
    mod = adapter()
    settings = {"column_order": setting}
    before = copy.deepcopy(settings)
    first = mod.generate(17, settings, 3, 4)
    second = mod.generate(17, settings, 3, 4)
    assert first == second
    assert settings == before
    assert first["settings"] == before
    assert first["seed"] == 17
    assert first["program_solution"] == mod.program(before)


def test_identical_seed_and_counts_use_identical_inputs_across_settings():
    mod = adapter()
    fixed = mod.generate(23, {"column_order": "color_order"}, 6, 4)
    ranked = mod.generate(23, {"column_order": "count_descending"}, 6, 4)
    assert visible_inputs(fixed) == visible_inputs(ranked)
    assert any(
        a["output"] != b["output"]
        for a, b in zip(fixed["train"] + fixed["test"], ranked["train"] + ranked["test"])
    )


@pytest.mark.parametrize("setting", ["color_order", "count_descending"])
def test_counts_are_independent_and_prefix_stable(setting):
    mod = adapter()
    settings = {"column_order": setting}
    full = mod.generate(31, settings, 6, 4)
    for demos in range(2, 7):
        for queries in range(1, 5):
            episode = mod.generate(31, settings, demos, queries)
            assert episode["train"] == full["train"][:demos]
            assert episode["test"] == full["test"][:queries]


@pytest.mark.parametrize("setting", ["color_order", "count_descending"])
def test_two_demonstrations_identify_setting_and_reject_declared_rivals(setting):
    mod = adapter()
    settings = {"column_order": setting}
    episode = mod.generate(41, settings, 2, 4)
    check = mod.teaching_check(episode, settings)
    assert check["survivors"] == [settings]
    assert check["surviving_rivals"] == []
    assert check["basis"] == "demonstrations_only"
    assert len(check["rivals_tested"]) >= 8


def test_teaching_check_uses_demonstrations_only_not_query_answers():
    mod = adapter()
    settings = {"column_order": "count_descending"}
    episode = mod.generate(43, settings, 2, 4)
    original = mod.teaching_check(episode, settings)
    tampered = copy.deepcopy(episode)
    tampered["test"][0]["output"] = [[9]]
    assert mod.teaching_check(tampered, settings) == original


def test_four_queries_are_distinct_profiled_and_include_substantive_30x30():
    mod = adapter()
    episode = mod.generate(47, {"column_order": "count_descending"}, 3, 4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(14, 16), (19, 21), (24, 27), (30, 30)]
    assert len({json.dumps(grid) for grid in visible_inputs(episode)}) == 7
    stress = episode["test"][3]["input"]
    nonzero = [(r, c, v) for r, row in enumerate(stress) for c, v in enumerate(row) if v]
    assert len(nonzero) >= 100
    assert {v for _, _, v in nonzero} >= {1, 2, 3, 4, 5, 6, 7, 8, 9}
    assert {0, 29} <= {r for r, _, _ in nonzero}
    assert {0, 29} <= {c for _, c, _ in nonzero}
    assert mod.counts(stress) == (4, 4, 6)


def test_query_profiles_exercise_unique_orders_and_ties():
    mod = adapter()
    episode = mod.generate(53, {"column_order": "count_descending"}, 3, 4)
    assert [mod.counts(pair["input"]) for pair in episode["test"]] == [
        (6, 2, 5),
        (3, 6, 1),
        (2, 5, 5),
        (4, 4, 6),
    ]
    assert [mod.ordered_bars(pair["input"], "count_descending") for pair in episode["test"]] == [
        ((1, 6), (3, 5), (2, 2)),
        ((2, 6), (1, 3), (3, 1)),
        ((2, 5), (3, 5), (1, 2)),
        ((3, 6), (1, 4), (2, 4)),
    ]


def test_public_turn_masks_answers_and_future_queries_without_mutating_episode():
    mod = adapter()
    episode = mod.generate(59, {"column_order": "count_descending"}, 3, 4)
    snapshot = copy.deepcopy(episode)
    turn = mod.public_turn(episode, 2)
    assert set(turn) == {"train", "test"}
    assert turn["train"] == episode["train"]
    assert turn["test"] == [{"input": episode["test"][2]["input"]}]
    assert "output" not in turn["test"][0]
    assert "settings" not in turn and "program_solution" not in turn and "seed" not in turn
    assert episode == snapshot


def test_first_query_is_identical_in_single_and_four_query_requests():
    mod = adapter()
    settings = {"column_order": "color_order"}
    one = mod.generate(61, settings, 3, 1)
    four = mod.generate(61, settings, 3, 4)
    assert mod.public_turn(one, 0) == mod.public_turn(four, 0)


def test_count_to_rank_to_render_causal_intermediate_changes_same_input_output():
    mod = adapter()
    grid = mod.generate(67, {"column_order": "count_descending"}, 2, 1)["train"][0]["input"]
    assert mod.counts(grid) == (2, 6, 4)
    ranked = mod.ordered_bars(grid, "count_descending")
    wrong = mod.ordered_bars(grid, "color_order")
    assert ranked == ((2, 6), (3, 4), (1, 2))
    assert wrong == ((1, 2), (2, 6), (3, 4))
    assert mod.render_bars(ranked) != mod.render_bars(wrong)
    assert mod.transform(grid, {"column_order": "count_descending"}) == mod.render_bars(ranked)


def test_every_generated_grid_and_label_uses_exact_integer_colors_within_30x30():
    mod = adapter()
    for setting in ("color_order", "count_descending"):
        episode = mod.generate(71, {"column_order": setting}, 6, 4)
        for pair in episode["train"] + episode["test"]:
            for grid in (pair["input"], pair["output"]):
                assert 1 <= len(grid) <= 30
                assert 1 <= len(grid[0]) <= 30
                assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)


def test_reusable_audit_tool_checks_settings_prefixes_rivals_and_stress(tmp_path):
    audit_path = PARAMETRIC / "audit_lessons.py"
    assert audit_path.is_file(), "reusable lesson audit has not been built"
    spec = importlib.util.spec_from_file_location("audit_64a8d13b4024_test", audit_path)
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    summary = audit.run_audit([0, 1])
    assert summary["status"] == "passed"
    assert summary["seeds"] == 2
    assert summary["episodes"] == 48
    assert summary["matched_input_checks"] == 24
    assert summary["harmful_survivors"] == []
    assert summary["exact_30x30_pairs"] == 12
    public = audit.write_public_samples(tmp_path, seed=0)
    assert public["files"] == 8
    assert public["duplicate_public_ids"] == []
    assert all(path.suffix == ".json" for path in tmp_path.iterdir())


def test_promotion_contract_declares_native_adapter_settings_and_independent_counts():
    contract_path = PARAMETRIC / "promotion.json"
    assert contract_path.is_file(), "promotion contract has not been built"
    contract = json.loads(contract_path.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/64a8d13b4024/workspace/parametric/adapter.py",
        "parameters": {"column_order": ["color_order", "count_descending"]},
        "default": {"column_order": "color_order"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/64a8d13b4024/workspace/parametric/canonical.rkt",
            "generators/64a8d13b4024/workspace/parametric/count_descending.rkt",
        ],
    }
