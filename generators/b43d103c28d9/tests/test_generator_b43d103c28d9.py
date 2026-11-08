"""Focused regression coverage for b43d103c28d9 columnwise gravity-up."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "b43d103c28d9"
    / "generator.py"
)


def load_generator():
    name = "generator_b43d103c28d9_regression"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


G = load_generator()
sys.path.insert(0, str(ROOT))
from scripts.canonical_profile_gate import canonical_pairs  # noqa: E402


def pair_for(seed: int, sample_index: int, band: str = "medium"):
    grid = G.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": G._gravity_up(grid)}


def test_canonical_pairs_are_accepted_strict_and_exact():
    pairs = canonical_pairs(G.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert G.self_check(pair["input"]) == []
        assert G.strict_canonical_like(pair["input"]) == []
        assert G._gravity_up(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_ambiguity_is_deliberately_killed_by_scheduled_witnesses():
    # Both shortcuts fit every official pair, which is why counterexamples are
    # mandatory in generated lessons rather than optional diversity.
    for pair in canonical_pairs(G.TASK_ID):
        assert G._rival_sort_numeric(pair["input"]) == pair["output"]
        assert G._rival_move_lower_only(pair["input"]) == pair["output"]

    pairs = [pair_for(40_000 + i, i, "hard") for i in range(4)]
    assert any(
        G._rival_sort_numeric(pair["input"]) != pair["output"]
        for pair in pairs
    )
    assert any(
        G._rival_move_lower_only(pair["input"]) != pair["output"]
        for pair in pairs
    )


def test_every_four_sample_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            episode = [
                pair_for(50_000 + start, sample_index, band)
                for sample_index in range(start, start + G.EXAMPLES_NEEDED + 1)
            ]
            demos = episode[: G.EXAMPLES_NEEDED]
            query = episode[-1]
            assert G.lesson_identifiable(demos, query) == []
            assert {G.observe_overrides(p["input"])["scene_type"] for p in demos} == set(
                G.SCENE_TYPES
            )


def test_default_generation_is_deterministic_fresh_and_rng_pure():
    for band in ("easy", "medium", "hard"):
        random.seed(123456)
        before = random.getstate()
        a = G.generate(61_001, 7, difficulty=band)
        after = random.getstate()
        b = G.generate(61_001, 7, difficulty=band)
        assert a == b
        assert a is not b
        assert all(row_a is not row_b for row_a, row_b in zip(a, b))
        assert before == after
        b[0][0] = 9 if b[0][0] != 9 else 8
        assert a != b


def test_every_declared_override_is_exact_and_observable_at_boundaries():
    for band in ("easy", "medium", "hard"):
        for size in (8, 14):
            for scene_type in G.SCENE_TYPES:
                for palette_mode in G.PALETTE_MODES:
                    grid = G.generate(
                        70_000 + size,
                        23,
                        difficulty=band,
                        grid_size=size,
                        scene_type=scene_type,
                        palette_mode=palette_mode,
                    )
                    assert G.self_check(grid, difficulty=band) == []
                    assert G.observe_overrides(grid) == {
                        "grid_size": size,
                        "scene_type": scene_type,
                        "palette_mode": palette_mode,
                    }
    with pytest.raises(ValueError, match="unknown override"):
        G.generate(1, 2, difficulty="easy", unsupported_axis="x")
    with pytest.raises(ValueError, match="unknown difficulty"):
        G.generate(1, 2, difficulty="impossible")


def test_structural_self_check_rejects_targeted_impostors():
    base = G.generate(
        81_001,
        0,
        difficulty="medium",
        scene_type="canonical_histograms",
        palette_mode="canonical",
        grid_size=10,
    )
    info, errors = G._analyse(base)
    assert errors == []
    upper = info["upper_color"]
    lower = info["lower_color"]
    occupied = list(info["occupied_columns"])

    impostors: dict[str, list[list[int]]] = {}

    packed = G._gravity_up(base)
    impostors["already_packed_identity"] = packed

    disconnected = copy.deepcopy(base)
    middle = occupied[len(occupied) // 2]
    for row in disconnected:
        row[middle] = 0
    impostors["disconnected_column_support"] = disconnected

    third_color = copy.deepcopy(base)
    r0 = next(r for r in range(len(base)) if third_color[r][occupied[0]] == upper)
    third_color[r0][occupied[0]] = 9 if 9 not in (upper, lower) else 8
    impostors["third_foreground_color"] = third_color

    lower_without_upper = copy.deepcopy(base)
    outside = 0 if occupied[0] > 0 else len(base[0]) - 1
    lower_without_upper[-1][outside] = lower
    impostors["lower_support_outside_upper"] = lower_without_upper

    mixed_first_role = copy.deepcopy(base)
    c = occupied[-1]
    first = next(r for r in range(len(base)) if mixed_first_role[r][c] != 0)
    mixed_first_role[first][c] = lower
    impostors["mixed_first_nonzero_role"] = mixed_first_role

    for name, grid in impostors.items():
        assert G.self_check(grid), name


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = G.generate(
        91_002,
        0,
        difficulty="easy",
        scene_type="canonical_histograms",
        palette_mode="canonical",
        grid_size=10,
    )
    info, errors = G._analyse(grid)
    assert errors == []
    occupied = list(info["occupied_columns"])
    outside = 0 if occupied[0] > 0 else len(grid[0]) - 1
    assert all(grid[r][outside] == 0 for r in range(len(grid)))

    recombined = copy.deepcopy(grid)
    recombined[-1][outside] = info["lower_color"]
    assert G.self_check(recombined)
    oracle_output = G._gravity_up(recombined)
    assert len(oracle_output) == len(recombined)
    assert oracle_output[0][outside] == info["lower_color"]


def test_rule_hash_matches_selected_canonical_authority():
    selected = json.loads(
        (
            ROOT
            / "data/base/solutions/training/3906de3d__b43d103c28d9.json"
        ).read_text()
    )["racket_target"]["target_code"]
    canonical = None
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == G.TASK_ID:
            canonical = row["program_solution"]
            break
    assert selected == canonical
    import hashlib

    normalized = " ".join(selected.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == G.RULE_HASH
