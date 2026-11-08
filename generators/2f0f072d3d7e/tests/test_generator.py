"""Focused regression tests for the reviewed 2f0f072d3d7e generator."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
probe_path = HERE.parents[1] / "workspace" / "review_probe.py"
if not probe_path.exists():
    import importlib

    gm = importlib.import_module(
        "puzzle_generators.per_puzzle.2f0f072d3d7e.generator"
    )
    probe_path = Path(gm.__file__).parent / "workspace" / "review_probe.py"
spec = importlib.util.spec_from_file_location("review_probe", probe_path)
probe = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(probe)
gen = probe.load_generator()


def test_rule_pin_and_exact_surface():
    assert getattr(gen, "RULE_HASH", None) == "5c71009c7048"
    assert set(gen.AXES) == {
        "panel_s", "n_candidates", "shape_size_a", "shape_size_c",
        "transform_code", "winner_rank",
    }


def test_unknown_axis_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(3, 4, typo_axis=1)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    requested = {
        "panel_s": 3,
        "n_candidates": 3,
        "shape_size_a": 6,
        "shape_size_c": 6,
        "transform_code": 4,
        "winner_rank": 2,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert probe.observed(grid) == requested
    assert gen._solve(grid) == probe.oracle(grid)


def test_only_declared_joint_incompatibility_is_rejected():
    with pytest.raises(ValueError, match="n_candidates.*winner_rank|winner_rank.*n_candidates"):
        gen.generate(1, 2, n_candidates=2, winner_rank=2)
    # Either control alone remains total and must not be silently clamped.
    assert gen.observe_overrides(gen.generate(1, 2, n_candidates=2))["n_candidates"] == 2
    assert gen.observe_overrides(gen.generate(1, 2, winner_rank=2))["winner_rank"] == 2


@pytest.mark.parametrize("axis,value", [
    ("panel_s", 2), ("panel_s", 5), ("panel_s", True),
    ("n_candidates", 1), ("n_candidates", 4),
    ("shape_size_a", 3), ("shape_size_a", 7),
    ("shape_size_c", 2), ("shape_size_c", 7),
    ("transform_code", -1), ("transform_code", 5),
    ("winner_rank", -1), ("winner_rank", 3),
    ("winner_rank", "1"),
])
def test_invalid_controls_are_rejected(axis, value):
    with pytest.raises(ValueError):
        gen.generate(1, 2, **{axis: value})


def test_entire_legal_joint_domain_is_constructive_and_exact():
    sample = 0
    for side, n, size_a, size_c, code, rank in itertools.product(
        range(3, 5), range(2, 4), range(4, 7), range(3, 7), range(5), range(3)
    ):
        requested = {
            "panel_s": side,
            "n_candidates": n,
            "shape_size_a": size_a,
            "shape_size_c": size_c,
            "transform_code": code,
            "winner_rank": rank,
        }
        if n == 2 and rank == 2:
            with pytest.raises(ValueError):
                gen.generate(971, sample, difficulty="hard", **requested)
        else:
            grid = gen.generate(971, sample, difficulty="hard", **requested)
            assert gen.self_check(grid) == [], requested
            assert gen.observe_overrides(grid) == requested
            assert probe.observed(grid) == requested
            assert gen._solve(grid) == probe.oracle(grid)
        sample += 1
    assert sample == 720


def test_canonical_inputs_are_owned_and_independent_oracle_is_correct():
    for pair in probe.canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert probe.oracle(pair["input"]) == pair["output"]
        assert gen._solve(pair["input"]) == pair["output"]


@pytest.mark.parametrize("bad", [
    None, [], [[]], [[0], [0, 1]], [[True] * 29 for _ in range(4)],
    [[0] * 29 for _ in range(4)],
])
def test_validator_rejects_malformed_or_semantically_empty_grids(bad):
    assert gen.self_check(bad)


def test_canonical_shortcut_declarations_are_truthful():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in probe.canonical_pairs()), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_six_profile_block_survives_every_rotated_query(band):
    for seed in range(4):
        for start in range(6):
            pairs = []
            for offset in range(6):
                grid = gen.generate(seed, start + offset, difficulty=band)
                assert gen.self_check(grid) == []
                pairs.append({"input": grid, "output": probe.oracle(grid)})
            report = probe.cyclic_rivals(gen, pairs)
            assert report["ambiguities"] == [], (band, seed, start, report["ambiguities"][:1])
            assert all(row["windows"] == 6 for row in report["counts"].values())


def test_schedule_exercises_exact_transform_direction_rank_and_offset():
    rows = [gen.generate(711, i, difficulty="medium") for i in range(6)]
    observed = [probe.observed(grid) for grid in rows]
    assert sum(row["winner_rank"] > 0 for row in observed) >= 4
    assert sum(row["transform_code"] in (1, 3) for row in observed) >= 2
    assert sum(probe.oracle(grid) != probe.inverse_transform(grid) for grid in rows) >= 2
    assert sum(probe.oracle(grid) != probe.normalized_output(grid) for grid in rows) >= 2


def test_joint_semantic_witness_refutes_every_rival_twice_per_block():
    witness = gen.SEMANTIC_WITNESSES["joint_shortcut_counterexample"]
    grids = [gen.generate(919, i, difficulty="medium") for i in range(6)]
    firing = [grid for grid in grids if witness(grid)]
    assert len(firing) >= 2
    for grid in firing:
        answer = gen._solve(grid)
        assert all(rival(grid) != answer for rival in gen.SEMANTIC_RIVALS.values())


def test_difficulty_bands_change_default_geometry():
    grids = [gen.generate(313, 2, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in grids}) == 3
    assert all(gen.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_canonical_support(band):
    canonical = {
        (len(p["input"]), len(p["input"][0]), len({x for row in p["input"] for x in row}))
        for p in probe.canonical_pairs()
    }
    hits = 0
    for i in range(20):
        seed = int(hashlib.sha256(
            f"profile-floor:v1:2f0f072d3d7e:{band}:{i}".encode()
        ).hexdigest()[:12], 16)
        grid = gen.generate(seed, seed % 7919 + i, difficulty=band)
        hits += (
            len(grid), len(grid[0]), len({x for row in grid for x in row})
        ) in canonical
    assert hits >= 1


def _is_shifted(cells):
    return probe.normalize(cells) != tuple(sorted(cells))


def test_every_rotated_lesson_breaks_transform_code_as_winner_rank_proxy():
    """No five-demo view may leave candidate rank encoded by transform code."""
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(4):
            base_seed = 50_000 + 1_000 * band_index + seed
            for start in range(18):
                observations = [
                    probe.observed(gen.generate(base_seed, start + offset, difficulty=band))
                    for offset in range(6)
                ]
                for query_index in range(6):
                    ranks_by_code = {}
                    for index, row in enumerate(observations):
                        if index == query_index:
                            continue
                        ranks_by_code.setdefault(row["transform_code"], set()).add(
                            row["winner_rank"]
                        )
                    assert any(len(ranks) > 1 for ranks in ranks_by_code.values()), (
                        band, seed, start, query_index, observations
                    )


def test_transform_rank_lookup_is_an_executable_declared_rival_and_is_refuted():
    name = "fixed_transform_code_winner_rank"
    assert name in gen.SEMANTIC_RIVALS
    rival = gen.SEMANTIC_RIVALS[name]
    grids = [gen.generate(82_001, index, difficulty="medium") for index in range(18)]
    assert sum(rival(grid) != probe.oracle(grid) for grid in grids) >= 6


def test_candidate_translation_mode_is_not_a_winner_only_cue():
    """Within one puzzle, winner and decoys share top-left/shifted placement mode."""
    shifted_winners = 0
    checked = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(18):
            grid = gen.generate(91_000 + band_index, sample_index, difficulty=band)
            _panels, supports, _code, _target, hits = probe.parsed(grid)
            candidate_supports = supports[3:]
            statuses = [_is_shifted(cells) for cells in candidate_supports]
            assert len(set(statuses)) == 1, (band, sample_index, statuses, hits)
            shifted_winners += int(statuses[hits[0]])
            checked += 1
    assert shifted_winners >= checked // 3


def test_lesson_hook_rejects_no_rotated_five_demo_view():
    for start in range(18):
        pairs = []
        for offset in range(6):
            grid = gen.generate(93_001, start + offset, difficulty="hard")
            pairs.append({"input": grid, "output": probe.oracle(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)
