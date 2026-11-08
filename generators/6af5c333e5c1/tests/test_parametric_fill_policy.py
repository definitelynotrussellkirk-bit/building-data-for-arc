from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "6af5c333e5c1"
ROOT = Path(__file__).resolve().parents[3]
PROTO_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_proto():
    assert PROTO_PATH.is_file(), "parametric fill-policy prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_6af_fill_policy", PROTO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid(value):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in value]


def _variant_pairs(variant):
    pairs = list(variant.get("train", []))
    test = variant.get("test", [])
    if isinstance(test, dict):
        pairs.append(test)
    else:
        pairs.extend(test)
    return pairs


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


def test_default_program_is_exact_selected_source_and_alternate_is_complete_rule():
    proto = load_proto()
    canonical = proto.program({"fill_policy": "all_pairs"})
    alternate = proto.program({"fill_policy": "top_span_threshold"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            source = _grid(pair["input"])
            before = deepcopy(source)
            assert proto.solve(source, {"fill_policy": "all_pairs"}) == _grid(pair["output"])
            assert source == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"fill_policy": "bad"}, {"fill_policy": 1},
     {"fill_policy": True}, {"fill_policy": "all_pairs", "extra": 1}],
)
def test_invalid_settings_fail_loudly(settings):
    proto = load_proto()
    with pytest.raises(ValueError):
        proto.program(settings)
    with pytest.raises(ValueError):
        proto.generate(0, settings, 3, 4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 3, 4), (-1, 3, 4), (0, 1, 4), (0, 7, 4),
     (0, 3, 0), (0, 3, 5), (0, True, 4), (0, 3, False)],
)
def test_invalid_request_boundaries_fail_loudly(seed, demos, queries):
    proto = load_proto()
    with pytest.raises(ValueError):
        proto.generate(seed, {"fill_policy": "all_pairs"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    all_pairs = proto.generate(23, {"fill_policy": "all_pairs"}, 6, 4)
    threshold = proto.generate(23, {"fill_policy": "top_span_threshold"}, 6, 4)
    assert [p["input"] for p in all_pairs["train"]] == [p["input"] for p in threshold["train"]]
    assert [p["input"] for p in all_pairs["test"]] == [p["input"] for p in threshold["test"]]
    encoded = [json.dumps(p["input"]) for p in [*all_pairs["train"], *all_pairs["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"fill_policy": "all_pairs"}, 2, 1)
    assert short["train"] == all_pairs["train"][:2]
    assert short["test"] == all_pairs["test"][:1]

    random.seed(819)
    state = random.getstate()
    replay = proto.generate(23, {"fill_policy": "all_pairs"}, 6, 4)
    assert random.getstate() == state
    assert replay == all_pairs and replay is not all_pairs
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"fill_policy": "all_pairs"}, 6, 4) == all_pairs


def test_generated_scenes_expose_top_pair_threshold_and_distractors():
    proto = load_proto()
    episode = proto.generate(7, {"fill_policy": "top_span_threshold"}, 3, 4)
    for pair in [*episode["train"], *episode["test"]]:
        assert proto.validate_input(pair["input"]) == []
        facts = proto.scene_facts(pair["input"])
        assert len(facts["pair_rows"]) >= 4
        assert facts["top_pair_row"] > 0
        assert facts["singleton_rows"]
        assert facts["triple_rows"]
        spans = [row["span"] for row in facts["pair_rows"]]
        assert min(spans) < facts["threshold"] < max(spans)
        assert proto.solve(pair["input"], {"fill_policy": "all_pairs"}) != proto.solve(
            pair["input"], {"fill_policy": "top_span_threshold"}
        )


def test_top_span_intermediate_changes_result_when_replaced_by_bottom_span():
    proto = load_proto()
    pair = proto.generate(91, {"fill_policy": "top_span_threshold"}, 3, 4)["test"][0]
    intermediate = proto.intermediate(pair["input"])
    assert intermediate["top_threshold"] != intermediate["bottom_threshold"]
    intended = proto.solve(pair["input"], {"fill_policy": "top_span_threshold"})
    wrong = proto.solve_with_threshold(pair["input"], intermediate["bottom_threshold"])
    assert intended != wrong


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"fill_policy": "top_span_threshold"}, 3, 4)
    shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert shapes == [(8, 11), (14, 18), (22, 26), (30, 30)]
    stress = episode["test"][-1]
    facts = proto.scene_facts(stress["input"])
    assert len(facts["pair_rows"]) >= 9
    output_blue = sum(v == 1 for row in stress["output"] for v in row)
    assert output_blue >= 100
    assert proto.solve(stress["input"], {"fill_policy": "all_pairs"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"fill_policy": "top_span_threshold"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "fill_policy" not in rendered
    assert "top_span_threshold" not in rendered
    assert episode["test"][2]["output"] != view["test"][0].get("output")


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 17, 97):
        for mode in ("all_pairs", "top_span_threshold"):
            report = proto.audit_episode(seed, mode, demos=3, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]


def test_authoring_preflight_compat_iterates_single_test_mapping():
    helper = PROTO_PATH.with_name("authoring_preflight.py")
    assert helper.is_file(), "compatibility preflight has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_6af_preflight_compat", helper)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pair = {"input": [[0]], "output": [[0]]}
    record = {"train": [pair], "test": pair}
    assert list(module._pairs(record, "train")) == [pair]
    assert list(module._pairs(record, "test")) == [pair]
