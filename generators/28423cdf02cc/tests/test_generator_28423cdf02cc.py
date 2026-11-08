"""Focused semantic regressions for generator 28423cdf02cc."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "28423cdf02cc"
ROOT = find_root(__file__)


def _base_path() -> Path:
    relative = Path("data/base/solutions/training/363442ee__28423cdf02cc.json")
    for prefix in (Path(), Path("shared")):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


BASE_PATH = _base_path()
MOD = importlib.import_module(
    "puzzle_generators.per_puzzle.28423cdf02cc.generator"
)


def _canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_active_authorities_are_exact_and_archival_source_is_preserved() -> None:
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text())
    assert MOD.VERSION == "3.1.1"
    assert MOD.RULE_HASH == _normalized_rule_hash(canonical)
    assert base["racket_target"]["target_code"] == canonical
    assert hashlib.sha256(base["racket_target"]["raw_code"].encode()).hexdigest() == (
        "63b41fa0b18703287defdaec215a69e9f3c15fb9e0db6764752ac135ff585677"
    )
    assert base["racket_target"]["canonicalization_status"] == (
        "synchronized_to_canonical"
    )


def test_every_canonical_pair_is_accepted_and_python_mirror_is_exact() -> None:
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for index, pair in enumerate(pairs):
        source = copy.deepcopy(pair["input"])
        analysis = MOD._analyze(source)
        assert analysis["errors"] == [], index
        assert analysis["facts"]["canonical_profile"] == index
        assert MOD.self_check(source) == []
        assert MOD.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_exact_override_boundaries_survive_every_difficulty_band() -> None:
    cases = (
        {"grid_h": 9, "grid_w": 13, "n_dots": 3, "palette_size": 3},
        {"grid_h": 16, "grid_w": 20, "n_dots": 6, "palette_size": 5},
        {"grid_h": 9, "grid_w": 20, "n_dots": 6, "palette_size": 3},
        {"grid_h": 16, "grid_w": 13, "n_dots": 3, "palette_size": 5},
    )
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for case in cases:
                grid = MOD.generate(
                    10_000 + seed,
                    seed * 31 + 7,
                    difficulty=band,
                    **case,
                )
                assert MOD.self_check(grid) == []
                assert MOD.observe_overrides(grid) == case


def test_defaults_are_deterministic_fresh_and_global_rng_isolated() -> None:
    state = random.getstate()
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            first = MOD.generate(seed, seed * 17 + 5, difficulty=band)
            second = MOD.generate(seed, seed * 17 + 5, difficulty=band)
            pristine = copy.deepcopy(first)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            first[0][0] = (first[0][0] + 1) % 10
            assert MOD.generate(seed, seed * 17 + 5, difficulty=band) == pristine
            assert random.getstate() == state


def test_default_distribution_anchors_canonical_manifold_and_generalizes() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        inputs = set()
        outputs = set()
        marker_counts = set()
        palette_sizes = set()
        edge_roles = Counter()
        for seed in range(600):
            grid = MOD.generate(
                100_000 * (band_index + 1) + seed,
                seed * 23 + 11,
                difficulty=band,
            )
            analysis = MOD._analyze(grid)
            assert analysis["errors"] == []
            facts = analysis["facts"]
            counts[facts["layout_family"]] += 1
            counts["strict_canonical"] += facts["canonical_profile"] is not None
            marker_counts.add(facts["n_dots"])
            palette_sizes.add(facts["palette_size"])
            for r, c in facts["markers"]:
                edge_roles["top"] += r == 1
                edge_roles["bottom"] += r == len(grid) - 2
                edge_roles["left"] += c == 5
                edge_roles["right"] += c == len(grid[0]) - 2
            inputs.add(tuple(map(tuple, grid)))
            output = MOD.rule_mirror(grid)
            outputs.add(tuple(map(tuple, output)))
            assert output != grid
        assert counts["strict_canonical"] >= 180
        assert counts["canonical_lattice"] >= 180
        assert counts["scattered"] >= 35
        assert marker_counts >= {3, 4, 5, 6}
        assert palette_sizes == {3, 4, 5}
        assert all(edge_roles[role] > 0 for role in edge_roles)
        assert len(inputs) >= 500
        assert len(outputs) >= 500


def test_self_check_rejects_task_specific_impostors() -> None:
    fixtures = dict(MOD.mutation_fixtures())
    assert len(fixtures) >= 5
    for name, grid in fixtures.items():
        assert MOD.self_check(grid), name

    valid = MOD.generate(
        777,
        29,
        difficulty="medium",
        grid_h=9,
        grid_w=13,
        n_dots=5,
        palette_size=4,
    )
    facts = MOD._analyze(valid)["facts"]

    symmetric_template = copy.deepcopy(valid)
    symmetric_template_values = (
        (2, 3, 2),
        (4, 6, 4),
        (2, 3, 2),
    )
    for r in range(3):
        for c in range(3):
            symmetric_template[r][c] = symmetric_template_values[r][c]

    one_row = copy.deepcopy(valid)
    for r, c in facts["markers"]:
        one_row[r][c] = 0
    for c in (5, 8, 11):
        one_row[4][c] = 1

    for name, grid in {
        "dihedrally_ambiguous_template": symmetric_template,
        "markers_only_one_row": one_row,
    }.items():
        assert MOD.self_check(grid), name


def test_negative_recombination_is_rejected_even_when_oracle_can_run() -> None:
    grid = MOD.generate(901, 37, difficulty="medium")
    recombined = copy.deepcopy(grid)
    marker = MOD._analyze(grid)["facts"]["markers"][0]
    absent = next(color for color in MOD._TEMPLATE_COLORS if color not in {
        value for row in grid for value in row
    })
    recombined[marker[0]][marker[1]] = absent
    errors = MOD.self_check(recombined)
    assert errors
    # The rule is total on this recombination; that does not make it a lawful
    # lesson because the replaced cue is absent from the remaining scene.
    out = MOD.rule_mirror(recombined)
    r, c = marker
    assert len(out) == len(recombined)
    assert all(len(a) == len(b) for a, b in zip(out, recombined))
    # The removed cue must not trigger a stamp; unrelated blue markers may still do so.
    assert [row[c - 1 : c + 2] for row in out[r - 1 : r + 2]] == [
        row[c - 1 : c + 2] for row in recombined[r - 1 : r + 2]
    ]


def test_invalid_calls_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MOD.generate(1, 2, mystery_axis=3)
    with pytest.raises(ValueError, match="outside"):
        MOD.generate(1, 2, grid_h=8)
    with pytest.raises(ValueError, match="outside"):
        MOD.generate(1, 2, n_dots=7)
    with pytest.raises(ValueError, match="difficulty"):
        MOD.generate(1, 2, difficulty="expert")



def _labeled_pair(grid: list[list[int]]) -> dict:
    source = copy.deepcopy(grid)
    return {"input": source, "output": MOD.rule_mirror(source)}


def _is_canonical_lattice_marker(point: tuple[int, int]) -> bool:
    r, c = point
    return (r - 1) % 3 == 0 and (c - 5) % 3 == 0


def test_declares_a_schedule_that_prevents_all_canonical_demo_windows() -> None:
    assert MOD.LESSON_SCHEDULE_PERIOD == 5
    assert tuple(MOD.SCHEDULE_PROFILES) == (
        "canonical_profile",
        "anti_lattice",
    )
    profiles = [
        MOD.schedule_profile(123, index, difficulty="medium")
        for index in range(MOD.LESSON_SCHEDULE_PERIOD)
    ]
    assert profiles == [
        "canonical_profile",
        "canonical_profile",
        "anti_lattice",
        "anti_lattice",
        "anti_lattice",
    ]
    cyclic = profiles * 3
    for start in range(MOD.LESSON_SCHEDULE_PERIOD):
        assert "anti_lattice" in cyclic[start : start + MOD.EXAMPLES_NEEDED]
        assert cyclic[start : start + MOD.EXAMPLES_NEEDED + 1].count(
            "anti_lattice"
        ) >= 2


def test_default_schedule_realizes_its_declared_profiles() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(MOD.LESSON_SCHEDULE_PERIOD):
            grid = MOD.generate(700_000 + start, start, difficulty=band)
            facts = MOD._analyze(grid)["facts"]
            profile = MOD.schedule_profile(700_000 + start, start, difficulty=band)
            if profile == "canonical_profile":
                assert facts["canonical_profile"] is not None
            else:
                assert facts["canonical_profile"] is None
                assert any(
                    not _is_canonical_lattice_marker(marker)
                    for marker in facts["markers"]
                )


def test_fixed_lattice_shortcut_fits_every_canonical_pair() -> None:
    rival = MOD.CANONICAL_SHORTCUTS["fixed_canonical_lattice_only"]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_every_scheduled_lesson_and_query_rotation_refutes_all_rivals() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(MOD.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _labeled_pair(
                    MOD.generate(
                        800_000 + 10_000 * band_index + start,
                        start + offset,
                        difficulty=band,
                    )
                )
                for offset in range(MOD.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(pairs)):
                query = pairs[query_index]
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                assert MOD.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )


def test_lesson_hook_reports_the_reproduced_fixed_lattice_ambiguity() -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    demos = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in pairs[:3]
    ]
    query_grid = MOD.generate(912_345, 2, difficulty="medium")
    facts = MOD._analyze(query_grid)["facts"]
    assert any(
        not _is_canonical_lattice_marker(marker) for marker in facts["markers"]
    )
    reasons = MOD.lesson_identifiable(demos, _labeled_pair(query_grid))
    assert any("fixed_canonical_lattice_only" in reason for reason in reasons)


def test_semantic_witness_claims_are_executable_counterexamples() -> None:
    seen = {name: 0 for name in MOD.SEMANTIC_WITNESSES}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(15):
            grid = MOD.generate(
                950_000 + band_index * 100 + sample_index,
                sample_index,
                difficulty=band,
            )
            expected = MOD.rule_mirror(grid)
            for witness_name, predicate in MOD.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    seen[witness_name] += 1
                    rival_names = MOD.WITNESS_RIVALS[witness_name]
                    assert any(
                        MOD.SEMANTIC_RIVALS[name](grid) != expected
                        for name in rival_names
                    ), witness_name
    assert all(count > 0 for count in seen.values()), seen


def test_strict_hook_accepts_exact_canonical_profiles_only() -> None:
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert MOD.strict_canonical_like(pair["input"]) == []
    generalized = MOD.generate(777_777, 2, difficulty="medium")
    assert MOD.strict_canonical_like(generalized)
