from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK = "01de328b19ce"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def crop_nonzero(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def independent_rule(grid):
    anchors = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 1 <= value <= 5
    ]
    erased = [[0 if 1 <= value <= 5 else value for value in row] for row in grid]
    template = crop_nonzero(erased)

    def cw(g):
        return [list(row) for row in zip(*g[::-1])]

    transforms = {
        1: lambda g: [row[:] for row in g],
        2: cw,
        3: lambda g: [row[::-1] for row in g[::-1]],
        4: lambda g: cw(cw(cw(g))),
        5: lambda g: [row[::-1] for row in g],
    }
    out = [[0] * len(grid[0]) for _ in grid]
    for top, left, code in anchors:
        sub = transforms[code](template)
        for dr, row in enumerate(sub):
            for dc, value in enumerate(row):
                rr, cc = top + dr, left + dc
                if value and 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                    out[rr][cc] = value
    return out


def test_rule_hash_and_independent_solver_match_all_canonical_pairs():
    assert GEN.RULE_HASH == "f6817aded7d7"
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_ordinary_schedule_is_lawful_observable_and_semantically_rich(difficulty):
    seen_textures = set()
    seen_profiles = set()
    for sample_index in range(20):
        grid = GEN.generate(71237, sample_index, difficulty=difficulty)
        observed = GEN.observe_overrides(grid)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert independent_rule(grid) == GEN.rule_mirror(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert observed["n_anchors"] == 3
        seen_textures.add(observed["texture"])
        seen_profiles.add(GEN.schedule_profile(71237, sample_index, difficulty))
    assert seen_textures == {"plain", "multicolor", "edge_clip"}
    assert seen_profiles == set(GEN.SCHEDULE_PROFILES)


def test_difficulty_bands_are_not_dead_or_aliased():
    for sample_index in range(12):
        scenes = {
            difficulty: frozen(GEN.generate(91, sample_index, difficulty=difficulty))
            for difficulty in ("easy", "medium", "hard")
        }
        assert len(set(scenes.values())) == 3


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "case",
    [
        {"grid_h": 8},
        {"grid_h": 14},
        {"grid_w": 10},
        {"grid_w": 16},
        {"n_anchors": 1},
        {"n_anchors": 5},
        {"texture": "plain"},
        {"texture": "multicolor"},
        {"texture": "edge_clip"},
        {"texture": "rot_symmetric_base"},
        {"grid_h": 8, "grid_w": 10, "n_anchors": 5, "texture": "edge_clip"},
        {"grid_h": 14, "grid_w": 16, "n_anchors": 1, "texture": "multicolor"},
    ],
)
def test_exact_override_boundaries_are_realized_and_observed(difficulty, case):
    grid = GEN.generate(8081, 17, difficulty=difficulty, **case)
    observed = GEN.observe_overrides(grid)
    for axis, expected in case.items():
        assert observed[axis] == expected
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": case}) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_no_anchor_degenerate_is_observable_and_has_blank_answer(difficulty):
    grid = GEN.generate(707, 4, difficulty=difficulty, texture="no_anchors")
    assert GEN.observe_overrides(grid)["texture"] == "no_anchors"
    assert GEN.observe_overrides(grid)["n_anchors"] == 0
    assert GEN.self_check(grid) == []
    assert independent_rule(grid) == [[0] * len(grid[0]) for _ in grid]


def test_incompatible_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises(ValueError, match="incompatible") as exc_info:
        GEN.generate(1, 0, texture="no_anchors", n_anchors=1)
    assert set(exc_info.value.incompatible_axes) == {"texture", "n_anchors"}
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_self_check_rejects_targeted_rule_hiding_impostors():
    base = GEN.generate(44, 2, texture="multicolor")

    ragged = deepcopy(base)
    ragged[-1].pop()

    invalid_color = deepcopy(base)
    invalid_color[0][0] = 10

    no_template = [[0 if 6 <= value <= 9 else value for value in row] for row in base]

    duplicate_commands = deepcopy(base)
    anchors = GEN._anchors(duplicate_commands)
    duplicate_commands[anchors[1][0]][anchors[1][1]] = anchors[0][2]

    touching_command = deepcopy(base)
    for r, c, _ in GEN._anchors(touching_command):
        touching_command[r][c] = 0
    template_cells = [
        (r, c)
        for r, row in enumerate(touching_command)
        for c, value in enumerate(row)
        if 6 <= value <= 9
    ]
    tr, tc = template_cells[0]
    candidates = [
        (tr + dr, tc + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
        and 0 <= tr + dr < len(touching_command)
        and 0 <= tc + dc < len(touching_command[0])
        and touching_command[tr + dr][tc + dc] == 0
    ]
    rr, cc = candidates[0]
    touching_command[rr][cc] = 1

    unlawful_symmetric = [[0] * 12 for _ in range(10)]
    for r in range(1, 4):
        for c in range(1, 4):
            unlawful_symmetric[r][c] = 6
    unlawful_symmetric[6][8] = 2

    for name, grid in {
        "ragged": ragged,
        "invalid_color": invalid_color,
        "no_template": no_template,
        "duplicate_commands": duplicate_commands,
        "touching_command": touching_command,
        "unlawful_symmetric": unlawful_symmetric,
    }.items():
        assert GEN.self_check(grid), name


def test_determinism_freshness_input_purity_and_global_rng_independence():
    random.seed(0x01DE)
    global_state = random.getstate()
    first = GEN.generate(123, 19, difficulty="hard", texture="edge_clip", n_anchors=5)
    assert random.getstate() == global_state
    second = GEN.generate(123, 19, difficulty="hard", texture="edge_clip", n_anchors=5)
    assert first == second
    assert first is not second and first[0] is not second[0]

    pristine = deepcopy(first)
    official = GEN.rule_mirror(first)
    assert first == pristine
    assert official == independent_rule(first)

    first[0][0] = 9
    assert GEN.generate(123, 19, difficulty="hard", texture="edge_clip", n_anchors=5) == second


def test_every_sliding_four_demo_window_identifies_every_query_rival():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(9991 + start, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_declared_witnesses_fire_and_refute_their_named_rivals():
    firings = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(24):
        grid = GEN.generate(314159, sample_index, difficulty="medium")
        official = GEN.rule_mirror(grid)
        for witness, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                firings[witness] += 1
                assert any(
                    GEN.SEMANTIC_RIVALS[name](deepcopy(grid)) != official
                    for name in GEN.WITNESS_RIVALS[witness]
                )
    assert all(count > 0 for count in firings.values())


def test_large_sample_has_input_output_and_layout_diversity():
    grids = [GEN.generate(seed, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3]) for seed in range(180)]
    outputs = [GEN.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 170
    assert len({frozen(grid) for grid in outputs}) >= 165
    assert {GEN.observe_overrides(grid)["texture"] for grid in grids} == {"plain", "multicolor", "edge_clip"}
