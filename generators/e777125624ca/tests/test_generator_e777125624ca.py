from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "e777125624ca"
ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def data_path(relative: str) -> Path:
    """Resolve authoring and copied-runtime data without depending on cwd."""
    for prefix in ("data", "shared/data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Missing data file {relative!r} under {ROOT}")


def canonical_row() -> dict:
    for line in canonical_path(ROOT).open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == generator.TASK_ID:
            return row
    raise AssertionError("canonical task missing")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def state_counts(grid):
    return generator.semantic_observables(grid)["state_counts"]


def test_metadata_hash_and_task_local_authority_are_exact():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == generator.RULE_HASH
    assert generator.VERSION == "2.1.0"
    base_row = json.loads(
        data_path("base/solutions/training/1b2d62fb__e777125624ca.json").read_text(encoding="utf-8")
    )
    canonical_normalized = " ".join(row["program_solution"].split())
    assert " ".join(base_row["racket_target"]["target_code"].split()) == canonical_normalized
    assert " ".join(base_row["racket_target"]["raw_code"].split()) == canonical_normalized


def test_every_canonical_pair_is_accepted_exact_and_input_pure():
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 6
    for pair in pairs:
        before = [line[:] for line in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_teach_all_nor_states_and_are_diverse(band):
    inputs = set()
    outputs = set()
    counts_seen = set()
    for seed in range(200):
        grid = generator.generate(100_000 + seed, seed * 17 + 3, difficulty=band)
        assert generator.self_check(grid) == []
        counts = state_counts(grid)
        assert all(counts[state] >= 1 for state in ("00", "10", "01", "11"))
        assert 8 not in {value for row in grid for value in row}
        counts_seen.add(counts["00"])
        inputs.add(frozen(grid))
        outputs.add(frozen(generator.rule_mirror(grid)))
    assert len(inputs) >= 190
    assert len(outputs) >= 130
    assert len(counts_seen) >= 3


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_override_boundaries_are_exact_in_every_band(band):
    cases = [
        {"grid_h": 3, "fg_color": 1, "sep_color": 9, "both_zero_count": 1, "layout": "random"},
        {"grid_h": 18, "fg_color": 9, "sep_color": 1, "both_zero_count": 6, "layout": "checker"},
        {"grid_h": 5, "fg_color": 2, "sep_color": 7, "both_zero_count": 4, "layout": "cluster"},
    ]
    for index, kwargs in enumerate(cases):
        grid = generator.generate(7 + index, 19 + index, difficulty=band, **kwargs)
        assert generator.self_check(grid) == []
        observed = generator.observe_overrides(grid)
        for key in ("grid_h", "fg_color", "sep_color", "both_zero_count", "layout"):
            assert observed[key] == kwargs[key]


def test_default_draw_provenance_matches_returned_grid():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(seed, seed * 31 + 1, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            drawn = captured[0].recorded_draws()
            observed = generator.observe_overrides(grid)
            for axis in ("grid_h", "fg_color", "sep_color", "both_zero_count", "layout"):
                assert drawn[axis] == observed[axis]


def test_semantic_contract_refutes_named_rivals():
    demos = []
    for sample_index in range(3):
        grid = generator.generate(808, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
    query_grid = generator.generate(808, 3, difficulty="medium")
    query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}

    assert generator.strict_canonical_like(query_grid) == []
    assert all(predicate(query_grid) for predicate in generator.SEMANTIC_WITNESSES.values())
    assert generator.lesson_identifiable(demos, query) == []

    broken = [{"input": pair["input"], "output": [[0] * 3 for _ in pair["output"]]} for pair in demos]
    assert any("disagrees" in reason for reason in generator.lesson_identifiable(broken, query))


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(12345)
    before_state = random.getstate()
    first = generator.generate(77, 91, difficulty="hard")
    after_state = random.getstate()
    second = generator.generate(77, 91, difficulty="hard")
    assert before_state == after_state
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 99
    assert second[0][0] != 99


def test_self_check_rejects_targeted_structural_impostors():
    source = generator.generate(42, 5, difficulty="medium")

    bad_width = [row[:-1] for row in source]
    assert any("width" in error for error in generator.self_check(bad_width))

    broken_separator = [row[:] for row in source]
    broken_separator[0][3] = 0
    assert any("separator" in error for error in generator.self_check(broken_separator))

    same_panels = [row[:] for row in source]
    for row in same_panels:
        row[4:7] = row[0:3]
    assert any("one-sided" in error for error in generator.self_check(same_panels))

    no_both_zero = [row[:] for row in source]
    fg = next(iter(generator.semantic_observables(source)["fg_values"]))
    for row in no_both_zero:
        for col in range(3):
            if row[col] == 0 and row[col + 4] == 0:
                row[col] = fg
    assert any("both-zero" in error for error in generator.self_check(no_both_zero))

    answer_leak = [row[:] for row in source]
    fg = next(iter(generator.semantic_observables(source)["fg_values"]))
    for row in answer_leak:
        for col in (0, 1, 2, 4, 5, 6):
            if row[col] == fg:
                row[col] = 8
    assert any("non-8" in error for error in generator.self_check(answer_leak))


def test_degenerate_negative_controls_are_rejected_but_oracle_executes():
    for name in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(8, 13, difficulty="medium", texture=name)
        assert generator.self_check(grid)
        output = generator.rule_mirror(grid)
        assert len(output) == len(grid)
        assert all(len(row) == 3 for row in output)


def test_conflicting_or_out_of_range_overrides_reject_loudly():
    bad = [
        {"fg_color": 1, "sep_color": 1},
        {"fg_color": 8},
        {"sep_color": 8},
        {"grid_h": 2},
        {"grid_h": 19},
        {"both_zero_count": 0},
        {"both_zero_count": 7},
        {"layout": "unknown"},
        {"bogus": 1},
        {"texture": "same_panels", "layout": "random"},
    ]
    for kwargs in bad:
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 0, **kwargs)
