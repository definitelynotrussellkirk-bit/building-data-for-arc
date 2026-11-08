from __future__ import annotations

import copy
import importlib
import random

import pytest


TASK_ID = "03829f6274d2"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def test_rule_hash_and_version_are_pinned() -> None:
    assert GEN.RULE_HASH == "dac192e5427e"
    assert GEN.VERSION == "2.0.0"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8},
        {"grid_h": 17},
        {"grid_w": 8},
        {"grid_w": 18},
        {"n_markers": 1},
        {"n_markers": 8},
        {"template_size": 2},
        {"template_size": 7},
        {"template_color": 1},
        {"template_color": 8},
        {"texture": "plain"},
        {"texture": "edge_fit"},
        {
            "grid_h": 8,
            "grid_w": 8,
            "n_markers": 8,
            "template_size": 7,
            "template_color": 8,
            "texture": "edge_fit",
        },
    ],
)
def test_declared_boundary_overrides_are_exact(band: str, overrides: dict) -> None:
    grid = GEN.generate(31, 7, difficulty=band, **overrides)
    observed = GEN.observe_overrides(grid)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    for key, value in overrides.items():
        assert observed[key] == value


def test_plain_and_edge_fit_are_observably_different() -> None:
    common = dict(
        grid_h=10,
        grid_w=10,
        n_markers=4,
        template_size=5,
        template_color=3,
    )
    plain = GEN.generate(9, 2, difficulty="medium", texture="plain", **common)
    edge = GEN.generate(9, 2, difficulty="medium", texture="edge_fit", **common)
    assert plain != edge
    assert GEN.observe_overrides(plain)["texture"] == "plain"
    assert GEN.observe_overrides(edge)["texture"] == "edge_fit"


def test_deterministic_replay_fresh_returns_and_global_rng_purity() -> None:
    random.seed(987654)
    state = random.getstate()
    first = GEN.generate(77, 11, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(77, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    third = GEN.generate(77, 11, difficulty="hard")
    assert third == second


def test_self_check_rejects_four_structural_impostors() -> None:
    valid = GEN.generate(101, 3, difficulty="medium")
    assert GEN.self_check(valid) == []

    no_markers = copy.deepcopy(valid)
    no_markers = [[0 if cell == 9 else cell for cell in row] for row in no_markers]
    assert any("anchor" in msg or "marker" in msg for msg in GEN.self_check(no_markers))

    second_template = copy.deepcopy(valid)
    color = GEN.observe_overrides(valid)["template_color"]
    for r, row in enumerate(second_template):
        for c, cell in enumerate(row):
            if cell == 0:
                second_template[r][c] = color
                # Find a distant zero for a disconnected second component.
                for rr in range(len(second_template) - 1, -1, -1):
                    for cc in range(len(second_template[0]) - 1, -1, -1):
                        if second_template[rr][cc] == 0 and abs(rr-r) + abs(cc-c) > 3:
                            second_template[rr][cc] = color
                            break
                    else:
                        continue
                    break
                break
        else:
            continue
        break
    assert any("connected" in msg for msg in GEN.self_check(second_template))

    two_colours = copy.deepcopy(valid)
    changed = False
    for r, row in enumerate(two_colours):
        for c, cell in enumerate(row):
            if cell not in (0, 9):
                two_colours[r][c] = 8 if cell != 8 else 7
                changed = True
                break
        if changed:
            break
    assert any("one colour" in msg for msg in GEN.self_check(two_colours))

    out_of_bounds_anchor = copy.deepcopy(valid)
    out_of_bounds_anchor[-1][-1] = 9
    assert any("fully in bounds" in msg for msg in GEN.self_check(out_of_bounds_anchor))


def test_four_slot_schedule_is_lesson_identifiable() -> None:
    demos = []
    for sample_index in range(4):
        grid = GEN.generate(12345, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": GEN._solve_python(grid)})
    query_grid = GEN.generate(12345, 4, difficulty="hard")
    query = {"input": query_grid, "output": GEN._solve_python(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_inputs_are_accepted_by_strict_hook() -> None:
    from scripts.canonical_profile_gate import canonical_inputs

    canonical = canonical_inputs(TASK_ID)
    assert len(canonical) == 3
    assert [GEN.strict_canonical_like(grid) for grid in canonical] == [[], [], []]
