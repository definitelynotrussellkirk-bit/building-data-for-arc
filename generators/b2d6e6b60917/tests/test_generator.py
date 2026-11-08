"""Focused regressions for generator b2d6e6b60917."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as read_canonical_pairs, find_root

GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = find_root(__file__)
GENERATOR_PATH = GENERATOR_DIR / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_b2d6e6b60917", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return read_canonical_pairs("b2d6e6b60917", root=REPO_ROOT, labeled_only=True)


def signature(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_every_canonical_pair_is_owned():
    generator = load_generator()
    assert generator.RULE_HASH == "73b1bc28244d"
    assert set(generator.AXES) == {"n_markers"}
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_is_total_observable_and_unknown_controls_fail():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for n_markers in (2, 3):
            for sample_index in range(6):
                grid = generator.generate(
                    20261003,
                    sample_index,
                    difficulty=band,
                    n_markers=n_markers,
                )
                assert generator.self_check(grid, difficulty=band) == []
                assert generator.observe_overrides(grid) == {"n_markers": n_markers}
                assert (len(grid), len(grid[0])) == (21, 21)
                assert len({value for row in grid for value in row}) in (4, 5)
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        generator.generate(1, 0, mystery_axis=7)
    with pytest.raises((TypeError, ValueError), match="n_markers"):
        generator.generate(1, 0, n_markers=True)
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(1, 0, difficulty="impossible")


def test_generated_census_has_strict_anchors_witnesses_and_diversity():
    generator = load_generator()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            generator.generate(700000 + band_index * 10000 + i, i, difficulty=band)
            for i in range(120)
        ]
        assert all(generator.self_check(grid, difficulty=band) == [] for grid in grids)
        strict_hits = sum(generator.strict_canonical_like(grid) == [] for grid in grids)
        assert strict_hits >= 35, (band, strict_hits)
        for name, witness in generator.SEMANTIC_WITNESSES.items():
            hits = sum(bool(witness(grid)) for grid in grids)
            assert hits > 0, (band, name)
        assert len({signature(grid) for grid in grids}) >= 115


def test_three_demo_schedule_refutes_every_named_competitor():
    generator = load_generator()
    assert generator.EXAMPLES_NEEDED == 3
    assert set(generator.SCHEDULE_PROFILES) == {
        "canonical_3x3",
        "wide_2x4",
        "tall_4x2",
    }
    for band in ("easy", "medium", "hard"):
        for start in range(9):
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
                assert not all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ), (band, start, name)


def test_fixed_stride_four_is_a_real_canonical_shortcut_and_is_countered():
    generator = load_generator()
    assert set(generator.CANONICAL_SHORTCUTS) == {"fixed_stride_4"}
    shortcut = generator.CANONICAL_SHORTCUTS["fixed_stride_4"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    counterexamples = []
    for sample_index in range(12):
        grid = generator.generate(424242, sample_index, difficulty="medium")
        if generator.schedule_profile(424242, sample_index, "medium") != "canonical_3x3":
            counterexamples.append(grid)
    assert counterexamples
    assert all(shortcut(grid) != generator.rule_mirror(grid) for grid in counterexamples)


def test_each_witness_claim_names_a_real_disagreement():
    generator = load_generator()
    assert set(generator.WITNESS_RIVALS) == set(generator.SEMANTIC_WITNESSES)
    grids = [generator.generate(123456, i) for i in range(18)]
    for witness_name, rival_names in generator.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if generator.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for grid in firing:
            oracle = generator.rule_mirror(grid)
            assert any(
                generator.SEMANTIC_RIVALS[name](grid) != oracle
                for name in rival_names
            ), (witness_name, rival_names)


def test_marker_fragments_encode_first_copy_and_repeated_ray_is_visible():
    generator = load_generator()
    for sample_index in range(18):
        grid = generator.generate(8675309, sample_index)
        scene = generator._analyze_grid(grid)
        source = scene["source"]
        h, w = source["height"], source["width"]
        source_cells = set(source["cells"])
        occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
        for marker in scene["markers"]:
            dr, dc = marker["direction"]
            recovered = {
                (r - dr * (h + 1), c - dc * (w + 1))
                for r, c in marker["cells"]
            }
            assert recovered < source_cells
            assert any(
                0 <= r + 2 * dr * (h + 1) < len(grid)
                and 0 <= c + 2 * dc * (w + 1) < len(grid[0])
                and (r + 2 * dr * (h + 1), c + 2 * dc * (w + 1)) not in occupied
                for r, c in source_cells
            )


def test_self_check_rejects_targeted_impostors():
    generator = load_generator()
    valid = generator.generate(314159, 4, n_markers=3)

    missing_marker = copy.deepcopy(valid)
    scene = generator._analyze_grid(missing_marker)
    for victim in scene["markers"][:2]:
        for r, c in victim["cells"]:
            missing_marker[r][c] = 0

    bad_fragment = copy.deepcopy(valid)
    scene = generator._analyze_grid(bad_fragment)
    marker = scene["markers"][0]
    source = scene["source"]
    dr, dc = marker["direction"]
    shift_r = dr * (source["height"] + 1)
    shift_c = dc * (source["width"] + 1)
    source_cells = set(source["cells"])
    injected = None
    for r, c in marker["cells"]:
        for rr in range(max(0, r - 1), min(len(bad_fragment), r + 2)):
            for cc in range(max(0, c - 1), min(len(bad_fragment[0]), c + 2)):
                if bad_fragment[rr][cc] != 0:
                    continue
                if (rr - shift_r, cc - shift_c) in source_cells:
                    continue
                bad_fragment[rr][cc] = marker["color"]
                injected = (rr, cc)
                break
            if injected is not None:
                break
        if injected is not None:
            break
    assert injected is not None

    tied_largest = copy.deepcopy(valid)
    scene = generator._analyze_grid(tied_largest)
    source_size = scene["source"]["size"]
    marker = scene["markers"][0]
    # Extend one marker with remote same-color cells in its ray until it ties the source.
    dr, dc = marker["direction"]
    for step in range(2, 10):
        for sr, sc in scene["source"]["cells"]:
            rr = sr + step * dr * (scene["source"]["height"] + 1)
            cc = sc + step * dc * (scene["source"]["width"] + 1)
            if 0 <= rr < len(tied_largest) and 0 <= cc < len(tied_largest[0]) and tied_largest[rr][cc] == 0:
                tied_largest[rr][cc] = marker["color"]
                if sum(value == marker["color"] for row in tied_largest for value in row) >= source_size:
                    break
        if sum(value == marker["color"] for row in tied_largest for value in row) >= source_size:
            break

    assert generator.self_check(missing_marker)
    assert generator.self_check(bad_fragment)
    assert generator.self_check(tied_largest)


def test_replay_is_deterministic_fresh_and_process_rng_pure():
    generator = load_generator()
    random.seed(20261003)
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


def test_selected_active_rule_text_matches_canonical_authority():
    from reviewer_support import canonical_path

    canonical = next(
        row["program_solution"]
        for row in map(json.loads, canonical_path(REPO_ROOT).read_text().splitlines())
        if row.get("task_id") == "b2d6e6b60917"
    )
    base_path = (
        REPO_ROOT
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "training"
        / "045e512c__b2d6e6b60917.json"
    )
    selected = json.loads(base_path.read_text())["racket_target"]["target_code"]
    assert selected == canonical
