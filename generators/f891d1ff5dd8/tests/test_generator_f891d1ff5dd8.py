"""Focused regressions for the reviewed f891d1ff5dd8 generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest


TASK_ID = "f891d1ff5dd8"
HERE = Path(__file__).resolve()
ROOT_CANDIDATES = [HERE.parents[3] / "shared" / "runtime", HERE.parents[4] / "shared" / "runtime", HERE.parents[3]]
for candidate in ROOT_CANDIDATES:
    if (candidate / "reviewer_support.py").is_file() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
        break

from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    f"reviewed_{TASK_ID}", HERE.parents[1] / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
ROOT = find_root(__file__)


def _canonical_source() -> str:
    sources = set()
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            sources.add(row["program_solution"])
    assert len(sources) == 1
    return sources.pop()


def _data_path(relative: str) -> Path:
    for prefix in (ROOT / "shared" / "data", ROOT / "data"):
        path = prefix / relative
        if path.is_file():
            return path
    raise FileNotFoundError(relative)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _object_count(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    objects = 0
    while remaining:
        objects += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return objects


def test_rule_pin_canonical_pairs_and_selected_authority_are_exact():
    source = _canonical_source()
    assert GEN.VERSION == "2.1.0"
    assert GEN.RULE_HASH == "9a77eb6a5412"
    assert GEN.RULE_HASH == _normalized_hash(source)

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

    selected = json.loads(
        _data_path("base/solutions/training/bd4472b8__f891d1ff5dd8.json").read_text(
            encoding="utf-8"
        )
    )["racket_target"]
    assert selected["target_code"] == source
    assert selected["raw_code"] == source


def test_four_slot_schedule_teaches_all_declared_shortcuts_under_all_rotations():
    assert GEN.EXAMPLES_NEEDED == 3
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                GEN.generate(10_000 + start, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            assert [GEN.schedule_profile(0, start + offset) for offset in range(4)] == [
                (start + offset) % 4 for offset in range(4)
            ]
            pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        difficulty,
                        start,
                        query_index,
                        name,
                    )


def test_two_cycle_canonical_shortcut_is_declared_and_refuted_in_every_rotation():
    assert "two_cycles_only" in GEN.LESSON_COMPETITORS
    rival = GEN.LESSON_COMPETITORS["two_cycles_only"]

    # This rival is plausible because it agrees with every original ARC pair:
    # all canonical bodies contain exactly two complete header cycles.
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert rival(pair["input"]) == pair["output"]

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 20, 91, 2026):
            grids = [
                GEN.generate(seed, sample_index, difficulty=difficulty)
                for sample_index in range(4)
            ]
            pairs = [
                {"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids
            ]
            for query_index in range(4):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, seed, query_index)
                assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_long_body_schedule_roles_always_extend_beyond_two_header_cycles():
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(32):
            for sample_index in (1, 3):
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                height, width = len(grid), len(grid[0])
                assert height - 2 > 2 * width, (
                    difficulty,
                    seed,
                    sample_index,
                    height,
                    width,
                )


def test_default_schedule_has_exact_profiles_low_object_count_and_all_witnesses():
    canonical_profiles = {(6, 2, 4), (8, 3, 5), (10, 4, 6), (12, 5, 7)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(20_000 + index, index, difficulty=difficulty) for index in range(20)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        observed_profiles = {
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        }
        assert observed_profiles & canonical_profiles
        assert max(_object_count(grid) for grid in grids) <= 10
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (difficulty, name)


def test_override_boundaries_round_trip_and_unknown_requests_fail_loudly():
    cases = (
        {"grid_h": 3, "grid_w": 2, "body_pattern": "blank"},
        {"grid_h": 18, "grid_w": 8, "body_pattern": "rectangle"},
        {"grid_h": 10, "grid_w": 5, "body_pattern": "rectangle"},
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(30_000 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested

    for invalid in (
        {"bogus_axis": 1},
        {"grid_h": 2},
        {"grid_h": True},
        {"grid_w": 9},
        {"body_pattern": "noise"},
    ):
        with pytest.raises((TypeError, ValueError), match="override|grid_|body_pattern|integer"):
            GEN.generate(1, 2, **invalid)


def test_generate_rejects_malformed_call_control_scalars():
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError), match="seed"):
            GEN.generate(bad_seed, 0, difficulty="easy")

    for bad_index in (True, False, 1.0, 1.75, -1):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            GEN.generate(1, bad_index, difficulty="easy")

    for bad_difficulty in (True, False, 0, 1.0, "__invalid_difficulty__"):
        with pytest.raises((TypeError, ValueError), match="difficulty"):
            GEN.generate(1, 0, difficulty=bad_difficulty)


def test_self_check_rejects_destructive_and_minimal_impostor_mutations():
    grid = GEN.generate(40_001, 3, difficulty="medium")
    assert GEN.self_check(grid) == []

    fixtures: dict[str, list[list[int]]] = {
        "blank": [[0 for _ in row] for row in grid],
        "all_one_color": [[1 for _ in row] for row in grid],
        "duplicate_header": copy.deepcopy(grid),
        "absent_color": copy.deepcopy(grid),
        "body_hole": copy.deepcopy(grid),
        "ragged": copy.deepcopy(grid),
        "boolean": copy.deepcopy(grid),
    }
    fixtures["duplicate_header"][-1] = fixtures["duplicate_header"][0][:]
    fixtures["absent_color"][0][0] = 0
    body_cells = [
        (r, c)
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    ]
    assert body_cells
    r, c = body_cells[len(body_cells) // 2]
    fixtures["body_hole"][r][c] = 0
    fixtures["ragged"][0].pop()
    fixtures["boolean"][0][0] = True

    for name, malformed in fixtures.items():
        assert GEN.self_check(malformed), name


def test_declared_witnesses_are_real_counterexamples_to_named_rivals():
    grids = [GEN.generate(50_000 + index, index, difficulty="medium") for index in range(12)]
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert matching, witness_name
        assert set(rival_names) <= set(GEN.SEMANTIC_RIVALS)
        for grid in matching:
            truth = GEN.rule_mirror(grid)
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261006)
    state = random.getstate()
    first = GEN.generate(60_001, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(60_001, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
