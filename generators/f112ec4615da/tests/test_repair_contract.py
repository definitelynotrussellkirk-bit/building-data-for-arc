from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "f112ec4615da"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
RAW_AUTHORITY_SHA256 = "8724ec70a45a246d517528c6024011d4af96fc926d73cc44e898a690515bace6"


def _base_authority_path() -> Path:
    candidates = (
        ROOT / "shared/data/base/solutions/training/ea9794b1__f112ec4615da.json",
        ROOT / "data/base/solutions/training/ea9794b1__f112ec4615da.json",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("selected base authority is absent")


def _canonical_program() -> str:
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def _numeric_color_rank(grid: list[list[int]]) -> list[list[int]]:
    """Independent copy of the retained canonical-fitting shortcut."""
    height, width = len(grid), len(grid[0])
    half_h, half_w = height // 2, width // 2
    quadrant_colors = []
    for top, left in ((0, 0), (0, half_w), (half_h, 0), (half_h, half_w)):
        colors = {
            grid[top + row][left + col]
            for row in range(half_h)
            for col in range(half_w)
            if grid[top + row][left + col] != 0
        }
        assert len(colors) == 1
        quadrant_colors.append(next(iter(colors)))
    smallest = min(quadrant_colors)
    output = []
    for row in range(half_h):
        out_row = []
        for col in range(half_w):
            values = (
                grid[row][col],
                grid[row][col + half_w],
                grid[row + half_h][col],
                grid[row + half_h][col + half_w],
            )
            out_row.append(smallest if smallest in values else max(values))
        output.append(out_row)
    return output


@pytest.mark.parametrize("bad_seed", [True, 1.5, "7"])
def test_generate_rejects_non_integer_seed(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, 1.5, "7", -1])
def test_generate_rejects_invalid_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, bad_index)


def test_selected_target_is_exact_canonical_while_raw_authority_is_archival():
    canonical = _canonical_program()
    authority = json.loads(_base_authority_path().read_text(encoding="utf-8"))["racket_target"]
    raw = authority["raw_code"]
    target = authority["target_code"]

    assert hashlib.sha256(raw.encode()).hexdigest() == RAW_AUTHORITY_SHA256
    assert raw != canonical
    assert " ".join(raw.split()) == " ".join(canonical.split())
    assert target == canonical


def test_declared_numeric_color_shortcut_fits_every_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["numeric_color_rank"]
    assert GEN.SEMANTIC_RIVALS["numeric_color_rank"] is shortcut
    assert GEN.LESSON_COMPETITORS["numeric_color_rank"] is shortcut
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        before = deepcopy(pair["input"])
        assert shortcut(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == _numeric_color_rank(pair["input"])
        assert pair["input"] == before


def test_every_generated_grid_refutes_numeric_color_rank_shortcut():
    shortcut = GEN.CANONICAL_SHORTCUTS["numeric_color_rank"]
    witness = GEN.SEMANTIC_WITNESSES["position_over_numeric_color"]
    assert GEN.WITNESS_RIVALS["position_over_numeric_color"] == ["numeric_color_rank"]

    for band in ("easy", "medium", "hard"):
        for sample_index in range(120):
            grid = GEN.generate(107, sample_index, difficulty=band)
            before = deepcopy(grid)
            assert shortcut(grid) == _numeric_color_rank(grid)
            assert shortcut(grid) != GEN.rule_mirror(grid)
            assert witness(grid) is True
            assert grid == before


def test_lesson_hook_reports_an_unrefuted_query_disagreement():
    demos = []
    for profile in GEN._PROFILE_MASKS[:2]:
        grid = GEN._draw_profile(profile, (4, 3, 9, 8))
        assert _numeric_color_rank(grid) == GEN.rule_mirror(grid)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})

    query_grid = GEN._draw_profile(GEN._PROFILE_MASKS[2], (1, 6, 9, 8))
    assert _numeric_color_rank(query_grid) != GEN.rule_mirror(query_grid)
    reasons = GEN.lesson_identifiable(
        demos,
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    )
    assert any("numeric_color_rank" in reason for reason in reasons)
