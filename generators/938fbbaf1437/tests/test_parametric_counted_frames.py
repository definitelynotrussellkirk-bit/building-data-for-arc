"""Focused tests for the repaired nesting generator and counted-frame family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
TASK = "938fbbaf1437"
HOME = ROOT / f"generators/{TASK}/workspace/parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
CONTRACT = HOME / "promotion.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _apply(program: str, grid: list[list[int]]) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    with RacketBridge() as bridge:
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_parametric_artifacts_exist():
    assert PROTOTYPE.is_file()
    assert ADAPTER.is_file()
    assert CONTRACT.is_file()
    assert (HOME / "canonical.rkt").is_file()
    assert (HOME / "square_only.rkt").is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_938fbbaf1437", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_938fbbaf1437_adapter", ADAPTER)


def test_base_generator_supports_deep_inset_and_exact_dimensions():
    generator, _path, _digest = load_selected_generator(TASK, root=ROOT)
    grid = generator.generate(
        7,
        0,
        difficulty="medium",
        grid_h=30,
        grid_w=30,
        n_frames=4,
        outer_inset=2,
        singleton_count=2,
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert generator.self_check(grid, difficulty="medium") == []

    small = generator.generate(
        7, 1, grid_h=9, grid_w=9, n_frames=2, outer_inset=0, singleton_count=1
    )
    assert (len(small), len(small[0])) == (9, 9)
    assert generator.self_check(small) == []

    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, 0, n_frames=5)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(7, 0, unknown_control=True)


def test_programs_preserve_exact_canonical_default_and_square_filter(prototype):
    from arcpuzzles import Catalog

    catalog_program = Catalog(ROOT).get(TASK)["variants"][0]["program_solution"]
    assert prototype.program_for("all") == catalog_program
    assert hashlib.sha256((HOME / "canonical.rkt").read_bytes()).hexdigest() == hashlib.sha256(
        catalog_program.encode()
    ).hexdigest()
    alternate = prototype.program_for("squares")
    assert alternate != catalog_program
    assert "square-frame?" in alternate
    for bad in ("square", "", 0, None, True):
        with pytest.raises(ValueError, match="counted_frames"):
            prototype.program_for(bad)


def test_real_racket_and_mirror_distinguish_counted_frame_modes(prototype):
    grid = prototype.build_input(17, 0, 7)
    assert prototype.frame_shape_kinds(grid) == {"square", "rectangle"}
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        expected = prototype.python_mirror(grid, counted_frames=mode)
        actual = _apply(prototype.program_for(mode), grid)
        assert actual == expected
        outputs[mode] = actual
    assert outputs["all"] != outputs["squares"]
    assert grid == before


def test_episode_contract_identifies_mode_and_keeps_four_novel_queries(prototype, adapter):
    for demos in (2, 3, 6):
        all_episode = adapter.generate(29, {"counted_frames": "all"}, demos=demos, queries=4)
        square_episode = adapter.generate(
            29, {"counted_frames": "squares"}, demos=demos, queries=4
        )
        assert len(all_episode["train"]) == demos
        assert len(all_episode["test"]) == 4
        assert [p["input"] for p in all_episode["train"] + all_episode["test"]] == [
            p["input"] for p in square_episode["train"] + square_episode["test"]
        ]
        assert len(
            {json.dumps(p["input"], separators=(",", ":")) for p in all_episode["train"] + all_episode["test"]}
        ) == demos + 4
        assert all(
            left["output"] != right["output"]
            for left, right in zip(all_episode["train"], square_episode["train"])
        )
        square_depths = []
        for pair in all_episode["train"]:
            proper = [box for box in prototype.frames(pair["input"]) if box[0] != box[1] or box[2] != box[3]]
            proper.sort(key=lambda box: (box[1] - box[0] + 1) * (box[3] - box[2] + 1), reverse=True)
            depths = tuple(
                index
                for index, (r0, r1, c0, c1) in enumerate(proper)
                if r1 - r0 == c1 - c0
            )
            assert depths and len(depths) < len(proper)
            square_depths.append(depths)
        assert len(set(square_depths)) >= 2, "visible demos must defeat a fixed nesting-depth shortcut"
        for mode, episode in (("all", all_episode), ("squares", square_episode)):
            assert episode["program_solution"] == prototype.program_for(mode)
            assert all(
                pair["output"] == prototype.python_mirror(pair["input"], counted_frames=mode)
                for pair in episode["train"] + episode["test"]
            )

    stress = all_episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(occupied) >= 100
    assert min(r for r, _ in occupied) <= 2 and max(r for r, _ in occupied) >= 27
    assert min(c for _, c in occupied) <= 2 and max(c for _, c in occupied) >= 27


def test_adapter_and_contract_are_strict(prototype, adapter):
    assert json.loads(CONTRACT.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/938fbbaf1437/workspace/parametric/adapter.py",
        "parameters": {"counted_frames": ["all", "squares"]},
        "default": {"counted_frames": "all"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    for settings in ({}, {"counted_frames": "bad"}, {"counted_frames": "all", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for demos in (1, 7, True):
        with pytest.raises((TypeError, ValueError), match="demos"):
            adapter.generate(0, {"counted_frames": "all"}, demos=demos, queries=4)
    for queries in (1, 3, 5, True):
        with pytest.raises((TypeError, ValueError), match="queries"):
            adapter.generate(0, {"counted_frames": "all"}, demos=3, queries=queries)


def test_base_sampler_is_reliable_across_bounded_seed_sweep():
    generator, _path, _digest = load_selected_generator(TASK, root=ROOT)
    for difficulty in (None, "medium"):
        for seed in range(50):
            grid = generator.generate(seed, seed, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
