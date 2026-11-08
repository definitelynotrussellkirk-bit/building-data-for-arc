from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "406739865b43"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.406739865b43.generator"
)


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_authority_pin_and_all_canonical_pairs() -> None:
    assert GEN.RULE_HASH == "c69934b21e7a"
    assert GEN.EXAMPLES_NEEDED == 4
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_schedule_window_and_query_rotation_refutes_all_rivals() -> None:
    bands = ("easy", "medium", "hard")
    for start in range(15):
        band = bands[start % len(bands)]
        lesson = [_pair(41000 + start, start + offset, band) for offset in range(5)]

        # Production order: four demonstrations followed by one query.
        demos, query = lesson[:4], lesson[4]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert not all(
                rival(pair["input"]) == pair["output"] for pair in demos
            ), f"window {start} failed to refute {name}"

        # The packet's census rotates every one of the five labelled pairs.
        for query_index, rotated_query in enumerate(lesson):
            rotated_demos = [
                pair for index, pair in enumerate(lesson) if index != query_index
            ]
            assert GEN.lesson_identifiable(rotated_demos, rotated_query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(pair["input"]) == pair["output"]
                    for pair in rotated_demos
                ), f"rotation {query_index} at window {start} kept {name}"


def test_exact_override_axes_round_trip_and_fail_closed() -> None:
    cases = [
        {
            "scene_profile": "canonical_10x10",
            "selection_profile": "anchor",
            "target_cells": 3,
            "palette_profile": "low",
        },
        {
            "scene_profile": "canonical_12x13",
            "selection_profile": "rank2",
            "target_cells": 6,
            "palette_profile": "high",
        },
        {
            "scene_profile": "broad",
            "selection_profile": "rank3",
            "target_cells": 4,
            "palette_profile": "mixed",
        },
    ]
    for index, expected in enumerate(cases):
        band = ("easy", "medium", "hard")[index]
        grid = GEN.generate(900 + index, 31 + index, difficulty=band, **expected)
        assert GEN.observe_overrides(grid) == expected
        assert GEN.self_check(grid, meta=expected) == []

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, misspelled_axis=1)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, target_cells=True)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, target_cells=7)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, selection_profile="not-a-profile")


def test_default_draws_are_strict_canonical_profiled_and_bands_are_live() -> None:
    canonical_profiles = {(10, 10, 4), (11, 11, 4), (12, 12, 4), (12, 13, 4)}
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = GEN.generate(12000 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            assert profile in canonical_profiles

    # Difficulty must change nuisance draws; no dead, byte-identical bands.
    grids = {
        band: GEN.generate(7331, 8, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) >= 2


def test_determinism_fresh_returns_rng_purity_and_mutation_rejection() -> None:
    before = random.getstate()
    first = GEN.generate(711, 13, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(711, 13, difficulty="hard")
    assert before == after == random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    pristine = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(711, 13, difficulty="hard") == pristine

    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), f"mutation {name!r} was accepted"


def test_declared_canonical_shortcuts_are_exactly_the_ambiguous_rivals() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    ambiguous = {
        name
        for name, rival in GEN.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    assert ambiguous == {"farthest_from_marker"}
    assert set(GEN.CANONICAL_SHORTCUTS) == ambiguous


def test_selection_rank_probe_exhausts_declared_rivals_and_rotations() -> None:
    import importlib.util

    probe_path = (
        find_root(__file__)
        / "generators"
        / TASK_ID
        / "workspace"
        / "selection_rank_probe.py"
    )
    spec = importlib.util.spec_from_file_location("selection_rank_probe", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.run_probe(starts_per_band=5, seed_base=52000)
    assert report["status"] == "pass", report["failures"][:3]
    assert report["counts"] == {
        "windows": 15,
        "pairs": 75,
        "rotations": 75,
        "unique_inputs": 75,
        "generation_errors": 0,
        "self_check_failures": 0,
        "production_failures": 0,
        "rotation_failures": 0,
    }
    assert set(report["competitors"]["names"]) == set(GEN.LESSON_COMPETITORS)
    assert report["canonical_shortcuts"]["declared_exact"] is True
    assert set(report["rank_signatures"]) == {
        "3-components/order-2/size-2/distance-2",
        "4-components/order-2/size-2/distance-2",
        "4-components/order-3/size-3/distance-3",
    }
