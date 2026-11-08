from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK = "d0a85a878975"
HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_test_d0_parametric_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _visible_inputs(episode):
    return [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["train"] + episode["test"]]


def test_program_preserves_exact_canonical_and_has_complete_alternative() -> None:
    adapter = _load_adapter()
    record = Catalog(Path(__file__).resolve().parents[3]).get(TASK)
    canonical = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(canonical) == 1
    assert adapter.program({"block_order": "construction"}) == canonical.pop()
    alternative = adapter.program({"block_order": "reverse_construction"})
    assert alternative.startswith("(rule!")
    assert alternative.rstrip().endswith(")")
    assert alternative != adapter.program({"block_order": "construction"})


def test_generate_supports_all_counts_matched_inputs_and_30x30() -> None:
    adapter = _load_adapter()
    for demos in range(2, 7):
        for queries in range(1, 5):
            episodes = [
                adapter.generate(19, {"block_order": setting}, demos, queries)
                for setting in adapter.BLOCK_ORDERS
            ]
            assert all(len(ep["train"]) == demos and len(ep["test"]) == queries for ep in episodes)
            assert [_visible_inputs(ep) for ep in episodes][0] == [_visible_inputs(ep) for ep in episodes][1]
            assert len(_visible_inputs(episodes[0])) == len(set(_visible_inputs(episodes[0])))
            for setting, episode in zip(adapter.BLOCK_ORDERS, episodes, strict=True):
                for pair in episode["train"] + episode["test"]:
                    assert pair["output"] == adapter.solve(pair["input"], {"block_order": setting})
                    assert adapter.solve(pair["input"], {"block_order": "construction"}) != adapter.solve(
                        pair["input"], {"block_order": "reverse_construction"}
                    )
    full = adapter.generate(19, {"block_order": "construction"}, 6, 4)
    assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in full["test"])


def test_two_demos_identify_each_setting_against_declared_rivals() -> None:
    adapter = _load_adapter()
    for setting in adapter.BLOCK_ORDERS:
        episode = adapter.generate(7, {"block_order": setting}, 2, 4)
        report = adapter.lesson_report(episode, {"block_order": setting})
        assert report["surviving_rivals"] == []
        assert report["query_disagreements"] == []
        assert set(report["rivals_tested"]) >= ({"construction", "reverse_construction"} - {setting})


def test_public_turn_hides_program_settings_answers_and_future_queries() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(23, {"block_order": "reverse_construction"}, 3, 4)
    views = [adapter.public_turn(episode, index) for index in range(4)]
    assert all(set(view) == {"train", "test"} for view in views)
    assert all(len(view["test"]) == 1 and set(view["test"][0]) == {"input"} for view in views)
    assert all("program_solution" not in view for view in views)
    assert [view["test"][0]["input"] for view in views] == [pair["input"] for pair in episode["test"]]


def test_invalid_settings_and_counts_fail_closed() -> None:
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(True, {"block_order": "construction"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"block_order": "construction", "extra": 1}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"block_order": "unknown"}, 2, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"block_order": "construction"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"block_order": "construction"}, 2, 5)


def test_sequential_intermediate_controls_rendering() -> None:
    adapter = _load_adapter()
    episode = adapter.generate(31, {"block_order": "reverse_construction"}, 2, 4)
    grid = episode["test"][0]["input"]
    facts = adapter.analyze(grid)
    assert facts["construction_blocks"]
    assert facts["construction_blocks"] != facts["reverse_construction_blocks"]
    assert adapter.render_from_blocks(grid, facts["construction_blocks"]) != adapter.render_from_blocks(
        grid, facts["reverse_construction_blocks"]
    )
