from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b5f36515995c import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "data/base/solutions/banks/edd0efb19ea0/H90__b5f36515995c.json"


def _axis_values(name):
    spec = gen.AXES[name]
    if spec["type"] == "int":
        lo, hi = map(int, spec["valid"].split(".."))
        return (lo, hi)
    return tuple(spec["valid"].split("|"))


def _canonical_program():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical source missing")


def _comment_stripped_normalized(source):
    lines = [line.split(";;", 1)[0] for line in source.splitlines()]
    return " ".join("\n".join(lines).split())


def _normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_sources_and_all_canonical_pairs_are_pinned():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    canonical = _canonical_program()
    assert gen.RULE_HASH == _normalized_rule_hash(canonical) == "3eba0ba7c07d"

    task_local = json.loads(BASE_SOURCE.read_text())
    racket = task_local["racket_target"]
    assert racket["target_code"] == canonical
    assert "predecessor links during BFS" in racket["target_code"]
    assert _comment_stripped_normalized(racket["raw_code"]) == _comment_stripped_normalized(canonical)
    assert racket["target_code_role"] == "selected_task_rule"
    assert racket["raw_code_role"] == "archival_executable_source"

    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_global_rng_pure_and_band_specific():
    random.seed(20260727)
    before = random.getstate()
    for band in ("easy", "medium", "hard"):
        first = gen.generate(814, 7, difficulty=band)
        middle = random.getstate()
        second = gen.generate(814, 7, difficulty=band)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first) == []
        assert before == middle == random.getstate()
        first[0][0] = 9 if first[0][0] != 9 else 0
        assert gen.generate(814, 7, difficulty=band) == second
    draws = [gen.generate(814, 7, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({json.dumps(grid) for grid in draws}) >= 2


def test_every_axis_boundary_is_exact_and_invalid_overrides_fail_loudly():
    for axis in gen.AXES:
        for value in _axis_values(axis):
            grid = gen.generate(44, 16, difficulty="hard", **{axis: value})
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid)[axis] == value

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", misspelled_axis=1)
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(0, 0, difficulty="easy", n_pairs=3, n_gaps=2)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_all_sliding_three_demo_windows_identify_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(15):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(3000 + start, index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(3000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert {gen.observe_overrides(p["input"])["routing_profile"] for p in demos} == set(gen.ROUTING_PROFILES)
            assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_four_targeted_impostors():
    valid = gen.generate(993, 1, difficulty="medium")

    all_background = [[0 for _ in row] for row in valid]
    assert any("wall column" in reason for reason in gen.self_check(all_background))

    missing_wall = copy.deepcopy(valid)
    wall_col = len(missing_wall[0]) // 2
    for row in missing_wall:
        row[wall_col] = 0
    assert any("wall column" in reason for reason in gen.self_check(missing_wall))

    singleton = copy.deepcopy(valid)
    endpoint_color = next(value for row in singleton for value in row if value not in (0, 8))
    removed = False
    for row in singleton:
        for col, value in enumerate(row):
            if value == endpoint_color:
                row[col] = 0
                removed = True
                break
        if removed:
            break
    assert any("exactly 2" in reason for reason in gen.self_check(singleton))

    closed_gap = copy.deepcopy(valid)
    for row in range(len(closed_gap)):
        if closed_gap[row][wall_col] == 0:
            closed_gap[row][wall_col] = 8
    assert any("1..3 gaps" in reason for reason in gen.self_check(closed_gap))


def test_rivals_are_killed_by_named_generated_witnesses():
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(90):
        grid = gen.generate(7000 + index, index, difficulty="hard")
        truth = gen.rule_mirror(grid)
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            hits[witness_name] += 1
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in hits.values()), hits


def test_negative_recombination_is_rejected_by_distribution_checker():
    grid = gen.generate(1901, 2, difficulty="hard")
    recombined = copy.deepcopy(grid)
    existing = {value for row in recombined for value in row}
    replacement = next(value for value in range(1, 10) if value not in existing and value != 8)
    old = next(value for value in existing if value not in (0, 8))
    changed = False
    for row in recombined:
        for col, value in enumerate(row):
            if value == old:
                row[col] = replacement
                changed = True
                break
        if changed:
            break
    assert replacement not in {value for row in grid for value in row}
    reasons = gen.self_check(recombined)
    assert any("appears 1 times" in reason for reason in reasons)
    assert any(f"color {old} appears 1 times" in reason for reason in reasons)
