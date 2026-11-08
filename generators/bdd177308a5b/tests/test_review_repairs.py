"""Focused regression tests added by review-4fb2a93096b60c50.

The inherited ``test_generator_bdd177308a5b.py`` is a frozen fixture.  These
checks cover the review repair without editing that file.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("review_bdd177308a5b_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


TASK_ID = "bdd177308a5b"
BANDS = ("easy", "medium", "hard")
LEGACY_RAW_SHA256 = "5b8904c8dacea878b644dcfadac38adcab78b69121d6f4eb6714c4ff708f31e0"
BASE_RELATIVE_PATHS = (
    "shared/data/base/solutions/training/63613498__bdd177308a5b.json",
    "shared/data/base/solutions/augmented/63613498__273d6c768d85.json",
)


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _canonical_source(root: Path) -> str:
    sources = {
        row["program_solution"]
        for row in (
            json.loads(line)
            for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row.get("task_id") == TASK_ID
    }
    assert len(sources) == 1
    return sources.pop()


def _canonical_output(grid: list[list[int]]) -> list[list[int]]:
    template, outside, matches = gen._semantic_parts(grid)
    assert template and len(outside) >= 3 and len(matches) == 1
    out = copy.deepcopy(grid)
    for row, col in matches[0]["cells"]:
        out[row][col] = 5
    return out


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty", "overrides"),
    [
        (True, 0, "easy", {}),
        (1.0, 0, "easy", {}),
        ("1", 0, "easy", {}),
        (1, False, "easy", {}),
        (1, -1, "easy", {}),
        (1, 1.5, "easy", {}),
        (1, "1", "easy", {}),
        (1, 0, True, {}),
        (1, 0, 1, {}),
        (1, 0, 0.5, {}),
        (1, 0, "expert", {}),
        (1, 0, "easy", {"grid_h": True}),
        (1, 0, "easy", {"grid_w": 10.0}),
        (1, 0, "easy", {"template_size": "3"}),
        (1, 0, "easy", {"distractor_count": 2.75}),
        (1, 0, "easy", {"target_zone": 1}),
    ],
)
def test_generate_rejects_invalid_public_scalars(seed, sample_index, difficulty, overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_pinned_profile_floor_has_support_in_every_band_and_pooled_envelope():
    support: dict[str, int] = {}
    for band in BANDS:
        count = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            if len(grid) == 10 and len(grid[0]) == 10:
                count += 1
        support[band] = count
    assert all(support[band] >= 1 for band in BANDS), support
    assert sum(support.values()) >= 15, support


def test_all_dimension_override_values_remain_exact_in_every_band():
    for band in BANDS:
        for value in range(10, 15):
            grid = gen.generate(
                901 + value,
                1701 + value,
                difficulty=band,
                grid_h=value,
                grid_w=value,
            )
            observed = gen.observe_overrides(grid)
            assert observed["grid_h"] == value
            assert observed["grid_w"] == value


def test_orientation_witness_and_rival_are_executable_and_nonmutating():
    grid = gen.generate(
        7001,
        811,
        difficulty="hard",
        grid_h=14,
        grid_w=14,
        template_size=5,
        distractor_count=4,
        target_zone="bottom_right",
    )
    original = copy.deepcopy(grid)
    witness = gen.SEMANTIC_WITNESSES["orientation_near_miss"]
    rival = gen.SEMANTIC_RIVALS["dihedral_invariant_all"]
    assert gen.strict_canonical_like(grid) == []
    assert witness(grid) is True
    rival_output = rival(grid)
    assert grid == original
    assert rival_output != _canonical_output(grid)
    assert sum(v == 5 for row in rival_output for v in row) > sum(
        v == 5 for row in _canonical_output(grid) for v in row
    )
    assert gen.WITNESS_RIVALS == {
        "orientation_near_miss": ["dihedral_invariant_all"]
    }
    assert gen.CANONICAL_SHORTCUTS == {}
    assert gen.LESSON_COMPETITORS["dihedral_invariant_all"] is rival


def test_selected_target_codes_are_exact_canonical_while_raw_source_is_preserved():
    root = find_root(__file__)
    canonical = _canonical_source(root)
    for relative in BASE_RELATIVE_PATHS:
        row = json.loads((root / relative).read_text(encoding="utf-8"))
        raw = row["racket_target"]["raw_code"]
        target = row["racket_target"]["target_code"]
        assert hashlib.sha256(raw.encode()).hexdigest() == LEGACY_RAW_SHA256
        assert target == canonical
