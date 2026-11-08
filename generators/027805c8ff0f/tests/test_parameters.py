"""Behavioral checks for the proposed transform-application family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes, normalize_grid

TASK_ID = "027805c8ff0f"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
ADAPTER = HOME / "workspace/parametric/adapter.py"
SETTINGS = ({"applications": "once"}, {"applications": "twice"})


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    assert PROTOTYPE.is_file(), "assigned runnable parametric prototype is missing"
    return _load(PROTOTYPE, "transform_application_prototype_test")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=90) as runtime:
        assert runtime.runtime_identity.get("protected") is True
        yield runtime


def _apply(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {literal})"))


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text(encoding="utf-8").splitlines())
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_prototype_and_native_adapter_exist():
    assert PROTOTYPE.is_file()
    assert ADAPTER.is_file()


def test_default_program_is_exact_canonical_bytes(p):
    assert p.program({"applications": "once"}) == _canonical_program()
    assert p.program({"applications": "once"}) != p.program({"applications": "twice"})


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_setting_independence_query_prefix_and_racket_labels(p, bridge, demos):
    episodes = {setting["applications"]: p.generate(113, setting, demos, 4) for setting in SETTINGS}
    once, twice = episodes["once"], episodes["twice"]
    assert len(once["train"]) == demos and len(once["test"]) == 4
    assert len(twice["train"]) == demos and len(twice["test"]) == 4
    for split in ("train", "test"):
        assert [pair["input"] for pair in once[split]] == [pair["input"] for pair in twice[split]]
    short = p.generate(113, {"applications": "once"}, demos, 1)
    visible_full = {"train": once["train"], "test": [{"input": once["test"][0]["input"]}]}
    assert public_challenge_bytes(visible_full) == public_challenge_bytes(short)
    all_inputs = [pair["input"] for split in ("train", "test") for pair in once[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == demos + 4
    for setting, episode in ((SETTINGS[0], once), (SETTINGS[1], twice)):
        source = p.program(setting)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert _apply(bridge, source, pair["input"]) == pair["output"]


def test_two_demonstrations_identify_the_selected_application_count(p, bridge):
    programs = {s["applications"]: p.program(s) for s in SETTINGS}
    for setting in SETTINGS:
        episode = p.generate(229, setting, 2, 4)
        survivors = []
        for name, source in programs.items():
            if all(_apply(bridge, source, pair["input"]) == pair["output"] for pair in episode["train"]):
                survivors.append(name)
        assert survivors == [setting["applications"]]


def test_intermediate_transform_is_input_derived_and_controls_final_output(p):
    original = p.sample_input(431, "dependency", 0, 12, 8, transform_code=2)
    changed = p.retarget_transform(original, 3)
    assert p.extract_query(original) == p.extract_query(changed)
    assert p.infer_transform(original) == 2
    assert p.infer_transform(changed) == 3
    for setting in SETTINGS:
        assert p.transform(original, setting) != p.transform(changed, setting)


def test_near_maximum_30_by_29_query_has_distributed_content_and_valid_labels(p, bridge):
    episode = p.generate(887, {"applications": "twice"}, 2, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert len(grid) == 30 and len(grid[0]) == 29
    # The stress input is not a tiny top-left token on an otherwise blank canvas.
    quadrants = [
        sum(grid[r][c] not in (0, 1) for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 14), range(14, 29))
    ]
    assert min(quadrants) > 0
    assert _apply(bridge, p.program({"applications": "twice"}), grid) == pair["output"]


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"settings": {"applications": "thrice"}},
        {"settings": {"applications": "once", "unknown": 1}},
    ],
)
def test_invalid_requests_fail_closed(p, case):
    kwargs = {"seed": 0, "settings": {"applications": "once"}, "demos": 2, "queries": 4}
    kwargs.update(case)
    with pytest.raises(ValueError):
        p.generate(**kwargs)


def test_native_adapter_is_adjacent_path_bound(p):
    import sys
    import types

    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        adapter = _load(ADAPTER, "transform_application_native_adapter_test")
        settings = {"applications": "twice"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(19, settings, 2, 4) == p.generate(19, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_python_verifier_rejects_corrupted_labels_and_underteaching(p):
    episode = p.generate(991, {"applications": "once"}, 2, 4)
    assert p.verify_episode(episode)["survivors"] == ["once"]
    broken = deepcopy(episode)
    broken["test"][0]["output"][0][0] = (broken["test"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        p.verify_episode(broken)
    blank = deepcopy(episode)
    blank["train"] = [
        {"input": pair["input"], "output": p.transform(pair["input"], {"applications": "once"})}
        for pair in blank["train"]
    ]
    # Replacing teaching outputs with a setting-independent claim must not be certified.
    blank["train"][0]["output"] = p.transform(blank["train"][0]["input"], {"applications": "twice"})
    with pytest.raises(ValueError):
        p.verify_episode(blank)


def test_profile_dimensions_do_not_reveal_the_inferred_transform(p):
    train_codes = {
        p.infer_transform(p.generate(seed, {"applications": "once"}, 2, 4)["train"][0]["input"])
        for seed in range(24)
    }
    query_codes = {
        p.infer_transform(p.generate(seed, {"applications": "once"}, 2, 4)["test"][0]["input"])
        for seed in range(24)
    }
    assert len(train_codes) >= 4
    assert len(query_codes) >= 4
    for seed in range(24):
        episode = p.generate(seed, {"applications": "once"}, 2, 4)
        assert len({p.infer_transform(pair["input"]) for pair in episode["train"]}) == 2
