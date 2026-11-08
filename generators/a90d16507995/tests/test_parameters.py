"""Focused contracts for the native crop-and-stamp parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK_ID = "a90d16507995"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAM = HOME / "workspace" / "parametric"
MODES = ("stamp_only", "stamp_majority_frame")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("stamp_adapter_tests", PARAM / "adapter.py")


def _family():
    return _load("stamp_family_tests", PARAM / "family.py")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_generator_honors_exact_controls_and_aliases():
    gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    grid = gen.generate(
        0,
        0,
        difficulty="easy",
        grid_h=14,
        grid_w=14,
        blob_size=6,
        palette_size=3,
        n_distinct_colors=3,
        palette_kind="cool",
        position_bias="blob_upper_marker_lower",
        density="sparse",
    )
    assert (len(grid), len(grid[0])) == (14, 14)
    cells = [v for row in grid for v in row if v not in (0, 9)]
    assert len(cells) == 6
    assert len(set(cells)) == 3
    assert gen.self_check(grid) == []
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, palette_size=2, n_distinct_colors=3)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, typo_axis=1)


def test_default_program_is_byte_exact_selected_authority():
    adapter = _adapter()
    record = Catalog(ROOT).get(TASK_ID)
    programs = {v["program_solution"] for v in record["variants"]}
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert (PARAM / "canonical.rkt").read_text() == canonical
    assert adapter.program({"mode": "stamp_only"}) == canonical
    assert adapter.program({"mode": "stamp_majority_frame"}) != canonical


def test_contract_is_finite_and_strict():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": list(MODES)}
    assert contract["default"] == {"mode": "stamp_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    adapter = _adapter()
    for bad in [None, {}, [], {"mode": True}, {"mode": "bad"}, {"mode": "stamp_only", "x": 1}]:
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


def test_majority_is_input_dependent_and_wrong_intermediate_changes_frame():
    family = _family()
    grid = family.scene(0, "train", 0)
    info = family.analyze(grid)
    assert info["majority_color"] != info["crop"][0][0]
    intended = family.solve(grid, "stamp_majority_frame")
    wrong = family.solve_wrong_frame_color(grid)
    assert intended != wrong


def test_fourth_query_is_substantive_30x30_stress():
    adapter = _adapter()
    family = _family()
    pair = adapter.generate(20261025, {"mode": "stamp_majority_frame"}, 3, 4)["test"][3]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    info = family.analyze(pair["input"])
    assert len(info["source_cells"]) >= 80
    assert info["crop_height"] >= 10 and info["crop_width"] >= 10
    assert sum(v != 0 for row in pair["output"] for v in row) >= 120


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 3, True), (0, 3, 0), (0, 3, 5)],
)
def test_invalid_request_controls_reject(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"mode": "stamp_only"}, demos, queries)
