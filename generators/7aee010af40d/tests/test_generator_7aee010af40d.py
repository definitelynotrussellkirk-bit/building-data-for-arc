"""Focused regression tests for semantic generator 7aee010af40d."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.7aee010af40d.generator"
)
ROOT = find_root(__file__)


def _canonical_pairs():
    yield from canonical_pairs(GEN.TASK_ID, root=ROOT)


def _erase_component(grid, component):
    out = copy.deepcopy(grid)
    for row, col in component["cells"]:
        out[row][col] = 0
    return out


def test_canonical_inputs_and_outputs_match_declared_rule():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_five_example_schedule_is_lesson_identifiable():
    for seed in range(12):
        pairs = []
        for sample_index in range(6):
            grid = GEN.generate(seed, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:5], pairs[5]) == []
        assert all(
            any(witness(pair["input"]) for pair in pairs[:5])
            for witness in GEN.SEMANTIC_WITNESSES.values()
        )


def test_every_six_pair_query_rotation_is_identifiable():
    """Holding out any one of six consecutive pairs must remain teachable."""
    for band in ("easy", "medium", "hard"):
        for seed in range(3):
            pairs = []
            for sample_index in range(6):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    seed,
                    query_index,
                )


def test_identifiability_does_not_require_arbitrary_room_count():
    """Named rivals can be refuted even when random placement repeats a room."""
    pairs = []
    for sample_index in range(26, 32):
        grid = GEN.generate(3012422862, sample_index, difficulty="hard")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:5], pairs[5]) == []


def test_semantic_witnesses_name_executable_wrong_rules():
    assert GEN.SEMANTIC_RIVALS
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS
    assert set(GEN.SEMANTIC_WITNESSES) <= set(GEN.WITNESS_RIVALS)

    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        assert witness_name in GEN.SEMANTIC_WITNESSES
        assert rival_names
        assert set(rival_names) <= set(GEN.SEMANTIC_RIVALS)

    witnessed = {name: False for name in GEN.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for seed in range(5):
            for sample_index in range(10):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                official = GEN.rule_mirror(grid)
                for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
                    if not witness(grid):
                        continue
                    witnessed[witness_name] = True
                    rivals = GEN.WITNESS_RIVALS[witness_name]
                    assert any(
                        GEN.SEMANTIC_RIVALS[name](grid) != official
                        for name in rivals
                    ), (witness_name, band, seed, sample_index)
    assert all(witnessed.values()), witnessed


def test_first_orange_is_a_real_canonical_shortcut():
    rival = GEN.CANONICAL_SHORTCUTS["first_orange"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]



def test_query_output_is_not_a_copy_of_any_demonstration():
    """A five-demo lesson must not reveal the query answer by output copying."""
    for band in ("easy", "medium", "hard"):
        for seed in range(3):
            for start in range(GEN.EXAMPLES_NEEDED):
                outputs = [
                    GEN.rule_mirror(
                        GEN.generate(seed, start + offset, difficulty=band)
                    )
                    for offset in range(GEN.EXAMPLES_NEEDED + 1)
                ]
                assert outputs[-1] not in outputs[:-1], (band, seed, start)

def test_override_boundaries_are_exact_in_every_band():
    cases = (
        {
            "grid_h": 8,
            "grid_w": 10,
            "small_k": 2,
            "n_big": 2,
            "n_distractors": 1,
            "distractor_color": 1,
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "small_k": 6,
            "n_big": 3,
            "n_distractors": 2,
            "distractor_color": 9,
        },
    )
    for band in ("easy", "medium", "hard"):
        for case in cases:
            grid = GEN.generate(991, 23, difficulty=band, **case)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == case


def test_determinism_fresh_returns_and_global_rng_purity():
    before = random.getstate()
    first = GEN.generate(90210, 17, difficulty="hard")
    second = GEN.generate(90210, 17, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 8
    assert GEN.generate(90210, 17, difficulty="hard") == second

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_self_check_rejects_targeted_structural_impostors():
    grid = GEN.generate(
        4242,
        3,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        small_k=4,
        n_big=3,
        n_distractors=2,
        distractor_color=5,
    )
    assert GEN.self_check(grid) == []
    oranges = sorted(GEN._components(grid, 7), key=lambda comp: len(comp["cells"]))
    others = [comp for comp in GEN._components(grid) if comp["color"] != 7]

    no_distractors = copy.deepcopy(grid)
    for component in others:
        for row, col in component["cells"]:
            no_distractors[row][col] = 0

    too_few_oranges = _erase_component(grid, oranges[-1])
    too_few_oranges = _erase_component(too_few_oranges, oranges[-2])

    tied_smallest = _erase_component(grid, oranges[1])
    target_shape = GEN._normalize(oranges[0]["cells"])
    row0 = min(row for row, _ in oranges[1]["cells"])
    col0 = min(col for _, col in oranges[1]["cells"])
    for row, col in target_shape:
        tied_smallest[row0 + row][col0 + col] = 7

    second_distractor_color = copy.deepcopy(grid)
    row, col = others[0]["cells"][0]
    second_distractor_color[row][col] = 6

    impostors = {
        "no_distractors": no_distractors,
        "too_few_oranges": too_few_oranges,
        "tied_smallest": tied_smallest,
        "second_distractor_color": second_distractor_color,
    }
    for name, impostor in impostors.items():
        assert GEN.self_check(impostor), name


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = GEN.generate(88, 3, difficulty="hard", distractor_color=5)
    target = GEN._target_component(grid)
    recombined = copy.deepcopy(grid)
    replacement_color = 6
    assert replacement_color not in {value for row in grid for value in row}
    for row, col in target["cells"]:
        recombined[row][col] = replacement_color

    assert GEN.self_check(recombined)
    # The Racket rule has two or more orange components left and therefore has
    # a lawful selection; the Python mirror proves the same executable shape.
    output = GEN.rule_mirror(recombined)
    assert output and output[0]
    assert all(value in (0, 8) for row in output for value in row)
