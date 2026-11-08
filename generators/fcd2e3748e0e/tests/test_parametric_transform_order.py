from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "fcd2e3748e0e"
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
    return _load(PROTO_PATH, "_test_fcd_transform_order")


def load_generator():
    return _load(GENERATOR_PATH, "_test_fcd_generator")


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


def test_base_generator_honors_exact_transform_controls_and_template_size():
    gen = load_generator()
    for dishonest in ("palette_kind", "palette_size", "position_bias", "n_distinct_colors"):
        assert dishonest not in gen.AXES
    grid = gen.generate(
        0,
        0,
        difficulty="medium",
        grid_h=15,
        grid_w=17,
        reflect_ctrl=2,
        rotate_ctrl=4,
        template_size=6,
    )
    values = [value for row in grid for value in row]
    assert values.count(2) == 1
    assert values.count(4) == 1
    assert not any(value in (3, 5, 6, 7) for value in values)
    assert values.count(1) == 6
    assert gen.self_check(grid, difficulty="medium") == []

    other = gen.generate(
        0,
        0,
        difficulty="medium",
        grid_h=15,
        grid_w=17,
        reflect_ctrl=3,
        rotate_ctrl=7,
        template_size=6,
    )
    assert [[value in (2, 3, 4, 5, 6, 7) for value in row] for row in grid] == [
        [value in (2, 3, 4, 5, 6, 7) for value in row] for row in other
    ]
    assert grid != other

    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, reflect_ctrl=True)


def test_default_program_is_exact_selected_source_and_alternate_is_complete_rule():
    proto = load_proto()
    canonical = proto.program({"transform_order": "reflect_then_rotate"})
    alternate = proto.program({"transform_order": "rotate_then_reflect"})
    assert canonical == selected_program()
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_default_python_claim_matches_every_selected_canonical_pair():
    from arcpuzzles import Catalog

    proto = load_proto()
    for variant in Catalog(ROOT).get(TASK_ID)["variants"]:
        for pair in _variant_pairs(variant):
            before = deepcopy(pair["input"])
            assert proto.solve(pair["input"], {"transform_order": "reflect_then_rotate"}) == pair["output"]
            assert pair["input"] == before


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"transform_order": "bad"}, {"transform_order": 1},
     {"transform_order": True}, {"transform_order": "reflect_then_rotate", "extra": 1}],
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
        proto.generate(seed, {"transform_order": "reflect_then_rotate"}, demos, queries)


def test_generation_is_matched_prefix_stable_distinct_and_fresh():
    proto = load_proto()
    reflect_first = proto.generate(23, {"transform_order": "reflect_then_rotate"}, 6, 4)
    rotate_first = proto.generate(23, {"transform_order": "rotate_then_reflect"}, 6, 4)
    assert [pair["input"] for pair in reflect_first["train"]] == [pair["input"] for pair in rotate_first["train"]]
    assert [pair["input"] for pair in reflect_first["test"]] == [pair["input"] for pair in rotate_first["test"]]
    encoded = [json.dumps(pair["input"]) for pair in [*reflect_first["train"], *reflect_first["test"]]]
    assert len(encoded) == len(set(encoded)) == 10

    short = proto.generate(23, {"transform_order": "reflect_then_rotate"}, 2, 1)
    assert short["train"] == reflect_first["train"][:2]
    assert short["test"] == reflect_first["test"][:1]

    random.seed(991)
    state = random.getstate()
    replay = proto.generate(23, {"transform_order": "reflect_then_rotate"}, 6, 4)
    assert random.getstate() == state
    assert replay == reflect_first and replay is not reflect_first
    replay["train"][0]["input"][0][0] = 9
    assert proto.generate(23, {"transform_order": "reflect_then_rotate"}, 6, 4) == reflect_first


def test_first_two_teaching_demos_force_noncommuting_transform_order():
    proto = load_proto()
    episode = proto.generate(7, {"transform_order": "reflect_then_rotate"}, 6, 4)
    for pair in [*episode["train"], *episode["test"]]:
        assert proto.validate_input(pair["input"]) == []
    for pair in episode["train"][:2]:
        facts = proto.scene_facts(pair["input"])
        assert facts["reflect_code"] == 3
        assert facts["rotate_code"] in (5, 7)
        assert proto.solve(pair["input"], {"transform_order": "reflect_then_rotate"}) != proto.solve(
            pair["input"], {"transform_order": "rotate_then_reflect"}
        )


def test_first_stage_intermediate_is_consumed_by_second_transform_and_wrong_order_changes_output():
    proto = load_proto()
    pair = proto.generate(91, {"transform_order": "rotate_then_reflect"}, 3, 4)["test"][0]
    intermediate = proto.intermediate(pair["input"], {"transform_order": "rotate_then_reflect"})
    assert intermediate["first_operation"] == "rotate"
    assert intermediate["second_operation"] == "reflect"
    assert len(intermediate["first_stage_cells"]) == len(intermediate["template_cells"])
    assert pair["output"] == proto.output_from_intermediate(pair["input"], intermediate)
    assert pair["output"] != proto.solve(pair["input"], {"transform_order": "reflect_then_rotate"})


def test_four_queries_cover_exact_30x30_substantive_stress():
    proto = load_proto()
    episode = proto.generate(41, {"transform_order": "rotate_then_reflect"}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(13, 15), (18, 21), (25, 28), (30, 30)]
    stress = episode["test"][-1]
    facts = proto.scene_facts(stress["input"])
    assert len(facts["template_cells"]) >= 20
    assert sum(value == 8 for row in stress["output"] for value in row) >= 20
    assert proto.solve(stress["input"], {"transform_order": "reflect_then_rotate"}) != stress["output"]


def test_public_view_masks_private_rule_and_query_answers():
    proto = load_proto()
    episode = proto.generate(5, {"transform_order": "rotate_then_reflect"}, 3, 4)
    view = proto.public_view(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["train"]) == 3 and len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    rendered = json.dumps(view, sort_keys=True)
    assert "transform_order" not in rendered
    assert "rotate_then_reflect" not in rendered
    assert "output" not in view["test"][0]


def test_bounded_demo_only_audit_has_no_query_changing_survivor():
    proto = load_proto()
    for seed in (0, 17, 97):
        for mode in proto.MODES:
            report = proto.audit_episode(seed, mode, demos=3, queries=4)
            assert report["fit_uses"] == "demonstrations_only"
            assert report["harmful_survivors"] == []
            assert report["query_shapes"][-1] == [30, 30]
