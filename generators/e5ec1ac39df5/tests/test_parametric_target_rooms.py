"""Focused regressions for the repaired room-boundary generator and family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK = "e5ec1ac39df5"
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


def _nonwall_components(grid: list[list[int]]):
    walls = {1, 7, 9}
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] in walls or (sr, sc) in seen:
                continue
            todo = [(sr, sc)]
            seen.add((sr, sc))
            cells = set()
            while todo:
                r, c = todo.pop()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] not in walls
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return result


def _has_off_center_seed(grid: list[list[int]]) -> bool:
    for cells in _nonwall_components(grid):
        seeds = [p for p in cells if grid[p[0]][p[1]] == 2]
        if not seeds:
            continue
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        center = (r0 + (r1 - r0 + 1) // 2, c0 + (c1 - c0 + 1) // 2)
        if seeds != [center]:
            return True
    return False


def test_parametric_artifacts_exist():
    assert PROTOTYPE.is_file()
    assert ADAPTER.is_file()
    assert CONTRACT.is_file()
    assert (HOME / "canonical.rkt").is_file()
    assert (HOME / "neighbors.rkt").is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_e5ec1ac39df5", PROTOTYPE)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_e5ec1ac39df5_adapter", ADAPTER)


def test_base_accepts_all_canonical_geometries_and_consumes_dimensions():
    generator, _path, _digest = load_selected_generator(TASK, root=ROOT)
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert generator.self_check(pair["input"]) == []

    grid = generator.generate(
        13,
        0,
        difficulty="hard",
        grid_h=30,
        grid_w=30,
        rooms_r=4,
        rooms_c=4,
        seed_count=3,
        off_center_seeds=True,
        door_count=12,
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value == 7 for row in grid for value in row) == 12
    assert _has_off_center_seed(grid)
    assert generator.self_check(grid, difficulty="hard") == []

    compact = generator.generate(
        2,
        2,
        grid_h=13,
        grid_w=13,
        rooms_r=2,
        rooms_c=2,
        seed_count=1,
        off_center_seeds=False,
        door_count=0,
    )
    assert (len(compact), len(compact[0])) == (13, 13)
    assert compact != generator.generate(2, 2)
    assert generator.self_check(compact) == []

    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, rooms_r=4, grid_h=7)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, off_center_seeds=1)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, unknown_control=True)


def test_programs_preserve_exact_default_and_define_graph_neighbor_variant(prototype):
    from arcpuzzles import Catalog

    catalog_program = Catalog(ROOT).get(TASK)["variants"][0]["program_solution"]
    assert prototype.program_for("seeded") == catalog_program
    assert hashlib.sha256((HOME / "canonical.rkt").read_bytes()).hexdigest() == hashlib.sha256(
        catalog_program.encode()
    ).hexdigest()
    alternate = prototype.program_for("neighbors")
    assert alternate != catalog_program
    assert "neighbor-ids" in alternate
    assert "hash-ref adj" in alternate
    for bad in ("neighbor", "", 0, None, True):
        with pytest.raises(ValueError, match="target_rooms"):
            prototype.program_for(bad)


def test_real_racket_and_mirror_distinguish_seeded_from_neighbor_rooms(prototype):
    grid = prototype.build_input(17, 1, 7)
    features = prototype.scene_features(grid)
    assert features["door_count"] >= 2
    assert features["room_count"] >= 4
    assert features["off_center_seed"] is True
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        expected = prototype.python_mirror(grid, target_rooms=mode)
        actual = _apply(prototype.program_for(mode), grid)
        assert actual == expected
        outputs[mode] = actual
    assert outputs["seeded"] != outputs["neighbors"]
    assert grid == before


def test_episode_contract_crosses_shortcuts_and_keeps_four_novel_queries(prototype, adapter):
    for demos in (2, 3, 6):
        seeded = adapter.generate(29, {"target_rooms": "seeded"}, demos=demos, queries=4)
        neighbors = adapter.generate(29, {"target_rooms": "neighbors"}, demos=demos, queries=4)
        assert len(seeded["train"]) == demos
        assert len(seeded["test"]) == 4
        assert [p["input"] for p in seeded["train"] + seeded["test"]] == [
            p["input"] for p in neighbors["train"] + neighbors["test"]
        ]
        assert len(
            {
                json.dumps(pair["input"], separators=(",", ":"))
                for pair in seeded["train"] + seeded["test"]
            }
        ) == demos + 4
        assert all(
            left["output"] != right["output"]
            for left, right in zip(seeded["train"], neighbors["train"])
        )
        features = [prototype.scene_features(pair["input"]) for pair in seeded["train"]]
        assert {row["off_center_seed"] for row in features} == {False, True}
        assert len({tuple(row["room_heights"]) for row in features}) >= 2
        assert all(
            0 < row["seeded_graph_neighbor_count"] < row["seeded_geometric_neighbor_count"]
            for row in features
        ), "visible demos must require color-7 graph edges, not plain room adjacency"
        for mode, episode in (("seeded", seeded), ("neighbors", neighbors)):
            assert episode["program_solution"] == prototype.program_for(mode)
            assert all(
                pair["output"] == prototype.python_mirror(pair["input"], target_rooms=mode)
                for pair in episode["train"] + episode["test"]
            )

    stress = seeded["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    stress_features = prototype.scene_features(stress)
    assert stress_features["room_count"] == 16
    assert stress_features["door_count"] >= 20
    assert sum(value != 0 for row in stress for value in row) >= 200


def test_adapter_and_contract_are_strict(adapter):
    assert json.loads(CONTRACT.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/e5ec1ac39df5/workspace/parametric/adapter.py",
        "parameters": {"target_rooms": ["seeded", "neighbors"]},
        "default": {"target_rooms": "seeded"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    for settings in ({}, {"target_rooms": "bad"}, {"target_rooms": "seeded", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for demos in (1, 7, True):
        with pytest.raises((TypeError, ValueError), match="demos"):
            adapter.generate(0, {"target_rooms": "seeded"}, demos=demos, queries=4)
    for queries in (1, 3, 5, True):
        with pytest.raises((TypeError, ValueError), match="queries"):
            adapter.generate(0, {"target_rooms": "seeded"}, demos=3, queries=queries)


def test_base_sampler_is_reliable_across_bounded_seed_sweep():
    generator, _path, _digest = load_selected_generator(TASK, root=ROOT)
    for difficulty in (None, "medium"):
        for seed in range(50):
            grid = generator.generate(seed, seed, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
