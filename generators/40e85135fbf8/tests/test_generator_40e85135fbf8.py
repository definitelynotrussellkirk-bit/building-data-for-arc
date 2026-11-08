from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("equality_header_generator", SOURCE)
assert SPEC and SPEC.loader
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def test_rule_hash_and_all_canonical_pairs():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = [row["program_solution"] for line in handle
                    if (row := json.loads(line)).get("task_id") == TASK_ID]
    assert programs
    # The catalog pins whitespace-normalized source, not the raw JSON string.
    assert {hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
            for program in programs} == {gen.RULE_HASH}
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_exact_axes_boundaries_and_observer_in_every_band():
    for band in ("easy", "medium", "hard"):
        for shape in gen.SHAPE_PROFILES:
            for scene in gen.SCENE_PROFILES:
                for palette in gen.PALETTE_KINDS:
                    requested = {
                        "shape_profile": shape,
                        "scene_profile": scene,
                        "palette_kind": palette,
                    }
                    grid = gen.generate(37, 53, difficulty=band, **requested)
                    assert gen.self_check(grid, difficulty=band) == []
                    assert gen.strict_canonical_like(grid) == []
                    assert gen.observe_overrides(grid) == requested


def test_every_advertised_window_is_identifiable_and_varied():
    for band in ("easy", "medium", "hard"):
        for seed in range(9):
            for start in range(9):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                assert gen.lesson_identifiable(demos, None) == []
                observed = [gen.observe_overrides(pair["input"]) for pair in demos]
                assert {row["scene_profile"] for row in observed} == set(gen.SCENE_PROFILES)
                assert len({row["shape_profile"] for row in observed}) == 3
                assert len({row["palette_kind"] for row in observed}) >= 2


def test_declared_canonical_shortcuts_fit_public_pairs_and_generated_witnesses_kill_them():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    grids = [
        gen.generate(
            71,
            index,
            scene_profile=gen.SCENE_PROFILES[index % len(gen.SCENE_PROFILES)],
            shape_profile="r6_c5",
            palette_kind="low",
        )
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for grid in firing:
            official = gen.rule_mirror(grid)
            assert any(gen.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)


def test_self_check_rejects_structural_and_semantic_impostor_mutations():
    grid = gen.generate(17, 23, shape_profile="r5_c4", scene_profile="canonical")
    mutations = []

    top_left = copy.deepcopy(grid)
    top_left[0][0] = 5
    mutations.append(top_left)

    missing_top = copy.deepcopy(grid)
    missing_top[0][1] = 0
    mutations.append(missing_top)

    missing_left = copy.deepcopy(grid)
    missing_left[1][0] = 0
    mutations.append(missing_left)

    painted_interior = copy.deepcopy(grid)
    painted_interior[1][1] = 6
    mutations.append(painted_interior)

    ragged = copy.deepcopy(grid)
    ragged[-1].pop()
    mutations.append(ragged)

    invalid_color = copy.deepcopy(grid)
    invalid_color[0][1] = 12
    mutations.append(invalid_color)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_determinism_fresh_returns_global_rng_and_bad_calls():
    random.seed(12345)
    state = random.getstate()
    first = gen.generate(19, 29, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(19, 29, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second

    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis="canonical")
    with pytest.raises(ValueError):
        gen.generate(1, 2, scene_profile="dual_gap")
    with pytest.raises(ValueError):
        gen.generate(1, 2, shape_profile="r9_c9")
    with pytest.raises(ValueError):
        gen.generate(1, 2, palette_kind="warm")
