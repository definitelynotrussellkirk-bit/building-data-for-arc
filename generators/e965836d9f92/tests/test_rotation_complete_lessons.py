from __future__ import annotations

import hashlib

import pytest

from puzzle_generators.per_puzzle.e965836d9f92 import generator as gen


ALL_CODES = set(range(1, 7))
EXPECTED_CODE_RIVALS = {
    "code1_is_flip_lr",
    "code2_is_identity",
    "code3_is_identity",
    "code4_is_identity",
    "code5_is_identity",
    "code6_is_rotate_cw",
}


def _codes(pair: dict[str, list[list[int]]]) -> list[int]:
    return [value for value in pair["input"][0][1:] if value != 0]


def _window(difficulty: str, start: int) -> list[dict[str, list[list[int]]]]:
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        inp = gen.generate(20261006, sample_index, difficulty=difficulty)
        pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
    return pairs


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_four_pair_window_is_identifiable_under_each_query_rotation(
    difficulty: str,
) -> None:
    """Any pair may become the query without leaving a declared rival alive."""
    for start in range(12):
        pairs = _window(difficulty, start)

        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            reasons = gen.lesson_identifiable(demos, query)
            surviving = [
                name
                for name, rival in gen.LESSON_COMPETITORS.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            assert reasons == [], (
                f"difficulty={difficulty}, start={start}, query_index={query_index}, "
                f"codes={[_codes(pair) for pair in pairs]}: {reasons}"
            )
            assert surviving == [], (
                f"difficulty={difficulty}, start={start}, query_index={query_index}, "
                f"codes={[_codes(pair) for pair in pairs]}: surviving={surviving}"
            )


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_query_rotation_keeps_all_transform_codes_in_demonstrations(
    difficulty: str,
) -> None:
    """Each leave-one-out lesson retains a direct witness for codes 1 through 6."""
    for start in range(12):
        pairs = _window(difficulty, start)
        for query_index in range(len(pairs)):
            covered = {
                code
                for index, pair in enumerate(pairs)
                if index != query_index
                for code in _codes(pair)
            }
            assert covered == ALL_CODES, (
                f"difficulty={difficulty}, start={start}, query_index={query_index}, "
                f"codes={[_codes(pair) for pair in pairs]}, covered={sorted(covered)}"
            )


def test_declares_one_wrong_mapping_rival_per_transform_code() -> None:
    assert EXPECTED_CODE_RIVALS <= set(gen.LESSON_COMPETITORS)
    for code in range(1, 7):
        assert gen.WITNESS_RIVALS[f"code_{code}"]


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_noncanonical_default_prototypes_have_square_footprints(
    difficulty: str,
) -> None:
    """Square panels prevent quarter-turn variants from being clipped together."""
    checked = 0
    for sample_index in range(24):
        if gen.schedule_profile(20261006, sample_index, difficulty) == "canonical_anchor":
            continue
        facts = gen._facts(gen.generate(20261006, sample_index, difficulty=difficulty))
        checked += 1
        assert facts["bbox_h"] == facts["bbox_w"], (
            f"difficulty={difficulty}, sample_index={sample_index}, "
            f"bbox={facts['bbox_h']}x{facts['bbox_w']}, codes={facts['codes']}"
        )
    assert checked > 0


def test_declared_strict_floor_survives_pinned_semantic_census() -> None:
    hits = 0
    draws = 0
    for difficulty in ("easy", "medium", "hard"):
        for index in range(200):
            digest = hashlib.sha256(
                f"profile-floor:v1:{gen.TASK_ID}:{difficulty}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            hits += int(not gen.strict_canonical_like(grid))
            draws += 1
    assert hits / draws >= gen.MIN_STRICT_FRAC, (
        f"strict support {hits}/{draws}={hits / draws:.1%} is below "
        f"declared floor {gen.MIN_STRICT_FRAC:.1%}"
    )


def test_every_semantic_witness_declares_a_named_rival() -> None:
    missing = sorted(
        name
        for name in gen.SEMANTIC_WITNESSES
        if not gen.WITNESS_RIVALS.get(name)
    )
    assert missing == []


@pytest.mark.parametrize(
    "seed,difficulty,start,query_index",
    (
        (4154478693, "easy", 96, 2),
        (1304531226, "medium", 72, 1),
    ),
)
def test_large_census_windows_refute_physical_header_position_rivals(
    seed: int, difficulty: str, start: int, query_index: int
) -> None:
    """Regression for two source-bound leave-one-out failures from the 300-lesson census."""
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        inp = gen.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": inp, "output": gen.rule_mirror(inp)})

    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
    survivors = [
        name
        for name in (
            "header_column_is_transform_code",
            "header_row_is_output_color",
        )
        if all(gen.SEMANTIC_RIVALS[name](pair["input"]) == pair["output"] for pair in demos)
    ]
    assert survivors == [], (
        f"seed={seed}, difficulty={difficulty}, start={start}, "
        f"query_index={query_index}, survivors={survivors}"
    )
