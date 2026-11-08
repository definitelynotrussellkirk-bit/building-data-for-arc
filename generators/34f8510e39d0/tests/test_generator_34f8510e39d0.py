from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "34f8510e39d0"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.34f8510e39d0.generator"
)


def _grid(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def test_34f8510e39d0_canonical_pairs_are_accepted_and_mirrored() -> None:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_34f8510e39d0_rule_hash_tracks_selected_authority() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "f97715331ac1"


def test_34f8510e39d0_every_profile_override_round_trips_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.PROFILE_NAMES):
            grid = gen.generate(
                7000 + index,
                index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) != grid


def test_34f8510e39d0_unknown_override_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__="x")


def test_34f8510e39d0_three_demo_windows_refute_named_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(9000 + start, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                9000 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty=band,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                )


def test_34f8510e39d0_self_check_rejects_targeted_impostors() -> None:
    blank = _grid(7, 12)
    assert gen.self_check(blank)

    too_small = _grid(7, 12)
    for r in (2, 3):
        for c in (2, 3):
            too_small[r][c] = 3
    assert gen.self_check(too_small)

    hollow = _grid(7, 12)
    for r in range(2, 5):
        for c in range(2, 5):
            if r in {2, 4} or c in {2, 4}:
                hollow[r][c] = 3
    assert gen.self_check(hollow)

    mixed_touch = _grid(7, 12)
    for r in range(2, 5):
        for c in range(2, 5):
            mixed_touch[r][c] = 3
    mixed_touch[3][5] = 5
    assert any("touches non-green" in err for err in gen.self_check(mixed_touch))

    no_background = [[3 for _ in range(6)] for _ in range(6)]
    assert any("background color 0" in err for err in gen.self_check(no_background))


def test_34f8510e39d0_replay_freshness_and_global_rng_purity() -> None:
    before = random.getstate()
    first = gen.generate(424242, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(424242, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(424242, 17, difficulty="hard")
