from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "2692a3e47a66"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"generator_{TASK_ID}", ROOT / f"generators/{TASK_ID}/generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    train = row.get("train") or []
    test = row.get("test") or []
    if isinstance(train, dict):
        train = [train]
    if isinstance(test, dict):
        test = [test]
    return [*train, *test]


def _same_grid(left, right) -> bool:
    return tuple(map(tuple, left)) == tuple(map(tuple, right))


def _has_error(errors: list[str], fragment: str) -> bool:
    return any(fragment in error for error in errors)


def test_rule_pin_canonical_acceptance_and_python_mirror():
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash == "f5a9e05539e5"

    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]


@pytest.mark.parametrize(
    "profile",
    (
        "all_same_uniform",
        "triple_single_mixed",
        "pair_singletons_uniform",
        "two_pairs_mixed",
    ),
)
def test_scene_profile_override_is_exact_observable_and_lawful(profile: str):
    grid = GEN.generate(
        20261002,
        11,
        difficulty="hard",
        grid_h=19,
        grid_w=23,
        scene_profile=profile,
    )
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 19,
        "grid_w": 23,
        "scene_profile": profile,
    }
    assert GEN.rule_mirror(grid) != grid


def test_every_four_sample_window_refutes_declared_canonical_shortcuts():
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "move_only_modal_object_color",
        "move_repeated_blocks_by_one_global_size",
    }
    assert GEN.LESSON_COMPETITORS == GEN.CANONICAL_SHORTCUTS

    for start in range(len(GEN.SCENE_PROFILES)):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(911, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(
            911, start + GEN.EXAMPLES_NEEDED, difficulty="medium"
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(
                not _same_grid(rival(pair["input"]), pair["output"])
                for pair in demos
            ), (start, name)


def test_canonical_shortcuts_really_fit_all_canonical_demonstrations():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert rival(pair["input"]) == pair["output"], name


def test_generated_witnesses_force_the_two_core_disagreements():
    modal_grid = GEN.generate(
        71,
        0,
        grid_h=15,
        grid_w=17,
        scene_profile="two_pairs_mixed",
    )
    assert GEN.SEMANTIC_WITNESSES["two_repeated_colors"](modal_grid)
    assert (
        GEN.CANONICAL_SHORTCUTS["move_only_modal_object_color"](modal_grid)
        != GEN.rule_mirror(modal_grid)
    )

    size_grid = GEN.generate(
        73,
        0,
        grid_h=17,
        grid_w=19,
        scene_profile="triple_single_mixed",
    )
    assert GEN.SEMANTIC_WITNESSES["repeated_blocks_have_unequal_sizes"](
        size_grid
    )
    assert (
        GEN.CANONICAL_SHORTCUTS["move_repeated_blocks_by_one_global_size"](
            size_grid
        )
        != GEN.rule_mirror(size_grid)
    )


def test_self_check_rejects_structural_impostors():
    base = GEN.generate(
        301,
        0,
        grid_h=17,
        grid_w=19,
        scene_profile="pair_singletons_uniform",
    )
    assert GEN.self_check(base) == []

    missing_corner = copy.deepcopy(base)
    missing_corner[0][0] = 7
    assert _has_error(GEN.self_check(missing_corner), "solid square")

    interior_noise = copy.deepcopy(base)
    interior_noise[len(base) // 2][len(base[0]) // 2] = 6
    assert _has_error(GEN.self_check(interior_noise), "exactly four")

    all_unique = [[7] * 11 for _ in range(11)]
    for color, (row, col) in enumerate(
        ((0, 0), (0, 10), (10, 0), (10, 10)), start=1
    ):
        all_unique[row][col] = color
    assert _has_error(GEN.self_check(all_unique), "at least one repeated")

    wrong_background = [[0] * 11 for _ in range(11)]
    wrong_background[0][0] = wrong_background[0][10] = 2
    wrong_background[10][0] = wrong_background[10][10] = 3
    assert _has_error(GEN.self_check(wrong_background), "background must be 7")


def test_generate_rejects_unknown_or_invalid_overrides_and_is_rng_pure():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis="ignored")
    with pytest.raises(ValueError, match="scene_profile"):
        GEN.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(0, 0, grid_h=6)

    random.seed(123456)
    before = random.getstate()
    left = GEN.generate(44, 5, difficulty="medium")
    after = random.getstate()
    right = GEN.generate(44, 5, difficulty="medium")
    assert before == after
    assert left == right
    assert left is not right
    assert all(lrow is not rrow for lrow, rrow in zip(left, right))
    left[0][0] = 9
    assert left != right


def test_selected_racket_authority_is_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    authority_path = (
        ROOT
        / "shared/data/base/solutions/training/22208ba4__2692a3e47a66.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == canonical


def _profile_floor_seed(band: str, index: int) -> int:
    return int(
        hashlib.sha256(
            f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
        ).hexdigest()[:12],
        16,
    )


def test_schedule_profile_is_public_and_matches_default_draws():
    for sample_index in range(12):
        expected = GEN.SCENE_PROFILES[sample_index % len(GEN.SCENE_PROFILES)]
        assert GEN.schedule_profile(991, sample_index, difficulty="hard") == expected
        grid = GEN.generate(991, sample_index, difficulty="hard")
        assert GEN.observe_overrides(grid)["scene_profile"] == expected


def test_pinned_profile_floor_has_at_least_five_percent_exact_support():
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({cell for row in pair["input"] for cell in row}),
        )
        for pair in _canonical_pairs()
    }
    hits = []
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({cell for row in grid for cell in row}),
            )
            if profile in canonical_profiles:
                hits.append((band, index, sample_index, profile))
    assert len(hits) >= 3, hits


def test_workspace_shortcut_probe_is_replayable_and_complete():
    probe_path = ROOT / f"generators/{TASK_ID}/workspace/probe_shortcuts.py"
    probe_spec = importlib.util.spec_from_file_location(
        f"probe_{TASK_ID}", probe_path
    )
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.build_report(seed=71, start_index=0, difficulty="medium")
    assert report["task_id"] == TASK_ID
    assert report["generator_sha256"] == hashlib.sha256(
        (ROOT / f"generators/{TASK_ID}/generator.py").read_bytes()
    ).hexdigest()
    assert report["canonical_pairs"] == 5
    assert all(
        item["fits_all_canonical_pairs"]
        for item in report["canonical_shortcuts"].values()
    )
    assert all(item["rival_disagrees"] for item in report["witnesses"].values())
    assert report["cyclic_lesson_windows"] == {
        "checked": len(GEN.SCENE_PROFILES),
        "surviving_competitors": {},
    }
