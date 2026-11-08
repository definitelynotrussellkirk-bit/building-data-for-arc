"""Native parametric family contract for 4e05481a2c21."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = _load("_4e05481a2c21_parametric_test", PARAMETRIC / "prototype.py")
adapter = _load("_4e05481a2c21_parametric_adapter_test", PARAMETRIC / "adapter.py")


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_canonical_program_is_exact_selected_authority():
    record = Catalog(HOME.parents[1]).get("4e05481a2c21")
    programs = {variant["program_solution"] for variant in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical
    assert adapter.program({"pack_order": "left_to_right"}) == canonical


def test_declared_programs_and_settings_are_total_and_strict():
    assert proto.PACK_ORDERS == ("left_to_right", "hole_area_descending")
    for setting in proto.PACK_ORDERS:
        source = adapter.program({"pack_order": setting})
        assert source.startswith("(rule!")
        assert len(source) > 500
    for bad in [None, {}, {"pack_order": "unknown"}, {"pack_order": 1},
                {"pack_order": "left_to_right", "extra": 1}]:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def test_counts_are_independent_prefix_stable_and_exact_integer_only():
    for order in proto.PACK_ORDERS:
        small = adapter.generate(41, {"pack_order": order}, 2, 1)
        large = adapter.generate(41, {"pack_order": order}, 6, 4)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]
        assert len(large["train"]) == 6
        assert len(large["test"]) == 4
        assert large["program_solution"] == adapter.program({"pack_order": order})
    for name, value in [("demos", 1), ("demos", 7), ("demos", True),
                        ("queries", 0), ("queries", 5), ("queries", 1.0)]:
        kwargs = {"demos": 3, "queries": 4}
        kwargs[name] = value
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {"pack_order": "left_to_right"}, **kwargs)


def test_inputs_are_matched_across_settings_and_distinct_within_episode():
    episodes = {
        order: adapter.generate(17, {"pack_order": order}, 6, 4)
        for order in proto.PACK_ORDERS
    }
    for split in ("train", "test"):
        left = [pair["input"] for pair in episodes["left_to_right"][split]]
        right = [pair["input"] for pair in episodes["hole_area_descending"][split]]
        assert left == right
    inputs = [pair["input"] for split in ("train", "test")
              for pair in episodes["left_to_right"][split]]
    assert len({_compact(grid) for grid in inputs}) == len(inputs)
    assert any(
        episodes["left_to_right"][split][i]["output"]
        != episodes["hole_area_descending"][split][i]["output"]
        for split in ("train", "test")
        for i in range(len(episodes["left_to_right"][split]))
    )


def test_python_labels_follow_complete_hole_analysis_without_mutation():
    for order in proto.PACK_ORDERS:
        episode = adapter.generate(23, {"pack_order": order}, 6, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                original = deepcopy(pair["input"])
                analysis = proto.analyze(pair["input"])
                assert 2 <= len(analysis["objects"]) <= 4
                assert all(obj["hole_area"] > 0 for obj in analysis["objects"])
                assert proto.solve_python(pair["input"], order) == pair["output"]
                assert pair["input"] == original


def test_first_two_demos_eliminate_declared_query_changing_rivals():
    for seed in (0, 17, 991):
        for order in proto.PACK_ORDERS:
            episode = adapter.generate(seed, {"pack_order": order}, 2, 4)
            audit = proto.teaching_check(episode, order)
            assert audit["harmful_survivors"] == []
            assert audit["rival_count"] >= 8
            assert audit["settings_disagree_on_demos"] is True


def test_four_query_profiles_include_substantive_30x30_boundary_stress():
    episode = adapter.generate(123, {"pack_order": "hole_area_descending"}, 3, 4)
    assert [tuple(map(len, (pair["input"], pair["input"][0]))) for pair in episode["test"]]
    stress = episode["test"][3]["input"]
    assert len(stress) == len(stress[0]) == 30
    info = proto.analyze(stress)
    assert len(info["objects"]) == 4
    assert sum(len(obj["cells"]) for obj in info["objects"]) >= 120
    boxes = [obj["bbox"] for obj in info["objects"]]
    assert any(box[0] == 0 for box in boxes)
    assert any(box[2] == 29 for box in boxes)
    assert any(box[1] == 0 for box in boxes)
    assert any(box[3] == 29 for box in boxes)
    assert len({obj["hole_area"] for obj in info["objects"]}) >= 3


def test_public_turn_masks_private_data_and_first_turn_is_query_count_invariant():
    one = proto.generate_episode(55, pack_order="hole_area_descending", demos=3, queries=1)
    four = proto.generate_episode(55, pack_order="hole_area_descending", demos=3, queries=4)
    public_one = proto.public_view(one, 0)
    public_four = proto.public_view(four, 0)
    assert public_one == public_four
    assert set(public_four) == {"train", "test"}
    assert len(public_four["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public_four["train"])
    assert all(set(pair) == {"input"} for pair in public_four["test"])
    text = _compact(public_four)
    assert "pack_order" not in text
    assert "program_solution" not in text
    assert four["test"][0]["output"] not in [pair for pair in public_four["test"]]
    assert hashlib.sha256(proto.public_bytes(four, 0)).hexdigest() == proto.public_id(four, 0)


def test_reusable_self_audit_static_checks_cover_counts_settings_and_stress():
    audit = _load("_4e05481a2c21_self_audit_test", PARAMETRIC / "self_audit.py")
    report = audit.static_report(seeds=(0,))
    assert report["status"] == "passed"
    assert report["counts"]["episodes"] == 6
    assert report["counts"]["matched_input_comparisons"] == 3
    assert report["counts"]["stress_30x30"] == 6
    assert report["findings"] == []
