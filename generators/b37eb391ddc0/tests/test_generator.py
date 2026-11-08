from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "b37eb391ddc0"
EXPECTED_RULE_HASH = "24318a9ceacd"
ROOT = find_root(__file__)


def _load_generator():
    """Load from the installed portable package, with a source-tree fallback."""
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location("reviewed_generator", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = str(row["program_solution"])
                return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    raise AssertionError(f"canonical rule missing for {TASK_ID}")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _palette_size(grid):
    return len({value for row in grid for value in row})


def _foreground_object_count(grid):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for cell in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    stack.append(cell)
    return count


def test_metadata_rule_pin_and_exact_public_axis_contract():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == _canonical_rule_hash() == EXPECTED_RULE_HASH
    assert set(GEN.AXES) == {"scene_profile"}
    assert tuple(GEN.HELPFUL_TEXTURES) == ()
    assert tuple(GEN.DEGENERATE_TEXTURES) == ()
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.EXAMPLES_NEEDED == 2


def test_canonical_inputs_are_owned_and_python_mirror_matches_every_label():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_authority_level_counterexample_overwrites_an_occupied_companion():
    grid = [[2, 3], [0, 2]]
    expected = [[2, 2], [2, 2]]
    before = copy.deepcopy(grid)
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert GEN._rival_isolated_pairs_only(grid) != expected
    assert GEN._rival_preserve_occupied(grid) != expected
    assert grid == before


def test_each_exact_profile_is_observable_rich_and_override_honored():
    expected_signatures = {
        "rich_7x8_p3": (7, 8, 3),
        "rich_8x8_p3": (8, 8, 3),
        "rich_8x9_p4": (8, 9, 4),
    }
    assert set(GEN.SCENE_PROFILES) == set(expected_signatures)
    assert set(GEN.SCHEDULE_PROFILES) == set(expected_signatures)

    for profile, signature in expected_signatures.items():
        for seed in (1, 19, 901):
            grid = GEN.generate(seed, 7, difficulty="medium", scene_profile=profile)
            assert (len(grid), len(grid[0]), _palette_size(grid)) == signature
            assert GEN.self_check(grid) == []
            assert GEN.teaching_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}
            assert GEN._has_occupied_companion(grid)
            assert GEN._has_multi_pair_color(grid)
            assert GEN._has_nonmatching_diagonal(grid)
            assert GEN._has_both_orientations(grid)
            assert _foreground_object_count(grid) == (6 if profile == "rich_8x9_p4" else 4)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_schedule_is_deterministic_complete_and_matches_generation(difficulty):
    observed = []
    for sample_index in range(9):
        profile = GEN.schedule_profile(123, sample_index, difficulty=difficulty)
        grid = GEN.generate(123, sample_index, difficulty=difficulty)
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert grid == GEN.generate(123, sample_index, difficulty=difficulty)
        observed.append(profile)
    assert set(observed) == set(GEN.SCENE_PROFILES)


def test_invalid_calls_fail_loudly_instead_of_swallowing_typos():
    invalid = (
        {"difficulty": "expert"},
        {"unknown_axis": 1},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 7},
    )
    for kwargs in invalid:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **kwargs)


def test_all_declared_shortcuts_fit_canonical_but_generated_inputs_refute_them():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "isolated_pairs_only",
        "preserve_occupied",
        "first_pair_per_color",
        "exactly_two_occurrences",
        "any_nonzero_diagonal",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    for profile in GEN.SCENE_PROFILES:
        for seed in range(8):
            grid = GEN.generate(seed + 700, seed, scene_profile=profile)
            expected = GEN.rule_mirror(grid)
            for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                assert rival(grid) != expected, (profile, seed, name)


def test_every_two_demo_window_and_every_query_rotation_refutes_all_competitors():
    assert GEN.EXAMPLES_NEEDED == 2
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(5):
            for start in range(6):
                pairs = [
                    _pair(GEN.generate(10_000 + seed, start + offset, difficulty=difficulty))
                    for offset in range(GEN.EXAMPLES_NEEDED + 1)
                ]
                for query_index in range(len(pairs)):
                    query = pairs[query_index]
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    assert GEN.lesson_identifiable(demos, query) == []
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        assert any(
                            rival(demo["input"]) != demo["output"] for demo in demos
                        ), (difficulty, seed, start, query_index, name)


def test_self_check_rejects_malformed_and_no_op_inputs():
    bad = (
        [],
        [[]],
        [[0, 0], [0]],
        [[0, True], [0, 0]],
        [[0, 10], [0, 0]],
        [[0, 0], [0, 0]],
        [[4, 4], [4, 4]],
    )
    for grid in bad:
        assert GEN.self_check(grid)


def test_real_racket_authority_matches_python_mirror_on_canonical_and_rich_inputs():
    from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        grids = [
            pair["input"]
            for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        ]
        grids.append([[2, 3], [0, 2]])
        grids.extend(
            GEN.generate(50_000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
            for index in range(18)
        )
        for grid in grids:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before
    finally:
        shutdown = getattr(bridge, "shutdown", None)
        if callable(shutdown):
            shutdown()
        else:
            bridge.close()
