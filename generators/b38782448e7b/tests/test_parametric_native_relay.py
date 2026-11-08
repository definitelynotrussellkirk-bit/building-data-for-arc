"""Native parametric contract tests for b38782448e7b."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "b38782448e7b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("_b387_native_adapter_test", path)
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
    return {"finish_rule": value}


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
                bridge.define_grid("b387-native-grid", grid)
                return bridge.eval_text("(" + wrap_rule(program) + " b387-native-grid)")

            yield apply


def test_default_program_is_exact_canonical_authority():
    module = _load_adapter()
    assert module.program(_settings("toggle_only")) == _canonical_program()
    assert module.program(_settings("toggle_then_relay")) != _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_prefix_stable_and_rng_local(demos):
    module = _load_adapter()
    state = random.getstate()
    canonical = module.generate(17, _settings("toggle_only"), demos, 4)
    alternate = module.generate(17, _settings("toggle_then_relay"), demos, 4)
    short = module.generate(17, _settings("toggle_only"), 2, 1)

    assert _inputs(canonical) == _inputs(alternate)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    assert canonical == module.generate(17, _settings("toggle_only"), demos, 4)
    assert random.getstate() == state
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4


@pytest.mark.parametrize("mode", ["toggle_only", "toggle_then_relay"])
def test_two_demos_uniquely_identify_selected_rule_and_declared_rivals(mode):
    module = _load_adapter()
    episode = module.generate(91, _settings(mode), 2, 4)
    certificate = module.teaching_certificate(episode)
    assert certificate["survivors"] == [mode]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert {
        "identity",
        "relay_first_active",
        "relay_last_active",
        "relay_min_completed",
        "relay_raw_source",
        "relay_right_of_cue",
        "all_top_controls_then_relay",
    } <= set(certificate["declared_hypotheses"])


def test_stage_b_relays_the_completed_stage_a_column_and_wrong_intermediate_differs():
    module = _load_adapter()
    episode = module.generate(33, _settings("toggle_then_relay"), 2, 4)
    for pair in episode["train"] + episode["test"]:
        completed = module.toggle_only(pair["input"])
        observed = module.observe(pair["input"])
        source_col = observed["winning_source_column"]
        destination_col = observed["destination_column"]
        assert pair["output"] == module.relay_column(completed, source_col, destination_col)
        assert pair["output"] != completed
        assert pair["output"] != module.predict(pair["input"], "relay_raw_source")


def test_four_queries_cover_scale_density_boundaries_and_30x30():
    module = _load_adapter()
    episode = module.generate(7, _settings("toggle_then_relay"), 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(13, 15), (18, 20), (24, 27), (30, 30)]

    grid = episode["test"][-1]["input"]
    bg = module.observe(grid)["background"]
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != bg
    ]
    assert min(row for row, _ in occupied) == 0
    assert max(row for row, _ in occupied) == 29
    assert min(col for _, col in occupied) == 0
    assert max(col for _, col in occupied) == 29
    assert len(occupied) >= 110
    observed = module.observe(grid)
    assert observed["unique_winner"] is True
    assert len(observed["active_columns"]) >= 3
    assert observed["raw_source_column"] != observed["completed_source_column"]


def test_public_turn_hides_private_fields_answers_future_queries_and_count():
    module = _load_adapter()
    episode = module.generate(5, _settings("toggle_then_relay"), 3, 4)
    visible = module.public_turn(episode, 0)
    assert visible == {
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    }

    poisoned = deepcopy(episode)
    poisoned["settings"] = {"private": "secret"}
    poisoned["program_solution"] = "secret"
    poisoned["seed"] = 999
    for pair in poisoned["test"]:
        pair["output"] = [[9]]
    for pair in poisoned["test"][1:]:
        pair["input"] = [[9]]
    assert module.public_turn(poisoned, 0) == visible


@pytest.mark.parametrize("mode", ["toggle_only", "toggle_then_relay"])
def test_claimed_labels_match_protected_racket(mode, racket):
    module = _load_adapter()
    episode = module.generate(11, _settings(mode), 2, 4)
    selected_program = module.program(_settings(mode))
    for pair in episode["train"] + episode["test"]:
        assert racket(selected_program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, _settings("toggle_only"), 2, 4),
        (-1, _settings("toggle_only"), 2, 4),
        (0, {"finish_rule": "wrong"}, 2, 4),
        (0, {"finish_rule": "toggle_only", "extra": 1}, 2, 4),
        (0, _settings("toggle_only"), 1, 4),
        (0, _settings("toggle_only"), 7, 4),
        (0, _settings("toggle_only"), 2, 0),
        (0, _settings("toggle_only"), 2, 5),
        (0, _settings("toggle_only"), 2, True),
    ],
)
def test_invalid_requests_fail_closed(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        _load_adapter().generate(seed, settings, demos, queries)
