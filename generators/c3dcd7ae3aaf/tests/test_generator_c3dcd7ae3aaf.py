from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "c3dcd7ae3aaf"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_record() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError(f"canonical record missing for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    record = _canonical_record()
    puzzle = record.get("puzzle", record)
    return [*puzzle["train"], *puzzle["test"]]


def _normalized_rule_hash() -> str:
    record = _canonical_record()
    program = record["program_solution"]
    normalized = " ".join(program.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _ordinary_draws(count: int = 36):
    difficulties = (None, "easy", "medium", "hard")
    for index in range(count):
        yield GEN.generate(
            seed=20_260_928,
            sample_index=index,
            difficulty=difficulties[index % len(difficulties)],
        )


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == _normalized_rule_hash()
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "n_targets": 2, "n_distractors": 2},
        {"grid_h": 10, "grid_w": 10, "n_targets": 4, "n_distractors": 3},
        {"grid_h": 9, "grid_w": 8, "n_targets": 3, "n_distractors": 3},
    ],
)
def test_public_override_boundaries_round_trip(difficulty, overrides):
    grid = GEN.generate(seed=91, sample_index=17, difficulty=difficulty, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid) == []


def test_unknown_override_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(seed=1, sample_index=0, made_up_axis=1)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(seed=1, sample_index=0, difficulty="impossible")


def test_every_ordinary_draw_contains_the_decisive_teaching_contrasts():
    for grid in _ordinary_draws():
        assert GEN.self_check(grid) == []
        expected = GEN.rule_mirror(grid)
        assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert witness(grid), witness_name
            named_rivals = GEN.WITNESS_RIVALS[witness_name]
            assert named_rivals
            assert all(GEN.SEMANTIC_RIVALS[name](grid) != expected for name in named_rivals)
        assert all(rival(grid) != expected for rival in GEN.SEMANTIC_RIVALS.values())


def test_two_example_sliding_lessons_are_identifiable():
    pairs = [
        {"input": grid, "output": GEN.rule_mirror(grid)}
        for grid in _ordinary_draws(18)
    ]
    assert GEN.EXAMPLES_NEEDED == 2
    for start in range(len(pairs) - GEN.EXAMPLES_NEEDED):
        demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
        query = pairs[start + GEN.EXAMPLES_NEEDED]
        assert GEN.lesson_identifiable(demos, query) == []


def test_mutation_fixtures_are_rejected_by_task_linked_checker():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
        assert GEN.strict_canonical_like(grid), name


def test_generation_is_deterministic_and_does_not_touch_global_rng():
    before = random.getstate()
    first = GEN.generate(seed=771, sample_index=13, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(seed=771, sample_index=13, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert before == middle == after
