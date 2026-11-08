from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str):
    path = PARAM / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_1bfb_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_source():
    p = _load("prototype")
    source = (PARAM / "canonical.rkt").read_text()
    assert p.program({"finish": "borders_only"}) == source
    assert hashlib.sha256(source.encode()).hexdigest() == p.CANONICAL_PROGRAM_SHA256


def test_counts_prefixes_matched_inputs_and_distinctness():
    p = _load("prototype")
    small = p.generate(17, {"finish": "borders_only"}, 3, 1)
    large = p.generate(17, {"finish": "borders_only"}, 6, 4)
    alt = p.generate(17, {"finish": "fill_largest_interior"}, 6, 4)
    assert small["train"] == large["train"][:3]
    assert small["test"] == large["test"][:1]
    assert [x["input"] for x in large["train"] + large["test"]] == [
        x["input"] for x in alt["train"] + alt["test"]
    ]
    inputs = [repr(x["input"]) for x in large["train"] + large["test"]]
    assert len(inputs) == len(set(inputs))


def test_three_demos_identify_largest_interior_finish_and_oracle_labels():
    p = _load("prototype")
    base = p.generate(3, {"finish": "borders_only"}, 3, 4)
    alt = p.generate(3, {"finish": "fill_largest_interior"}, 3, 4)
    assert all(a["output"] != b["output"] for a, b in zip(base["train"], alt["train"]))
    for finish, episode in (("borders_only", base), ("fill_largest_interior", alt)):
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == p.solve(pair["input"], finish)


def test_selected_rectangle_is_unique_largest_interior_not_longest_perimeter():
    p = _load("prototype")
    episode = p.generate(11, {"finish": "fill_largest_interior"}, 3, 4)
    info = p.describe(episode["train"][0]["input"], {"finish": "fill_largest_interior"})
    assert info["winner_interior_area"] > 0
    assert info["winner_color"] != info["longest_perimeter_color"]
    assert info["winner_color"] != info["largest_bbox_color"]
    assert info["unique_largest_interior"] is True


def test_fourth_query_is_substantive_30x30_with_four_rectangles():
    p = _load("prototype")
    episode = p.generate(29, {"finish": "fill_largest_interior"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = p.describe(grid, {"finish": "fill_largest_interior"})
    assert info["rectangles"] == 4
    assert info["total_border_cells"] >= 100
    assert info["winner_interior_area"] >= 60


def test_public_turn_reveals_one_query_input_only():
    p = _load("prototype")
    episode = p.generate(5, {"finish": "fill_largest_interior"}, 3, 4)
    view = p.public_turn(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert "settings" not in repr(view)


@pytest.mark.parametrize("demos,queries", [(2, 4), (7, 4), (3, 0), (3, 5)])
def test_invalid_count_requests_fail_closed(demos, queries):
    p = _load("prototype")
    with pytest.raises(ValueError):
        p.generate(0, {"finish": "borders_only"}, demos, queries)


def test_invalid_settings_fail_closed():
    p = _load("prototype")
    with pytest.raises(ValueError):
        p.program({"finish": "unknown"})
    with pytest.raises(ValueError):
        p.program({"finish": "borders_only", "extra": 1})


def test_reusable_self_audit_covers_domain_and_shortcut_rivals():
    audit = _load("audit")
    report = audit.run()
    assert report["status"] == "passed"
    assert report["seeds"] == [0, 17, 97]
    assert report["checks"]["matched_inputs"] > 0
    assert report["checks"]["stable_prefixes"] > 0
    assert report["checks"]["privacy_views"] > 0
    assert all(count > 0 for count in report["rival_disagreements"].values())
