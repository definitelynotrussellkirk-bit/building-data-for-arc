from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "2314acbb67be"
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
    return _load(PROTO_PATH, "_test_231_motif_order")


def load_generator():
    return _load(GENERATOR_PATH, "_test_231_generator")


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


def test_base_generator_controls_are_exact_and_invalid_requests_fail():
    gen = load_generator()
    assert set(gen.AXES) == {"grid_h", "grid_w", "n", "palette_kind"}
    grid = gen.generate(8123, 0, difficulty="medium", grid_h=12, grid_w=17, n=4, palette_kind="warm")
    assert (len(grid), len(grid[0])) == (12, 17)
    observed = gen.observe_overrides(grid)
    assert observed["n"] == 4
    assert set(observed["colors"]) <= set(gen.PALETTES["warm"])
    assert len(set(observed["sizes"])) == 4
    assert gen.self_check(grid, difficulty="medium") == []
    with pytest.raises(ValueError):
        gen.generate(0, 0, unknown=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, n=True)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=7, n=4)


def test_default_program_is_exact_selected_source_and_alternate_is_complete_rule():
    proto = load_proto()
    canonical = proto.program({"order_key": "cell_count"})
    alternate = proto.program({"order_key": "bounding_box_area"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            before = deepcopy(pair["input"])
            assert proto.solve(pair["input"], {"order_key": "cell_count"}) == pair["output"]
            assert pair["input"] == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"order_key": "bad"}, {"order_key": 1},
     {"order_key": True}, {"order_key": "cell_count", "extra": 1}],
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
        proto.generate(seed, {"order_key": "cell_count"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    cell = proto.generate(23, {"order_key": "cell_count"}, 6, 4)
    area = proto.generate(23, {"order_key": "bounding_box_area"}, 6, 4)
    assert [pair["input"] for pair in cell["train"]] == [pair["input"] for pair in area["train"]]
    assert [pair["input"] for pair in cell["test"]] == [pair["input"] for pair in area["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*cell["train"], *cell["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"order_key": "cell_count"}, 2, 1)
    assert short["train"] == cell["train"][:2]
    assert short["test"] == cell["test"][:1]

    random.seed(991)
    state = random.getstate()
    replay = proto.generate(23, {"order_key": "cell_count"}, 6, 4)
    assert random.getstate() == state
    assert replay == cell and replay is not cell
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"order_key": "cell_count"}, 6, 4) == cell


def test_two_demos_identify_each_setting_and_every_scene_is_lawful():
    proto = load_proto()
    for mode in proto.MODES:
        episode = proto.generate(7, {"order_key": mode}, 2, 4)
        assert all(proto.validate_input(pair["input"]) == [] for pair in [*episode["train"], *episode["test"]])
        survivors = []
        for candidate in proto.MODES:
            if all(proto.solve(pair["input"], {"order_key": candidate}) == pair["output"] for pair in episode["train"]):
                survivors.append(candidate)
        assert survivors == [mode]
        assert all(proto.solve(pair["input"], {"order_key": proto.MODES[0]}) != proto.solve(
            pair["input"], {"order_key": proto.MODES[1]}
        ) for pair in episode["train"])


def test_order_intermediate_controls_packing_and_wrong_order_changes_output():
    proto = load_proto()
    pair = proto.generate(91, {"order_key": "bounding_box_area"}, 3, 4)["test"][0]
    value = proto.intermediate(pair["input"], {"order_key": "bounding_box_area"})
    assert len(value["objects"]) >= 3
    assert value["ordered_colors"]
    assert pair["output"] == proto.output_from_intermediate(value)
    wrong = proto.intermediate(pair["input"], {"order_key": "cell_count"})
    assert proto.output_from_intermediate(wrong) != pair["output"]


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"order_key": "bounding_box_area"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(10, 14), (16, 20), (24, 27), (30, 30)]
    stress = episode["test"][-1]
    assert sum(value != 0 for row in stress["input"] for value in row) >= 50
    assert len(stress["output"]) >= 5 and len(stress["output"][0]) >= 20
    assert proto.solve(stress["input"], {"order_key": "cell_count"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"order_key": "bounding_box_area"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "order_key" not in rendered
    assert "bounding_box_area" not in rendered
    assert "output" not in view["test"][0]


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 17, 97):
        for mode in proto.MODES:
            report = proto.audit_episode(seed, mode, demos=2, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
