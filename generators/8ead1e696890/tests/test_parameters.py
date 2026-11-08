"""Behavioral checks for the border-vs-top-reference-area family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, normalize_grid, public_challenge_bytes

TASK_ID = "8ead1e696890"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
ADAPTER = HOME / "workspace/parametric/adapter.py"
SETTINGS = ({"selection": "border"}, {"selection": "top_area"})


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    assert PROTOTYPE.is_file(), "assigned runnable parametric prototype is missing"
    return _load(PROTOTYPE, "border_area_prototype_test")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=90) as runtime:
        assert runtime.runtime_identity.get("protected") is True
        yield runtime


def _apply(bridge, source, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def _canonical_program():
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text(encoding="utf-8").splitlines())
        if row.get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_prototype_and_adapter_exist():
    assert PROTOTYPE.is_file()
    assert ADAPTER.is_file()


def test_default_program_is_exact_canonical_bytes(p):
    assert p.program({"selection": "border"}) == _canonical_program()
    assert p.program({"selection": "border"}) != p.program({"selection": "top_area"})


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_setting_independence_query_prefix_and_racket_labels(p, bridge, demos):
    episodes = {setting["selection"]: p.generate(141, setting, demos, 4) for setting in SETTINGS}
    border, top_area = episodes["border"], episodes["top_area"]
    assert len(border["train"]) == demos and len(border["test"]) == 4
    assert len(top_area["train"]) == demos and len(top_area["test"]) == 4
    for split in ("train", "test"):
        assert [pair["input"] for pair in border[split]] == [pair["input"] for pair in top_area[split]]
    one = p.generate(141, {"selection": "border"}, demos, 1)
    visible = {"train": border["train"], "test": [{"input": border["test"][0]["input"]}]}
    assert public_challenge_bytes(visible) == public_challenge_bytes(one)
    all_inputs = [pair["input"] for split in ("train", "test") for pair in border[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == demos + 4
    for setting, episode in ((SETTINGS[0], border), (SETTINGS[1], top_area)):
        source = p.program(setting)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert _apply(bridge, source, pair["input"]) == pair["output"]


def test_two_demos_identify_selected_rule_from_labels_only(p, bridge):
    programs = {setting["selection"]: p.program(setting) for setting in SETTINGS}
    for setting in SETTINGS:
        episode = p.generate(313, setting, 2, 4)
        survivors = [
            name for name, source in programs.items()
            if all(_apply(bridge, source, pair["input"]) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [setting["selection"]]


def test_top_reference_area_is_input_derived_and_changes_downstream_selection(p):
    original = p.sample_input(401, "dependency", 0, 14, 16, reference_area=3)
    changed = p.retarget_reference_area(original, 4)
    assert p.top_reference_area(original) == 3
    assert p.top_reference_area(changed) == 4
    original_kept = p.kept_component_areas(p.transform(original, {"selection": "top_area"}))
    changed_kept = p.kept_component_areas(p.transform(changed, {"selection": "top_area"}))
    assert original_kept and set(original_kept) == {3}
    assert changed_kept and set(changed_kept) == {4}
    assert p.transform(original, {"selection": "top_area"}) != p.transform(
        changed, {"selection": "top_area"}
    )


def test_every_sample_has_unique_top_reference_matching_interior_and_wrong_area_border(p):
    for index, (height, width, area) in enumerate(p.DEMO_PROFILES + p.QUERY_PROFILES):
        grid = p.sample_input(517, "grammar", index, height, width, reference_area=area)
        components = p.components(grid)
        top = [cells for _, cells in components if any(r == 0 for r, _ in cells)]
        assert len(top) == 1 and len(top[0]) == area
        assert any(len(cells) == area and not p.touches_border(cells, height, width)
                   for _, cells in components)
        assert any(len(cells) != area and p.touches_border(cells, height, width)
                   for _, cells in components)


def test_30_by_30_stress_uses_all_quadrants_and_racket_label(p, bridge):
    pair = p.generate(773, {"selection": "top_area"}, 2, 4)["test"][3]
    grid = pair["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    quadrant_counts = [
        sum(grid[r][c] != 0 for r in rr for c in cc)
        for rr in (range(0, 15), range(15, 30))
        for cc in (range(0, 15), range(15, 30))
    ]
    assert min(quadrant_counts) > 0
    assert _apply(bridge, p.program({"selection": "top_area"}), grid) == pair["output"]


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"settings": {"selection": "size"}},
        {"settings": {"selection": "border", "unknown": 1}},
    ],
)
def test_invalid_requests_fail_closed(p, case):
    kwargs = {"seed": 0, "settings": {"selection": "border"}, "demos": 2, "queries": 4}
    kwargs.update(case)
    with pytest.raises(ValueError):
        p.generate(**kwargs)


def test_native_adapter_is_bound_to_adjacent_prototype(p):
    import sys
    import types

    previous = sys.modules.get("prototype")
    sys.modules["prototype"] = types.ModuleType("prototype")
    try:
        adapter = _load(ADAPTER, "border_area_native_adapter_test")
        settings = {"selection": "top_area"}
        assert adapter.program(settings) == p.program(settings)
        assert adapter.generate(37, settings, 2, 4) == p.generate(37, settings, 2, 4)
    finally:
        if previous is None:
            sys.modules.pop("prototype", None)
        else:
            sys.modules["prototype"] = previous


def test_python_verifier_rejects_corruption_and_mixed_teaching_labels(p):
    episode = p.generate(881, {"selection": "top_area"}, 2, 4)
    assert p.verify_episode(episode)["survivors"] == ["top_area"]
    corrupted = deepcopy(episode)
    corrupted["test"][0]["output"][0][0] = (corrupted["test"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        p.verify_episode(corrupted)
    mixed = deepcopy(episode)
    mixed["train"][0]["output"] = p.transform(mixed["train"][0]["input"], {"selection": "border"})
    with pytest.raises(ValueError):
        p.verify_episode(mixed)


def test_profile_dimensions_do_not_reveal_the_reference_area(p):
    train_areas = {
        p.top_reference_area(p.generate(seed, {"selection": "border"}, 2, 4)["train"][0]["input"])
        for seed in range(24)
    }
    query_areas = {
        p.top_reference_area(p.generate(seed, {"selection": "border"}, 2, 4)["test"][0]["input"])
        for seed in range(24)
    }
    assert len(train_areas) >= 4
    assert len(query_areas) >= 4
    for seed in range(24):
        episode = p.generate(seed, {"selection": "border"}, 2, 4)
        assert len({p.top_reference_area(pair["input"]) for pair in episode["train"]}) == 2


def test_30_by_30_stress_uses_all_quadrants_across_reference_areas(p):
    areas = set()
    for seed in range(32):
        grid = p.generate(seed, {"selection": "border"}, 2, 4)["test"][3]["input"]
        areas.add(p.top_reference_area(grid))
        quadrant_counts = [
            sum(grid[r][c] != 0 for r in rr for c in cc)
            for rr in (range(0, 15), range(15, 30))
            for cc in (range(0, 15), range(15, 30))
        ]
        assert min(quadrant_counts) > 0
    assert areas == set(p.REFERENCE_AREAS)
