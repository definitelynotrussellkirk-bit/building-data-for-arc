from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "97b3f59b5cc4"
ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric connectivity prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_97b3_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_program() -> str:
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


DIAGONAL_WITNESS = [
    [2, 0, 0, 0, 3],
    [2, 0, 0, 0, 3],
    [0, 2, 2, 0, 0],
    [0, 2, 0, 4, 0],
    [0, 0, 0, 0, 0],
]
FOUR_OUTPUT = [
    [2, 0, 0, 0, 3],
    [2, 0, 0, 0, 3],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
EIGHT_OUTPUT = [
    [2, 0, 0, 0, 3],
    [2, 0, 0, 0, 3],
    [0, 2, 2, 0, 0],
    [0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0],
]


def test_four_setting_returns_exact_selected_program_and_eight_is_distinct():
    proto = load_prototype()
    canonical = proto.program({"connectivity": "four"})
    alternate = proto.program({"connectivity": "eight"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_python_claim_mirror_distinguishes_diagonal_border_inheritance():
    proto = load_prototype()
    original = deepcopy(DIAGONAL_WITNESS)
    assert proto.solve(DIAGONAL_WITNESS, {"connectivity": "four"}) == FOUR_OUTPUT
    assert proto.solve(DIAGONAL_WITNESS, {"connectivity": "eight"}) == EIGHT_OUTPUT
    assert DIAGONAL_WITNESS == original


def test_default_setting_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_prototype()
    variant = Catalog(ROOT).get(TASK_ID)["variants"][0]
    for pair in [*variant["train"], *variant["test"]]:
        assert proto.solve(pair["input"], {"connectivity": "four"}) == pair["output"]


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"connectivity": "diagonal"},
        {"connectivity": 4},
        {"connectivity": True},
        {"connectivity": "four", "extra": 1},
        None,
    ],
)
def test_invalid_settings_fail_loudly(settings):
    proto = load_prototype()
    with pytest.raises(ValueError):
        proto.program(settings)
    with pytest.raises(ValueError):
        proto.generate(0, settings, 2, 4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 2, 4),
        (-1, 2, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 2, 0),
        (0, 2, 5),
        (0, True, 4),
        (0, 2, False),
    ],
)
def test_invalid_request_boundaries_fail_loudly(seed, demos, queries):
    proto = load_prototype()
    with pytest.raises(ValueError):
        proto.generate(seed, {"connectivity": "four"}, demos, queries)


def test_generation_uses_matched_distinct_inputs_and_exact_count_prefixes():
    proto = load_prototype()
    four = proto.generate(23, {"connectivity": "four"}, 6, 4)
    eight = proto.generate(23, {"connectivity": "eight"}, 6, 4)
    assert len(four["train"]) == len(eight["train"]) == 6
    assert len(four["test"]) == len(eight["test"]) == 4
    assert [pair["input"] for pair in four["train"]] == [pair["input"] for pair in eight["train"]]
    assert [pair["input"] for pair in four["test"]] == [pair["input"] for pair in eight["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*four["train"], *four["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"connectivity": "four"}, 2, 1)
    assert short["train"] == four["train"][:2]
    assert short["test"] == four["test"][:1]


def test_every_generated_pair_is_lawful_labeled_and_setting_distinguishing():
    proto = load_prototype()
    for seed in (0, 17, 999):
        for mode in ("four", "eight"):
            settings = {"connectivity": mode}
            episode = proto.generate(seed, settings, 2, 4)
            assert episode["program_solution"] == proto.program(settings)
            for pair in [*episode["train"], *episode["test"]]:
                assert proto.validate_input(pair["input"]) == []
                assert pair["output"] == proto.solve(pair["input"], settings)
            other = {"connectivity": "eight" if mode == "four" else "four"}
            assert any(
                proto.solve(pair["input"], other) != pair["output"]
                for pair in episode["train"]
            )


def test_query_profiles_include_substantive_exact_30_by_30_stress():
    proto = load_prototype()
    episode = proto.generate(41, {"connectivity": "eight"}, 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(11, 13), (17, 19), (24, 27), (30, 30)]
    stress = episode["test"][-1]["input"]
    nonzero = sum(value != 0 for row in stress for value in row)
    assert nonzero >= 80
    assert proto.solve(stress, {"connectivity": "four"}) != proto.solve(
        stress, {"connectivity": "eight"}
    )


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    proto = load_prototype()
    random.seed(9917)
    state = random.getstate()
    first = proto.generate(91, {"connectivity": "eight"}, 4, 4)
    assert random.getstate() == state
    second = proto.generate(91, {"connectivity": "eight"}, 4, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert proto.generate(91, {"connectivity": "eight"}, 4, 4) == second


def test_public_view_reveals_one_query_without_private_settings_or_answers():
    proto = load_prototype()
    episode = proto.generate(5, {"connectivity": "eight"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert view["test"][0]["input"] == episode["test"][2]["input"]
    rendered = json.dumps(view, sort_keys=True)
    assert "connectivity" not in rendered
    assert episode["test"][2]["output"] != view["test"][0].get("output")


def test_finite_demo_only_rival_audit_has_no_query_changing_survivor():
    proto = load_prototype()
    for seed in range(12):
        for mode in ("four", "eight"):
            report = proto.audit_episode(seed, mode, demos=2, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
