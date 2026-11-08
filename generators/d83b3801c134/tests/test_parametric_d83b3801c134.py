from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "generators/d83b3801c134/workspace/parametric/adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("d83_parametric_adapter_test", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def test_forward_and_reverse_use_the_marker_vector_in_opposite_directions() -> None:
    adapter = load_adapter()
    grid = blank(7, 8)
    grid[1][1] = 1
    grid[2][3] = 2
    grid[3][2] = 3
    grid[3][3] = 3
    grid[4][2] = 3

    forward = blank(7, 8)
    forward[4][4] = 3
    forward[4][5] = 3
    forward[5][4] = 3
    reverse = blank(7, 8)
    reverse[2][0] = 3
    reverse[2][1] = 3
    reverse[3][0] = 3

    assert adapter.transform(grid, "one_to_two") == forward
    assert adapter.transform(grid, "two_to_one") == reverse


def test_default_program_is_the_exact_selected_canonical_source() -> None:
    adapter = load_adapter()
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get("d83b3801c134")
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    assert adapter.program({"direction": "one_to_two"}) == next(iter(programs))
    assert adapter.program({"direction": "two_to_one"}) != next(iter(programs))


def test_generate_is_deterministic_distinct_and_supports_all_counts() -> None:
    adapter = load_adapter()
    for direction in adapter.DIRECTIONS:
        settings = {"direction": direction}
        for demos in range(2, 7):
            episode = adapter.generate(31, settings, demos=demos, queries=4)
            assert episode == adapter.generate(31, settings, demos=demos, queries=4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(settings)
            pairs = episode["train"] + episode["test"]
            serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
            assert len(serialized) == len(set(serialized))
            assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                       for pair in episode["test"])
            for pair in pairs:
                assert pair["output"] == adapter.transform(pair["input"], direction)
                assert adapter.scene_invariants(pair["input"]) == []


def test_settings_share_inputs_and_every_pair_distinguishes_direction() -> None:
    adapter = load_adapter()
    forward = adapter.generate(17, {"direction": "one_to_two"}, demos=3, queries=4)
    reverse = adapter.generate(17, {"direction": "two_to_one"}, demos=3, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in forward[split]] == [p["input"] for p in reverse[split]]
        assert all(a["output"] != b["output"]
                   for a, b in zip(forward[split], reverse[split], strict=True))


def test_scenes_have_multiple_green_components_and_bidirectional_room() -> None:
    adapter = load_adapter()
    episode = adapter.generate(5, {"direction": "one_to_two"}, demos=6, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        assert adapter.green_component_count(grid) >= 2
        assert adapter.transform(grid, "one_to_two")
        assert adapter.transform(grid, "two_to_one")


def test_rejects_malformed_settings_and_counts() -> None:
    adapter = load_adapter()
    bad_settings = [None, {}, {"direction": "sideways"},
                    {"direction": "one_to_two", "extra": 1}]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, {"direction": "one_to_two"}, demos=1, queries=4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"direction": "one_to_two"}, demos=3, queries=5)


def test_bounded_audit_rejects_declared_shortcuts() -> None:
    path = ROOT / "generators/d83b3801c134/workspace/parametric/audit.py"
    spec = importlib.util.spec_from_file_location("d83_parametric_audit_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_audit(range(4))
    assert report["status"] == "passed"
    assert report["episodes"] == 8
    assert report["teaching_holes"] == []
    assert report["minimum_green_cells_30x30"] >= 20
    assert report["vectors_seen"] >= 8
