from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "00ed2544a15e"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.00ed2544a15e.generator"
)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def _selected_rule_source() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return row["program_solution"]
    raise AssertionError("selected canonical rule source not found")


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_rule_hash_is_pinned_to_selected_canonical_source():
    expected = hashlib.sha256(
        " ".join(_selected_rule_source().split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "92ea0e00d9a5"


def test_canonical_pairs_are_owned_and_match_the_python_mirror():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_declared_shortcuts_really_fit_every_canonical_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "ignore_blockers",
        "simple_pairs_only",
    }
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS), name


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["h_chain", "v_chain", "cross"])
@pytest.mark.parametrize("grid_h,grid_w", [(8, 9), (12, 13)])
def test_exact_axis_boundaries_are_honored_in_every_band(
    difficulty, profile, grid_h, grid_w
):
    grid = GEN.generate(
        4101,
        23,
        difficulty=difficulty,
        profile=profile,
        grid_h=grid_h,
        grid_w=grid_w,
    )
    expected = {"grid_h": grid_h, "grid_w": grid_w, "profile": profile}
    assert GEN.observe_overrides(grid) == expected
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": expected}) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"imaginary_axis": 1},
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 8},
        {"grid_w": 14},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"profile": "diagonal"},
    ],
)
def test_invalid_or_unknown_overrides_reject_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_unknown_difficulty_rejects_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_schedule_profiles_are_observable_and_each_refutes_every_competitor():
    expected_profile_witness = {
        "h_chain": "horizontal_chain",
        "v_chain": "vertical_chain",
        "cross": "shared_endpoint_cross",
    }
    assert tuple(GEN.SCHEDULE_PROFILES) == ("h_chain", "v_chain", "cross")
    for sample_index, profile in enumerate(GEN.SCHEDULE_PROFILES):
        assert GEN.schedule_profile(99, sample_index, difficulty="easy") == profile
        grid = GEN.generate(99, sample_index, difficulty="easy", grid_h=8, grid_w=9)
        assert GEN.observe_overrides(grid)["profile"] == profile
        truth = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES[expected_profile_witness[profile]](grid)
        assert all(
            competitor(grid) != truth
            for competitor in GEN.LESSON_COMPETITORS.values()
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_cyclic_lesson_and_every_query_rotation_is_identifiable(difficulty):
    for start in range(12):
        demos, query = _lesson(1701, start, difficulty)
        assert GEN.lesson_identifiable(demos, query) == []
        all_pairs = demos + [query]
        for query_index, held_out in enumerate(all_pairs):
            rotated = [pair for index, pair in enumerate(all_pairs) if index != query_index]
            assert GEN.lesson_identifiable(rotated, held_out) == []


def test_generated_profiles_supply_exact_counterexamples_to_both_shortcuts():
    for sample_index, profile in enumerate(GEN.SCHEDULE_PROFILES):
        grid = GEN.generate(731, sample_index, profile=profile, grid_h=8, grid_w=9)
        truth = GEN.rule_mirror(grid)
        for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
            assert shortcut(grid) != truth, (profile, name)


def test_self_check_rejects_structural_and_palette_impostors():
    base = GEN.generate(31, 2, profile="cross", grid_h=8, grid_w=9)
    assert GEN.self_check(base) == []

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    boolean_cell = copy.deepcopy(base)
    boolean_cell[0][0] = True

    answer_leak = copy.deepcopy(base)
    answer_leak[0][0] = 8

    no_red = [[0 if value == 2 else value for value in row] for row in base]

    extra_role = copy.deepcopy(base)
    existing = {value for row in base for value in row}
    new_color = next(value for value in range(1, 10) if value not in existing and value != 8)
    extra_role[0][0] = new_color

    for mutation in (ragged, boolean_cell, answer_leak, no_red, extra_role):
        assert GEN.self_check(mutation), mutation


def test_determinism_fresh_returns_and_global_random_purity():
    random.seed(20261004)
    before = random.getstate()
    first = GEN.generate(54321, 17, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(54321, 17, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    assert before == middle == after



def _component_count(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    count = 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            count += 1
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def test_default_distribution_reaches_the_canonical_component_envelope():
    counts = [
        _component_count(GEN.generate(6100 + index, index, difficulty=difficulty))
        for difficulty in ("easy", "medium", "hard")
        for index in range(18)
    ]
    # Canonical median is five; the inherited strict detector allows +/-2.
    assert min(counts) <= 7
    assert max(counts) <= 9

def test_every_default_draw_meets_the_declared_teaching_contract():
    profile_hits = set()
    shapes = set()
    inputs = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(48):
            grid = GEN.generate(9000 + sample_index, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            profile_hits.add(observed["profile"])
            shapes.add((len(grid), len(grid[0])))
            inputs.add(tuple(tuple(row) for row in grid))
            truth = GEN.rule_mirror(grid)
            assert all(rival(grid) != truth for rival in GEN.LESSON_COMPETITORS.values())
    assert profile_hits == set(GEN.SCHEDULE_PROFILES)
    assert len(shapes) >= 8
    assert len(inputs) >= 130


def test_workspace_curriculum_probe_uses_live_contracts_and_exhausts_the_small_schedule():
    probe_path = Path(__file__).resolve().parents[1] / "workspace" / "curriculum_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(
        generator=GEN,
        canonical_root=ROOT,
        seed=24680,
        sampled_draws_per_band=9,
    )
    assert report["task_id"] == TASK_ID
    assert report["canonical_mirror_failures"] == []
    assert set(report["canonical_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert all(
        item["fits_all_canonical_pairs"]
        for item in report["canonical_shortcuts"].values()
    )
    assert set(report["lesson_competitors"]) == set(GEN.LESSON_COMPETITORS)
    assert report["cyclic_start_count_per_band"] == len(GEN.SCHEDULE_PROFILES)
    assert report["failed_windows"] == []
    assert report["surviving_competitor_windows"] == []
    assert report["rotation_failures"] == []
    assert report["exact_axis_case_count"] == 4 * 5 * 5 * 3
    assert report["exact_axis_failures"] == []
    assert report["sampled_component_counts"]["minimum"] <= 7
    assert report["sampled_component_counts"]["maximum"] <= 9
    assert all(
        witness["rival_differs"]
        for witness in report["shortcut_witnesses"].values()
    )
