from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK = "3fb5ef8ad60e"
HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_test_3fb_parametric_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["train"] + episode["test"]]


def test_program_preserves_exact_canonical_and_has_frame_variant() -> None:
    adapter = _load_adapter()
    record = Catalog(Path(__file__).resolve().parents[3]).get(TASK)
    canonical = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(canonical) == 1
    assert adapter.program({"divider_reference": "block_midrange"}) == canonical.pop()
    alternate = adapter.program({"divider_reference": "frame_midpoint"})
    assert alternate.startswith("(rule!")
    assert alternate.rstrip().endswith(")")
    assert alternate != adapter.program({"divider_reference": "block_midrange"})


def test_all_counts_use_matched_distinct_inputs_and_setting_labels_disagree() -> None:
    adapter = _load_adapter()
    for demos in range(2, 7):
        for queries in range(1, 5):
            episodes = [
                adapter.generate(41, {"divider_reference": setting}, demos, queries)
                for setting in adapter.DIVIDER_REFERENCES
            ]
            assert _inputs(episodes[0]) == _inputs(episodes[1])
            assert len(_inputs(episodes[0])) == len(set(_inputs(episodes[0])))
            for setting, episode in zip(adapter.DIVIDER_REFERENCES, episodes, strict=True):
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                for pair in episode["train"] + episode["test"]:
                    facts = adapter.analyze(pair["input"])
                    assert len(facts["blocks"]) == 3
                    assert len({tuple(item) for item in facts["block_midrange_quadrants"]}) == 3
                    assert len({tuple(item) for item in facts["frame_midpoint_quadrants"]}) == 3
                    assert pair["output"] == adapter.solve(pair["input"], {"divider_reference": setting})
                    assert adapter.solve(pair["input"], {"divider_reference": "block_midrange"}) != adapter.solve(
                        pair["input"], {"divider_reference": "frame_midpoint"}
                    )
    full = adapter.generate(41, {"divider_reference": "block_midrange"}, 6, 4)
    assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in full["test"])


def test_two_demos_reject_declared_midpoint_and_layout_rivals() -> None:
    adapter = _load_adapter()
    for setting in adapter.DIVIDER_REFERENCES:
        episode = adapter.generate(5, {"divider_reference": setting}, 2, 4)
        report = adapter.lesson_report(episode, {"divider_reference": setting})
        assert report["surviving_rivals"] == []
        assert report["query_disagreements"] == []
        assert set(report["rivals_tested"]) >= (
            ({"block_midrange", "frame_midpoint"} - {setting})
            | {"canvas_midpoint", "numeric_color_layout"}
        )


def test_scene_bank_varies_frame_offset_geometry_colors_and_missing_cells() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(73, {"divider_reference": "frame_midpoint"}, 6, 4)
    facts = [adapter.analyze(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert len({tuple(item["frame_bbox"]) for item in facts}) >= 8
    assert len({tuple(item["grid_size"]) for item in facts}) == 10
    assert len({tuple(sorted(item["colors"])) for item in facts}) >= 4
    assert len({item["block_midrange_missing_quadrant"] for item in facts}) >= 2
    assert len({item["frame_midpoint_missing_quadrant"] for item in facts}) >= 2


def test_public_turn_is_one_query_and_private_fields_do_not_leak() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(11, {"divider_reference": "frame_midpoint"}, 3, 4)
    views = [adapter.public_turn(episode, index) for index in range(4)]
    assert all(set(view) == {"train", "test"} for view in views)
    assert all(len(view["test"]) == 1 and set(view["test"][0]) == {"input"} for view in views)
    assert [view["test"][0]["input"] for view in views] == [pair["input"] for pair in episode["test"]]


def test_invalid_settings_counts_and_scalars_fail_closed() -> None:
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(True, {"divider_reference": "block_midrange"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"divider_reference": "unknown"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"divider_reference": "block_midrange", "extra": 1}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"divider_reference": "block_midrange"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"divider_reference": "block_midrange"}, 2, 5)


def test_divider_intermediate_causally_controls_quadrant_rendering() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(29, {"divider_reference": "frame_midpoint"}, 2, 4)
    grid = episode["test"][0]["input"]
    facts = adapter.analyze(grid)
    assert facts["block_midrange_divider"] != facts["frame_midpoint_divider"]
    assert adapter.render_with_divider(facts["blocks"], facts["block_midrange_divider"]) != adapter.render_with_divider(
        facts["blocks"], facts["frame_midpoint_divider"]
    )
