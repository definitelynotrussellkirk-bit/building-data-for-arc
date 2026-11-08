"""Behavior regressions; run explicitly (the repository's testpaths excludes these)."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("generator_ee64b9b0fe20", HOME / "generator.py")
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def objects(grid):
    """Independent row-major, same-color, FOUR-connected component census."""
    counts = Counter(v for row in grid for v in row if v != 0)
    bg = max(counts, key=counts.get)
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            color, todo, cells = grid[r][c], [(r, c)], []
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = y + dy, x + dx
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        todo.append(p)
            bbox = min(y for y, x in cells), min(x for y, x in cells), max(y for y, x in cells), max(x for y, x in cells)
            if bbox != (0, 0, h - 1, w - 1):
                result.append((color, cells, bbox))
    return bg, result


def canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.open():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID and row.get("source") == "training":
            return row["train"] + row["test"]
    raise AssertionError("missing training authority")


def test_original_count_loss_seed_is_repaired():
    grid = gen.generate(1, 0, difficulty="easy", shape_count=3, grid_h=10, grid_w=11, frame=True)
    assert len(objects(grid)[1]) == 3
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_canonical_grid_dimensions_are_legal_in_every_band(band):
    grid = gen.generate(1, 0, difficulty=band, grid_h=10, grid_w=10, shape_count=4)
    assert (len(grid), len(grid[0])) == (10, 10)
    assert len(objects(grid)[1]) == 4
    assert gen.self_check(grid) == []


def test_palette_size_is_real_not_an_ignored_keyword():
    grid = gen.generate(12, 0, shape_count=4, palette_size=1)
    assert len({c for c, cells, bbox in objects(grid)[1]}) == 1
    assert len(objects(grid)[1]) == 4


def test_unknown_and_retired_phantom_axes_raise():
    for keyword in ("bogus_axis", "palette_kind", "position_bias"):
        with pytest.raises(TypeError, match="unknown override"):
            gen.generate(0, 0, **{keyword: "unused"})


def test_invalid_difficulty_is_rejected_instead_of_treated_as_medium():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="__invalid_difficulty__")


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_a_literal_integer(bad):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_sample_index_requires_a_literal_integer(bad):
    with pytest.raises(TypeError, match="sample_index"):
        gen.generate(0, bad)


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError, match="nonnegative"):
        gen.generate(0, -1)


@pytest.mark.parametrize("bad", [None, [], [[]], [[1], [1, 2]], [[True]], [[11]], [[0] * 10 for _ in range(10)]])
def test_validator_returns_reasons_without_crashing(bad):
    errors = gen.self_check(bad)
    assert isinstance(errors, list) and errors


def test_rule_hash_pins_the_unchanged_canonical_program():
    assert gen.RULE_HASH == "e0863705f64c"


def test_zero_foreground_and_twelve_cell_shapes_are_in_support():
    corpus = [gen.generate(151, i, difficulty="medium") for i in range(100)]
    shapes = [obj for grid in corpus for obj in objects(grid)[1]]
    assert any(color == 0 for color, cells, bbox in shapes)
    assert any(len(cells) >= 12 for color, cells, bbox in shapes)


def test_canonical_examples_are_accepted_and_mirrored():
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_replay_freshness_and_no_global_random_mutation():
    random.seed(314159)
    before = random.getstate()
    first, second = gen.generate(71, 3), gen.generate(71, 3)
    assert random.getstate() == before
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w", [(10, 10), (10, 18), (18, 10), (18, 18)])
@pytest.mark.parametrize("count", [2, 4, 6])
@pytest.mark.parametrize("frame", [False, True])
def test_corner_overrides_never_silently_change_count(band, h, w, count, frame):
    for palette in (1, count):
        grid = gen.generate(4901, 0, difficulty=band, grid_h=h, grid_w=w,
                            shape_count=count, palette_size=palette, frame=frame)
        assert gen.self_check(grid) == []
        bg, found = objects(grid)
        assert (len(grid), len(grid[0])) == (h, w)
        assert len(found) == count
        assert len({color for color, cells, bbox in found}) == palette
        assert len({len(cells) for color, cells, bbox in found}) == count
        assert sum(b[3] - b[1] + 1 for c, cells, b in found) <= w


def test_declared_rivals_fit_all_canonical_demonstrations():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs():
            assert rival(pair["input"]) == pair["output"], name


def test_two_demo_schedule_refutes_the_declared_shortcuts():
    for seed in range(12):
        grids = [gen.generate(seed, i) for i in range(8)]
        for offset in range(6):
            demos = [{"input": g, "output": gen.rule_mirror(g)} for g in grids[offset:offset + 2]]
            query = {"input": grids[offset + 2]}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                assert any(rival(d["input"]) != d["output"] for d in demos), name


def test_default_two_example_windows_cover_both_frame_branches():
    """A lesson must show that whole-canvas frames are discarded, not preserved."""
    for seed in range(12):
        grids = [gen.generate(seed, i, difficulty="easy") for i in range(10)]
        for offset in range(9):
            window = grids[offset:offset + 2]
            flags = {gen.observe_overrides(grid)["frame"] for grid in window}
            assert flags == {False, True}, (seed, offset, flags)
            assert any(gen.rival_preserve_frame(grid) != gen.rule_mirror(grid)
                       for grid in window)


def test_retained_seed_zero_frame_gap_is_no_longer_ambiguous():
    """Regression for review-c88b79a930311a45:v0001, easy seed 0, offset 7."""
    pairs = []
    for index in range(7, 11):
        grid = gen.generate(0, index, difficulty="easy")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    demos, query = pairs[:3], pairs[3]
    rival_fits_demos = all(gen.rival_preserve_frame(pair["input"]) == pair["output"]
                           for pair in demos)
    rival_changes_query = gen.rival_preserve_frame(query["input"]) != query["output"]
    assert not (rival_fits_demos and rival_changes_query)


def test_frame_preserving_rule_is_an_executable_declared_rival():
    assert gen.SEMANTIC_RIVALS["preserve_frame"] is gen.rival_preserve_frame
    retained = (HOME / "counterexamples/review-c88b79a930311a45-v0001/retained/checks/"
                "audit/ee64b9b0fe20/frame-gap/counterexample.json")
    evidence = json.loads(retained.read_text())
    assert gen.rival_preserve_frame(evidence["query_input"]) == evidence["query_rival_output"]
    assert gen.rival_preserve_frame(evidence["query_input"]) != evidence["query_racket_output"]


@pytest.mark.parametrize("texture", ["mixed", "rectangles", "area_trap"])
def test_texture_overrides_are_executed(texture):
    for seed in range(5):
        grid = gen.generate(seed, 0, texture=texture)
        assert gen.self_check(grid) == []
        if texture == "rectangles":
            assert all(len(cells) == (b[2] - b[0] + 1) * (b[3] - b[1] + 1)
                       for color, cells, b in objects(grid)[1])
        if texture == "area_trap":
            assert gen.rival_bbox_area(grid) != gen.rule_mirror(grid)


def test_impossible_overrides_reject_instead_of_clamping():
    for kwargs in ({"shape_count": 1}, {"shape_count": 7}, {"bg_color": 0},
                   {"grid_h": 9}, {"frame": "false"}, {"shape_count": 2, "palette_size": 3},
                   {"grid_h": 10.5}, {"shape_count": True}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, **kwargs)


def test_original_demo_rivals_are_already_refuted_by_augmented_example():
    pairs = canonical_pairs()
    for rival in (gen.rival_bbox_area, gen.rival_group_by_color):
        assert all(rival(p["input"]) == p["output"] for p in pairs[:3])
        assert rival(pairs[3]["input"]) != pairs[3]["output"]


def test_selected_targets_match_canonical_without_discarding_archival_source():
    canonical = next(json.loads(line)["program_solution"]
                     for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
                     if json.loads(line).get("task_id") == gen.TASK_ID)
    for name in ("training/4df5b0ae__ee64b9b0fe20.json", "augmented/4df5b0ae__8c468fc326c7.json"):
        target = json.loads((REPO / "shared/data/base/solutions" / name).read_text())["racket_target"]
        assert target["target_code"] == canonical
        assert target["raw_code"] != target["target_code"]


def test_diagonal_seed_index_probe_does_not_alias_away_shared_color_family():
    corpus = [gen.generate(i, i) for i in range(1, 9)]
    assert any(gen.rival_group_by_color(grid) != gen.rule_mirror(grid) for grid in corpus)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_canvas_has_explicit_mass_not_accidental_joint_probability(band):
    corpus = [gen.generate(seed, index, difficulty=band) for seed in range(30) for index in range(2)]
    hits = sum((len(grid), len(grid[0])) == (10, 10) for grid in corpus)
    assert 20 <= hits <= 50, hits
