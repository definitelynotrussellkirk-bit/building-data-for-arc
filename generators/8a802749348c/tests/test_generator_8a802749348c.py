"""Focused regressions and semantic checks for generator 8a802749348c."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.8a802749348c.generator")
ROOT = find_root(__file__)


def _data_path(relative: str) -> Path:
    for prefix in ("shared/data", "data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


BASE_PATHS = (
    _data_path("base/solutions/training/6e19193c__8a802749348c.json"),
    _data_path("base/solutions/augmented/6e19193c__cba05274505b.json"),
)


def canonical_rows() -> list[dict]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def canonical_pairs() -> list[dict]:
    return [
        pair
        for row in canonical_rows()
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def rule_application(source: str, grid: list[list[int]]) -> str:
    return f"({wrap_rule(source)} {_grid_literal(grid)})"


def purity_body(source: str, first_grid: list[list[int]], second_grid: list[list[int]]) -> str:
    wrapped = wrap_rule(source)
    first = _grid_literal(first_grid)
    second = _grid_literal(second_grid)
    return (
        f"(let* ([rule {wrapped}] [a {first}] [b {second}] "
        "[out-a1 (rule a)] [ignored (rule b)] [out-a2 (rule a)]) "
        "(list out-a1 out-a2 a))"
    )


def test_rule_hash_and_selected_authorities_are_exact_canonical() -> None:
    rows = canonical_rows()
    sources = {row["program_solution"] for row in rows}
    assert len(sources) == 1
    canonical = next(iter(sources))
    assert gen.RULE_HASH == normalized_hash(canonical) == "96a0505bb364"

    for path in BASE_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert target["raw_code"] != canonical
        assert "archival_raw_execution_parity_required" in target["target_status"]


def test_all_six_canonical_inputs_and_outputs_match() -> None:
    pairs = canonical_pairs()
    assert len(pairs) == 6
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_racket_is_exact_input_pure_and_a_b_a() -> None:
    source = canonical_rows()[0]["program_solution"]
    pairs = canonical_pairs()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            assert bridge.eval_text(rule_application(source, pair["input"])) == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(8802749348)
    before = random.getstate()
    first = gen.generate(71, 19, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(71, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(71, 19, difficulty="hard") == second
    assert gen.generate(72, 19, difficulty="hard") != second
    assert gen.generate(71, 20, difficulty="hard") != second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_and_observer(difficulty: str) -> None:
    serial = 0
    for h in (8, 16):
        for w in (8, 16):
            for count in (1, 5):
                grid = gen.generate(
                    1000 + serial,
                    17,
                    difficulty=difficulty,
                    grid_h=h,
                    grid_w=w,
                    object_count=count,
                )
                assert gen.self_check(grid, difficulty=difficulty) == []
                assert gen.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "object_count": count,
                }
                serial += 1


def test_four_consecutive_demos_refute_named_rivals_in_every_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for lesson_start in (0, 11, 22):
            demos = []
            for sample_index in range(lesson_start, lesson_start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(42 + lesson_start, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen._mirror(grid)})
            q_grid = gen.generate(
                42 + lesson_start,
                lesson_start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": q_grid, "output": gen._mirror(q_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_each_named_witness_has_a_real_rival_disagreement() -> None:
    grids = [gen.generate(9000 + i, i, difficulty="hard") for i in range(24)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        fired = [grid for grid in grids if witness(grid)]
        assert fired, witness_name
        for grid in fired[:4]:
            official = gen._mirror(grid)
            assert official is not None
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != official
                for rival_name in gen.WITNESS_RIVALS[witness_name]
            ), witness_name


def test_self_check_rejects_targeted_impostors() -> None:
    straight = [[0] * 8 for _ in range(8)]
    straight[3][2] = straight[3][3] = straight[3][4] = 2
    assert any("not three corners" in error for error in gen.self_check(straight))

    square = [[0] * 8 for _ in range(8)]
    for r in (2, 3):
        for c in (2, 3):
            square[r][c] = 4
    assert any("size 4" in error for error in gen.self_check(square))

    too_small = [[0] * 8 for _ in range(8)]
    too_small[2][2] = too_small[2][3] = 5
    assert any("size 2" in error for error in gen.self_check(too_small))

    ray_hits_object = [[0] * 8 for _ in range(8)]
    # First L misses bottom-right, so its ray begins at (3,3).
    for r, c in ((1, 1), (1, 2), (2, 1)):
        ray_hits_object[r][c] = 2
    # Second valid L occupies that first ray cell.
    for r, c in ((3, 3), (3, 4), (4, 3)):
        ray_hits_object[r][c] = 7
    assert any("intersects input object" in error for error in gen.self_check(ray_hits_object))

    adjacent = [[0] * 8 for _ in range(8)]
    for r, c in ((1, 1), (1, 2), (2, 1)):
        adjacent[r][c] = 2
    for r, c in ((2, 2), (2, 3), (3, 3)):
        adjacent[r][c] = 7
    assert any("orthogonally adjacent" in error for error in gen.self_check(adjacent))

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, palette_kind="warm")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
