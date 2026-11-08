from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def load_prototype():
    path = PARAM / "prototype.py"
    name = "_test_a7d4_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def visible_inputs(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    module = load_prototype()
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert module.program({"placement": "bbox_top_left"}) == canonical
    alternate = module.program({"placement": "preserve_first_cell"})
    assert alternate == (PARAM / "preserve_first_cell.rkt").read_text(encoding="utf-8")
    assert alternate != canonical


def test_count_prefixes_matched_inputs_and_claim_labels():
    module = load_prototype()
    episodes = {}
    for setting in module.SETTINGS:
        small = module.generate(17, setting, demos=2, queries=1)
        large = module.generate(17, setting, demos=6, queries=4)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]
        assert small["program_solution"] == module.program(setting)
        assert len(set(visible_inputs(large))) == 10
        for split in ("train", "test"):
            for pair in large[split]:
                assert pair["output"] == module.solve(pair["input"], setting)
        episodes[setting["placement"]] = large
    assert [p["input"] for split in ("train", "test") for p in episodes["bbox_top_left"][split]] == [
        p["input"] for split in ("train", "test") for p in episodes["preserve_first_cell"][split]
    ]


def test_two_demos_identify_setting_and_refute_declared_shortcuts():
    module = load_prototype()
    for seed in range(24):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            review = module.self_review(episode)
            assert review["intended_survivors"] == [setting["placement"]]
            assert review["harmful_survivors"] == [], (seed, setting, review)


def test_fourth_query_is_substantive_30x30_and_both_settings_differ():
    module = load_prototype()
    left = module.generate(0, {"placement": "bbox_top_left"}, demos=2, queries=4)
    pivot = module.generate(0, {"placement": "preserve_first_cell"}, demos=2, queries=4)
    grid = left["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    motif = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value and (r, c) != (0, 0)}
    assert len(motif) >= 70
    assert len({grid[r][c] for r, c in motif}) == 1
    assert left["test"][3]["output"] != pivot["test"][3]["output"]
    assert module.diff_cells(left["test"][3]["output"], pivot["test"][3]["output"]) >= 40
    assert module.causal_case()["difference_cells"] > 0


def test_public_turn_masks_all_private_material_and_future_queries():
    module = load_prototype()
    episode = module.generate(3, {"placement": "preserve_first_cell"}, demos=3, queries=4)
    public = module.public_turn(episode, 2)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert public["test"][0] == {"input": episode["test"][2]["input"]}
    text = json.dumps(public)
    for forbidden in ("placement", "program_solution", "preserve_first_cell", "bbox_top_left"):
        assert forbidden not in text


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"placement": "bbox_top_left"}, 3, 4),
        (True, {"placement": "bbox_top_left"}, 3, 4),
        (0, {"placement": "unknown"}, 3, 4),
        (0, {"placement": "bbox_top_left", "extra": 1}, 3, 4),
        (0, {"placement": "bbox_top_left"}, 1, 4),
        (0, {"placement": "bbox_top_left"}, 3, 5),
    ],
)
def test_invalid_requests_are_rejected(args):
    module = load_prototype()
    with pytest.raises(ValueError):
        module.generate(*args)
