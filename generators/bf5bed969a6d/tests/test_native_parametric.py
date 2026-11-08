from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "bf5bed969a6d"
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


def test_native_program_preserves_exact_default_and_rotates_extracted_template():
    adapter = _load("adapter.py")
    assert adapter.program({"template_transform": "as_is"}) == _canonical_program()
    rotated = adapter.program({"template_transform": "rotate_cw"})
    assert rotated != _canonical_program()
    assert "(- tr0 1 (first p))" in rotated


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_episode_counts_are_deterministic_distinct_and_setting_independent(demos, queries):
    adapter = _load("adapter.py")
    family = _load("family.py")
    canonical = adapter.generate(23, {"template_transform": "as_is"}, demos, queries)
    rotated = adapter.generate(23, {"template_transform": "rotate_cw"}, demos, queries)
    assert canonical == adapter.generate(23, {"template_transform": "as_is"}, demos, queries)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in rotated["train"] + rotated["test"]
    ]
    inputs = [json.dumps(p["input"], separators=(",", ":"))
              for p in canonical["train"] + canonical["test"]]
    assert len(inputs) == len(set(inputs))
    for mode, episode in [("as_is", canonical), ("rotate_cw", rotated)]:
        assert episode["program_solution"] == adapter.program({"template_transform": mode})
        assert all(pair["output"] == family.transform(pair["input"], mode)
                   for pair in episode["train"] + episode["test"])


def test_minimum_lesson_identifies_both_settings_and_covers_occlusion_and_30x30():
    adapter = _load("adapter.py")
    family = _load("family.py")
    episodes = {mode: adapter.generate(0, {"template_transform": mode}, 2, 4)
                for mode in ("as_is", "rotate_cw")}
    for mode, episode in episodes.items():
        rival = "rotate_cw" if mode == "as_is" else "as_is"
        assert any(pair["output"] != family.transform(pair["input"], rival)
                   for pair in episode["train"])
    queries = episodes["as_is"]["test"]
    assert len(queries[-1]["input"]) == 30 and len(queries[-1]["input"][0]) == 30
    assert sum(cell != 0 for row in queries[-1]["input"] for cell in row) >= 100
    assert any(family.same_color_component_count(pair["input"]) > 3 for pair in queries)


def test_count_prefix_stability_and_validation():
    adapter = _load("adapter.py")
    short = adapter.generate(91, {"template_transform": "as_is"}, 2, 1)
    long = adapter.generate(91, {"template_transform": "as_is"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    for bad in ({}, {"template_transform": "flip"}, {"template_transform": 1},
                {"template_transform": "as_is", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    with pytest.raises(ValueError):
        adapter.generate(0, {"template_transform": "as_is"}, 1, 4)
    with pytest.raises(ValueError):
        adapter.generate(0, {"template_transform": "as_is"}, 2, 5)


def test_extracted_template_intermediate_is_required_by_stamping_step():
    family = _load("family.py")
    pair = family.generate_episode(7, template_transform="rotate_cw", demos=2, queries=4)["test"][-1]
    intermediate = family.template_intermediate(pair["input"], "rotate_cw")
    assert intermediate["source_cells"]
    assert intermediate["offsets"]
    assert family.transform(pair["input"], "rotate_cw") == pair["output"]
    assert family.transform_with_fixed_intermediate(pair["input"], "rotate_cw") != pair["output"]
