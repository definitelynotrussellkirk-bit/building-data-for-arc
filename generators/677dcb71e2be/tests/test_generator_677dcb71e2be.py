from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "677dcb71e2be"
generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def blank(h: int = 10, w: int = 10) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def paint(grid, top, left, cells, color) -> None:
    for r, c in cells:
        grid[top + r][left + c] = color


def valid_three() -> list[list[int]]:
    grid = blank()
    paint(grid, 0, 0, [(0, 0), (0, 1)], 2)
    paint(grid, 0, 6, [(0, 0), (0, 1), (1, 0)], 5)
    paint(grid, 6, 0, [(0, 0), (0, 1), (1, 0), (1, 1)], 8)
    assert generator.self_check(grid) == []
    return grid


def _old_corner_slot(comp: dict, h: int, w: int) -> bool:
    top, left, _, _ = comp["bbox"]
    return top in {0, 1, h - 4} and left in {0, 1, w - 4, w - 3}


def _old_corner_rival(grid) -> list[list[int]]:
    comps = [
        comp
        for comp in generator._components(grid)
        if _old_corner_slot(comp, len(grid), len(grid[0]))
    ]
    return generator._bars_from_components(
        sorted(comps, key=lambda comp: (-comp["size"], comp["color"]))
    )


def _old_palette_rank_rival(grid) -> list[list[int]]:
    comps = generator._components(grid)
    colors = sorted(comp["color"] for comp in comps)
    ranks = (1, 2, 0) if len(colors) == 3 else (1, 3, 0, 2)
    by_color = {comp["color"]: comp for comp in comps}
    return generator._bars_from_components([by_color[colors[index]] for index in ranks])


def test_active_rule_is_exactly_pinned_to_canonical_source() -> None:
    source = canonical_row()["program_solution"]
    actual = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert generator.VERSION == "3.0.0"
    assert generator.RULE_HASH == actual == "a1028386df20"


def test_all_five_canonical_pairs_accept_and_match_the_rule_mirror() -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert generator.self_check(grid) == []
        assert generator._official_output(grid) == pair["output"]
        assert grid == snapshot


def test_determinism_fresh_returns_and_global_random_state() -> None:
    state = random.getstate()
    a = generator.generate(901, 7, difficulty="hard")
    b = generator.generate(901, 7, difficulty="hard")
    assert a == b and a is not b and a[0] is not b[0]
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert generator.generate(901, 7, difficulty="hard") == b
    assert random.getstate() == state


def test_public_scalar_and_difficulty_contract_is_strict() -> None:
    for seed in (True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="seed"):
            generator.generate(seed, 0)
    for sample_index in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            generator.generate(1, sample_index)
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(1, 0, difficulty="extreme")


def test_exact_override_boundaries_are_observable_and_unknowns_reject() -> None:
    cases = [
        {"grid_h": 10}, {"grid_h": 18}, {"grid_w": 10}, {"grid_w": 18},
        {"n_blobs": 3}, {"n_blobs": 4},
        {"size_pattern": "consecutive"}, {"size_pattern": "spread"},
        {"input_size_order": "ascending"}, {"input_size_order": "descending"},
        {"input_size_order": "zigzag"},
        {"palette_kind": "low"}, {"palette_kind": "high"}, {"palette_kind": "mixed"},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = generator.generate(1000 + index, index, difficulty=band, **overrides)
            observed = generator.observe_overrides(grid)
            for key, value in overrides.items():
                assert observed[key] == value
    for key in ("grid_h", "grid_w", "n_blobs"):
        with pytest.raises(TypeError, match="integer"):
            generator.generate(0, 0, **{key: True})
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, bogus_axis="accepted-by-old-generator")


def test_self_check_rejects_four_targeted_structural_impostors() -> None:
    diagonal = blank()
    paint(diagonal, 0, 0, [(0, 0), (0, 1)], 2)
    paint(diagonal, 1, 2, [(0, 0), (0, 1), (1, 0)], 5)
    paint(diagonal, 6, 0, [(0, 0), (0, 1), (1, 0), (1, 1)], 8)
    assert any("touch" in err for err in generator.self_check(diagonal))

    duplicate_color = valid_three()
    duplicate_color[0][6] = duplicate_color[0][7] = duplicate_color[1][6] = 2
    assert any("colors" in err for err in generator.self_check(duplicate_color))

    tied = valid_three()
    tied[1][6] = 0
    assert any("counts" in err for err in generator.self_check(tied))

    oversized = blank()
    paint(oversized, 0, 0, [(0, 0), (0, 1)], 2)
    paint(oversized, 0, 6, [(0, 0), (0, 1), (1, 0)], 5)
    paint(oversized, 4, 0, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)], 8)
    assert any("4x3" in err for err in generator.self_check(oversized))


def test_every_sliding_four_example_window_kills_all_named_rivals() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            pairs = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = generator.generate(50000 + band_index * 100 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": generator._official_output(grid)})
            assert generator.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_repaired_curriculum_breaks_both_retained_shortcuts() -> None:
    rows = []
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for index in range(4):
                grid = generator.generate(seed, index, difficulty=band)
                rows.append(
                    (
                        _old_corner_rival(grid) == generator._official_output(grid),
                        _old_palette_rank_rival(grid) == generator._official_output(grid),
                        tuple(
                            sorted(
                                (comp["color"] for comp in generator._components(grid)),
                            )
                        ),
                    )
                )
    assert rows
    assert not any(corner_matches for corner_matches, _, _ in rows)
    assert sum(palette_matches for _, palette_matches, _ in rows) < len(rows) // 2


def test_negative_recombination_is_rejected_by_grammar_but_oracle_executes() -> None:
    grid = generator.generate(31415, 3, difficulty="hard", n_blobs=4)
    used = {value for row in grid for value in row}
    fresh = next(color for color in range(1, 10) if color not in used)
    impostor = copy.deepcopy(grid)
    impostor[len(impostor) // 2][len(impostor[0]) // 2] = fresh
    assert any("components" in err or "count" in err for err in generator.self_check(impostor))
    assert generator._official_output(impostor)
