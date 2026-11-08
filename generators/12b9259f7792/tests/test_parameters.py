"""Focused contracts for the native nearest-marker parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK_ID = "12b9259f7792"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
MODES = ("all_nearest", "dominant_assignment")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("nearest_marker_adapter_tests", PARAM / "adapter.py")


def _family():
    return _load("nearest_marker_family_tests", PARAM / "family.py")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_generator_honors_exact_controls_and_rejects_unknowns():
    gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    grid = gen.generate(
        0,
        0,
        difficulty="easy",
        grid_h=16,
        grid_w=16,
        n_blobs=4,
        n_distinct_colors=4,
        palette_size=4,
        palette_kind="warm",
        position_bias="varied",
        density="sparse",
    )
    assert (len(grid), len(grid[0])) == (16, 16)
    assert len(gen._components_of_color(grid, 5)) == 4
    assert len([(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3, 4)]) == 4
    assert gen.self_check(grid) == []
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, typo_axis=1)


def test_default_program_is_byte_exact_selected_authority():
    adapter = _adapter()
    record = Catalog(ROOT).get(TASK_ID)
    programs = {v["program_solution"] for v in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAM / "canonical.rkt").read_text() == canonical
    assert adapter.program({"mode": "all_nearest"}) == canonical
    assert adapter.program({"mode": "dominant_assignment"}) != canonical


def test_contract_is_finite_and_strict():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": list(MODES)}
    assert contract["default"] == {"mode": "all_nearest"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    adapter = _adapter()
    for bad in [None, {}, [], {"mode": True}, {"mode": "bad"}, {"mode": "all_nearest", "x": 1}]:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_match_across_modes_and_prefixes_are_stable(seed):
    adapter = _adapter()
    full = {mode: adapter.generate(seed, {"mode": mode}, 6, 4) for mode in MODES}
    assert _inputs(full[MODES[0]]) == _inputs(full[MODES[1]])
    assert len({json.dumps(g, separators=(",", ":")) for g in _inputs(full[MODES[0]])}) == 10
    for mode, baseline in full.items():
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(seed, {"mode": mode}, demos, queries)
                assert episode["train"] == baseline["train"][:demos]
                assert episode["test"] == baseline["test"][:queries]
                assert episode["program_solution"] == adapter.program({"mode": mode})


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("mode", MODES)
def test_two_demos_identify_mode_and_refute_named_rivals(seed, mode):
    adapter = _adapter()
    family = _family()
    episode = adapter.generate(seed, {"mode": mode}, 2, 4)
    survivors = [
        candidate
        for candidate in MODES
        if all(family.solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    assert survivors == [mode]
    for name, rival in family.audit_rivals(mode).items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), name
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["test"]), name


def test_scene_construction_is_memoized_and_returns_fresh_copy(monkeypatch):
    family = _family()
    original = family._ordinary_scene
    calls = 0

    def counted(seed, split, index):
        nonlocal calls
        calls += 1
        return original(seed, split, index)

    monkeypatch.setattr(family, "_ordinary_scene", counted)
    first = family.scene(444444, "train", 1)
    second = family.scene(444444, "train", 1)
    assert calls == 1
    first[0][0] = 9
    assert second[0][0] != 9


def test_sequential_intermediate_and_skip_a_change_final_output():
    family = _family()
    grid = family.scene(0, "train", 0)
    analysis = family.analyze(grid)
    assert len(set(analysis["assigned_area_by_color"].values())) > 1
    intended = family.solve(grid, "dominant_assignment")
    skipped = family.solve_skip_assignment(grid)
    assert intended != skipped
    assert analysis["winner_color"] in analysis["assigned_area_by_color"]


def test_fourth_query_is_substantive_30x30_stress():
    adapter = _adapter()
    family = _family()
    pair = adapter.generate(20261025, {"mode": "dominant_assignment"}, 3, 4)["test"][3]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    info = family.analyze(pair["input"])
    assert len(info["blobs"]) >= 10
    assert sum(len(blob["cells"]) for blob in info["blobs"]) >= 50
    assert len(info["markers"]) == 4
    assert any(r in (0, 29) or c in (0, 29) for blob in info["blobs"] for r, c in blob["cells"])


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 3, True), (0, 3, 0), (0, 3, 5)],
)
def test_invalid_request_controls_reject(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"mode": "all_nearest"}, demos, queries)
