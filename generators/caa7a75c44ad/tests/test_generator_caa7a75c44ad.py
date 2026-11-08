from __future__ import annotations

import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "caa7a75c44ad"
GEN_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"test_gen_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row():
    for line in (ROOT / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _pairs(generator, seed: int):
    pairs = []
    for sample_index in range(4):
        grid = generator.generate(seed, sample_index)
        pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
    return pairs


def test_canonical_pairs_hash_and_python_mirror_are_exact():
    generator = _load_generator()
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert generator.RULE_HASH == expected_hash == "6877fd432f60"

    for split in ("train", "test"):
        for pair in row[split]:
            before = [r[:] for r in pair["input"]]
            assert generator.self_check(pair["input"]) == []
            assert generator.strict_canonical_like(pair["input"]) == []
            assert generator.rule_mirror(pair["input"]) == pair["output"]
            assert pair["input"] == before


def test_four_sample_lesson_schedule_includes_both_negative_controls():
    generator = _load_generator()
    pairs = _pairs(generator, 4317)
    observations = [generator.observe_overrides(pair["input"]) for pair in pairs]

    assert generator.strict_canonical_like(pairs[0]["input"]) == []
    assert observations[1]["distractor_mode"] == "blocked_span"
    assert observations[1]["color_mode"] == "reused"
    assert observations[2]["distractor_mode"] == "mixed_endpoints"
    assert generator.strict_canonical_like(pairs[3]["input"]) == []
    assert all(pair["input"] != pair["output"] for pair in pairs)
    assert generator.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_every_declared_axis_boundary_is_exact_in_every_band():
    generator = _load_generator()
    values = {
        "grid_h": (7, 12),
        "grid_w": (8, 11),
        "span_count": (2, 5),
        "gap_profile": ("short", "mixed", "long"),
        "edge_profile": ("interior", "top", "bottom", "both"),
        "color_mode": ("distinct", "reused"),
        "distractor_mode": ("none", "mixed_endpoints", "blocked_span"),
    }
    for difficulty in ("easy", "medium", "hard"):
        for axis, axis_values in values.items():
            for index, value in enumerate(axis_values):
                grid = generator.generate(
                    8000 + index,
                    index,
                    difficulty=difficulty,
                    **{axis: value},
                )
                observed = generator.observe_overrides(grid)
                assert observed[axis] == value
                assert generator.self_check(
                    grid, difficulty=difficulty, meta={"overrides": {axis: value}}
                ) == []

    requested = {
        "grid_h": 12,
        "grid_w": 11,
        "span_count": 5,
        "gap_profile": "long",
        "edge_profile": "both",
        "color_mode": "reused",
        "distractor_mode": "blocked_span",
    }
    grid = generator.generate(991, 6, difficulty="easy", **requested)
    assert generator.observe_overrides(grid) == requested


def test_self_check_rejects_targeted_impostors():
    generator = _load_generator()
    good = generator.generate(72, 0)
    assert generator.self_check(good) == []

    ragged = [row[:] for row in good]
    ragged[0].pop()
    assert generator.self_check(ragged)

    invalid_color = [row[:] for row in good]
    invalid_color[0][0] = 10
    assert generator.self_check(invalid_color)

    all_background = [[0 for _ in row] for row in good]
    assert generator.self_check(all_background)

    single_endpoint = [row[:] for row in good]
    span = generator._analyze(single_endpoint)["active_spans"][0]
    single_endpoint[span["r2"]][span["col"]] = 0
    assert generator.self_check(single_endpoint)

    adjacent_pair = [row[:] for row in good]
    span = generator._analyze(adjacent_pair)["active_spans"][0]
    adjacent_pair[span["r2"]][span["col"]] = 0
    adjacent_pair[span["r1"] + 1][span["col"]] = span["color"]
    assert generator.self_check(adjacent_pair)

    two_distractors = [row[:] for row in good]
    spans = generator._analyze(two_distractors)["active_spans"][:2]
    used = {value for row in two_distractors for value in row}
    replacements = [value for value in range(1, 10) if value not in used][:2]
    for span, replacement in zip(spans, replacements):
        two_distractors[span["r2"]][span["col"]] = replacement
    assert generator.self_check(two_distractors)

    malformed_three_entry = [row[:] for row in good]
    span = generator._analyze(malformed_three_entry)["active_spans"][0]
    midpoint = span["r1"] + 1
    malformed_three_entry[midpoint][span["col"]] = span["color"]
    assert generator.self_check(malformed_three_entry)


def test_negative_controls_are_not_filled_but_active_spans_are():
    generator = _load_generator()
    for sample_index, expected_mode in ((1, "blocked_span"), (2, "mixed_endpoints")):
        grid = generator.generate(401, sample_index)
        info = generator._analyze(grid)
        assert info["distractor_mode"] == expected_mode
        out = generator.rule_mirror(grid)
        assert out != grid
        distractor_col = info["distractor_columns"][0]["col"]
        assert [row[distractor_col] for row in out] == [
            row[distractor_col] for row in grid
        ]
        for span in info["active_spans"]:
            assert all(
                out[row][span["col"]] == span["color"]
                for row in range(span["r1"], span["r2"] + 1)
            )


def test_determinism_freshness_rng_isolation_and_loud_validation():
    generator = _load_generator()
    random.seed(12345)
    state = random.getstate()
    a = generator.generate(123, 7, difficulty="hard")
    assert random.getstate() == state
    b = generator.generate(123, 7, difficulty="hard")
    assert a == b
    assert a is not b
    assert all(left is not right for left, right in zip(a, b))
    assert generator.generate(124, 7, difficulty="hard") != a
    assert generator.generate(123, 8, difficulty="hard") != a

    with pytest.raises(TypeError):
        generator.generate(1, 0, made_up_axis="x")
    with pytest.raises(ValueError):
        generator.generate(1, 0, difficulty="impossible")
    with pytest.raises(ValueError):
        generator.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        generator.generate(1, 0, distractor_mode="bogus")


def test_semantic_and_stability_census_across_disjoint_seed_ranges():
    generator = _load_generator()
    for difficulty, seed_base in (("easy", 100_000), ("medium", 200_000), ("hard", 300_000)):
        strict = 0
        witness_counts = {name: 0 for name in generator.SEMANTIC_WITNESSES}
        unique = set()
        for offset in range(200):
            grid = generator.generate(seed_base + offset, offset, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            strict += not generator.strict_canonical_like(grid)
            unique.add(tuple(tuple(row) for row in grid))
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(predicate(grid))
        assert strict >= 70
        assert len(unique) >= 190
        assert all(count > 0 for count in witness_counts.values())

        stable_unique = {
            tuple(tuple(row) for row in generator.generate(seed_base + 1_000 + offset, offset, difficulty=difficulty))
            for offset in range(200)
        }
        assert len(stable_unique) >= 190
