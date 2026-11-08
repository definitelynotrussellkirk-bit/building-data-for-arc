"""Native contract tests for phase tiling plus component erasure."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "78ab57735469"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_native_files_and_exact_default_contract():
    proto = _load("arc_78_proto", HOME / "prototype.py")
    adapter = _load("arc_78_adapter", HOME / "adapter.py")
    promotion = json.loads((HOME / "promotion.json").read_text())

    assert proto.PHASES == ("even", "odd")
    assert proto.FINISHES == ("tile_only", "erase_center_component")
    assert len(proto.SETTINGS) == 8
    default = {
        "column_flip_phase": "even",
        "finish": "tile_only",
        "row_flip_phase": "even",
    }
    assert adapter.program(default) == _canonical_program()
    assert promotion["default"] == default
    assert promotion["limits"] == {"demos": [3, 6], "queries": [1, 4]}
    assert promotion["qualification_demos"] == 3
    assert "generators/78ab57735469/workspace/parametric/verify.py" in promotion["resources"]


def test_matched_inputs_all_eight_settings_and_30x30_query():
    adapter = _load("arc_78_adapter_inputs", HOME / "adapter.py")
    settings = [
            {"row_flip_phase": r, "column_flip_phase": c, "finish": f}
            for r in ("even", "odd")
            for c in ("even", "odd")
            for f in ("tile_only", "erase_center_component")
    ]
    episodes = [
        adapter.generate(41, setting, demos=3, queries=4)
        for setting in settings
    ]
    reference = episodes[0]
    reference_inputs = [p["input"] for p in reference["train"] + reference["test"]]
    for episode in episodes:
        assert [p["input"] for p in episode["train"] + episode["test"]] == reference_inputs
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in reference_inputs]
    assert len(serialized) == len(set(serialized)) == 7
    assert [len(p["input"]) for p in reference["test"]] == [4, 7, 8, 10]
    assert len(reference["test"][-1]["output"]) == 30
    assert len(reference["test"][-1]["output"][0]) == 30


def test_each_pair_has_eight_distinct_outputs_and_python_labels_match():
    proto = _load("arc_78_proto_labels", HOME / "prototype.py")
    episode = proto.generate_episode(
        7, "odd", "even", "erase_center_component", demos=3, queries=4
    )
    for pair in episode["train"] + episode["test"]:
        before = deepcopy(pair["input"])
        outputs = {
            setting: proto.solve(pair["input"], *setting)
            for setting in proto.SETTINGS
        }
        assert len({json.dumps(value, separators=(",", ":")) for value in outputs.values()}) == 8
        assert pair["output"] == outputs[("odd", "even", "erase_center_component")]
        assert pair["input"] == before
        intermediate = proto.tile_intermediate(pair["input"], "odd", "even")
        component = proto.center_seam_component(intermediate, len(pair["input"]))
        assert len(component) >= 4
        assert all(pair["output"][r][c] == 0 for r, c in component)
        target_color = intermediate[len(pair["input"])][len(pair["input"])]
        assert any(
            intermediate[r][c] == target_color and (r, c) not in component
            for r in range(len(intermediate))
            for c in range(len(intermediate[0]))
        )


def test_three_demos_refute_other_settings_and_named_shortcuts():
    proto = _load("arc_78_proto_teaching", HOME / "prototype.py")
    for setting in proto.SETTINGS:
        episode = proto.generate_episode(13, *setting, demos=3, queries=4)
        certificate = proto.teaching_certificate(episode, setting)
        assert certificate["surviving_rivals"] == []
        assert certificate["query_changing_survivors"] == []
        assert certificate["rivals_checked"] >= 10


def test_public_turn_prefix_and_no_private_fields():
    adapter = _load("arc_78_adapter_public", HOME / "adapter.py")
    settings = {
        "row_flip_phase": "odd",
        "column_flip_phase": "odd",
        "finish": "erase_center_component",
    }
    four = adapter.generate(5, settings, demos=3, queries=4)
    one = adapter.generate(5, settings, demos=3, queries=1)
    assert adapter.public_turn(four, 0) == adapter.public_turn(one, 0)
    first = adapter.public_turn(four, 0)
    assert len(first["train"]) == 3 and len(first["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert set(first["test"][0]) == {"input"}
    for index in range(1, 4):
        assert adapter.public_turn(four, index) == {
            "test": [{"input": four["test"][index]["input"]}]
        }


def test_strict_validation_rejects_bad_settings_counts_and_zero_input():
    proto = _load("arc_78_proto_validation", HOME / "prototype.py")
    adapter = _load("arc_78_adapter_validation", HOME / "adapter.py")
    for bad in ({}, {"row_flip_phase": "even"}, {"row_flip_phase": "x", "column_flip_phase": "even", "finish": "tile_only"}, None):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for bad in (2, 7, True):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, {
                "row_flip_phase": "even",
                "column_flip_phase": "even",
                "finish": "tile_only",
            }, demos=bad, queries=4)
    episode = proto.generate_episode(0, "even", "even", "tile_only", demos=3, queries=4)
    grid = deepcopy(episode["train"][0]["input"])
    grid[0][0] = 0
    with pytest.raises(ValueError):
        proto.solve(grid, "even", "even", "tile_only")


def test_task_local_verifier_runs_current_contract_through_racket(tmp_path):
    verify = _load("arc_78_verify_current", HOME / "verify.py")
    setting = ("odd", "even", "erase_center_component")
    report = verify.build_report(
        seed_base=73,
        artifact_dir=tmp_path,
        settings=[setting],
    )
    assert report["schema"] == "78ab57735469-parametric-component-v2"
    assert report["status"] == "passed"
    assert report["settings_checked"] == 1
    assert report["pairs_checked"] == 7
    assert report["protected_racket"] is True
    assert report["max_output_shape"] == [30, 30]
    saved = json.loads((tmp_path / "report.json").read_text())
    assert saved == report
