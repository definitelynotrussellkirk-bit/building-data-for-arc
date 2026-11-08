"""Focused regressions for the 2026-10 ARCpuzzles review repair.

This file is intentionally separate from the packet's frozen imported fixture.
It uses only portable reviewer helpers so the same assertions bind to the
selected source tree in the repository and in task-test snapshots.
"""
from __future__ import annotations

import hashlib
import json

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "a3c33cc348fb"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PATH = canonical_path(ROOT)
DATA_ROOT = CANONICAL_PATH.parents[1]
BASE_PATHS = (
    DATA_ROOT / "base/solutions/training/b548a754__a3c33cc348fb.json",
    DATA_ROOT / "base/solutions/augmented/b548a754__a2f39c96cab9.json",
)
CANONICAL_PROFILES = {(11, 11, 4), (13, 12, 4), (13, 13, 4)}


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _canonical_rule() -> str:
    rows = [
        json.loads(line)
        for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    return programs.pop()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_literal_integer_seed(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(991, bad_index)


def test_pinned_profile_floor_meets_strict_after_policy():
    exact_by_band: dict[str, int] = {}
    exact_total = 0
    envelope_total = 0
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = MODULE.generate(seed, sample_index, difficulty=band)
            profile = _profile(grid)
            exact += profile in CANONICAL_PROFILES
            envelope_total += (
                11 <= profile[0] <= 13
                and 11 <= profile[1] <= 13
                and profile[2] == 4
            )
        exact_by_band[band] = exact
        exact_total += exact
    assert all(count >= 1 for count in exact_by_band.values()), exact_by_band
    assert exact_total >= 3, exact_by_band
    assert envelope_total >= 15, {
        "exact_by_band": exact_by_band,
        "exact_total": exact_total,
        "envelope_total": envelope_total,
    }


def test_semantic_contract_refutes_marker_line_shortcut_and_teaches_it():
    assert MODULE.strict_canonical_like(MODULE.generate(100, 0)) == []
    rival = MODULE.SEMANTIC_RIVALS["marker_line_only"]
    witness = MODULE.SEMANTIC_WITNESSES["full_bbox_repaint"]
    assert MODULE.WITNESS_RIVALS["full_bbox_repaint"] == ["marker_line_only"]
    assert MODULE.LESSON_COMPETITORS["marker_line_only"] is rival

    pairs = []
    for index in range(4):
        grid = MODULE.generate(6100 + index, index, difficulty="medium")
        assert MODULE.strict_canonical_like(grid) == []
        assert witness(grid)
        expected = MODULE.rule_mirror(grid)
        assert rival(grid) != expected
        pairs.append({"input": grid, "output": expected})
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_selected_authority_target_is_exact_canonical_text_but_raw_is_archival():
    canonical = _canonical_rule()
    for path in BASE_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical
        assert " ".join(target["raw_code"].split()) == " ".join(canonical.split())
