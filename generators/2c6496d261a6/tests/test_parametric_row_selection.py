from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "2c6496d261a6"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
PROTO_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_proto():
    return _load(PROTO_PATH, "_test_2c_row_selection")


def _variant_pairs(variant):
    pairs = list(variant.get("train", []))
    test = variant.get("test", [])
    pairs.extend([test] if isinstance(test, dict) else test)
    return pairs


def selected_program() -> str:
    from arcpuzzles import Catalog

    programs = {
        variant["program_solution"]
        for variant in Catalog(ROOT).get(TASK_ID)["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_selected_source_and_alternate_is_complete_rule():
    proto = load_proto()
    canonical = proto.program({"row_selection": "one_row_only"})
    alternate = proto.program({"row_selection": "fewest_rows"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            before = deepcopy(pair["input"])
            assert proto.solve(pair["input"], {"row_selection": "one_row_only"}) == pair["output"]
            assert pair["input"] == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"row_selection": "bad"}, {"row_selection": 1},
     {"row_selection": True}, {"row_selection": "one_row_only", "extra": 1}],
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
        proto.generate(seed, {"row_selection": "one_row_only"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    canonical = proto.generate(23, {"row_selection": "one_row_only"}, 6, 4)
    alternate = proto.generate(23, {"row_selection": "fewest_rows"}, 6, 4)
    assert [pair["input"] for pair in canonical["train"]] == [pair["input"] for pair in alternate["train"]]
    assert [pair["input"] for pair in canonical["test"]] == [pair["input"] for pair in alternate["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*canonical["train"], *canonical["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"row_selection": "one_row_only"}, 2, 1)
    assert short["train"] == canonical["train"][:2]
    assert short["test"] == canonical["test"][:1]

    random.seed(991)
    state = random.getstate()
    replay = proto.generate(23, {"row_selection": "one_row_only"}, 6, 4)
    assert random.getstate() == state
    assert replay == canonical and replay is not canonical
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"row_selection": "one_row_only"}, 6, 4) == canonical


def test_two_demos_identify_each_setting_and_cover_mixed_and_no_single_row_scenes():
    proto = load_proto()
    for mode in proto.MODES:
        episode = proto.generate(7, {"row_selection": mode}, 2, 4)
        assert all(proto.validate_input(pair["input"]) == [] for pair in [*episode["train"], *episode["test"]])
        survivors = []
        for candidate in proto.MODES:
            if all(proto.solve(pair["input"], {"row_selection": candidate}) == pair["output"] for pair in episode["train"]):
                survivors.append(candidate)
        assert survivors == [mode]
        assert any(not any(value for row in pair["output"] for value in row) for pair in episode["train"]) if mode == "one_row_only" else True
        assert any(any(value for row in pair["output"] for value in row) for pair in episode["train"])


def test_minimum_row_intermediate_controls_filter_and_wrong_threshold_changes_output():
    proto = load_proto()
    pair = proto.generate(91, {"row_selection": "fewest_rows"}, 3, 4)["train"][0]
    value = proto.intermediate(pair["input"], {"row_selection": "fewest_rows"})
    assert value["threshold"] >= 2
    assert value["selected_colors"]
    assert pair["output"] == proto.output_from_intermediate(pair["input"], value)
    wrong = {**value, "threshold": 1, "selected_colors": [
        color for color, rows in value["row_counts"].items() if rows == 1
    ]}
    assert proto.output_from_intermediate(pair["input"], wrong) != pair["output"]


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"row_selection": "fewest_rows"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(9, 12), (15, 18), (24, 27), (30, 30)]
    stress = episode["test"][-1]
    assert sum(value != 0 for row in stress["input"] for value in row) >= 90
    assert proto.solve(stress["input"], {"row_selection": "one_row_only"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"row_selection": "fewest_rows"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "row_selection" not in rendered
    assert "fewest_rows" not in rendered
    assert "output" not in view["test"][0]


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 9, 17, 97):
        for mode in proto.MODES:
            report = proto.audit_episode(seed, mode, demos=2, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
