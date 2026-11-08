"""Focused regression coverage for the top-row color-legend generator."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d3c9fc4479d8"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("d3c9fc4479d8_generator_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _parse_mapping(grid: list[list[int]]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    c = 0
    while c + 1 < len(grid[0]):
        left, right = grid[0][c], grid[0][c + 1]
        if left != 0 and right != 0:
            mapping[left] = right
            c += 2
        else:
            c += 1
    return mapping


def _expected(grid: list[list[int]]) -> list[list[int]]:
    mapping = _parse_mapping(grid)
    return [[mapping.get(value, value) for value in row] for row in grid[1:]]


def _episode(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": _expected(grid)}


def test_rule_pin_and_all_canonical_pairs_are_owned_exact_and_input_pure():
    assert GEN.RULE_HASH == "08068e7e2317"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_axis_joint_boundary_is_constructive_and_observable(band):
    cases = itertools.product(
        (4, 10),
        (7, 14),
        (2, 3),
        (2, 3, 4),
        (0, 1),
        ("disjoint", "chain"),
        ("none", "target", "neutral"),
    )
    for index, values in enumerate(cases):
        requested = dict(zip(
            ("grid_h", "grid_w", "n_pairs", "source_uses", "legend_offset", "mapping_overlap", "control_kind"),
            values,
            strict=True,
        ))
        grid = GEN.generate(10_000 + index, index, difficulty=band, **requested)
        assert GEN.self_check(grid) == [], (band, requested)
        assert GEN.strict_canonical_like(grid) == [], (band, requested)
        assert GEN.observe_overrides(grid) == requested
        assert _expected(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 3},
        {"grid_h": 11},
        {"grid_h": True},
        {"grid_w": 6},
        {"grid_w": 15},
        {"grid_w": 7.0},
        {"n_pairs": 1},
        {"n_pairs": 4},
        {"source_uses": 1},
        {"source_uses": 5},
        {"legend_offset": 2},
        {"mapping_overlap": "cycle"},
        {"control_kind": "source"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        GEN.generate(1, 0, **overrides)


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(
        77,
        5,
        grid_h=6,
        grid_w=10,
        n_pairs=3,
        source_uses=3,
        legend_offset=1,
        mapping_overlap="chain",
        control_kind="neutral",
    )
    assert GEN.self_check(base) == []
    mapping = _parse_mapping(base)
    sources = list(mapping)

    cases: dict[str, object] = {}

    grid = copy.deepcopy(base)
    grid[0][-1] = 9 if grid[0][-1] != 9 else 8
    cases["isolated legend color"] = grid

    grid = copy.deepcopy(base)
    # Duplicate a source key without changing the row length.
    starts = [c for c in range(len(grid[0]) - 1) if grid[0][c] and grid[0][c + 1]]
    grid[0][starts[-1]] = grid[0][starts[0]]
    cases["duplicate source"] = grid

    grid = copy.deepcopy(base)
    first = next(c for c in range(len(grid[0]) - 1) if grid[0][c] and grid[0][c + 1])
    grid[0][first + 1] = grid[0][first]
    cases["identity mapping"] = grid

    grid = copy.deepcopy(base)
    missing = sources[0]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if value == missing:
                grid[r][c] = 0
    cases["source absent from body"] = grid

    grid = copy.deepcopy(base)
    moved = sources[0]
    points = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value == moved]
    for r, c in points:
        grid[r][c] = 0
    grid[1][0] = moved
    grid[-1][-1] = moved
    cases["disconnected source"] = grid

    grid = copy.deepcopy(base)
    used = {value for row in grid for value in row}
    extras = [color for color in range(1, 10) if color not in used]
    assert len(extras) >= 2
    zeros = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value == 0]
    grid[zeros[0][0]][zeros[0][1]] = extras[0]
    grid[zeros[1][0]][zeros[1][1]] = extras[1]
    cases["multiple controls"] = grid

    cases["empty"] = []
    cases["ragged"] = [[0, 1], [0]]
    cases["boolean cell"] = [[False] * 7 for _ in range(4)]

    for name, grid in cases.items():
        assert GEN.self_check(grid), name
        assert GEN.observe_overrides(grid) == {}, name


def test_each_band_hits_both_canonical_coarse_profiles_in_twenty_draws():
    wanted = {(4, 7, 5), (4, 8, 7)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        for index in range(20):
            grid = GEN.generate(1234, index, difficulty=band)
            seen.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert wanted <= seen, (band, seen)


def test_declared_shortcuts_fit_canonical_but_schedule_refutes_them():
    pairs = _pairs()
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    for band in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [GEN.generate(333, start + offset, difficulty=band) for offset in range(4)]
            official = [_expected(grid) for grid in grids]
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                assert sum(rival(grid) != answer for grid, answer in zip(grids, official)) >= 2, (
                    band,
                    start,
                    name,
                )


def test_every_cyclic_three_demo_window_and_query_rotation_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = [_episode(GEN.generate(8_000, start + offset, difficulty=band)) for offset in range(4)]
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                assert GEN.lesson_identifiable(demos, query) == [], (band, start, query_index)


def test_each_declared_witness_really_refutes_a_named_rival():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for index in range(32):
            grid = GEN.generate(9_000, index, difficulty=band)
            truth = _expected(grid)
            for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                hits[witness_name] += 1
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
                    for rival_name in GEN.WITNESS_RIVALS[witness_name]
                ), (band, index, witness_name)
    assert all(hits.values()), hits


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(42, 17, difficulty="hard")
    middle = GEN.generate(99, 3, difficulty="easy")
    second = GEN.generate(42, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert first != middle
    assert random.getstate() == state


def test_reusable_workspace_probe_exists_and_passes_all_schedule_starts():
    path = HOME / "workspace" / "lesson_probe.py"
    assert path.is_file(), "workspace/lesson_probe.py should be a reusable authoring probe"
    spec = importlib.util.spec_from_file_location("d3c9fc4479d8_lesson_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_probe(GEN, starts=range(8))
    assert report["status"] == "pass", report
    assert report["ambiguous_windows"] == []
    assert report["canonical_shortcut_failures"] == []


def test_reusable_workspace_probe_cli_runs_from_repository_root(tmp_path):
    path = HOME / "workspace" / "lesson_probe.py"
    out = tmp_path / "lesson-probe.json"
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            str(path),
            "--generator",
            str(HOME / "generator.py"),
            "--starts",
            "4",
            "--out",
            str(out),
        ],
        cwd=HOME.parents[1],
        env=clean_env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = __import__("json").loads(out.read_text())
    assert report["status"] == "pass"
    assert report["rotations_checked"] == 48
