from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"


def load_adapter():
    name = "_test_e8_parametric_" + hashlib.sha256(str(ADAPTER_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def flatten_pairs(episode):
    return episode["train"] + episode["test"]


def test_default_program_is_byte_exact_canonical_and_variant_is_distinct():
    adapter = load_adapter()
    canonical = CANONICAL_PATH.read_text(encoding="utf-8")
    assert adapter.program({"route_overlay": "none"}) == canonical
    routed = adapter.program({"route_overlay": "terminal_path"})
    assert routed != canonical
    assert routed.startswith("(rule!")


def test_episode_counts_are_prefix_stable_and_setting_neutral():
    adapter = load_adapter()
    short = adapter.generate(17, {"route_overlay": "none"}, 2, 1)
    full = adapter.generate(17, {"route_overlay": "none"}, 6, 4)
    routed = adapter.generate(17, {"route_overlay": "terminal_path"}, 6, 4)

    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert [pair["input"] for pair in flatten_pairs(full)] == [
        pair["input"] for pair in flatten_pairs(routed)
    ]
    assert full["program_solution"] == adapter.program({"route_overlay": "none"})
    assert routed["program_solution"] == adapter.program({"route_overlay": "terminal_path"})


def test_python_labels_match_policy_and_every_scene_distinguishes_settings():
    adapter = load_adapter()
    plain = adapter.generate(991, {"route_overlay": "none"}, 6, 4)
    routed = adapter.generate(991, {"route_overlay": "terminal_path"}, 6, 4)
    for a, b in zip(flatten_pairs(plain), flatten_pairs(routed)):
        assert a["input"] == b["input"]
        assert a["output"] == adapter.native_transform(a["input"], "none")
        assert b["output"] == adapter.native_transform(b["input"], "terminal_path")
        assert a["output"] != b["output"]


def test_terminal_path_is_wall_constrained_and_all_shapes_execute():
    adapter = load_adapter()
    for height in range(5, 31):
        for width in range(5, 31):
            grid = [[0] * width for _ in range(height)]
            plain = adapter.native_transform(grid, "none")
            routed = adapter.native_transform(grid, "terminal_path")
            blue = {
                (row, col)
                for row in range(height)
                for col in range(width)
                if routed[row][col] == 2
            }
            assert blue
            assert (1, 0) in blue
            assert all(plain[row][col] == 0 for row, col in blue)
            assert all(routed[row][col] == plain[row][col] for row in range(height) for col in range(width) if (row, col) not in blue)
            for row, col in blue:
                assert any(
                    (row + dr, col + dc) in blue
                    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
                ) or len(blue) == 1


def test_scene_bank_is_distinct_seed_variable_and_contains_30x30_stress():
    adapter = load_adapter()
    first = adapter.generate(3, {"route_overlay": "terminal_path"}, 6, 4)
    second = adapter.generate(4, {"route_overlay": "terminal_path"}, 6, 4)
    pairs = flatten_pairs(first)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in pairs]
    other_shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in flatten_pairs(second)]

    assert len(set(shapes)) == 10
    assert shapes != other_shapes
    assert shapes[-1] == (30, 30)
    assert all(value == 0 for pair in pairs for row in pair["input"] for value in row)
    stress = first["test"][-1]["output"]
    assert sum(value == 2 for row in stress for value in row) >= 20


def test_invalid_contract_arguments_are_rejected():
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.program({"route_overlay": "unknown"})
    with pytest.raises(ValueError):
        adapter.generate(-1, {"route_overlay": "none"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"route_overlay": "none"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"route_overlay": "none"}, 2, 5)
    with pytest.raises(ValueError):
        adapter.native_transform([[0] * 4 for _ in range(5)], "terminal_path")
    with pytest.raises(ValueError):
        adapter.native_transform([[0] * 5 for _ in range(5)] + [[0] * 4], "terminal_path")


def test_bounded_named_rival_audit_passes():
    path = PARAMETRIC / "audit.py"
    name = "_test_e8_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 17, 991))
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["findings"] == []
    assert report["has_30x30"] is True
