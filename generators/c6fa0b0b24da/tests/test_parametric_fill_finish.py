"""Native parametric contract for fill-then-select composition."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK = "c6fa0b0b24da"
HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


native = _load("_test_c6fa0b0b24da_native", PARAM / "native.py")
adapter = _load("_test_c6fa0b0b24da_adapter", PARAM / "adapter.py")


def _compact(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_canonical_program_is_byte_exact_selected_authority():
    record = Catalog(ROOT).get(TASK)
    programs = {row["program_solution"] for row in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAM / "canonical.rkt").read_text(encoding="utf-8") == canonical
    assert adapter.program({"fill_finish": "canonical"}) == canonical


def test_settings_counts_and_seed_are_strict():
    for finish in native.FILL_FINISHES:
        assert adapter.program({"fill_finish": finish}).startswith("(rule!")
    for bad in [None, {}, {"fill_finish": "bad"}, {"fill_finish": 1},
                {"fill_finish": "canonical", "extra": 1}]:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for name, value in [("seed", -1), ("seed", True), ("seed", 2**63),
                        ("demos", 1), ("demos", 7), ("demos", 2.0),
                        ("queries", 0), ("queries", 5), ("queries", True)]:
        kwargs = {"seed": 0, "settings": {"fill_finish": "canonical"},
                  "demos": 3, "queries": 4}
        kwargs[name] = value
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(**kwargs)


def test_prefix_stability_matched_inputs_and_distinct_outputs():
    episodes = {}
    for finish in native.FILL_FINISHES:
        short = adapter.generate(41, {"fill_finish": finish}, 2, 1)
        full = adapter.generate(41, {"fill_finish": finish}, 6, 4)
        assert short["train"] == full["train"][:2]
        assert short["test"] == full["test"][:1]
        episodes[finish] = full
    for split in ("train", "test"):
        assert [p["input"] for p in episodes["canonical"][split]] == [
            p["input"] for p in episodes["largest_new_region_to_8"][split]
        ]
        assert all(a["output"] != b["output"] for a, b in zip(
            episodes["canonical"][split],
            episodes["largest_new_region_to_8"][split], strict=True))
    visible = [p["input"] for split in ("train", "test")
               for p in episodes["canonical"][split]]
    assert len({_compact(grid) for grid in visible}) == len(visible)


def test_python_labels_fill_then_recolor_unique_largest_new_region():
    episode = adapter.generate(9, {"fill_finish": "largest_new_region_to_8"}, 6, 4)
    for split in ("train", "test"):
        for pair in episode[split]:
            before = deepcopy(pair["input"])
            info = native.analyze(pair["input"])
            sizes = [len(region) for region in info["new_regions"]]
            assert len(sizes) >= 2
            assert sizes.count(max(sizes)) == 1
            assert pair["output"] == native.solve_python(
                pair["input"], "largest_new_region_to_8")
            assert pair["input"] == before
            selected = set(map(tuple, info["selected_new_region"]))
            for r, row in enumerate(pair["output"]):
                for c, value in enumerate(row):
                    if (r, c) in selected:
                        assert value == 8


def test_two_demos_refute_declared_query_changing_rivals():
    for seed in (0, 17, 991):
        for finish in native.FILL_FINISHES:
            episode = native.generate_episode(seed, finish, demos=2, queries=4)
            report = native.teaching_check(episode, finish)
            assert report["harmful_survivors"] == []
            assert report["demo_survivors"] == []
            assert report["settings_disagree_on_demos"] is True


def test_fourth_query_is_dense_30x30_boundary_stress():
    episode = adapter.generate(123, {"fill_finish": "largest_new_region_to_8"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(v != 0 for row in grid for v in row) >= 30
    out = episode["test"][3]["output"]
    assert 600 <= sum(v != 0 for row in out for v in row) < 900
    boundary_contacts = sum((
        any(grid[0][c] != 0 for c in range(30)),
        any(grid[29][c] != 0 for c in range(30)),
        any(grid[r][0] != 0 for r in range(30)),
        any(grid[r][29] != 0 for r in range(30)),
    ))
    assert boundary_contacts >= 2
    assert any(v == 0 for row in out for v in row)


def test_reusable_self_audit_static_report_is_clean():
    audit = _load("_test_c6fa0b0b24da_audit", PARAM / "self_audit.py")
    report = audit.static_report(seeds=range(4))
    assert report["status"] == "passed"
    assert report["findings"] == []
    assert report["counts"]["episodes"] == 24
