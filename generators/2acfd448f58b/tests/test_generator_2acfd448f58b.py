"""Focused contract and semantic tests for generator 2acfd448f58b."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.helpers.grid import draw_rect_outline, full_grid
from scripts.coder_synth_verify import ProgramVerifier

ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.2acfd448f58b.generator"
)
AUTHORITY_FILES = (
    ROOT / "data/base/solutions/augmented/41e4d17e__7d4d023a4a03.json",
    ROOT / "data/base/solutions/training/41e4d17e__2acfd448f58b.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == GEN.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs() -> list[dict]:
    pairs = []
    for row in _canonical_rows():
        pairs.extend(row.get("train", []))
        test = row.get("test", [])
        pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def _rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frame_shapes(grid) -> list[tuple[int, int]]:
    return [
        (frame["height"], frame["width"])
        for frame in GEN._lawful_frames(grid)
    ]


def test_metadata_rule_hash_and_active_authorities_are_exactly_synchronized():
    rows = _canonical_rows()
    assert len(rows) == 2
    canonical = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical for row in rows)
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == "d929eea715e7"
    assert _rule_hash(canonical) == GEN.RULE_HASH
    for path in AUTHORITY_FILES:
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["racket_target"]["target_code"] == canonical
        assert record["racket_target"]["raw_code"].startswith("(rule!")


def test_all_canonical_inputs_are_accepted_and_outputs_are_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 6
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_six_example_schedule_covers_every_semantic_branch_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(20260724, index, difficulty=band) for index in range(6)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert [len(GEN._lawful_frames(grid)) for grid in grids] == [1, 2, 2, 2, 1, 2]
        assert GEN.strict_canonical_like(grids[0]) == []
        assert GEN.strict_canonical_like(grids[1]) == []
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (band, name)


def test_declared_overrides_are_exact_or_rejected_for_explicit_incompatibility():
    for band in ("easy", "medium", "hard"):
        for grid_h in (9, 22):
            grid = GEN.generate(71, 4, difficulty=band, grid_h=grid_h)
            assert len(grid) == grid_h
        for grid_w in (9, 22):
            grid = GEN.generate(73, 4, difficulty=band, grid_w=grid_w)
            assert len(grid[0]) == grid_w
        for n_frames in (1, 2):
            grid = GEN.generate(79, 5, difficulty=band, n_frames=n_frames)
            assert GEN.observe_overrides(grid)["n_frames"] == n_frames
        for frame_h in GEN.ODD_SIZES:
            grid = GEN.generate(
                83,
                4,
                difficulty=band,
                frame_h_min=frame_h,
                frame_h_max=frame_h,
            )
            assert {height for height, _ in _frame_shapes(grid)} == {frame_h}
        for frame_w in GEN.ODD_SIZES:
            grid = GEN.generate(
                89,
                4,
                difficulty=band,
                frame_w_min=frame_w,
                frame_w_max=frame_w,
            )
            assert {width for _, width in _frame_shapes(grid)} == {frame_w}
        for bias in GEN.POSITION_BIASES:
            grid = GEN.generate(
                97,
                5,
                difficulty=band,
                n_frames=2,
                position_bias=bias,
            )
            centers = [frame["center"] for frame in GEN._lawful_frames(grid)]
            if bias == "row_aligned":
                assert centers[0][0] == centers[1][0]
            elif bias == "col_aligned":
                assert centers[0][1] == centers[1][1]
            else:
                assert centers[0][0] != centers[1][0]
                assert centers[0][1] != centers[1][1]

    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 0, grid_h=8)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="single_frame")
    with pytest.raises(ValueError):
        GEN.generate(
            1,
            5,
            grid_h=9,
            grid_w=9,
            n_frames=2,
            frame_h_min=9,
            frame_h_max=9,
            frame_w_min=9,
            frame_w_max=9,
        )


def test_determinism_fresh_returns_global_rng_isolation_and_no_aliasing():
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(111, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 1
    assert GEN.generate(111, 5, difficulty="hard") == second


def test_targeted_impostors_are_rejected():
    valid = GEN.generate(211, 0)
    assert GEN.self_check(valid) == []

    broken = copy.deepcopy(valid)
    frame = GEN._lawful_frames(broken)[0]
    r0, c0, _r1, _c1 = frame["box"]
    broken[r0][c0 + 1] = 8

    even_frame = full_grid(12, 12, 8)
    draw_rect_outline(even_frame, 2, 2, 4, 5, 1)

    wrong_color = copy.deepcopy(valid)
    wrong_color[0][0] = 2

    touching = full_grid(12, 12, 8)
    draw_rect_outline(touching, 1, 1, 3, 3, 1)
    draw_rect_outline(touching, 1, 4, 3, 3, 1)

    edge_frame = full_grid(12, 12, 8)
    draw_rect_outline(edge_frame, 0, 2, 5, 5, 1)

    blank = full_grid(12, 12, 8)

    for impostor in (broken, even_frame, wrong_color, touching, edge_frame, blank):
        assert GEN.self_check(impostor), impostor
        with pytest.raises(ValueError):
            GEN.observe_overrides(impostor)


def test_lesson_identifiability_and_negative_recombination_witness():
    demos = []
    for index in range(6):
        grid = GEN.generate(307, index, difficulty="medium")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(307, 6, difficulty="medium")
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []

    single_demo = [demos[0]]
    pair_query_grid = GEN.generate(307, 7, difficulty="medium")
    reasons = GEN.lesson_identifiable(
        single_demo,
        {"input": pair_query_grid, "output": GEN.rule_mirror(pair_query_grid)},
    )
    assert any("first_frame_only" in reason for reason in reasons)


def test_python_mirror_matches_racket_with_aba_and_restarts():
    program = _canonical_rows()[0]["program_solution"]
    grids = [
        GEN.generate(401 + band_index * 20 + offset, offset, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for offset in range(3)
    ]
    with ProgramVerifier(timeout=20) as verifier:
        first = verifier.apply(program, grids[0])
        verifier.apply(program, grids[-1])
        assert verifier.apply(program, grids[0]) == first
        for grid in grids:
            assert verifier.apply(program, grid) == GEN.rule_mirror(grid)
    with ProgramVerifier(timeout=20) as restarted:
        assert restarted.apply(program, grids[0]) == GEN.rule_mirror(grids[0])
