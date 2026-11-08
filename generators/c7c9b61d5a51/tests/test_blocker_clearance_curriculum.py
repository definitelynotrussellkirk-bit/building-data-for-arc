from __future__ import annotations

import importlib

import pytest

TASK_ID = "c7c9b61d5a51"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_default_schedule_exposes_elbow_leg_and_mixed_blockers() -> None:
    assert tuple(gen.BLOCKER_PATTERNS) == ("elbow", "leg", "mixed")
    expected = ("leg", "mixed", "elbow", "mixed")

    for sample_index, pattern in enumerate(expected):
        grid = gen.generate(31_337, sample_index, difficulty="hard")
        observed = gen.semantic_observables(grid)
        assert observed["blocker_pattern"] == pattern
        positions = [pair["blocker_position"] for pair in gen._analyze(grid)["pairs"]]
        if pattern == "elbow":
            assert set(positions) == {"elbow"}
        elif pattern == "leg":
            assert set(positions) == {"leg"}
        else:
            assert set(positions) == {"elbow", "leg"}
        assert gen.self_check(grid) == []


def test_elbow_only_shortcut_is_declared_and_refuted() -> None:
    rival_name = "elbow_only_clearance"
    witness_name = "off_elbow_blocker_requires_full_path_scan"
    assert rival_name in gen.SEMANTIC_RIVALS
    assert rival_name in gen.LESSON_COMPETITORS
    assert witness_name in gen.SEMANTIC_WITNESSES
    assert gen.WITNESS_RIVALS[witness_name] == [rival_name]

    # Residue 1 carries a mixed elbow/leg blocker pattern.  Overriding the route
    # pattern to "second" makes the leg-blocked pair answer-changing for an
    # elbow-only solver while retaining the existing public exact-axis surface.
    grid = gen.generate(
        41_041,
        1,
        difficulty="medium",
        pair_count=2,
        route_pattern="second",
    )
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES[witness_name](grid)
    assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_default_four_slot_lesson_refutes_elbow_only_under_all_query_rotations(
    difficulty: str,
) -> None:
    rival_name = "elbow_only_clearance"
    assert rival_name in gen.LESSON_COMPETITORS

    for start in range(8):
        pairs = [
            _pair(gen.generate(52_000 + start, start + offset, difficulty=difficulty))
            for offset in range(gen.EXAMPLES_NEEDED + 1)
        ]
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            rival = gen.LESSON_COMPETITORS[rival_name]
            assert any(rival(demo["input"]) != demo["output"] for demo in demos)
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("route_pattern", gen.ROUTE_PATTERNS)
@pytest.mark.parametrize("sample_index", range(4))
def test_existing_route_pattern_overrides_remain_total(
    route_pattern: str, sample_index: int
) -> None:
    grid = gen.generate(
        73_000 + sample_index,
        sample_index,
        difficulty="easy",
        pair_count=2,
        route_pattern=route_pattern,
    )
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid)["route_pattern"] == route_pattern
