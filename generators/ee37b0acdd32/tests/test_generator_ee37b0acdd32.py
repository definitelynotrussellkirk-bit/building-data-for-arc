from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK = "ee37b0acdd32"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_module():
    name = f"candidate_{TASK}"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, TASK_HOME / "generator.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_module()


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for raw in path.read_text().splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return list(row["train"]) + list(test)
    raise AssertionError("canonical task row missing")


def palette_size(grid):
    return len({value for row in grid for value in row})


def test_metadata_pins_rule_and_exposes_only_observable_controls():
    assert GEN.RULE_HASH == "5db437049d2b"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "path_len", "branch_count"}
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == ()
    assert GEN.EXAMPLES_NEEDED == 3


def test_every_canonical_input_is_accepted_and_exactly_solved():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_default_profiles_repeat_and_hit_all_three_canonical_signatures():
    expected = {
        "straight": (8, 10, 6),
        "elbow": (10, 11, 7),
        "zigzag": (10, 13, 8),
    }
    for band in ("easy", "medium", "hard"):
        realized = []
        for sample_index in range(9):
            grid = GEN.generate(10_000 + sample_index, sample_index, difficulty=band)
            profile = GEN.schedule_profile(10_000 + sample_index, sample_index, band)
            realized.append(profile)
            assert GEN.self_check(grid, difficulty=band) == []
            assert (len(grid), len(grid[0]), palette_size(grid)) == expected[profile]
        for start in range(7):
            assert set(realized[start:start + 3]) == set(expected)


def test_exact_axis_overrides_are_recoverable_at_domain_boundaries():
    for band in ("easy", "medium", "hard"):
        for h in (8, 14):
            for w in (10, 16):
                for path_len in (4, 5, 6):
                    for branch_count in (1, 2):
                        requested = {
                            "grid_h": h,
                            "grid_w": w,
                            "path_len": path_len,
                            "branch_count": branch_count,
                        }
                        grid = GEN.generate(
                            20_000 + h * 100 + w * 10 + path_len,
                            path_len + branch_count,
                            difficulty=band,
                            **requested,
                        )
                        assert GEN.self_check(
                            grid, difficulty=band, meta={"overrides": requested}
                        ) == []
                        assert GEN.observe_overrides(grid) == requested


def test_generated_contact_graph_is_a_unique_blue_to_red_tree_with_real_branches():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(90):
            grid = GEN.generate(30_000 + 1_000 * band_index + sample_index, sample_index, difficulty=band)
            info = GEN._analyze(grid)
            assert info["errors"] == []
            assert info["graph_is_tree"] is True
            assert info["shortest_path_count"] == 1
            assert 4 <= info["path_len"] <= 6
            assert 1 <= info["branch_count"] <= 2
            assert all(
                info["degrees"][index] == 1
                for index in info["off_path_indices"]
            )



def test_generated_inputs_reserve_output_color_eight_for_the_transformation():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(40):
            grid = GEN.generate(35_000 + sample_index, sample_index, difficulty=band)
            assert 8 not in {value for row in grid for value in row}
            assert 8 in {value for row in GEN.rule_mirror(grid) for value in row}

def test_schedule_contains_executable_witnesses_for_each_declared_rival():
    grids = [GEN.generate(40_000, index, difficulty="medium") for index in range(3)]
    truth = {id(grid): GEN.rule_mirror(grid) for grid in grids}
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness = GEN.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        assert any(
            GEN.SEMANTIC_RIVALS[rival](grid) != truth[id(grid)]
            for grid in firing
            for rival in rival_names
        ), witness_name


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs():
            assert shortcut(pair["input"]) == pair["output"], name


def test_each_three_demo_window_identifies_the_next_query_against_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            episode = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(50_000 + start, sample_index, difficulty=band)
                episode.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(episode[:-1], episode[-1]) == []


def test_self_check_fails_closed_on_disconnected_and_ambiguous_impostors():
    disconnected = [[0] * 10 for _ in range(8)]
    disconnected[1][1] = 1
    disconnected[6][8] = 2
    assert GEN.self_check(disconnected)

    base = GEN.generate(61, 1, difficulty="medium")
    info = GEN._analyze(base)
    assert info["off_path_indices"]
    # Repaint one off-path leaf with its parent color: the objects merge and the
    # declared branch control no longer describes the scene.
    mutated = copy.deepcopy(base)
    for branch in info["off_path_indices"]:
        parent = next(iter(info["adjacency"][branch]))
        parent_color = info["colors"][parent]
        for r, c in info["components"][branch]:
            mutated[r][c] = parent_color
    assert GEN.self_check(mutated)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 7},
        {"grid_w": 17},
        {"path_len": 3},
        {"branch_count": 0},
        {"grid_h": True},
        {"path_len": 4.0},
    ],
)
def test_invalid_overrides_reject_instead_of_silently_coercing(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_deterministic_fresh_returns_without_global_rng_side_effects():
    random.seed(991)
    state = random.getstate()
    first = GEN.generate(71, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(71, 5, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(71, 5, difficulty="hard") == second
