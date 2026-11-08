from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random
from collections import Counter

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "d3575d4206d7"
ROOT = find_root(__file__)
DATA = canonical_path(ROOT).parent.parent
TRAINING_BASE = DATA / "base/solutions/training/4ff4c9da__d3575d4206d7.json"
AUGMENTED_BASE = DATA / "base/solutions/augmented/4ff4c9da__1c48922c1f8a.json"


def _load_generator():
    source = ROOT / "generators" / TASK_ID / "generator.py"
    if source.is_file():
        spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


gen = _load_generator()


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in canonical_pairs(TASK_ID, root=ROOT, variant=0)
    ]


def test_rule_pin_all_canonical_pairs_and_task_local_authorities() -> None:
    row = _canonical_row()
    assert gen.RULE_HASH == "abf875129734"
    normalized_rule = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized_rule.encode()).hexdigest()[:12] == gen.RULE_HASH
    assert gen.EXAMPLES_NEEDED == 3

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "Python audit oracle mutated a canonical input"

    training = json.loads(TRAINING_BASE.read_text(encoding="utf-8"))
    augmented = json.loads(AUGMENTED_BASE.read_text(encoding="utf-8"))
    assert training["racket_target"]["target_code"] == row["program_solution"]
    assert augmented["racket_target"]["target_code"] == row["program_solution"]
    assert augmented["racket_target"]["raw_code"] != row["program_solution"]

    # The augmented source exposes all four canonical input/output pairs as
    # training examples, in a different order.  Audit every source-row pair.
    augmented_pairs = json.loads(augmented["visible_context"]["samples_text"])["train"]
    assert len(augmented_pairs) == 4
    canonical_keys = {
        json.dumps(pair, sort_keys=True, separators=(",", ":")) for pair in pairs
    }
    assert {
        json.dumps(pair, sort_keys=True, separators=(",", ":"))
        for pair in augmented_pairs
    } == canonical_keys
    for pair in augmented_pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_three_demo_sliding_schedule_is_identifiable_and_refutes_rivals() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                gen.generate(17_071, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[: gen.EXAMPLES_NEEDED]
            ]
            query = {
                "input": grids[gen.EXAMPLES_NEEDED],
                "output": gen.rule_mirror(grids[gen.EXAMPLES_NEEDED]),
            }
            assert gen.lesson_identifiable(demos, query) == [], (difficulty, start)

            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_grid = next(
                    (grid for grid in grids[: gen.EXAMPLES_NEEDED] if witness(grid)),
                    None,
                )
                assert witness_grid is not None, (difficulty, start, witness_name)
                official = gen.rule_mirror(witness_grid)
                for rival_name in gen.WITNESS_RIVALS[witness_name]:
                    assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != official


def test_override_matrix_is_exact_observable_and_band_safe() -> None:
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for layout in gen.LAYOUTS:
            for scene_mode in gen.SCENE_MODES:
                for signal_color in (1, 9):
                    for divider_color in (0, 1, 9):
                        requested = {
                            "layout": layout,
                            "scene_mode": scene_mode,
                            "signal_color": signal_color,
                            "divider_color": divider_color,
                        }
                        grid = gen.generate(
                            30_000 + case_index,
                            case_index * 11 + 3,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.strict_canonical_like(grid) == []
                        assert gen.observe_overrides(grid) == requested
                        case_index += 1

    # Equal signal/divider colors are a supported, observable boundary case.
    grid = gen.generate(
        17,
        19,
        difficulty="hard",
        layout="canonical_27",
        scene_mode="mixed",
        signal_color=6,
        divider_color=6,
    )
    assert gen.observe_overrides(grid)["signal_color"] == 6
    assert gen.observe_overrides(grid)["divider_color"] == 6

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


@pytest.mark.parametrize(
    "axis,value",
    [
        ("layout", "canonical_19"),
        ("scene_mode", "degenerate"),
        ("signal_color", 0),
        ("signal_color", 8),
        ("divider_color", 8),
        ("divider_color", 10),
    ],
)
def test_invalid_override_values_reject(axis: str, value: object) -> None:
    with pytest.raises(ValueError):
        gen.generate(7, 9, difficulty="medium", **{axis: value})


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second

    by_band = {
        band: gen.generate(991, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in by_band.values()}) >= 2


def test_mutation_fixtures_and_negative_recombination_are_calibrated() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    source, recombined = gen.negative_recombination_fixture()
    assert gen.self_check(source) == []
    assert gen.self_check(recombined), "distribution checker accepted recombination"
    # Recombination is outside the generator distribution, not outside the
    # total oracle's executable input domain.
    output = gen.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert len(output[0]) == len(recombined[0])


def test_returned_draw_census_keeps_profiles_branches_and_rivals_live() -> None:
    profile_counts: Counter[tuple[str, str]] = Counter()
    witness_counts: Counter[tuple[str, str]] = Counter()
    rival_disagreements: Counter[tuple[str, str]] = Counter()

    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for sample_index in range(80):
            grid = gen.generate(800_000 + band_index, sample_index, difficulty=difficulty)
            assert gen.strict_canonical_like(grid) == []
            observed = gen.observe_overrides(grid)
            profile_counts[(difficulty, f"{observed['layout']}:{observed['scene_mode']}")] += 1
            official = gen.rule_mirror(grid)
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                witness_counts[(difficulty, witness_name)] += 1
                for rival_name in gen.WITNESS_RIVALS[witness_name]:
                    rival_disagreements[(difficulty, rival_name)] += int(
                        gen.SEMANTIC_RIVALS[rival_name](grid) != official
                    )

    for difficulty in ("easy", "medium", "hard"):
        assert all(
            witness_counts[(difficulty, name)] > 0
            for name in gen.SEMANTIC_WITNESSES
        )
        assert all(
            rival_disagreements[(difficulty, name)] > 0
            for name in gen.SEMANTIC_RIVALS
        )
        assert sum(count for (band, _), count in profile_counts.items() if band == difficulty) == 80
