"""Native parametric contract tests for c1ee27b39d13."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "c1ee27b39d13"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("_c1ee_parametric_adapter_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _settings(value: str) -> dict[str, str]:
    return {"column_order": value}


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ARC_REPL_SKIP_BANK_HELPERS", "1")
        with RacketBridge(timeout=12) as bridge:
            assert bridge.runtime_identity["backend"] == "racket"
            assert bridge.runtime_identity["protected"] is True

            def apply(program, grid):
                bridge.define_grid("c1ee-parametric-grid", grid)
                return bridge.eval_text(
                    "(" + wrap_rule(program) + " c1ee-parametric-grid)"
                )

            yield apply


def test_default_program_is_exact_canonical_authority():
    module = _load_adapter()
    assert module.program(_settings("source")) == _canonical_program()
    assert module.program(_settings("first_row_rank")) != _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_prefix_stable_and_rng_local(demos):
    module = _load_adapter()
    state = random.getstate()
    source = module.generate(17, _settings("source"), demos, 4)
    ranked = module.generate(17, _settings("first_row_rank"), demos, 4)
    short = module.generate(17, _settings("source"), 2, 1)

    assert _inputs(source) == _inputs(ranked)
    assert short["train"] == source["train"][:2]
    assert short["test"] == source["test"][:1]
    assert source == module.generate(17, _settings("source"), demos, 4)
    assert random.getstate() == state
    assert len(source["train"]) == demos
    assert len(source["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(source)]
    assert len(serialized) == len(set(serialized)) == demos + 4


@pytest.mark.parametrize("mode", ["source", "first_row_rank"])
def test_two_demos_uniquely_identify_the_selected_rule(mode):
    module = _load_adapter()
    episode = module.generate(91, _settings(mode), 2, 4)
    certificate = module.teaching_certificate(episode)
    assert certificate["survivors"] == [mode]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert {
        "reverse_columns",
        "first_row_descending",
        "last_row_rank",
        "second_row_rank",
        "column_sum_rank",
        "row_rank",
        "transpose",
    } <= set(certificate["declared_hypotheses"])


def test_ranked_rule_uses_the_extracted_first_row_as_column_key():
    module = _load_adapter()
    episode = module.generate(123, _settings("first_row_rank"), 2, 4)
    for pair in episode["train"] + episode["test"]:
        extracted = module.extract(pair["input"])
        expected_order = sorted(range(len(extracted[0])), key=lambda col: extracted[0][col])
        assert expected_order != list(range(len(expected_order)))
        assert pair["output"] == [
            [row[col] for col in expected_order] for row in extracted
        ]
        assert pair["output"] != module.predict(pair["input"], "last_row_rank")


def test_four_queries_cover_scale_density_and_exact_30x30_stress():
    module = _load_adapter()
    episode = module.generate(7, _settings("first_row_rank"), 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(13, 15), (18, 21), (24, 27), (30, 30)]

    grid = episode["test"][-1]["input"]
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert min(row for row, _ in occupied) == 0
    assert max(row for row, _ in occupied) == 29
    assert min(col for _, col in occupied) == 0
    assert max(col for _, col in occupied) == 29
    assert len(occupied) >= 350
    observed = module.observe(grid)
    assert observed["selected_rows"] >= 5
    assert observed["selected_cols"] >= 6


def test_public_turn_hides_settings_program_answers_future_queries_and_count():
    module = _load_adapter()
    episode = module.generate(5, _settings("first_row_rank"), 3, 4)
    visible = module.public_turn(episode, 0)
    assert visible == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}

    poisoned = deepcopy(episode)
    poisoned["settings"] = {"private": "secret"}
    poisoned["program_solution"] = "secret"
    poisoned["seed"] = 999
    for pair in poisoned["test"]:
        pair["output"] = [[9]]
    for pair in poisoned["test"][1:]:
        pair["input"] = [[9]]
    assert module.public_turn(poisoned, 0) == visible
    assert "query" not in json.dumps(visible).lower()


@pytest.mark.parametrize("mode", ["source", "first_row_rank"])
def test_claimed_labels_match_protected_racket(mode, racket):
    module = _load_adapter()
    episode = module.generate(11, _settings(mode), 2, 4)
    selected_program = module.program(_settings(mode))
    for pair in episode["train"] + episode["test"]:
        assert racket(selected_program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, _settings("source"), 2, 4),
        (-1, _settings("source"), 2, 4),
        (0, {"column_order": "wrong"}, 2, 4),
        (0, {"column_order": "source", "extra": 1}, 2, 4),
        (0, _settings("source"), 1, 4),
        (0, _settings("source"), 7, 4),
        (0, _settings("source"), 2, 0),
        (0, _settings("source"), 2, 5),
        (0, _settings("source"), 2, True),
    ],
)
def test_invalid_requests_fail_closed(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        _load_adapter().generate(seed, settings, demos, queries)
