from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
PARAMETRIC = HERE.parents[1]
TASK_HOME = HERE.parents[3]
REPO = HERE.parents[5]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_prototype():
    path = PARAMETRIC / "prototype.py"
    if not path.is_file():
        pytest.fail(f"missing parametric prototype: {path}")
    spec = importlib.util.spec_from_file_location("_b9ada70e7181_parametric_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "b9ada70e7181":
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def _input_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def _walls(grid):
    return [c for c in range(len(grid[0])) if all(row[c] == 8 for row in grid)]


def _pebble_count(grid):
    return sum(cell not in (0, 8) for row in grid for cell in row)


def _chamber_index_parity_output(prototype, grid, *, reverse=False):
    states = prototype.derive_chamber_states(grid, "all_down")
    for index, state in enumerate(states):
        even_index = index % 2 == 0
        state["direction"] = "up" if even_index != reverse else "down"
    return prototype.pack_columns(grid, states)


def _nuisance_parity_output(prototype, grid, metric):
    report = prototype.analyze_scene(grid)
    states = prototype.derive_chamber_states(grid, "all_down")
    for state, chamber in zip(states, report["chambers"]):
        cells = [
            (row, column["column"], value)
            for column in chamber["columns"]
            for row, value in zip(column["rows"], column["values"])
        ]
        values = [value for _row, _column, value in cells]
        if metric == "occupied_rows":
            value = len({row for row, _column, _color in cells})
        elif metric == "first_color":
            value = min(cells)[2]
        elif metric == "bottom_row":
            value = max(row for row, _column, _color in cells)
        elif metric == "unique_colors":
            value = len(set(values))
        elif metric == "color_sum":
            value = sum(values)
        elif metric == "max_color":
            value = max(values)
        else:  # pragma: no cover - test helper guard
            raise AssertionError(metric)
        state["direction"] = "up" if value % 2 == 0 else "down"
    return prototype.pack_columns(grid, states)


def _chamber_metric_rows(prototype, pairs, metric):
    rows = []
    for pair in pairs:
        report = prototype.analyze_scene(pair["input"])
        for chamber in report["chambers"]:
            values = [value for column in chamber["columns"] for value in column["values"]]
            rows.append({
                "value": chamber["count"] if metric == "count" else sum(values),
                "direction": chamber["direction"],
            })
    return rows


def _surviving_thresholds(rows):
    values = sorted({row["value"] for row in rows})
    cuts = [values[0] - 0.5, *[(a + b) / 2 for a, b in zip(values, values[1:])], values[-1] + 0.5]
    survivors = []
    for cut in cuts:
        for low_is_up in (True, False):
            def predict(value, *, _cut=cut, _low_is_up=low_is_up):
                up = (value <= _cut) == _low_is_up
                return "up" if up else "down"

            if all(predict(row["value"]) == row["direction"] for row in rows):
                survivors.append(predict)
    return survivors


def test_default_program_is_exact_canonical_bytes():
    prototype = _load_prototype()
    assert prototype.program({"gravity_policy": "all_down"}) == _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_bytes() == _canonical_program().encode("utf-8")


def test_generation_supports_two_to_six_demos_and_four_distinct_queries():
    prototype = _load_prototype()
    for demos in (2, 3, 6):
        episode = prototype.generate(17, {"gravity_policy": "chamber_parity"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({_input_key(grid) for grid in inputs}) == len(inputs)
        assert episode["program_solution"] == prototype.program(episode["settings"])


def test_certificate_reports_only_episode_shortcuts_it_actually_checked():
    prototype = _load_prototype()
    down = prototype.generate(9, {"gravity_policy": "all_down"}, 2, 4)
    parity = prototype.generate(9, {"gravity_policy": "chamber_parity"}, 2, 4)
    assert down["certificate"]["rejected_episode_shortcuts"] == []
    assert parity["certificate"]["rejected_episode_shortcuts"] == [
        "count_threshold",
        "color_sum_threshold",
    ]


def test_inputs_are_setting_neutral_for_matching_seed_and_counts():
    prototype = _load_prototype()
    down = prototype.generate(29, {"gravity_policy": "all_down"}, 3, 4)
    parity = prototype.generate(29, {"gravity_policy": "chamber_parity"}, 3, 4)
    assert [pair["input"] for pair in down["train"] + down["test"]] == [
        pair["input"] for pair in parity["train"] + parity["test"]
    ]
    assert any(
        left["output"] != right["output"]
        for left, right in zip(down["train"] + down["test"], parity["train"] + parity["test"])
    )


def test_two_demo_minimum_rejects_relevant_shortcut_rivals():
    prototype = _load_prototype()
    for seed in range(12):
        for policy in prototype.GRAVITY_POLICIES:
            episode = prototype.generate(seed, {"gravity_policy": policy}, 2, 4)
            labels = [pair["output"] for pair in episode["train"]]
            for rival in prototype.RIVAL_POLICIES[policy]:
                guesses = [prototype.transform_rival(pair["input"], rival) for pair in episode["train"]]
                assert guesses != labels, (seed, policy, rival)


def test_two_demo_minimum_rejects_static_chamber_rank_and_first_chamber_shortcuts():
    prototype = _load_prototype()
    for seed in range(12):
        episode = prototype.generate(seed, {"gravity_policy": "chamber_parity"}, 2, 4)
        labels = [pair["output"] for pair in episode["train"]]
        rank_guesses = [
            _chamber_index_parity_output(prototype, pair["input"])
            for pair in episode["train"]
        ]
        reverse_rank_guesses = [
            _chamber_index_parity_output(prototype, pair["input"], reverse=True)
            for pair in episode["train"]
        ]
        assert rank_guesses != labels, (seed, "chamber_index_parity")
        assert reverse_rank_guesses != labels, (seed, "reverse_chamber_index_parity")

        directions = [
            [state["direction"] for state in prototype.derive_chamber_states(pair["input"], "chamber_parity")]
            for pair in episode["train"]
        ]
        common = min(map(len, directions))
        assert any(directions[0][index] != directions[1][index] for index in range(common))
        assert any(
            (directions[0][index] == directions[0][0])
            != (directions[1][index] == directions[1][0])
            for index in range(1, common)
        )


def test_two_demo_minimum_rejects_color_and_row_geometry_parity_shortcuts():
    prototype = _load_prototype()
    surviving_examples = (
        (17, "occupied_rows"),
        (83, "first_color"),
        (101, "bottom_row"),
        (129, "unique_colors"),
        (215, "color_sum"),
        (731, "max_color"),
    )
    for seed, metric in surviving_examples:
        episode = prototype.generate(seed, {"gravity_policy": "chamber_parity"}, 2, 4)
        guesses = [
            _nuisance_parity_output(prototype, pair["input"], metric)
            for pair in episode["train"]
        ]
        assert guesses != [pair["output"] for pair in episode["train"]], (seed, metric)


def test_two_demo_minimum_rejects_count_and_color_sum_threshold_shortcuts():
    prototype = _load_prototype()
    for seed in range(12):
        episode = prototype.generate(seed, {"gravity_policy": "chamber_parity"}, 2, 4)
        for metric in ("count", "color_sum"):
            train_rows = _chamber_metric_rows(prototype, episode["train"], metric)
            query_rows = _chamber_metric_rows(prototype, episode["test"], metric)
            bad = [
                predict
                for predict in _surviving_thresholds(train_rows)
                if any(predict(row["value"]) != row["direction"] for row in query_rows)
            ]
            assert not bad, (seed, metric)


def test_two_demo_minimum_teaches_both_parities_at_multiple_count_magnitudes():
    prototype = _load_prototype()
    expected = {(6, "up"), (7, "down"), (8, "up"), (9, "down")}
    for seed in range(12):
        episode = prototype.generate(seed, {"gravity_policy": "chamber_parity"}, 2, 4)
        observed = {
            (chamber["count"], chamber["direction"])
            for pair in episode["train"]
            for chamber in prototype.analyze_scene(pair["input"])["chambers"]
        }
        assert expected <= observed, (seed, observed)


def test_scene_contains_crossed_controls_for_chamber_and_column_counts():
    prototype = _load_prototype()
    episode = prototype.generate(0, {"gravity_policy": "chamber_parity"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        report = prototype.analyze_scene(pair["input"])
        parities = {chamber["count"] % 2 for chamber in report["chambers"]}
        assert parities == {0, 1}
        assert report["opposite_parity_shared_stack_profiles"]
        assert report["mixed_column_count_chambers"]
        assert report["nonpalindromic_stack_count"] >= 2


def test_query_bank_includes_substantive_exact_30_by_30_stress():
    prototype = _load_prototype()
    episode = prototype.generate(3, {"gravity_policy": "chamber_parity"}, 2, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(_walls(grid)) == 3
    assert _pebble_count(grid) >= 32
    occupied_rows = {r for r, row in enumerate(grid) for cell in row if cell not in (0, 8)}
    occupied_cols = {c for row in grid for c, cell in enumerate(row) if cell not in (0, 8)}
    assert max(occupied_rows) - min(occupied_rows) >= 26
    assert max(occupied_cols) - min(occupied_cols) >= 24


def test_stage_b_changes_when_stage_a_direction_is_wrong():
    prototype = _load_prototype()
    grid = prototype.generate(5, {"gravity_policy": "chamber_parity"}, 2, 4)["test"][0]["input"]
    states = prototype.derive_chamber_states(grid, "chamber_parity")
    correct = prototype.pack_columns(grid, states)
    changed = [dict(state) for state in states]
    index = next(i for i, state in enumerate(changed) if state["direction"] == "up")
    changed[index]["direction"] = "down"
    counterfactual = prototype.pack_columns(grid, changed)
    assert correct != counterfactual


def test_python_claims_match_protected_racket_for_both_settings():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=60) as bridge:
        for policy in prototype.GRAVITY_POLICIES:
            episode = prototype.generate(11, {"gravity_policy": policy}, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert prototype.execute_rule(
                    episode["program_solution"], pair["input"], bridge=bridge
                ) == pair["output"]


def test_invalid_settings_counts_and_numeric_types_are_rejected():
    prototype = _load_prototype()
    with pytest.raises(ValueError):
        prototype.program({"gravity_policy": "sideways"})
    with pytest.raises(ValueError):
        prototype.program({"gravity_policy": "all_down", "extra": 1})
    for demos, queries in ((1, 4), (7, 4), (2, 3), (True, 4), (2, True)):
        with pytest.raises(ValueError):
            prototype.generate(0, {"gravity_policy": "all_down"}, demos, queries)


def test_certificate_rejects_duplicate_inputs_tampered_labels_and_bool_cells():
    prototype = _load_prototype()
    episode = prototype.generate(41, {"gravity_policy": "chamber_parity"}, 2, 4)

    duplicate = json.loads(json.dumps(episode))
    duplicate["test"][0]["input"] = duplicate["train"][0]["input"]
    duplicate["test"][0]["output"] = duplicate["train"][0]["output"]
    with pytest.raises(ValueError, match="distinct"):
        prototype.certify(duplicate)

    tampered = json.loads(json.dumps(episode))
    tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label mismatch"):
        prototype.certify(tampered)

    bool_cell = json.loads(json.dumps(episode))
    bool_cell["train"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="exact integer"):
        prototype.certify(bool_cell)


def test_certificate_rejects_demo_counts_outside_promised_two_to_six():
    prototype = _load_prototype()
    episode = prototype.generate(43, {"gravity_policy": "chamber_parity"}, 2, 4)

    too_few = json.loads(json.dumps(episode))
    too_few["train"] = too_few["train"][:1]
    with pytest.raises(ValueError, match=r"2\.\.6 demonstrations"):
        prototype.certify(too_few)

    too_many = json.loads(json.dumps(episode))
    extra = prototype.generate(44, {"gravity_policy": "chamber_parity"}, 6, 4)
    too_many["train"] = extra["train"] + [episode["train"][0]]
    with pytest.raises(ValueError, match=r"2\.\.6 demonstrations"):
        prototype.certify(too_many)


def test_certificate_rejects_count_threshold_lesson_even_after_named_rivals_fail():
    prototype = _load_prototype()
    settings = {"gravity_policy": "chamber_parity"}
    train_inputs = [
        prototype.sample_input(1, "query", 3),
        prototype.sample_input(2, "query", 0),
    ]
    test_inputs = [prototype.sample_input(50, "query", index) for index in range(4)]
    episode = {
        "settings": settings,
        "program_solution": prototype.program(settings),
        "train": [
            {"input": grid, "output": prototype.transform(grid, settings)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": prototype.transform(grid, settings)}
            for grid in test_inputs
        ],
    }
    with pytest.raises(ValueError, match="threshold shortcut"):
        prototype.certify(episode)
