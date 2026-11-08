"""Focused regression and teaching-contract tests for 5c0bcc9d1b8b."""
from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError:
    sys.path.insert(0, str(HOME.parents[1] / "shared" / "runtime"))
    from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
TASK_ID = "5c0bcc9d1b8b"
CANONICAL_COUNT_BY_SIZE = {9: 5, 11: 9, 13: 13, 19: 11}


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_under_test", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _divider_rows(grid):
    width = len(grid[0])
    return [
        row
        for row in range(len(grid))
        if all(grid[row][col] in (0, 5) for col in range(width))
        or sum(grid[row][col] == 0 for col in range(width)) > width // 2
    ]


def _divider_cols(grid):
    height = len(grid)
    return [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] in (0, 5) for row in range(height))
        or sum(grid[row][col] == 0 for row in range(height)) > height // 2
    ]


def _profile_facts(grid):
    n = len(grid)
    mid = n // 2
    rows = _divider_rows(grid)
    cols = _divider_cols(grid)
    track = "vertical" if len(cols) == 2 else "horizontal"
    walls = cols if track == "vertical" else rows
    return {
        "n": n,
        "track": track,
        "wall_offset": walls[1] - mid,
        "gray_count": sum(value == 5 for row in grid for value in row),
        "divider_rows": rows,
        "divider_cols": cols,
    }


def test_contract_metadata_is_pinned_and_literal():
    assert gen.RULE_HASH == "326f0e0036c3"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {"scene_profile"}
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 16 == len(gen.SCENE_PROFILES)

    tree = ast.parse(GEN_PATH.read_text())
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "RULE_HASH" for target in node.targets)
        for node in tree.body
    )
    axes_assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert ast.literal_eval(axes_assignment.value) == gen.AXES


def test_scene_profile_axis_is_finite_exact_and_boundary_probeable():
    checker_path = ROOT / "shared" / "tools" / "check_generator_override_contract.py"
    checker_spec = importlib.util.spec_from_file_location("override_contract_checker", checker_path)
    checker = importlib.util.module_from_spec(checker_spec)
    assert checker_spec.loader is not None
    checker_spec.loader.exec_module(checker)

    domains = checker.axis_domain_report(gen.AXES)
    assert [(domain.name, domain.status) for domain in domains] == [
        ("scene_profile", "probeable")
    ]
    assert domains[0].values == list(gen.SCENE_PROFILES)

    counts_by_size = {size: set() for size in gen.WALL_OFFSET_BY_SIZE}
    tracks_by_size = {size: set() for size in gen.WALL_OFFSET_BY_SIZE}
    for profile in gen.SCENE_PROFILES:
        size, track, count = gen._parse_profile(profile)
        counts_by_size[size].add(count)
        tracks_by_size[size].add(track)
    assert all(len(counts) == 2 for counts in counts_by_size.values())
    assert all(tracks == {"vertical", "horizontal"} for tracks in tracks_by_size.values())


def test_declared_output_codomain_is_exactly_exhausted_by_profiles():
    outputs = {
        tuple(map(tuple, gen.rule_mirror(gen.generate(4040, index, scene_profile=profile))))
        for index, profile in enumerate(gen.SCENE_PROFILES)
    }
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
def test_canonical_inputs_are_lawful_and_python_mirror_matches_labels(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_profile_override_round_trips_exactly_in_every_band(band):
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(20261011 + index, index, difficulty=band, scene_profile=profile)
        assert gen.self_check(grid) == [], (band, profile)
        assert gen.strict_canonical_like(grid) == [], (band, profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        facts = _profile_facts(grid)
        assert facts["divider_rows"] == [facts["n"] // 2] if facts["track"] == "vertical" else [facts["n"] // 2 - facts["wall_offset"], facts["n"] // 2 + facts["wall_offset"]]
        assert facts["divider_cols"] == [facts["n"] // 2 - facts["wall_offset"], facts["n"] // 2 + facts["wall_offset"]] if facts["track"] == "vertical" else [facts["n"] // 2]
        assert gen.rule_mirror(grid) != grid
        assert gen.SEMANTIC_WITNESSES["gray_count_not_size_lookup"](grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_population_is_lawful_diverse_and_teaches_counting(band):
    seen = set()
    sizes = set()
    tracks = set()
    counts_by_size = {}
    for sample_index in range(160):
        grid = gen.generate(7001, sample_index, difficulty=band)
        before = deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) != grid
        assert gen.SEMANTIC_WITNESSES["gray_count_not_size_lookup"](grid)
        assert grid == before
        facts = _profile_facts(grid)
        sizes.add(facts["n"])
        tracks.add(facts["track"])
        counts_by_size.setdefault(facts["n"], set()).add(facts["gray_count"])
        seen.add(tuple(map(tuple, grid)))
        assert grid == gen.generate(7001, sample_index, difficulty=band)
    assert sizes == {9, 11, 13, 19}
    assert tracks == {"vertical", "horizontal"}
    assert all(len(counts) >= 2 for counts in counts_by_size.values())
    assert len(seen) >= 100


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_rejects_invalid_scalars(bad_sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, bad_sample_index)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_invalid_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_difficulty", ["__invalid_difficulty__", 1, True])
def test_generate_rejects_invalid_difficulty_scalars(bad_difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"scene_profile": 11},
        {"scene_profile": True},
        {"scene_profile": "n11_vertical_c9"},
        {"scene_profile": "not-a-profile"},
    ],
)
def test_unknown_and_invalid_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError), match="override|scene_profile|unknown"):
        gen.generate(1, 0, **overrides)


def test_declared_shortcut_fits_every_canonical_pair_but_every_emitted_profile_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_size_to_count"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        original = deepcopy(pair["input"])
        assert shortcut(pair["input"]) == pair["output"]
        assert pair["input"] == original

    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(9000 + index, index, scene_profile=profile)
        assert shortcut(grid) != gen.rule_mirror(grid), profile


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_consecutive_three_demo_lessons_refute_declared_rivals(band):
    for start in range(40):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(12345 + start, start + offset, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            12345 + start,
            start + gen.EXAMPLES_NEEDED,
            difficulty=band,
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_destructive_mutations():
    grid = gen.generate(17, 3, scene_profile="n11_vertical_c7")
    mutations = []

    wrong_color = deepcopy(grid)
    wrong_color[0][0] = 4
    mutations.append(wrong_color)

    ragged = deepcopy(grid)
    ragged[-1].pop()
    mutations.append(ragged)

    missing_wall = deepcopy(grid)
    facts = _profile_facts(grid)
    missing_wall[0][11 // 2 - facts["wall_offset"]] = 7
    mutations.append(missing_wall)

    off_center_crossbar = deepcopy(grid)
    off_center_crossbar[11 // 2][0] = 7
    mutations.append(off_center_crossbar)

    disconnected_gray = deepcopy(grid)
    for row in range(11):
        for col in range(11):
            if disconnected_gray[row][col] == 5:
                disconnected_gray[row][col] = 7
    disconnected_gray[4][4] = 5
    disconnected_gray[6][6] = 5
    disconnected_gray[5][5] = 5
    mutations.append(disconnected_gray)

    assert all(gen.self_check(candidate) for candidate in mutations)


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(9)]],
)
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_replay_is_fresh_and_does_not_touch_global_rng():
    before = random.getstate()
    first = gen.generate(424242, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(424242, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(424242, 17, difficulty="hard")


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(GEN_PATH)],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]
