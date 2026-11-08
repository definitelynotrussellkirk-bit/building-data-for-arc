from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "62757098b2dd"
ROOT = Path(__file__).resolve().parents[3]
PROTO_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_proto():
    assert PROTO_PATH.is_file(), "parametric palette-scope prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_627_palette_scope", PROTO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    canonical = proto.program({"palette_scope": "local"})
    alternate = proto.program({"palette_scope": "largest_rectangle"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            before = deepcopy(pair["input"])
            assert proto.solve(pair["input"], {"palette_scope": "local"}) == pair["output"]
            assert pair["input"] == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"palette_scope": "bad"}, {"palette_scope": 1},
     {"palette_scope": True}, {"palette_scope": "local", "extra": 1}],
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
        proto.generate(seed, {"palette_scope": "local"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    local = proto.generate(23, {"palette_scope": "local"}, 6, 4)
    global_ = proto.generate(23, {"palette_scope": "largest_rectangle"}, 6, 4)
    assert [p["input"] for p in local["train"]] == [p["input"] for p in global_["train"]]
    assert [p["input"] for p in local["test"]] == [p["input"] for p in global_["test"]]
    encoded = [json.dumps(p["input"]) for p in [*local["train"], *local["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"palette_scope": "local"}, 2, 1)
    assert short["train"] == local["train"][:2]
    assert short["test"] == local["test"][:1]

    random.seed(991)
    state = random.getstate()
    replay = proto.generate(23, {"palette_scope": "local"}, 6, 4)
    assert random.getstate() == state
    assert replay == local and replay is not local
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"palette_scope": "local"}, 6, 4) == local


def test_generated_scenes_have_unique_nonfirst_nonlast_largest_anchor_and_distinguish_settings():
    proto = load_proto()
    episode = proto.generate(7, {"palette_scope": "largest_rectangle"}, 3, 4)
    for pair in [*episode["train"], *episode["test"]]:
        assert proto.validate_input(pair["input"]) == []
        facts = proto.scene_facts(pair["input"])
        assert len(facts["rectangles"]) == 3
        areas = [r["area"] for r in facts["rectangles"]]
        assert areas.count(max(areas)) == 1
        anchor_index = areas.index(max(areas))
        assert anchor_index == 1
        assert facts["rectangles"][0]["perimeter"] > facts["rectangles"][1]["perimeter"]
        assert proto.solve(pair["input"], {"palette_scope": "local"}) != proto.solve(
            pair["input"], {"palette_scope": "largest_rectangle"}
        )


def test_largest_rectangle_intermediate_controls_every_target_rectangle():
    proto = load_proto()
    pair = proto.generate(91, {"palette_scope": "largest_rectangle"}, 3, 4)["test"][0]
    intermediate = proto.intermediate(pair["input"])
    assert intermediate["anchor_index"] == 1
    assert len(intermediate["marker_colors"]) == 4
    intended = proto.solve(pair["input"], {"palette_scope": "largest_rectangle"})
    wrong = proto.solve_with_anchor(pair["input"], 0)
    assert intended != wrong
    for rect in intermediate["rectangles"]:
        observed = proto.quadrant_colors(intended, rect["bbox"])
        assert observed == intermediate["marker_colors"]


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"palette_scope": "largest_rectangle"}, 3, 4)
    shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert shapes == [(16, 20), (21, 25), (27, 29), (30, 30)]
    stress = episode["test"][-1]
    facts = proto.scene_facts(stress["input"])
    assert sum(r["area"] for r in facts["rectangles"]) >= 100
    assert proto.solve(stress["input"], {"palette_scope": "local"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"palette_scope": "largest_rectangle"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "palette_scope" not in rendered
    assert "largest_rectangle" not in rendered
    assert episode["test"][2]["output"] != view["test"][0].get("output")


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 17, 97):
        for mode in ("local", "largest_rectangle"):
            report = proto.audit_episode(seed, mode, demos=3, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
