from __future__ import annotations

import copy
import hashlib
import importlib
import json
import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "084de7b050a1"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parent.parent


def canonical_rule_source(task_id):
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{task_id}: no canonical program_solution")


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_canonical_pairs_are_owned_and_mirror_matches_authority_examples():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 10  # two canonical source rows, five train/test pairs each
    for pair in pairs:
        assert MOD.self_check(pair["input"]) == []
        assert MOD.strict_canonical_like(pair["input"]) == []
        assert MOD._mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_selected_task_local_sources_are_pinned():
    source = canonical_rule_source(TASK_ID)
    assert normalized_rule_hash(source) == MOD.RULE_HASH == "e059ff61aa1e"
    for rel in (
        "base/solutions/augmented/963f59bc__d6513b2b494d.json",
        "base/solutions/training/963f59bc__084de7b050a1.json",
    ):
        payload = json.loads((DATA_ROOT / rel).read_text())
        assert normalized_rule_hash(
            payload["racket_target"]["target_code"]
        ) == MOD.RULE_HASH
        # raw_code is intentionally archival; execution parity is checked by
        # check_task_authority_sync.py rather than forcing archival text equal.
        assert payload["racket_target"]["raw_code"]


def test_every_five_default_draws_cover_profiles_and_decisive_semantics():
    required = {
        "core_connected": {"vertical_branch", "horizontal_branch"},
        "global_disconnected": {"global_multi_component_reflection"},
        "priority_first_match": {
            "column_priority_when_both_aligned",
            "first_matching_anchor_not_nearest",
        },
        "inert_decoy": {"unaligned_dot_is_inert"},
        "clip_overlap": {"cellwise_boundary_clipping", "later_dot_wins_overlap"},
    }
    for band in ("easy", "medium", "hard"):
        for seed in (3, 17, 101):
            start = seed % 13
            profiles = []
            for sample_index in range(start, start + 5):
                grid = MOD.generate(seed, sample_index, difficulty=band)
                profile = MOD.schedule_profile(seed, sample_index, band)
                profiles.append(profile)
                fired = {
                    name
                    for name, predicate in MOD.SEMANTIC_WITNESSES.items()
                    if predicate(grid)
                }
                assert required[profile] <= fired
            assert set(profiles) == set(MOD.SCHEDULE_PROFILES)


def test_named_rival_claims_have_task_local_counterexamples():
    seen = set()
    for sample_index in range(25):
        grid = MOD.generate(71, sample_index, difficulty="medium")
        truth = MOD._mirror(grid)
        for witness, rival_names in MOD.WITNESS_RIVALS.items():
            if not MOD.SEMANTIC_WITNESSES[witness](grid):
                continue
            assert any(MOD.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)
            seen.add(witness)
    assert seen == set(MOD.WITNESS_RIVALS)


def test_override_boundaries_round_trip_and_unknown_keys_fail():
    boundaries = {
        "grid_h": (11, 16),
        "grid_w": (11, 16),
        "n_dots": (1, 4),
        "blue_size": (6, 10),
    }
    for band in ("easy", "medium", "hard"):
        for axis, values in boundaries.items():
            for value in values:
                grid = MOD.generate(211, 7, difficulty=band, **{axis: value})
                assert MOD.self_check(grid) == []
                assert MOD.observe_overrides(grid)[axis] == value
    with pytest.raises(ValueError, match="unknown override axis"):
        MOD.generate(1, 2, typo_axis=123)


def test_self_check_rejects_targeted_destructive_mutations():
    grid = MOD.generate(19, 3, difficulty="medium")  # inert_decoy => two dots

    no_blue = [[0 if value == 1 else value for value in row] for row in grid]
    assert MOD.self_check(no_blue)

    no_dots = [[0 if value not in (0, 1) else value for value in row] for row in grid]
    assert MOD.self_check(no_dots)

    duplicate_dot_color = copy.deepcopy(grid)
    dots = MOD._grid_roles(duplicate_dot_color)[1]
    assert len(dots) >= 2
    r0, c0, color0 = dots[0]
    r1, c1, _ = dots[1]
    duplicate_dot_color[r1][c1] = color0
    assert any("distinct singleton" in reason for reason in MOD.self_check(duplicate_dot_color))

    ragged = copy.deepcopy(grid)
    ragged[0] = ragged[0][:-1]
    assert MOD.self_check(ragged)


def test_deterministic_and_fresh_returns():
    first = MOD.generate(31337, 29, difficulty="hard")
    second = MOD.generate(31337, 29, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty", "overrides"),
    [
        (True, 0, None, {}),
        (1.5, 0, None, {}),
        ("1", 0, None, {}),
        (1, True, None, {}),
        (1, -1, None, {}),
        (1, 0, True, {}),
        (1, 0, 1, {}),
        (1, 0, 1.5, {}),
        (1, 0, "__invalid_difficulty__", {}),
        *[
            (1, 0, "medium", {axis: value})
            for axis in ("grid_h", "grid_w", "n_dots", "blue_size")
            for value in (True, 12.5, "12")
        ],
    ],
)
def test_generate_rejects_malformed_scalar_arguments(
    seed, sample_index, difficulty, overrides
):
    with pytest.raises((TypeError, ValueError)):
        MOD.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )


def test_axis_priority_parametric_prototype_is_source_bound_and_distinct():
    import importlib.util

    path = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "axis_priority.py"
    spec = importlib.util.spec_from_file_location("axis_priority_prototype", path)
    assert spec is not None and spec.loader is not None
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)

    canonical = prototype.racket_source("column_first", root=ROOT)
    alternative = prototype.racket_source("row_first", root=ROOT)
    assert prototype.normalized_hash(canonical) == MOD.RULE_HASH
    assert prototype.normalized_hash(alternative) != MOD.RULE_HASH

    witness = MOD.generate(17, 2, difficulty="medium")
    assert MOD.SEMANTIC_WITNESSES["column_priority_when_both_aligned"](witness)
    assert MOD._mirror(witness) != MOD._mirror_variant(witness, row_priority=True)
    with pytest.raises(ValueError, match="axis_priority"):
        prototype.racket_source("diagonal_first", root=ROOT)
