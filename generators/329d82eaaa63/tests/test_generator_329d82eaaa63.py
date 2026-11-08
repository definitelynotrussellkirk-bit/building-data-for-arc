"""Source-bound regressions for ARC generator 329d82eaaa63."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "329d82eaaa63"
RULE_HASH = "c3b26f3f0fc8"
ROOT = find_root(__file__)
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", GEN_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row missing for {TASK_ID}")


def _authority_path() -> Path:
    relative = Path("data/base/solutions/training/3ac3eb23__329d82eaaa63.json")
    for prefix in (ROOT / "shared", ROOT):
        candidate = prefix / relative
        if candidate.is_file():
            return candidate
    raise AssertionError("task-local base authority missing")


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _lesson(grids, query_index):
    pairs = [{"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)} for grid in grids]
    return [pair for index, pair in enumerate(pairs) if index != query_index], pairs[query_index]


def test_rule_hash_and_selected_task_authority_are_exactly_canonical():
    canonical = _canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert digest == GEN.RULE_HASH == RULE_HASH

    target = json.loads(_authority_path().read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == canonical
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"
    assert target["raw_code"] != target["target_code"]


def test_all_canonical_inputs_are_accepted_and_python_mirror_matches_exact_outputs():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == before


def test_four_profile_schedule_is_lawful_complete_and_rotation_identifiable():
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_single",
        "canonical_multi",
        "broad_single",
        "broad_multi",
    )
    for band in (None, "easy", "medium", "hard"):
        grids = [GEN.generate(923, index, difficulty=band) for index in range(4)]
        assert [GEN.schedule_profile(923, index, band) for index in range(4)] == list(
            GEN.SCHEDULE_PROFILES
        )
        assert all(GEN.self_check(grid, difficulty=band) == [] for grid in grids)
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)

        fired = {
            name
            for name, predicate in GEN.SEMANTIC_WITNESSES.items()
            if any(predicate(grid) for grid in grids)
        }
        assert fired == set(GEN.SEMANTIC_WITNESSES)

        for query_index in range(4):
            demos, query = _lesson(grids, query_index)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not (
                    all(rival(demo["input"]) == demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ), (band, query_index, name)


def test_each_firing_witness_has_a_named_rival_disagreement():
    grids = [GEN.generate(101, index) for index in range(4)]
    for name, predicate in GEN.SEMANTIC_WITNESSES.items():
        matching = [grid for grid in grids if predicate(grid)]
        assert matching, name
        named = GEN.WITNESS_RIVALS[name]
        assert named, name
        assert any(
            GEN.SEMANTIC_RIVALS[rival](grid) != GEN.rule_mirror(grid)
            for grid in matching
            for rival in named
        ), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 3),
        ("grid_h", 18),
        ("grid_w", 4),
        ("grid_w", 24),
        ("n_seeds", 1),
        ("n_seeds", 8),
    ],
)
def test_declared_axis_boundaries_are_exact_observable_and_lawful(axis, value, band):
    grid = GEN.generate(271, 13, difficulty=band, **{axis: value})
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 3, "grid_w": 4, "n_seeds": 1},
        {"grid_h": 18, "grid_w": 24, "n_seeds": 8},
        {"grid_h": 6, "grid_w": 10, "n_seeds": 2},
    ],
)
def test_feasible_joint_override_boundaries_are_exact(requested, band):
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == requested


def test_impossible_width_seed_pair_is_rejected_with_structured_axis_tag():
    with pytest.raises(ValueError) as caught:
        GEN.generate(1, 1, grid_w=4, n_seeds=2)
    assert set(caught.value.incompatible_axes) == {"grid_w", "n_seeds"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 3},
        {"grid_h": True},
        {"grid_h": 3.0},
        {"grid_h": "3"},
        {"grid_w": 3},
        {"grid_w": 25},
        {"n_seeds": 0},
        {"n_seeds": 9},
    ],
)
def test_unknown_or_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random():
    random.seed(99213)
    state = random.getstate()
    first = GEN.generate(44, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(44, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9
    replay = GEN.generate(44, 7, difficulty="hard")
    assert replay == second


def test_self_check_rejects_each_ambiguous_or_malformed_seed_scene():
    lawful = GEN.generate(73, 1, grid_h=6, grid_w=10, n_seeds=2)
    assert GEN.self_check(lawful) == []

    mutations = []
    no_seeds = copy.deepcopy(lawful)
    no_seeds[0] = [0] * len(no_seeds[0])
    mutations.append(no_seeds)

    body = copy.deepcopy(lawful)
    body[1][1] = 4
    mutations.append(body)

    edge = copy.deepcopy(lawful)
    old_col = next(c for c, value in enumerate(edge[0]) if value)
    edge[0][0], edge[0][old_col] = edge[0][old_col], 0
    mutations.append(edge)

    duplicate = copy.deepcopy(lawful)
    cols = [c for c, value in enumerate(duplicate[0]) if value]
    duplicate[0][cols[1]] = duplicate[0][cols[0]]
    mutations.append(duplicate)

    close = copy.deepcopy(lawful)
    colors = [lawful[0][c] for c in cols]
    close[0] = [0] * len(close[0])
    close[0][1], close[0][3] = colors
    mutations.append(close)

    invalid_cell = copy.deepcopy(lawful)
    invalid_cell[0][cols[0]] = True
    mutations.append(invalid_cell)

    assert all(GEN.self_check(grid) for grid in mutations)


def test_valid_column_sets_have_exact_count_interior_bounds_and_three_cell_gap():
    for width in range(4, 25):
        for count in range(1, 9):
            options = GEN._valid_column_sets(width, count)
            for columns in options:
                assert len(columns) == count
                assert columns == tuple(sorted(columns))
                assert all(1 <= column <= width - 2 for column in columns)
                assert all(right - left >= 3 for left, right in zip(columns, columns[1:]))
            assert bool(options) == (count <= GEN._max_seeds(width))


def test_generated_distribution_has_distinct_inputs_and_outputs_without_aliases():
    inputs = set()
    outputs = set()
    for index in range(80):
        grid = GEN.generate(1000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert GEN.self_check(grid) == []
        inputs.add(_frozen(grid))
        outputs.add(_frozen(GEN.rule_mirror(grid)))
    assert len(inputs) >= 70
    assert len(outputs) >= 70


def test_reviewer_probe_emits_clean_portable_report(tmp_path):
    import os
    import subprocess

    probe = ROOT / "generators" / TASK_ID / "workspace" / "probe_generator.py"
    report = tmp_path / "probe.json"
    env = os.environ.copy()
    runtime = ROOT / "shared" / "runtime"
    env["PYTHONPATH"] = str(runtime) + os.pathsep + str(ROOT / "src") + os.pathsep + str(ROOT)
    run = subprocess.run(
        [
            sys.executable,
            str(probe),
            "--seed",
            "41",
            "--per-profile",
            "1",
            "--out",
            str(report),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["status"] == "clean"
    assert payload["canonical"]["matched"] == 3
    assert payload["rotations"]["checked"] == 16
    assert payload["rotations"]["ambiguous"] == 0
    assert payload["overrides"]["structured_incompatibility"] is True
