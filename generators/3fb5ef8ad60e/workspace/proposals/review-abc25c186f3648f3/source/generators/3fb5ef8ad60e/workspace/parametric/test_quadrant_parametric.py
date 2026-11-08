from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_quadrant_key_adapter_test", HERE / "adapter.py")
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def test_default_program_is_exact_canonical_bytes():
    assert ADAPTER.program({"finish_mode": "quadrant_summary"}) == (HERE / "canonical.rkt").read_text()
    assert ADAPTER.program({"finish_mode": "indexed_color_rotate"}) == (HERE / "indexed_color_rotate.rkt").read_text()
    assert ADAPTER.program({"finish_mode": "indexed_color_rotate"}) != ADAPTER.program({"finish_mode": "quadrant_summary"})


def test_generate_is_prefix_stable_and_setting_neutral():
    full = {
        mode: ADAPTER.generate(731, {"finish_mode": mode}, 6, 4)
        for mode in ("quadrant_summary", "indexed_color_rotate")
    }
    assert [p["input"] for p in full["quadrant_summary"]["train"] + full["quadrant_summary"]["test"]] == [
        p["input"] for p in full["indexed_color_rotate"]["train"] + full["indexed_color_rotate"]["test"]
    ]
    for demos in range(2, 7):
        short = ADAPTER.generate(731, {"finish_mode": "indexed_color_rotate"}, demos, 4)
        assert short["train"] == full["indexed_color_rotate"]["train"][:demos]
    for queries in range(1, 5):
        short = ADAPTER.generate(731, {"finish_mode": "quadrant_summary"}, 2, queries)
        assert short["test"] == full["quadrant_summary"]["test"][:queries]
    inputs = [json.dumps(p["input"], separators=(",", ":")) for p in full["indexed_color_rotate"]["train"] + full["indexed_color_rotate"]["test"]]
    assert len(inputs) == len(set(inputs))


def test_two_demos_distinguish_settings_and_selected_color_controls_rotation():
    for seed in range(8):
        canonical = ADAPTER.generate(seed, {"finish_mode": "quadrant_summary"}, 2, 4)
        keyed = ADAPTER.generate(seed, {"finish_mode": "indexed_color_rotate"}, 2, 4)
        assert any(a["output"] != b["output"] for a, b in zip(canonical["train"], keyed["train"]))
        for pair in keyed["train"] + keyed["test"]:
            key = summary = ADAPTER.quadrant_summary(pair["input"])
            index = ADAPTER.selector_index(pair["input"])
            selected = summary[index // 2][index % 2]
            assert pair["output"] == ADAPTER.rotate_by_color(summary, selected)
            assert sorted(v for row in pair["output"] for v in row if v) == sorted(
                v for row in summary for v in row if v
            )


def test_fourth_query_is_substantive_30_by_30():
    episode = ADAPTER.generate(99, {"finish_mode": "indexed_color_rotate"}, 2, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 600
    assert len({value for row in grid for value in row if value not in (0, 8)}) == 4
    r0, c0, r1, c1 = ADAPTER.eight_bbox(grid)
    assert all(value in (0, 8) for r, row in enumerate(grid) for c, value in enumerate(row) if not (r0 <= r <= r1 and c0 <= c <= c1))


@pytest.mark.parametrize("bad", [None, {}, {"finish_mode": "bad"}, {"finish_mode": 1}, {"finish_mode": "quadrant_summary", "x": 1}])
def test_settings_are_strict(bad):
    with pytest.raises(ValueError):
        ADAPTER.program(bad)


@pytest.mark.parametrize("kwargs", [
    {"seed": True, "settings": {"finish_mode": "quadrant_summary"}, "demos": 2, "queries": 4},
    {"seed": 0, "settings": {"finish_mode": "quadrant_summary"}, "demos": 1, "queries": 4},
    {"seed": 0, "settings": {"finish_mode": "quadrant_summary"}, "demos": 2, "queries": 5},
])
def test_counts_and_seed_are_type_strict(kwargs):
    with pytest.raises(ValueError):
        ADAPTER.generate(**kwargs)
