from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
)


TASK_ID = "a2b749aefc65"
ROOT = find_root(__file__)
GEN, _GEN_PATH, _GEN_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _data_file(relative: str) -> Path:
    for base in (ROOT / "data", ROOT / "shared/data"):
        candidate = base / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


BASE_PATHS = (
    _data_file("base/solutions/training/5034a0b5__a2b749aefc65.json"),
    _data_file("base/solutions/augmented/5034a0b5__a8ecd9db2810.json"),
)


def _canonical_rows() -> list[dict]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_selected_authorities_and_real_racket_are_exact_pure_and_reentrant() -> None:
    rows = _canonical_rows()
    sources = {row["program_solution"] for row in rows}
    assert len(sources) == 1
    source = next(iter(sources))
    assert GEN.RULE_HASH == _normalized_hash(source) == "d151397a0cab"
    for path in BASE_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == source
        assert target["needs_conversion"] is False

    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    bridge = RacketBridge(max_calls_before_restart=128)
    wrapped = wrap_rule(source)
    try:
        for index, pair in enumerate(pairs):
            before = copy.deepcopy(pair["input"])
            bridge.define_grid(f"canonical_{index}", pair["input"])
            assert bridge.eval_text(f"({wrapped} canonical_{index})") == pair["output"]
            assert pair["input"] == before

        # A -> B -> A in one protected namespace catches retained mutable state.
        bridge.define_grid("purity_a", pairs[0]["input"])
        bridge.define_grid("purity_b", pairs[1]["input"])
        assert bridge.eval_text(f"({wrapped} purity_a)") == pairs[0]["output"]
        assert bridge.eval_text(f"({wrapped} purity_b)") == pairs[1]["output"]
        assert bridge.eval_text(f"({wrapped} purity_a)") == pairs[0]["output"]
    finally:
        bridge.shutdown()


def test_all_canonical_pairs_are_recognized_and_mirrored_exactly() -> None:
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 10
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.observe_overrides(pair["input"])["scene_profile"] in GEN.CANONICAL_PROFILES
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("profile", GEN.PROFILE_NAMES)
def test_each_declared_profile_override_is_exact_and_observable(profile: str) -> None:
    grid = GEN.generate(7301, 19, difficulty="hard", scene_profile=profile)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}
    expected_strict = profile in GEN.CANONICAL_PROFILES
    assert (GEN.strict_canonical_like(grid) == []) is expected_strict


def test_default_schedule_is_deterministic_fresh_and_rng_isolated() -> None:
    random.seed(8842)
    before = random.getstate()
    first = GEN.generate(91, 7, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(91, 7, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert GEN.observe_overrides(first)["scene_profile"] == GEN.schedule_profile(91, 7, "medium")


def test_invalid_calls_fail_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, made_up_axis="x")
    with pytest.raises(ValueError, match="scene_profile"):
        GEN.generate(1, 0, scene_profile="not_a_profile")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_structural_mutations_are_rejected() -> None:
    original = GEN.generate(404, 1, scene_profile="canonical_9_mixed")
    analysis, errors = GEN._analyze(original)
    assert errors == [] and analysis is not None
    bg = analysis["background"]
    side_colors = analysis["side_colors"]

    bad_corner = copy.deepcopy(original)
    bad_corner[0][0] = side_colors["top"]
    assert any("corner" in error for error in GEN.self_check(bad_corner))

    broken_side = copy.deepcopy(original)
    broken_side[0][2] = side_colors["left"]
    assert any("top" in error and "uniform" in error for error in GEN.self_check(broken_side))

    duplicate_sides = copy.deepcopy(original)
    for c in range(1, len(duplicate_sides[0]) - 1):
        duplicate_sides[0][c] = side_colors["bottom"]
    assert any("pairwise distinct" in error for error in GEN.self_check(duplicate_sides))

    no_markers = GEN.generate(405, 0, scene_profile="canonical_8_clean")
    for r in range(1, len(no_markers) - 1):
        for c in range(1, len(no_markers[0]) - 1):
            no_markers[r][c] = no_markers[0][0]
    assert any("marker" in error for error in GEN.self_check(no_markers))

    collision = copy.deepcopy(original)
    distractor_color = next(iter(analysis["distractor_counts"]))
    candidate = next(
        marker for marker in analysis["side_markers"]
        if not marker["blocked"]
        and original[marker["destination"][0]][marker["destination"][1]] == bg
    )
    r, c = candidate["destination"]
    collision[r][c] = distractor_color
    assert any("final destinations" in error for error in GEN.self_check(collision))


def test_every_four_demo_window_eliminates_all_named_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(991, start + offset, difficulty) for offset in range(GEN.EXAMPLES_NEEDED)]
            query = _pair(991, start + GEN.EXAMPLES_NEEDED, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos), name


def test_every_semantic_witness_fires_in_every_band_and_refutes_its_rival() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(808, index, difficulty=difficulty) for index in range(12)]
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (difficulty, witness_name)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                rival = GEN.SEMANTIC_RIVALS[rival_name]
                assert all(GEN.rule_mirror(grid) != rival(grid) for grid in firing)


def test_schedule_exposes_every_declared_profile_pooled_across_bands() -> None:
    observed = {
        GEN.schedule_profile(17, index, difficulty)
        for difficulty in ("easy", "medium", "hard")
        for index in range(12)
    }
    assert observed == set(GEN.SCHEDULE_PROFILES)
