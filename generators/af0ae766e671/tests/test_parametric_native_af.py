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
    name = "_test_af0a_parametric_native_" + hashlib.sha256(str(path).encode()).hexdigest()
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
    assert module.program({"selection": "xor"}) == canonical
    alternate = module.program({"selection": "sparser_panel_only"})
    assert alternate == (PARAM / "sparser_panel_only.rkt").read_text(encoding="utf-8")
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
        episodes[setting["selection"]] = large
    assert [p["input"] for split in ("train", "test") for p in episodes["xor"][split]] == [
        p["input"] for split in ("train", "test") for p in episodes["sparser_panel_only"][split]
    ]


def test_two_demos_identify_setting_and_refute_declared_shortcuts():
    module = load_prototype()
    for seed in range(32):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            review = module.self_review(episode)
            assert review["intended_survivors"] == [setting["selection"]]
            assert review["harmful_survivors"] == [], (seed, setting, review)


def test_fourth_query_is_substantive_30x30_and_density_dependent():
    module = load_prototype()
    xor = module.generate(0, {"selection": "xor"}, demos=2, queries=4)
    sparse = module.generate(0, {"selection": "sparser_panel_only"}, demos=2, queries=4)
    grid = xor["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 350
    stats = module.occupancy_stats(grid)
    assert stats["upper_count"] != stats["lower_count"]
    assert set(stats["state_counts"]) == {0, 1, 2, 3}
    assert min(stats["state_counts"].values()) > 0
    assert xor["test"][3]["output"] != sparse["test"][3]["output"]
    assert module.diff_cells(xor["test"][3]["output"], sparse["test"][3]["output"]) >= 60
    assert module.causal_case()["difference_cells"] > 0


def test_public_turn_masks_private_material_and_future_queries():
    module = load_prototype()
    episode = module.generate(5, {"selection": "sparser_panel_only"}, demos=3, queries=4)
    public = module.public_turn(episode, 1)
    assert set(public) == {"train", "test"}
    assert public["test"] == [{"input": episode["test"][1]["input"]}]
    text = json.dumps(public)
    for forbidden in ("selection", "program_solution", "sparser_panel_only"):
        assert forbidden not in text


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"selection": "xor"}, 3, 4),
        (True, {"selection": "xor"}, 3, 4),
        (0, {"selection": "and"}, 3, 4),
        (0, {"selection": "xor", "extra": 1}, 3, 4),
        (0, {"selection": "xor"}, 1, 4),
        (0, {"selection": "xor"}, 3, 5),
    ],
)
def test_invalid_requests_are_rejected(args):
    module = load_prototype()
    with pytest.raises(ValueError):
        module.generate(*args)
