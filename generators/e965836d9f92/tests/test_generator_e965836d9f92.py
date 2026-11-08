from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.e965836d9f92 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_inputs_remain_accepted() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_exact_override_axes_and_unknown_key_rejection() -> None:
    requested = {
        "grid_h": 8,
        "grid_w": 8,
        "n_codes": 4,
        "n_colors": 4,
        "proto_size": 9,
    }
    grid = gen.generate(17, 5, difficulty="easy", **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, meta={"overrides": requested}) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(17, 5, texture="warm")


def test_three_consecutive_samples_cover_every_transform_code() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(3):
            covered = set()
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(31, sample_index, difficulty=difficulty)
                covered.update(gen._facts(grid)["codes"])
            assert covered == set(range(1, 7))


def test_self_check_rejects_targeted_impostors() -> None:
    base = gen.generate(11, 1, difficulty="medium")
    facts = gen._facts(base)

    duplicate_code = copy.deepcopy(base)
    duplicate_code[0][facts["code_positions"][1]] = duplicate_code[0][facts["code_positions"][0]]
    assert "distinct" in " ".join(gen.self_check(duplicate_code))

    bad_code = copy.deepcopy(base)
    bad_code[0][facts["code_positions"][0]] = 7
    assert "outside" in " ".join(gen.self_check(bad_code))

    duplicate_color = copy.deepcopy(base)
    duplicate_color[facts["color_positions"][1]][0] = duplicate_color[facts["color_positions"][0]][0]
    assert "distinct" in " ".join(gen.self_check(duplicate_color))

    disconnected = copy.deepcopy(base)
    r, c = next(iter(facts["body_cells"]))
    disconnected[r][c] = 0
    disconnected[1][len(disconnected[0]) - 1] = next(iter(facts["body_colors"]))
    assert "connected" in " ".join(gen.self_check(disconnected))

    multicolor = copy.deepcopy(base)
    r, c = next(iter(facts["body_cells"]))
    multicolor[r][c] = 1 if multicolor[r][c] != 1 else 2
    assert "monochrome" in " ".join(gen.self_check(multicolor))


def test_lesson_schedule_refutes_declared_rivals() -> None:
    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(gen.EXAMPLES_NEEDED):
            inp = gen.generate(23, sample_index, difficulty=difficulty)
            demos.append({"input": inp, "output": gen.rule_mirror(inp)})
        query_in = gen.generate(23, gen.EXAMPLES_NEEDED, difficulty=difficulty)
        query = {"input": query_in, "output": gen.rule_mirror(query_in)}
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_deterministic_fresh_returns_and_global_rng() -> None:
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] == 0
    assert before == middle == after
