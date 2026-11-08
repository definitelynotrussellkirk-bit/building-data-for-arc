"""Task-local regression checks. Run explicitly: the root suite omits these."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_generator_11ebef5b0986", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def canonical_pairs():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row["task_id"] == gen.TASK_ID:
            return [{key: [[int(v) for v in row] for row in pair[key]]
                     for key in ("input", "output")}
                    for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task absent")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_gray_five_and_canonical_dimensions_are_in_ordinary_support(band):
    grids = [gen.generate(17, i, difficulty=band) for i in range(90)]
    assert any(5 in g[0] for g in grids), "canonical palette color 5 is unreachable"
    assert any(len(g) == 11 for g in grids), "canonical height 11 is unreachable"
    assert any(len(g[0]) == 9 for g in grids), "canonical width 9 is unreachable"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", itertools.product([7, 16], [8, 16]))
def test_size_overrides_use_full_declared_domain(band, h, w):
    grid = gen.generate(0, 0, difficulty=band, grid_h=h, grid_w=w)
    assert (len(grid), len(grid[0])) == (h, w)
    assert gen.self_check(grid) == []


def test_unknown_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown"):
        gen.generate(0, 0, palete_kind="cool_palette")


@pytest.mark.parametrize("kind,allowed", [
    ("warm_palette", {2, 4, 6, 7}), ("cool_palette", {3, 5, 6, 8})])
def test_palette_kind_controls_the_actual_palette(kind, allowed):
    for i in range(30):
        assert set(gen.generate(13, i, palette_kind=kind)[0][1:4]) <= allowed


@pytest.mark.parametrize("value", [0, 1, 9, 10, -1, True, 2.5])
def test_validator_rejects_invalid_palette_cells(value):
    grid = gen.generate(0, 0)
    grid[0][1] = value
    assert gen.self_check(grid)


def test_validator_rejects_stray_body_color():
    grid = gen.generate(0, 0)
    grid[-1][-1] = 2
    assert gen.self_check(grid), "stray paint is outside the documented input grammar"


@pytest.mark.parametrize("grid", [None, [], [[]], [1, 2], ["012", "012"], [[0], [0, 0]]])
def test_validator_is_total_on_malformed_grids(grid):
    assert gen.self_check(grid)


def test_rule_hash_pin_is_current():
    assert getattr(gen, "RULE_HASH", None) == "37be31441b18"


def test_canonical_inputs_are_accepted_and_mirror_matches():
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_shortcuts_really_fit_all_five_canonical_pairs():
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(p["input"]) == p["output"] for p in canonical_pairs())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_demo_window_refutes_declared_shortcuts(band):
    for seed in range(8):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(14)]
        for start in range(11):
            demos = [{"input": g, "output": gen.rule_mirror(g)} for g in grids[start:start+3]]
            query = {"input": grids[start+3], "output": gen.rule_mirror(grids[start+3])}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                assert any(rival(p["input"]) != p["output"] for p in demos), (name, seed, start)


@pytest.mark.parametrize("mode", ["fit", "inset"])
def test_frame_override_is_real_for_every_size_boundary(mode):
    for h, w in itertools.product([7, 16], [8, 16]):
        for seed in range(8):
            grid = gen.generate(seed, 0, grid_h=h, grid_w=w, frame_mode=mode)
            assert gen.self_check(grid) == []
            cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
            bbox = min(r for r,c in cells), max(r for r,c in cells), min(c for r,c in cells), max(c for r,c in cells)
            if mode == "fit":
                assert bbox == (1, h - 2, 1, w - 2)
            else:
                assert gen.rule_mirror(grid) != gen.fixed_canvas_chamber(grid)


def test_no_mutation_and_deterministic_calls():
    for seed in range(8):
        a = gen.generate(seed, 4)
        saved = copy.deepcopy(a)
        assert a == gen.generate(seed, 4)
        if hasattr(gen, "rule_mirror"):
            gen.rule_mirror(a)
        assert a == saved


def test_selected_racket_target_is_exactly_canonical():
    path = REPO / "shared/data/base/solutions/banks/fd166f81148e/H141__11ebef5b0986.json"
    target = json.loads(path.read_text())["racket_target"]
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row["task_id"] == gen.TASK_ID:
            assert target["target_code"] == row["program_solution"]
            assert target["raw_code"] == row["program_solution"]
            return
    raise AssertionError("canonical task absent")


def test_difficulty_bands_do_not_repeat_the_same_anchor_scenes():
    grids = {json.dumps(gen.generate(seed, index, difficulty=band))
             for seed in range(10) for index in (0, 1)
             for band in ("easy", "medium", "hard")}
    assert len(grids) >= 54, f"only {len(grids)}/60 distinct cross-band scenes"
