from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "generators/39ad03f74acb/workspace/parametric/adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("seg_parametric_adapter_test", ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def literal_scene() -> list[list[int]]:
    grid = blank(9, 10)
    for c in range(1, 7):
        grid[1][c] = 1
    for c in range(1, 4):
        grid[3][c] = 1
    for r in range(5, 9):
        grid[r][7] = 1
    return grid


def test_all_segments_and_perpendicular_relay_have_literal_outputs() -> None:
    adapter = load_adapter()
    grid = literal_scene()

    all_expected = literal_scene()
    for c in range(2, 6):
        all_expected[1][c] = 2
    all_expected[3][2] = 2
    all_expected[6][7] = 2
    all_expected[7][7] = 2

    relay_expected = literal_scene()
    relay_expected[6][7] = 2
    relay_expected[7][7] = 2

    assert adapter.transform(grid, "all_segments") == all_expected
    assert adapter.transform(grid, "perpendicular_to_longest") == relay_expected
    assert adapter.controller_orientation(grid) == "horizontal"


def test_default_program_is_exact_selected_canonical_source() -> None:
    adapter = load_adapter()
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get("39ad03f74acb")
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program({"scope": "all_segments"}) == canonical
    assert adapter.program({"scope": "perpendicular_to_longest"}) != canonical


def test_generate_is_deterministic_distinct_and_supports_all_counts() -> None:
    adapter = load_adapter()
    for scope in adapter.SCOPES:
        settings = {"scope": scope}
        for demos in range(2, 7):
            episode = adapter.generate(23, settings, demos=demos, queries=4)
            assert episode == adapter.generate(23, settings, demos=demos, queries=4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(settings)
            pairs = episode["train"] + episode["test"]
            encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
            assert len(encoded) == len(set(encoded))
            assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                       for pair in episode["test"])
            for pair in pairs:
                assert pair["output"] == adapter.transform(pair["input"], scope)
                assert adapter.scene_invariants(pair["input"]) == []


def test_matched_inputs_always_distinguish_the_two_rules() -> None:
    adapter = load_adapter()
    canonical = adapter.generate(17, {"scope": "all_segments"}, demos=3, queries=4)
    relay = adapter.generate(17, {"scope": "perpendicular_to_longest"}, demos=3, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in canonical[split]] == [p["input"] for p in relay[split]]
        assert all(a["output"] != b["output"]
                   for a, b in zip(canonical[split], relay[split], strict=True))
        assert all(any(cell == 2 for row in pair["output"] for cell in row)
                   for pair in relay[split])


def test_sampler_varies_controller_orientation_and_builds_substantive_stress() -> None:
    adapter = load_adapter()
    orientations = set()
    minimum_blue_30 = 10**9
    for seed in range(8):
        episode = adapter.generate(seed, {"scope": "all_segments"}, demos=3, queries=4)
        for pair in episode["train"] + episode["test"]:
            orientations.add(adapter.controller_orientation(pair["input"]))
            if len(pair["input"]) == 30:
                minimum_blue_30 = min(
                    minimum_blue_30,
                    sum(cell == 1 for row in pair["input"] for cell in row),
                )
    assert orientations == {"horizontal", "vertical"}
    assert minimum_blue_30 >= 50


def test_rejects_malformed_settings_counts_and_non_segment_scenes() -> None:
    adapter = load_adapter()
    for settings in (None, {}, {"scope": "other"}, {"scope": "all_segments", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, {"scope": "all_segments"}, demos=1, queries=4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"scope": "all_segments"}, demos=3, queries=5)
    bad = blank(5, 5)
    bad[1][1] = bad[1][2] = bad[2][2] = 1
    with pytest.raises(ValueError):
        adapter.transform(bad, "all_segments")


def test_bounded_audit_rejects_selector_and_paint_shortcuts() -> None:
    path = ROOT / "generators/39ad03f74acb/workspace/parametric/audit.py"
    spec = importlib.util.spec_from_file_location("seg_parametric_audit_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_audit(range(4))
    assert report["status"] == "passed"
    assert report["episodes"] == 8
    assert report["teaching_holes"] == []
    assert report["minimum_blue_cells_30x30"] >= 50
    assert report["controller_orientations"] == ["horizontal", "vertical"]
