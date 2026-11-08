"""Native parametric family contract for b39674306606."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


proto = _load("_b39674306606_parametric_test", PARAMETRIC / "prototype.py")
adapter = _load("_b39674306606_parametric_adapter_test", PARAMETRIC / "adapter.py")


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_canonical_program_is_exact_selected_authority():
    record = Catalog(HOME.parents[1]).get("b39674306606")
    programs = {variant["program_solution"] for variant in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical
    assert adapter.program({"frequency_target": "singleton"}) == canonical


def test_declared_programs_settings_and_counts_are_strict():
    assert proto.FREQUENCY_TARGETS == ("singleton", "most_frequent")
    for target in proto.FREQUENCY_TARGETS:
        assert adapter.program({"frequency_target": target}).startswith("(rule!")
    for bad in [None, {}, {"frequency_target": "bad"}, {"frequency_target": 1},
                {"frequency_target": "singleton", "extra": 1}]:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for name, value in [("demos", 1), ("demos", 7), ("demos", True),
                        ("queries", 0), ("queries", 5), ("queries", 1.0),
                        ("seed", -1), ("seed", True), ("seed", 2**63)]:
        kwargs = {"seed": 0, "settings": {"frequency_target": "singleton"},
                  "demos": 3, "queries": 4}
        kwargs[name] = value
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(**kwargs)


def test_counts_are_independent_prefix_stable_and_inputs_match_settings():
    episodes = {}
    for target in proto.FREQUENCY_TARGETS:
        small = adapter.generate(41, {"frequency_target": target}, 2, 1)
        large = adapter.generate(41, {"frequency_target": target}, 6, 4)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]
        assert len(large["train"]) == 6
        assert len(large["test"]) == 4
        episodes[target] = large
    for split in ("train", "test"):
        assert [p["input"] for p in episodes["singleton"][split]] == [
            p["input"] for p in episodes["most_frequent"][split]
        ]
        assert all(
            a["output"] != b["output"]
            for a, b in zip(episodes["singleton"][split],
                            episodes["most_frequent"][split], strict=True)
        )
    inputs = [p["input"] for split in ("train", "test")
              for p in episodes["singleton"][split]]
    assert len({_compact(grid) for grid in inputs}) == len(inputs)


def test_python_labels_use_exact_shape_frequency_without_input_mutation():
    for target in proto.FREQUENCY_TARGETS:
        episode = adapter.generate(23, {"frequency_target": target}, 6, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                original = deepcopy(pair["input"])
                info = proto.analyze(pair["input"])
                assert sorted(info["frequency_values"]) == [1, 2, 3]
                assert len(info["components"]) == 6
                assert proto.solve_python(pair["input"], target) == pair["output"]
                assert pair["input"] == original


def test_first_two_demos_eliminate_declared_query_changing_rivals():
    for seed in (0, 17, 991):
        for target in proto.FREQUENCY_TARGETS:
            episode = proto.generate_episode(seed, frequency_target=target, demos=2, queries=4)
            audit = proto.teaching_check(episode, target)
            assert audit["harmful_survivors"] == []
            assert audit["demo_survivors"] == []
            assert audit["rival_count"] >= 8
            assert audit["settings_disagree_on_demos"] is True


def test_four_queries_include_substantive_30x30_boundary_stress():
    episode = adapter.generate(123, {"frequency_target": "most_frequent"}, 3, 4)
    assert len(episode["test"]) == 4
    stress = episode["test"][3]["input"]
    assert len(stress) == len(stress[0]) == 30
    foreground = sum(cell != 0 for row in stress for cell in row)
    assert foreground >= 100
    assert any(stress[0][c] != 0 for c in range(30))
    assert any(stress[29][c] != 0 for c in range(30))
    assert any(stress[r][0] != 0 for r in range(30))
    assert any(stress[r][29] != 0 for r in range(30))
    assert sum(a != b for ra, rb in zip(
        proto.solve_python(stress, "singleton"),
        proto.solve_python(stress, "most_frequent"), strict=True)
        for a, b in zip(ra, rb, strict=True)) >= 60


def test_public_turn_masks_private_data_and_first_turn_is_count_invariant():
    one = proto.generate_episode(55, frequency_target="most_frequent", demos=3, queries=1)
    four = proto.generate_episode(55, frequency_target="most_frequent", demos=3, queries=4)
    public_one = proto.public_view(one, 0)
    public_four = proto.public_view(four, 0)
    assert public_one == public_four
    assert set(public_four) == {"train", "test"}
    assert len(public_four["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public_four["train"])
    assert all(set(pair) == {"input"} for pair in public_four["test"])
    text = _compact(public_four)
    assert "frequency_target" not in text
    assert "program_solution" not in text
    assert hashlib.sha256(proto.public_bytes(four, 0)).hexdigest() == proto.public_id(four, 0)


def test_reusable_self_audit_static_checks_cover_counts_settings_and_stress():
    audit = _load("_b39674306606_self_audit_test", PARAMETRIC / "self_audit.py")
    report = audit.static_report(seeds=(0,))
    assert report["status"] == "passed"
    assert report["counts"]["episodes"] == 6
    assert report["counts"]["matched_input_comparisons"] == 3
    assert report["counts"]["stress_30x30"] == 6
    assert report["findings"] == []
