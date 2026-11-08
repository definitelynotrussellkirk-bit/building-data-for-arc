from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "99f58784e7a0"
ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric chamber-color prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_99f5_parametric", PROTOTYPE_PATH)
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


TWO_ROOM_WITNESS = [
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
    [8, 1, 0, 0, 8, 0, 0, 2, 8],
    [8, 0, 0, 0, 8, 0, 0, 0, 8],
    [8, 0, 0, 0, 8, 0, 0, 0, 8],
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
]
OWN_TWO_ROOM = [
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
    [8, 1, 1, 1, 8, 2, 2, 2, 8],
    [8, 1, 1, 1, 8, 2, 2, 2, 8],
    [8, 1, 1, 1, 8, 2, 2, 2, 8],
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
]
NEXT_TWO_ROOM = [
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
    [8, 2, 2, 2, 8, 1, 1, 1, 8],
    [8, 2, 2, 2, 8, 1, 1, 1, 8],
    [8, 2, 2, 2, 8, 1, 1, 1, 8],
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
]

FOUR_ROOM_WITNESS = [
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
    [8, 1, 0, 0, 8, 2, 0, 0, 8],
    [8, 0, 0, 0, 8, 0, 0, 0, 8],
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
    [8, 3, 0, 0, 8, 4, 0, 0, 8],
    [8, 0, 0, 0, 8, 0, 0, 0, 8],
    [8, 8, 8, 8, 8, 8, 8, 8, 8],
]


def test_own_setting_returns_exact_selected_program_and_next_is_distinct():
    proto = load_prototype()
    canonical = proto.program({"color_source": "own"})
    alternate = proto.program({"color_source": "next"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_python_claim_mirror_fills_from_own_or_next_room_seed():
    proto = load_prototype()
    original = deepcopy(TWO_ROOM_WITNESS)
    assert proto.solve(TWO_ROOM_WITNESS, {"color_source": "own"}) == OWN_TWO_ROOM
    assert proto.solve(TWO_ROOM_WITNESS, {"color_source": "next"}) == NEXT_TWO_ROOM
    assert TWO_ROOM_WITNESS == original


def test_next_setting_uses_row_major_cyclic_room_order():
    proto = load_prototype()
    facts = proto.observables(FOUR_ROOM_WITNESS)
    assert facts["seed_colors"] == [1, 2, 3, 4]
    assert facts["next_seed_colors"] == [2, 3, 4, 1]
    output = proto.solve(FOUR_ROOM_WITNESS, {"color_source": "next"})
    for room, expected in zip(facts["rooms"], [2, 3, 4, 1], strict=True):
        assert all(output[row][col] == expected for row, col in room["cells"])


def test_default_setting_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_prototype()
    variant = Catalog(ROOT).get(TASK_ID)["variants"][0]
    for pair in [*variant["train"], *variant["test"]]:
        assert proto.solve(pair["input"], {"color_source": "own"}) == pair["output"]


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"color_source": "previous"},
        {"color_source": 1},
        {"color_source": True},
        {"color_source": "own", "extra": 1},
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
        proto.generate(seed, {"color_source": "own"}, demos, queries)


def test_generation_uses_matched_distinct_inputs_and_exact_count_prefixes():
    proto = load_prototype()
    own = proto.generate(23, {"color_source": "own"}, 6, 4)
    nxt = proto.generate(23, {"color_source": "next"}, 6, 4)
    assert len(own["train"]) == len(nxt["train"]) == 6
    assert len(own["test"]) == len(nxt["test"]) == 4
    assert [pair["input"] for pair in own["train"]] == [pair["input"] for pair in nxt["train"]]
    assert [pair["input"] for pair in own["test"]] == [pair["input"] for pair in nxt["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*own["train"], *own["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"color_source": "own"}, 2, 1)
    assert short["train"] == own["train"][:2]
    assert short["test"] == own["test"][:1]


def test_every_generated_pair_is_lawful_labeled_and_setting_distinguishing():
    proto = load_prototype()
    for seed in (0, 17, 999):
        for mode in ("own", "next"):
            settings = {"color_source": mode}
            episode = proto.generate(seed, settings, 2, 4)
            assert episode["program_solution"] == proto.program(settings)
            for pair in [*episode["train"], *episode["test"]]:
                assert proto.validate_input(pair["input"]) == []
                assert pair["output"] == proto.solve(pair["input"], settings)
            other = {"color_source": "next" if mode == "own" else "own"}
            assert any(proto.solve(pair["input"], other) != pair["output"] for pair in episode["train"])


def test_query_profiles_include_substantive_exact_30_by_30_stress():
    proto = load_prototype()
    episode = proto.generate(41, {"color_source": "next"}, 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(9, 17), (15, 19), (22, 25), (30, 30)]
    stress = episode["test"][-1]["input"]
    nonwall = sum(value != 8 for row in stress for value in row)
    assert nonwall >= 600
    assert proto.solve(stress, {"color_source": "own"}) != proto.solve(
        stress, {"color_source": "next"}
    )


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    proto = load_prototype()
    random.seed(9917)
    state = random.getstate()
    first = proto.generate(91, {"color_source": "next"}, 4, 4)
    assert random.getstate() == state
    second = proto.generate(91, {"color_source": "next"}, 4, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][1][1] = 9
    assert proto.generate(91, {"color_source": "next"}, 4, 4) == second


def test_public_view_reveals_one_query_without_private_settings_or_answers():
    proto = load_prototype()
    episode = proto.generate(5, {"color_source": "next"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert view["test"][0]["input"] == episode["test"][2]["input"]
    rendered = json.dumps(view, sort_keys=True)
    assert "color_source" not in rendered
    assert episode["test"][2]["output"] != view["test"][0].get("output")


def test_finite_demo_only_rival_audit_has_no_query_changing_survivor():
    proto = load_prototype()
    for seed in range(12):
        for mode in ("own", "next"):
            report = proto.audit_episode(seed, mode, demos=2, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
