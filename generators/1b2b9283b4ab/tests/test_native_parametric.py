from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "1b2b9283b4ab"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / name
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def test_native_program_preserves_exact_default_and_changes_only_tie_marker():
    adapter = _load("adapter.py")
    assert adapter.program({"tie_marker": 8}) == _canonical_program()
    alternate = adapter.program({"tie_marker": 6})
    assert alternate != _canonical_program()
    assert alternate.count("(fill (if (= (length best-colors) 1) (first best-colors) 6))") == 1


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_episode_counts_are_deterministic_distinct_and_setting_independent(demos, queries):
    adapter = _load("adapter.py")
    family = _load("family.py")
    a = adapter.generate(19, {"tie_marker": 8}, demos, queries)
    b = adapter.generate(19, {"tie_marker": 6}, demos, queries)
    again = adapter.generate(19, {"tie_marker": 8}, demos, queries)
    assert a == again
    assert [p["input"] for p in a["train"] + a["test"]] == [
        p["input"] for p in b["train"] + b["test"]
    ]
    assert len(a["train"]) == demos
    assert len(a["test"]) == queries
    inputs = [json.dumps(p["input"], separators=(",", ":")) for p in a["train"] + a["test"]]
    assert len(inputs) == len(set(inputs))
    for marker, episode in [(8, a), (6, b)]:
        assert episode["program_solution"] == adapter.program({"tie_marker": marker})
        assert all(pair["output"] == family.transform(pair["input"], marker)
                   for pair in episode["train"] + episode["test"])


def test_minimum_lesson_identifies_both_settings_and_queries_include_real_30x30_stress():
    adapter = _load("adapter.py")
    episodes = {marker: adapter.generate(0, {"tie_marker": marker}, 2, 4) for marker in (8, 6)}
    assert [len(pair["input"]) for pair in episodes[8]["test"]][-1] == 30
    assert len(episodes[8]["test"][-1]["input"][0]) == 30
    nonwall = sum(cell not in (1, 7, 9) for row in episodes[8]["test"][-1]["input"] for cell in row)
    assert nonwall >= 300
    for marker, episode in episodes.items():
        rival = 6 if marker == 8 else 8
        assert any(pair["output"] != _load("family.py").transform(pair["input"], rival)
                   for pair in episode["train"])


def test_count_prefix_stability_and_validation():
    adapter = _load("adapter.py")
    short = adapter.generate(37, {"tie_marker": 8}, 2, 1)
    long = adapter.generate(37, {"tie_marker": 8}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    for bad in ({}, {"tie_marker": 7}, {"tie_marker": True}, {"tie_marker": 8, "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    with pytest.raises(ValueError):
        adapter.generate(0, {"tie_marker": 8}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"tie_marker": 8}, 2, 5)


def test_input_dependent_intermediate_drives_output_and_wrong_intermediate_changes_it():
    family = _load("family.py")
    pair = family.generate_episode(11, tie_marker=6, demos=2, queries=4)["test"][-1]
    intermediate = family.nearest_color_intermediate(pair["input"])
    assert len(intermediate["rooms"]) >= 20
    assert any(len(row["nearest_colors"]) > 1 for row in intermediate["rooms"])
    assert family.transform(pair["input"], 6) == pair["output"]
    assert family.transform_all_colors_as_nearest(pair["input"], 6) != pair["output"]
