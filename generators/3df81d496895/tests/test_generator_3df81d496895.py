"""Focused semantic and override regressions for generator 3df81d496895."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "3df81d496895"
ROOT = Path(__file__).resolve().parents[1]
module = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_rule() -> str:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical row not found")


def _normalized_hash(source: str) -> str:
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _axis_bounds(name: str) -> tuple[int, int]:
    lo, hi = module.AXES[name]["valid"].split("..")
    return int(lo), int(hi)


def test_rule_hash_version_and_axis_surface_are_pinned():
    assert module.VERSION == "2.0.0"
    assert module.RULE_HASH == "313add7d0e0d"
    assert module.RULE_HASH == _normalized_hash(_canonical_rule())
    assert set(module.AXES) == {"grid_h", "grid_w", "n_pairs"}


def test_all_canonical_pairs_are_accepted_and_match_the_rule():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        expected = copy.deepcopy(pair["output"])
        assert module.self_check(source) == []
        assert module.strict_canonical_like(source) == []
        assert module.rule_mirror(source) == expected
        assert source == pair["input"]


def test_every_axis_boundary_combination_is_exact_in_every_band():
    for band in ("easy", "medium", "hard"):
        for height in _axis_bounds("grid_h"):
            for width in _axis_bounds("grid_w"):
                for n_pairs in _axis_bounds("n_pairs"):
                    grid = module.generate(
                        9107,
                        33,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        n_pairs=n_pairs,
                    )
                    assert module.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "n_pairs": n_pairs,
                    }
                    assert module.self_check(grid) == []


def test_unknown_and_mistyped_overrides_are_rejected_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        module.generate(1, 2, typo_axis=3)
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        module.generate(1, 2, grid_h=True)
    with pytest.raises(ValueError, match="n_pairs must be an integer"):
        module.generate(1, 2, n_pairs="3")


def test_determinism_freshness_and_global_random_state():
    before = random.getstate()
    first = module.generate(4242, 17, difficulty="hard")
    after_first = random.getstate()
    second = module.generate(4242, 17, difficulty="hard")
    after_second = random.getstate()
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert before == after_first == after_second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert module.generate(4242, 17, difficulty="hard") == second


def test_every_ordinary_draw_refutes_all_named_rivals():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(40):
            grid = module.generate(50_000 + band_index * 1000 + index, index, difficulty=band)
            truth = module.rule_mirror(grid)
            assert module.self_check(grid) == []
            for witness in module.SEMANTIC_WITNESSES.values():
                assert witness(grid)
            for rival in module.SEMANTIC_RIVALS.values():
                assert rival(grid) != truth


def test_consecutive_lessons_are_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for sample_index in range(start, start + module.EXAMPLES_NEEDED + 1):
                grid = module.generate(77_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": module.rule_mirror(grid)})
            assert module.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_self_check_rejects_targeted_structural_impostors():
    lawful = module.generate(1234, 19, difficulty="medium", n_pairs=3)
    facts = module._analysis(lawful)
    assert facts["errors"] == []

    half_pair = copy.deepcopy(lawful)
    col = facts["legend_cols"][0]
    half_pair[1][col] = 0
    assert any("unpaired" in error for error in module.self_check(half_pair))

    duplicate_source = copy.deepcopy(lawful)
    first, second = facts["legend_cols"][:2]
    duplicate_source[0][second] = duplicate_source[0][first]
    assert any("source colors" in error for error in module.self_check(duplicate_source))

    source_target_overlap = copy.deepcopy(lawful)
    source_target_overlap[1][first] = source_target_overlap[0][second]
    assert any("disjoint" in error for error in module.self_check(source_target_overlap))

    missing_mapping_witness = copy.deepcopy(lawful)
    missing_source = facts["sources"][0]
    replacement_source = facts["sources"][1]
    for row in range(2, len(missing_mapping_witness)):
        for col in range(len(missing_mapping_witness[0])):
            if missing_mapping_witness[row][col] == missing_source:
                missing_mapping_witness[row][col] = replacement_source
    assert any("does not exercise" in error for error in module.self_check(missing_mapping_witness))

    unmapped_body = copy.deepcopy(lawful)
    used = {value for row in unmapped_body for value in row}
    novel = next(color for color in range(1, 10) if color not in used)
    row, col = next(
        (row, col)
        for row in range(2, len(unmapped_body))
        for col in range(len(unmapped_body[0]))
        if unmapped_body[row][col] != 0
    )
    unmapped_body[row][col] = novel
    assert any("unmapped" in error for error in module.self_check(unmapped_body))
    # The teaching grammar rejects it, while the canonical oracle semantics are
    # still represented accurately by the mirror: an unmapped color is kept.
    assert module.rule_mirror(unmapped_body)[row - 2][col] == novel
