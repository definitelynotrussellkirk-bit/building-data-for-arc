"""Native parametric family contract for b5df32f2dc17."""
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


proto = _load("_b5df32f2dc17_parametric_test", PARAMETRIC / "prototype.py")
adapter = _load("_b5df32f2dc17_parametric_adapter_test", PARAMETRIC / "adapter.py")


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_canonical_program_is_exact_selected_authority():
    record = Catalog(HOME.parents[1]).get("b5df32f2dc17")
    programs = {variant["program_solution"] for variant in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical
    assert adapter.program({"length_order": "descending"}) == canonical


def test_declared_programs_settings_and_counts_are_strict():
    assert proto.LENGTH_ORDERS == ("descending", "ascending")
    for order in proto.LENGTH_ORDERS:
        assert adapter.program({"length_order": order}).startswith("(rule!")
    for bad in [None, {}, {"length_order": "bad"}, {"length_order": 1},
                {"length_order": "descending", "extra": 1}]:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for name, value in [("demos", 1), ("demos", 7), ("demos", True),
                        ("queries", 0), ("queries", 5), ("queries", 1.0),
                        ("seed", -1), ("seed", True), ("seed", 2**63)]:
        kwargs = {"seed": 0, "settings": {"length_order": "descending"},
                  "demos": 3, "queries": 4}
        kwargs[name] = value
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(**kwargs)


def test_counts_are_independent_prefix_stable_and_inputs_match_settings():
    episodes = {}
    for order in proto.LENGTH_ORDERS:
        small = adapter.generate(41, {"length_order": order}, 2, 1)
        large = adapter.generate(41, {"length_order": order}, 6, 4)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]
        episodes[order] = large
    for split in ("train", "test"):
        assert [p["input"] for p in episodes["descending"][split]] == [
            p["input"] for p in episodes["ascending"][split]
        ]
        assert all(a["output"] != b["output"] for a, b in zip(
            episodes["descending"][split], episodes["ascending"][split], strict=True))
    inputs = [p["input"] for split in ("train", "test")
              for p in episodes["descending"][split]]
    assert len({_compact(grid) for grid in inputs}) == len(inputs)


def test_python_labels_sort_each_row_then_repack_without_mutating_input():
    for order in proto.LENGTH_ORDERS:
        episode = adapter.generate(23, {"length_order": order}, 6, 4)
        for split in ("train", "test"):
            for pair in episode[split]:
                original = deepcopy(pair["input"])
                analysis = proto.analyze(pair["input"])
                assert analysis["row_roles"] >= {
                    "blank", "single", "already_ascending", "already_descending", "needs_reorder", "tie"
                }
                assert proto.solve_python(pair["input"], order) == pair["output"]
                assert pair["input"] == original


def test_first_two_demos_eliminate_declared_query_changing_rivals():
    for seed in (0, 17, 991):
        for order in proto.LENGTH_ORDERS:
            episode = proto.generate_episode(seed, length_order=order, demos=2, queries=4)
            audit = proto.teaching_check(episode, order)
            assert audit["harmful_survivors"] == []
            assert audit["demo_survivors"] == []
            assert audit["rival_count"] >= 10
            assert audit["settings_disagree_on_demos"] is True


def test_four_queries_include_dense_30x30_boundary_stress():
    episode = adapter.generate(123, {"length_order": "ascending"}, 3, 4)
    stress = episode["test"][3]["input"]
    assert len(stress) == len(stress[0]) == 30
    foreground = sum(cell != 0 for row in stress for cell in row)
    assert foreground >= 380
    assert any(stress[0][c] != 0 for c in range(30))
    assert any(stress[29][c] != 0 for c in range(30))
    assert any(stress[r][0] != 0 for r in range(30))
    assert any(stress[r][29] != 0 for r in range(30))
    descending = proto.solve_python(stress, "descending")
    ascending = proto.solve_python(stress, "ascending")
    changed = sum(a != b for ra, rb in zip(descending, ascending, strict=True)
                  for a, b in zip(ra, rb, strict=True))
    assert changed >= 200


def test_public_turn_masks_private_data_and_first_turn_is_count_invariant():
    one = proto.generate_episode(55, length_order="ascending", demos=3, queries=1)
    four = proto.generate_episode(55, length_order="ascending", demos=3, queries=4)
    public_one = proto.public_view(one, 0)
    public_four = proto.public_view(four, 0)
    assert public_one == public_four
    assert set(public_four) == {"train", "test"}
    assert len(public_four["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public_four["train"])
    assert all(set(pair) == {"input"} for pair in public_four["test"])
    text = _compact(public_four)
    assert "length_order" not in text
    assert "program_solution" not in text
    assert hashlib.sha256(proto.public_bytes(four, 0)).hexdigest() == proto.public_id(four, 0)


def test_reusable_self_audit_static_checks_cover_counts_settings_and_stress():
    audit = _load("_b5df32f2dc17_self_audit_test", PARAMETRIC / "self_audit.py")
    report = audit.static_report(seeds=(0,))
    assert report["status"] == "passed"
    assert report["counts"]["episodes"] == 6
    assert report["counts"]["matched_input_comparisons"] == 3
    assert report["counts"]["stress_30x30"] == 6
    assert report["findings"] == []
