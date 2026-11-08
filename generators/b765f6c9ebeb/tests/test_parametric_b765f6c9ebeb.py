"""Native parametric contract tests for b765f6c9ebeb."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "b765f6c9ebeb"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("_b765_parametric_adapter_test", path)
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
                bridge.define_grid("b765-parametric-grid", grid)
                return bridge.eval_text(
                    "(" + wrap_rule(program) + " b765-parametric-grid)"
                )

            yield apply


def test_default_program_is_exact_canonical_authority():
    module = _load_adapter()
    assert module.program(_settings("erase_only")) == _canonical_program()
    assert module.program(_settings("erase_then_bridge")) != _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_prefix_stable_and_rng_local(demos):
    module = _load_adapter()
    state = random.getstate()
    canonical = module.generate(17, _settings("erase_only"), demos, 4)
    bridge = module.generate(17, _settings("erase_then_bridge"), demos, 4)
    short = module.generate(17, _settings("erase_only"), 2, 1)

    assert _inputs(canonical) == _inputs(bridge)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]
    assert canonical == module.generate(17, _settings("erase_only"), demos, 4)
    assert random.getstate() == state
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4


@pytest.mark.parametrize("mode", ["erase_only", "erase_then_bridge"])
def test_two_demos_uniquely_identify_the_selected_rule(mode):
    module = _load_adapter()
    episode = module.generate(91, _settings(mode), 2, 4)
    certificate = module.teaching_certificate(episode)
    assert certificate["survivors"] == [mode]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert {
        "identity",
        "bridge_before_erase",
        "bridge_raw_only",
        "erase_then_rows_only",
        "erase_then_cols_only",
        "erase_size_le2_then_bridge",
        "erase_then_fixed_color_7",
        "erase_then_color_blind",
    } <= set(certificate["declared_hypotheses"])


def test_first_two_demos_teach_both_bridge_orientations_and_colors():
    module = _load_adapter()
    episode = module.generate(123, _settings("erase_then_bridge"), 2, 4)
    observations = [module.observe(pair["input"]) for pair in episode["train"]]
    assert [item["bridge_axes"] for item in observations] == [["row"], ["column"]]
    assert observations[0]["bridge_colors"] == [7]
    assert observations[1]["bridge_colors"] == [8]


def test_stage_b_consumes_the_cleaned_stage_a_grid():
    module = _load_adapter()
    episode = module.generate(33, _settings("erase_then_bridge"), 2, 4)
    for pair in episode["train"] + episode["test"]:
        cleaned = module.erase_singletons(pair["input"])
        assert pair["output"] == module.bridge(cleaned)
        assert pair["output"] != module.predict(pair["input"], "bridge_before_erase")
        assert pair["output"] != cleaned


def test_four_queries_cover_scale_density_boundaries_and_30x30():
    module = _load_adapter()
    episode = module.generate(7, _settings("erase_then_bridge"), 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(13, 15), (18, 20), (24, 27), (30, 30)]

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
    assert len(occupied) >= 120
    observed = module.observe(grid)
    assert set(observed["bridge_axes"]) == {"row", "column"}
    assert observed["singleton_count"] >= 6
    assert observed["survivor_count"] >= 6


def test_public_turn_hides_private_fields_answers_future_queries_and_count():
    module = _load_adapter()
    episode = module.generate(5, _settings("erase_then_bridge"), 3, 4)
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


@pytest.mark.parametrize("mode", ["erase_only", "erase_then_bridge"])
def test_claimed_labels_match_protected_racket(mode, racket):
    module = _load_adapter()
    episode = module.generate(11, _settings(mode), 2, 4)
    selected_program = module.program(_settings(mode))
    for pair in episode["train"] + episode["test"]:
        assert racket(selected_program, pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, _settings("erase_only"), 2, 4),
        (-1, _settings("erase_only"), 2, 4),
        (0, {"finish_rule": "wrong"}, 2, 4),
        (0, {"finish_rule": "erase_only", "extra": 1}, 2, 4),
        (0, _settings("erase_only"), 1, 4),
        (0, _settings("erase_only"), 7, 4),
        (0, _settings("erase_only"), 2, 0),
        (0, _settings("erase_only"), 2, 5),
        (0, _settings("erase_only"), 2, True),
    ],
)
def test_invalid_requests_fail_closed(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        _load_adapter().generate(seed, settings, demos, queries)
