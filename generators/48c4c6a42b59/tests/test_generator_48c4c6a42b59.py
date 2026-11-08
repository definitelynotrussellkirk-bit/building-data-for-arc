"""Focused regressions for generator 48c4c6a42b59."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = GENERATOR_DIR / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_48c4c6a42b59", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "48c4c6a42b59":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise AssertionError("canonical task 48c4c6a42b59 is missing")


def blank(h=11, w=11):
    return [[0 for _ in range(w)] for _ in range(h)]


def paint(grid, shape, top, left, color):
    for r, c in shape:
        grid[top + r][left + c] = color


def test_contract_hash_axes_and_every_canonical_pair_is_owned():
    generator = load_generator()
    assert generator.RULE_HASH == "cecf4f1691f5"
    assert set(generator.AXES) == {"grid_h", "grid_w", "n_blobs"}
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_override_boundaries_are_exact_observable_and_total_in_every_band():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for h in (11, 13):
            for w in (11, 13):
                for n in (2, 3):
                    expected = {"grid_h": h, "grid_w": w, "n_blobs": n}
                    grid = generator.generate(
                        1701, 29, difficulty=band, grid_h=h, grid_w=w, n_blobs=n
                    )
                    assert generator.observe_overrides(grid) == expected
                    assert generator.self_check(grid, difficulty=band) == []
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        generator.generate(1, 0, mystery_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(1, 0, difficulty="impossible")


def test_generated_distribution_has_canonical_support_and_every_semantic_branch():
    generator = load_generator()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            generator.generate(700000 + band_index * 10000 + i, i, difficulty=band)
            for i in range(200)
        ]
        assert all(generator.self_check(grid, difficulty=band) == [] for grid in grids)
        strict_hits = sum(generator.strict_canonical_like(grid) == [] for grid in grids)
        assert strict_hits >= 10, (band, strict_hits)
        for name, witness in generator.SEMANTIC_WITNESSES.items():
            hits = sum(bool(witness(grid)) for grid in grids)
            assert hits > 0, (band, name)
        signatures = {tuple(tuple(row) for row in grid) for grid in grids}
        assert len(signatures) >= 190, (band, len(signatures))


def test_schedule_windows_refute_named_rivals_and_identify_queries():
    generator = load_generator()
    assert set(generator.SCHEDULE_PROFILES) == {
        "canonical_square",
        "mixed_bbox",
        "size_contrast",
        "palette_counterexample",
    }
    assert {
        generator.schedule_profile(1234, sample_index, difficulty="medium")
        for sample_index in range(12)
    } == set(generator.SCHEDULE_PROFILES)

    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                grid = generator.generate(998877, sample_index, difficulty=band)
                demos.append({"input": grid, "output": generator.rule_mirror(grid)})
            query_grid = generator.generate(
                998877, start + generator.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
            assert generator.lesson_identifiable(demos, query) == []
            for name, competitor in generator.LESSON_COMPETITORS.items():
                survives = all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                )
                assert not survives or competitor(query["input"]) == query["output"], name


def test_witness_rival_claims_are_real_on_generated_grids():
    generator = load_generator()
    assert set(generator.WITNESS_RIVALS) == set(generator.SEMANTIC_WITNESSES)
    assert set(generator.CANONICAL_SHORTCUTS) <= set(generator.SEMANTIC_RIVALS)
    grids = [generator.generate(424242, i) for i in range(40)]
    for witness_name, rival_names in generator.WITNESS_RIVALS.items():
        firing = [g for g in grids if generator.SEMANTIC_WITNESSES[witness_name](g)]
        assert firing, witness_name
        for grid in firing:
            oracle = generator.rule_mirror(grid)
            assert any(
                generator.SEMANTIC_RIVALS[name](grid) != oracle
                for name in rival_names
            ), (witness_name, rival_names)


def test_self_check_rejects_targeted_impostors():
    generator = load_generator()
    asym6 = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2))
    asym8 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 2), (3, 3))

    one_blob = blank()
    paint(one_blob, asym6, 1, 1, 2)

    symmetric = blank()
    paint(symmetric, ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)), 1, 1, 2)
    paint(symmetric, ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)), 6, 6, 3)

    split_color = blank()
    paint(split_color, asym6, 0, 0, 2)
    paint(split_color, asym6, 7, 0, 2)
    paint(split_color, asym8, 2, 6, 3)

    colliding_mirrors = blank()
    paint(colliding_mirrors, asym6, 1, 1, 2)
    # Separate source objects, but their bbox-local unions overlap at (2, 4).
    paint(colliding_mirrors, ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)), 1, 4, 3)

    too_small = blank()
    paint(too_small, ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)), 1, 1, 2)
    paint(too_small, asym8, 5, 6, 3)

    same_color_touching = blank()
    paint(same_color_touching, asym6, 1, 1, 2)
    paint(same_color_touching, asym8, 5, 6, 3)
    same_color_touching[4][3] = 2

    impostors = {
        "one object": one_blob,
        "all objects horizontal-symmetric": symmetric,
        "one color split across objects": split_color,
        "local mirrored footprints collide": colliding_mirrors,
        "object below canonical size envelope": too_small,
        "stray same-color bridge/noise": same_color_touching,
    }
    for name, grid in impostors.items():
        assert generator.self_check(grid), name


def test_negative_recombination_is_rejected_while_other_valid_object_remains():
    generator = load_generator()
    grid = generator.generate(481516, 23, grid_h=11, grid_w=11, n_blobs=2)
    comps = generator._components(grid)
    assert len(comps) == 2
    mutated = copy.deepcopy(grid)
    victim = comps[0]
    for r, c in victim["cells"]:
        mutated[r][c] = 0
    r1, c1, _, _ = victim["bbox"]
    symmetric = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1))
    paint(mutated, symmetric, r1, c1, victim["color"])
    assert generator.self_check(mutated)
    assert any(obj["color"] != victim["color"] for obj in generator._components(mutated))


def test_replay_is_deterministic_fresh_and_process_rng_pure():
    generator = load_generator()
    random.seed(20261002)
    before = random.getstate()
    first = generator.generate(777, 19, difficulty="hard")
    after = random.getstate()
    second = generator.generate(777, 19, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert generator.generate(777, 19, difficulty="hard") == second
