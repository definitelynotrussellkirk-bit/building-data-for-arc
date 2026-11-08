from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
GENERATOR, SOURCE, HASH = load_selected_generator("8b6a2892a064", root=ROOT)

def test_arc_size_limit_is_part_of_the_validator():
    grid = GENERATOR.generate(3, 4, scene_profile="two_mixed")
    while len(grid) < 31:
        grid.append([7] * len(grid[0]))
    assert GENERATOR.self_check(grid), "A 31-row input must not be admitted as an ARC grid"

def test_explicit_lesson_rivals_are_present_and_nonvacuous():
    assert hasattr(GENERATOR, "LESSON_COMPETITORS"), "Lesson evidence needs executable rivals"
    pairs = canonical_pairs("8b6a2892a064", root=ROOT)
    required = {"identity", "horizontal_only", "vertical_only", "skip_short_lines"}
    assert required <= set(GENERATOR.LESSON_COMPETITORS)
    for name in required:
        rival = GENERATOR.LESSON_COMPETITORS[name]
        assert any(rival(p["input"]) != p["output"] for p in pairs), name

def test_semantic_contract_accepts_all_canonical_pairs():
    assert hasattr(GENERATOR, "strict_canonical_like")
    for pair in canonical_pairs("8b6a2892a064", root=ROOT):
        assert GENERATOR.strict_canonical_like(pair["input"]) == []
        assert GENERATOR.rule_mirror(pair["input"]) == pair["output"]

def test_rivals_do_not_mutate_inputs():
    assert hasattr(GENERATOR, "LESSON_COMPETITORS")
    import copy
    grid = GENERATOR.generate(29, 7, scene_profile="three_mixed")
    original = copy.deepcopy(grid)
    for rival in GENERATOR.LESSON_COMPETITORS.values():
        result = rival(grid)
        assert grid == original
        assert len(result) == len(grid)
        assert all(len(row) == len(grid[0]) for row in result)

@pytest.mark.parametrize("band", ["easy", None, "hard"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_integer_scalars(band, bad):
    with pytest.raises(ValueError):
        GENERATOR.generate(bad, 0, difficulty=band)

@pytest.mark.parametrize("band", ["easy", None, "hard"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_rejects_non_integer_or_negative_scalars(band, bad):
    with pytest.raises(ValueError):
        GENERATOR.generate(991, bad, difficulty=band)

def test_signed_integer_seed_and_nonnegative_index_remain_supported():
    for seed in [-1, 0, 2**80]:
        grid = GENERATOR.generate(seed, 0)
        assert GENERATOR.self_check(grid) == []


@pytest.mark.parametrize("band,seed,index,expected", [
    ("easy", 0, 0, "cb56c2640b27355f44e328433fd43f652e129ca563b101f8b94785af407996cb"),
    ("medium", 17, 23, "c4da539d6a1bd560a1c91f3669fde4b748328c1955d4a1980d1e9d6bd09b33bf"),
    ("hard", 83, 3403, "ea01c86bb84582beb22c62becfa54dd43ccec240a738301afb967e4543b3effc"),
])
def test_valid_seed_stream_matches_version_4_0_0(band, seed, index, expected):
    import hashlib
    import json
    grid = GENERATOR.generate(seed, index, difficulty=band)
    assert hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest() == expected
