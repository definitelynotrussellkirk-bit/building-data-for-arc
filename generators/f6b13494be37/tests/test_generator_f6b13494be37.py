"""Focused semantic regressions for generator f6b13494be37."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


TASK_ID = "f6b13494be37"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs.extend(row.get("train", []))
                test = row.get("test", [])
                pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def test_all_five_canonical_inputs_are_owned_and_mirrored_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    observed = []
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]
        observed.append(GEN.observe_overrides(pair["input"]))
    assert {item["grid_size"] for item in observed} == {20, 25, 30}
    assert {item["n_notches"] for item in observed} == {1, 2, 3}
    assert {item["common_mode"] for item in observed} == {"unique", "rarest_tiebreak"}


def test_exact_override_boundaries_are_observable_in_every_band():
    valid_cases = (
        {"grid_size": 20, "n_notches": 1, "common_mode": "rarest_tiebreak"},
        {"grid_size": 30, "n_notches": 4, "common_mode": "unique"},
        {"grid_size": 20, "n_notches": 4, "common_mode": "rarest_tiebreak"},
        {"grid_size": 30, "n_notches": 2, "common_mode": "unique"},
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(valid_cases):
            grid = GEN.generate(100 + index, 50 + index, difficulty=band, **overrides)
            assert GEN.observe_overrides(grid) == overrides
            assert GEN.self_check(grid) == []


def test_independent_overrides_adjust_only_unpinned_incompatible_defaults():
    # n=1 forces the unpinned mode to rarity; explicit unique forces the
    # unpinned count away from the one-notch profile. Both remain observable.
    one = GEN.generate(17, 0, n_notches=1)
    assert GEN.observe_overrides(one) == {
        "grid_size": 20,
        "n_notches": 1,
        "common_mode": "rarest_tiebreak",
    }
    unique = GEN.generate(17, 1, common_mode="unique")
    assert GEN.observe_overrides(unique) == {
        "grid_size": 25,
        "n_notches": 3,
        "common_mode": "unique",
    }


def test_linked_three_demo_schedule_kills_every_named_shortcut():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + 3):
                grid = GEN.generate(31337, sample_index, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(31337, start + 3, difficulty=band)
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"] for demo in demos
                ), name


def test_default_schedule_exposes_all_required_semantic_witnesses_per_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        distinct = set()
        for sample_index in range(60):
            grid = GEN.generate(9000 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            distinct.add(GEN._freeze(grid))
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                hits[name] += int(predicate(grid))
        assert all(count > 0 for count in hits.values()), hits
        assert len(distinct) >= 58


def test_short_notches_select_but_do_not_fill():
    grid = GEN.generate(41, 0)
    analysis = GEN._analyze(grid)
    assert analysis["marker_without_short"] != analysis["marker"]
    truth = GEN.rule_mirror(grid)
    for notch in analysis["short"]:
        assert all(truth[r][c] == grid[r][c] for r, c in notch["cells"])
    assert GEN.SEMANTIC_RIVALS[
        "ignore one- and two-cell notches when choosing the marker"
    ](grid) != truth
    assert GEN.SEMANTIC_RIVALS["fill short notches too"](grid) != truth


def test_self_check_rejects_targeted_structural_and_semantic_impostors():
    base = GEN.generate(41, 0)
    analysis = GEN._analyze(base)

    no_walls = [[(r + c) % 10 for c in range(20)] for r in range(20)]

    no_common = copy.deepcopy(base)
    short = analysis["short"][0]
    short_wall = next(iter(short["wall_colors"]))
    replacement = next(
        comp["color"]
        for comp in analysis["wall_components"]
        if comp["color"] != short_wall
    )
    marker_cell = next(
        (r, c) for r, c in short["cells"] if no_common[r][c] == analysis["marker"]
    )
    no_common[marker_cell[0]][marker_cell[1]] = replacement

    no_visible_change = copy.deepcopy(base)
    for notch in analysis["fillable"]:
        for r, c in notch["cells"]:
            no_visible_change[r][c] = analysis["marker"]

    no_fillable = GEN.generate(52, 2)
    nf_analysis = GEN._analyze(no_fillable)
    fillable = nf_analysis["fillable"][0]
    wall_color = next(iter(fillable["wall_colors"]))
    cells = set(fillable["cells"])
    adjacent_pair = next(
        ((r, c), (r + dr, c + dc))
        for r, c in cells
        for dr, dc in GEN._DIRS
        if (r + dr, c + dc) in cells
    )
    for r, c in cells:
        no_fillable[r][c] = wall_color
    decoy = next(iter(set(nf_analysis["common"]) - {nf_analysis["marker"]}))
    no_fillable[adjacent_pair[0][0]][adjacent_pair[0][1]] = nf_analysis["marker"]
    no_fillable[adjacent_pair[1][0]][adjacent_pair[1][1]] = decoy

    rarity_tie = GEN.generate(73, 1)
    rt_analysis = GEN._analyze(rarity_tie)
    marker = rt_analysis["marker"]
    decoy = min(
        set(rt_analysis["common"]) - {marker},
        key=lambda color: rt_analysis["counts"][color],
    )
    needed = rt_analysis["counts"][decoy] - rt_analysis["counts"][marker]
    forbidden = set(rt_analysis["wall"])
    forbidden.update(cell for notch in rt_analysis["notches"] for cell in notch["cells"])
    selected = []
    for r in range(len(rarity_tie)):
        for c in range(len(rarity_tie[0])):
            if needed == 0:
                break
            if (r, c) in forbidden or rarity_tie[r][c] in (marker, decoy):
                continue
            if any(abs(r - rr) + abs(c - cc) == 1 for rr, cc in selected):
                continue
            selected.append((r, c))
            rarity_tie[r][c] = marker
            needed -= 1
        if needed == 0:
            break
    assert needed == 0
    assert GEN._analyze(rarity_tie)["rarity_tie"] is True

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    boolean_cell = copy.deepcopy(base)
    boolean_cell[0][0] = True

    for mutation in (
        no_walls,
        no_common,
        no_visible_change,
        no_fillable,
        rarity_tie,
        ragged,
        boolean_cell,
    ):
        assert GEN.self_check(mutation), mutation


def test_unknown_invalid_and_incompatible_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="warm")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, grid_size=19)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, grid_size=31)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, n_notches=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, n_notches=5)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, common_mode="majority")
    with pytest.raises(ValueError, match="incompatible overrides"):
        GEN.generate(1, 2, n_notches=1, common_mode="unique")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 2, difficulty="extreme")


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(97, 103, difficulty="hard") == second


def test_rule_hash_matches_selected_canonical_authority():
    programs = set()
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    selected = next(iter(programs))
    expected = hashlib.sha256(" ".join(selected.split()).encode()).hexdigest()[:12]
    assert "(>= (length cells) 3)" in selected
    assert "argmin" in selected
    assert GEN.RULE_HASH == expected == "4a6c0f5d3a4a"

    authority = json.loads(
        (ROOT / "data/base/solutions/training/c3fa4749__f6b13494be37.json").read_text(
            encoding="utf-8"
        )
    )
    assert authority["racket_target"]["target_code"] == selected
