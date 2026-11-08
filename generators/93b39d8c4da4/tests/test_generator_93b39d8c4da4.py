"""Source-bound regression tests for the template-stamping generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from itertools import product
from pathlib import Path

import pytest

TASK_ID = "93b39d8c4da4"
TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} missing")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + (list(test) if isinstance(test, list) else [test])


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _normalized_template(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    assert cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def test_rule_hash_and_every_canonical_pair_match_python_mirror() -> None:
    normalized = " ".join(_canonical_row()["program_solution"].split())
    expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "d20fb64e7b01"

    pairs = _canonical_pairs()
    assert len(pairs) == 6
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_all_exact_axis_boundaries_are_constructive_and_observable() -> None:
    final_template = len(GEN.TEMPLATE_BANK) - 1
    index = 0
    for difficulty, values in product(
        BANDS,
        product(
            (12, 18),
            (14, 20),
            (0, final_template),
            (2, 7),
            ("separated", "overlap"),
        ),
    ):
        grid_h, grid_w, template_id, n_marks, layout_mode = values
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "template_id": template_id,
            "n_marks": n_marks,
            "layout_mode": layout_mode,
        }
        grid = GEN.generate(
            71000 + index,
            2000 + index,
            difficulty=difficulty,
            **requested,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested
        index += 1


def test_every_template_bank_member_is_constructive_in_both_layout_modes() -> None:
    for template_id, layout_mode in product(
        range(len(GEN.TEMPLATE_BANK)), ("separated", "overlap")
    ):
        grid = GEN.generate(
            93000 + template_id,
            500 + template_id,
            difficulty="medium",
            grid_h=12,
            grid_w=14,
            template_id=template_id,
            n_marks=7,
            layout_mode=layout_mode,
        )
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        assert observed["template_id"] == template_id
        assert observed["layout_mode"] == layout_mode
        assert observed["n_marks"] == 7


def test_unknown_invalid_overrides_and_difficulty_fail_closed() -> None:
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 1, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 1, grid_h=11)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 1, grid_w=21)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 1, n_marks=8)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 1, template_id=len(GEN.TEMPLATE_BANK))
    with pytest.raises(ValueError, match="layout_mode"):
        GEN.generate(1, 1, layout_mode="touching")
    with pytest.raises((TypeError, ValueError), match="integer"):
        GEN.generate(1, 1, n_marks=True)


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(93739)
    state_before = random.getstate()
    first = GEN.generate(17, 9, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(17, 9, difficulty="medium")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != GEN.generate(18, 9, difficulty="medium")
    assert second != GEN.generate(17, 10, difficulty="medium")


def test_schedule_is_source_bound_and_covers_every_required_profile() -> None:
    expected = set(GEN.SCHEDULE_PROFILES)
    assert expected == {
        "canonical_profile",
        "offset_anchor",
        "many_marks",
        "overlap",
    }
    assert GEN.EXAMPLES_NEEDED == len(expected) == 4

    canonical_sizes = {(12, 14), (12, 15), (12, 16), (13, 15), (13, 16), (14, 16)}
    for difficulty in BANDS:
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            profiles = {
                GEN.schedule_profile(8000 + start, start + offset, difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert profiles == expected

            by_profile = {}
            for offset in range(GEN.EXAMPLES_NEEDED):
                sample_index = start + offset
                profile = GEN.schedule_profile(8000 + start, sample_index, difficulty)
                grid = GEN.generate(8000 + start, sample_index, difficulty=difficulty)
                assert GEN.self_check(grid) == []
                by_profile[profile] = grid

            canonical = by_profile["canonical_profile"]
            assert (len(canonical), len(canonical[0])) in canonical_sizes
            assert (0, 0) not in _normalized_template(by_profile["offset_anchor"])
            assert GEN.observe_overrides(by_profile["many_marks"])["n_marks"] >= 5
            assert GEN.observe_overrides(by_profile["overlap"])["layout_mode"] == "overlap"


def test_every_four_demo_window_refutes_all_declared_lesson_competitors() -> None:
    for difficulty in BANDS:
        for seed in (51001, 51002, 51003):
            for start in range(8):
                demos = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(seed, start + GEN.EXAMPLES_NEEDED, difficulty)
                assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_fitting_shortcuts_really_fit_and_generated_witnesses_kill_them() -> None:
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "first_four_marks_only",
        "discard_overlapping_stamps",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert rival(pair["input"]) == pair["output"], name

    witnesses = {}
    for sample_index in range(len(GEN.SCHEDULE_PROFILES)):
        profile = GEN.schedule_profile(62001, sample_index, "medium")
        witnesses[profile] = GEN.generate(62001, sample_index, difficulty="medium")

    intended_many = GEN.rule_mirror(witnesses["many_marks"])
    assert intended_many != GEN.SEMANTIC_RIVALS["first_four_marks_only"](
        witnesses["many_marks"]
    )
    intended_overlap = GEN.rule_mirror(witnesses["overlap"])
    assert intended_overlap != GEN.SEMANTIC_RIVALS["discard_overlapping_stamps"](
        witnesses["overlap"]
    )
    intended_offset = GEN.rule_mirror(witnesses["offset_anchor"])
    assert intended_offset != GEN.SEMANTIC_RIVALS["anchor_first_occupied"](
        witnesses["offset_anchor"]
    )

    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        grid = next(
            grid
            for grid in witnesses.values()
            if GEN.SEMANTIC_WITNESSES[witness_name](grid)
        )
        for rival_name in rival_names:
            assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[rival_name](grid)


def test_self_check_rejects_targeted_malformed_inputs() -> None:
    valid = GEN.generate(77001, 0, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    blank = [[0 for _ in row] for row in valid]
    fixtures.append(("blank", blank))

    no_marks = copy.deepcopy(valid)
    for r, row in enumerate(no_marks):
        for c, value in enumerate(row):
            if value == 3:
                no_marks[r][c] = 0
    fixtures.append(("no marks", no_marks))

    disconnected_template = copy.deepcopy(valid)
    mark = next(
        (r, c)
        for r, row in enumerate(disconnected_template)
        for c, value in enumerate(row)
        if value == 3
    )
    disconnected_template[mark[0]][mark[1]] = 2
    fixtures.append(("disconnected template", disconnected_template))

    bad_color = copy.deepcopy(valid)
    zero = next(
        (r, c)
        for r, row in enumerate(bad_color)
        for c, value in enumerate(row)
        if value == 0
    )
    bad_color[zero[0]][zero[1]] = 7
    fixtures.append(("foreign color", bad_color))

    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]
    fixtures.append(("ragged", ragged))

    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_rule_mirror_is_pure_and_output_uses_only_zero_and_eight() -> None:
    for difficulty in BANDS:
        for sample_index in range(12):
            grid = GEN.generate(88000 + sample_index, sample_index, difficulty=difficulty)
            before = copy.deepcopy(grid)
            output = GEN.rule_mirror(grid)
            assert grid == before
            assert len(output) == len(grid)
            assert all(len(row) == len(grid[0]) for row in output)
            assert {value for row in output for value in row} <= {0, 8}
            assert output != grid


def test_reusable_qualification_probe_uses_live_semantic_declarations() -> None:
    probe_path = TASK_ROOT / "workspace/qualify_distribution.py"
    spec = importlib.util.spec_from_file_location(
        f"qualification_probe_{TASK_ID}", probe_path
    )
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.qualify(
        generator=GEN,
        lessons_per_band=4,
        seed_base=991000,
    )
    assert report["failures"] == []
    assert report["contract"]["lesson_competitors"] == sorted(
        GEN.LESSON_COMPETITORS
    )
    assert report["contract"]["canonical_shortcuts"] == sorted(
        GEN.CANONICAL_SHORTCUTS
    )
    for band in BANDS:
        assert report["bands"][band]["lessons_identifiable"] == 4
        assert report["bands"][band]["lessons_total"] == 4
