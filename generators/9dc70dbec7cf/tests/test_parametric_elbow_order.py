from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "9dc70dbec7cf"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
PROTO_PATH = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR_PATH = HOME / "generator.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_proto():
    return _load(PROTO_PATH, "_test_9dc_elbow_order")


def load_generator():
    return _load(GENERATOR_PATH, "_test_9dc_generator")


def _variant_pairs(variant):
    pairs = list(variant.get("train", []))
    test = variant.get("test", [])
    pairs.extend([test] if isinstance(test, dict) else test)
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


def test_base_generator_controls_are_exact_and_advertised_domain_is_honest():
    gen = load_generator()
    assert "palette_size" not in gen.AXES
    assert "n_distinct_colors" not in gen.AXES
    assert "no_pairs" not in gen.AXES.get("texture", {}).get("valid", "")
    assert "single_pair" not in gen.AXES.get("texture", {}).get("valid", "")

    grid = gen.generate(
        8123,
        0,
        difficulty="medium",
        grid_h=10,
        grid_w=12,
        n_pairs=5,
        palette_kind="warm",
    )
    counts = Counter(value for row in grid for value in row if value)
    assert len(counts) == 5
    assert set(counts.values()) == {2}
    assert set(counts) <= set(gen.PALETTES["warm"])
    assert gen.self_check(grid, difficulty="medium") == []

    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, n_pairs=True)


def test_default_program_is_exact_selected_source_and_alternate_is_complete_rule():
    proto = load_proto()
    canonical = proto.program({"elbow_order": "horizontal_then_vertical"})
    alternate = proto.program({"elbow_order": "vertical_then_horizontal"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            before = deepcopy(pair["input"])
            assert proto.solve(pair["input"], {"elbow_order": "horizontal_then_vertical"}) == pair["output"]
            assert pair["input"] == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"elbow_order": "bad"}, {"elbow_order": 1},
     {"elbow_order": True}, {"elbow_order": "horizontal_then_vertical", "extra": 1}],
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
        proto.generate(seed, {"elbow_order": "horizontal_then_vertical"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    horizontal = proto.generate(23, {"elbow_order": "horizontal_then_vertical"}, 6, 4)
    vertical = proto.generate(23, {"elbow_order": "vertical_then_horizontal"}, 6, 4)
    assert [pair["input"] for pair in horizontal["train"]] == [pair["input"] for pair in vertical["train"]]
    assert [pair["input"] for pair in horizontal["test"]] == [pair["input"] for pair in vertical["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*horizontal["train"], *horizontal["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"elbow_order": "horizontal_then_vertical"}, 2, 1)
    assert short["train"] == horizontal["train"][:2]
    assert short["test"] == horizontal["test"][:1]

    random.seed(991)
    state = random.getstate()
    replay = proto.generate(23, {"elbow_order": "horizontal_then_vertical"}, 6, 4)
    assert random.getstate() == state
    assert replay == horizontal and replay is not horizontal
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"elbow_order": "horizontal_then_vertical"}, 6, 4) == horizontal


def test_constructed_scenes_are_lawful_and_each_teaching_demo_distinguishes_order():
    proto = load_proto()
    episode = proto.generate(7, {"elbow_order": "horizontal_then_vertical"}, 6, 4)
    for pair in [*episode["train"], *episode["test"]]:
        assert proto.validate_input(pair["input"]) == []
    for pair in episode["train"][:2]:
        assert proto.solve(pair["input"], {"elbow_order": "horizontal_then_vertical"}) != proto.solve(
            pair["input"], {"elbow_order": "vertical_then_horizontal"}
        )


def test_path_intermediate_controls_count_map_and_wrong_order_changes_output():
    proto = load_proto()
    pair = proto.generate(91, {"elbow_order": "vertical_then_horizontal"}, 3, 4)["test"][0]
    intermediate = proto.intermediate(pair["input"], {"elbow_order": "vertical_then_horizontal"})
    assert len(intermediate["paths"]) >= 3
    assert any(path["bend_multiplicity"] == 2 for path in intermediate["paths"])
    assert intermediate["coverage_histogram"].get("2", 0) > 0
    assert pair["output"] == proto.output_from_intermediate(pair["input"], intermediate)
    assert pair["output"] != proto.solve(pair["input"], {"elbow_order": "horizontal_then_vertical"})


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"elbow_order": "vertical_then_horizontal"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 17), (20, 23), (26, 29), (30, 30)]
    stress = episode["test"][-1]
    assert sum(value != 0 for row in stress["output"] for value in row) >= 100
    assert proto.solve(stress["input"], {"elbow_order": "horizontal_then_vertical"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"elbow_order": "vertical_then_horizontal"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "elbow_order" not in rendered
    assert "vertical_then_horizontal" not in rendered
    assert "output" not in view["test"][0]


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 17, 97):
        for mode in proto.MODES:
            report = proto.audit_episode(seed, mode, demos=3, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
