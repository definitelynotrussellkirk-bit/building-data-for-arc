from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "7aed1f233b46"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
TARGET = HERE.parents[1]
GENERATOR_PATH = TARGET / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    name = f"review_{TASK_ID}_generator"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row missing for {TASK_ID}")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    return list(row["train"]) + [row["test"]]


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_pin_and_canonical_examples() -> None:
    row = canonical_row()
    assert gen.RULE_HASH == normalized_rule_hash(row["program_solution"]) == "20b242594e4b"
    for pair in canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_census_is_canonical_scale_and_semantically_valid() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seen_profiles = set()
        seen_winner_colors = set()
        output_shapes = set()
        for sample_index in range(60):
            grid = gen.generate(90_000 + band_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == [], (band, sample_index)
            assert gen.strict_canonical_like(grid) == [], (band, sample_index)
            facts = gen.semantic_observables(grid)
            assert len(facts["winners"]) == 1
            assert 9 not in facts["palette"]
            assert 8 not in facts["palette"]
            assert len(facts["palette"]) == 3
            assert gen.rule_mirror(grid) != grid
            seen_profiles.add(facts["scene_profile"])
            seen_winner_colors.add(facts["winner"]["color"])
            output = gen.rule_mirror(grid)
            output_shapes.add((len(output), len(output[0])))
        assert seen_profiles == set(gen.SCHEDULE_PROFILES)
        assert seen_winner_colors >= {2, 3, 4}
        assert len(output_shapes) >= 12


def test_each_profile_refutes_its_named_shortcut() -> None:
    expected = {
        "dense_decoy": "most_cells",
        "larger_decoy": "largest_bbox",
        "extra_winner": "exactly_four",
        "position_decoy": "leftmost",
    }
    for index, profile in enumerate(gen.SCHEDULE_PROFILES):
        grid = gen.generate(
            811_000 + index,
            index,
            difficulty="hard",
            scene_profile=profile,
            winner_height=4,
            winner_width=6,
            n_colors=3,
        )
        truth = gen.rule_mirror(grid)
        assert gen.self_check(grid) == []
        if profile in expected:
            rival_name = expected[profile]
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
        if profile in {"dense_decoy", "larger_decoy", "position_decoy"}:
            assert gen.SEMANTIC_RIVALS["lowest_color"](grid) != truth


def test_canonical_shortcuts_really_fit_all_public_examples() -> None:
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_every_consecutive_five_demo_window_identifies_the_rule() -> None:
    assert gen.EXAMPLES_NEEDED == 5
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            grids = [
                gen.generate(120_000 + band_index, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[: gen.EXAMPLES_NEEDED]
            ]
            query = {"input": grids[-1], "output": [[999]]}
            assert gen.lesson_identifiable(demos, query) == [], (band, start)


def test_override_contract_is_exact_observable_and_band_safe() -> None:
    case_index = 0
    for band in ("easy", "medium", "hard"):
        for scene_profile in gen.SCHEDULE_PROFILES:
            for winner_height, winner_width in ((3, 3), (6, 8)):
                for n_colors in (3, 4):
                    for winner_color in (2, 4):
                        requested = {
                            "scene_profile": scene_profile,
                            "winner_height": winner_height,
                            "winner_width": winner_width,
                            "n_colors": n_colors,
                            "winner_color": winner_color,
                        }
                        grid = gen.generate(
                            330_000 + case_index,
                            case_index * 17 + 3,
                            difficulty=band,
                            **requested,
                        )
                        assert gen.self_check(grid) == [], (band, requested)
                        assert gen.observe_overrides(grid) == requested
                        case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, misspelled_axis=3)


@pytest.mark.parametrize(
    "axis,value",
    [
        ("scene_profile", "not_a_profile"),
        ("winner_height", 2),
        ("winner_height", 7),
        ("winner_width", 2),
        ("winner_width", 9),
        ("n_colors", 2),
        ("n_colors", 5),
        ("winner_color", 1),
        ("winner_color", 5),
    ],
)
def test_invalid_override_values_reject(axis: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, 9, difficulty="hard", **{axis: value})


def test_replay_freshness_global_rng_purity_and_input_purity() -> None:
    random.seed(20261002)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    original = copy.deepcopy(first)
    gen.self_check(first)
    gen.strict_canonical_like(first)
    gen.semantic_observables(first)
    gen.rule_mirror(first)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(first)
    assert first == original


def test_targeted_impostors_are_rejected() -> None:
    grid = gen.generate(441, 4, scene_profile="canonical_corners")
    facts = gen.semantic_observables(grid)
    winner = facts["winner"]

    no_winner = copy.deepcopy(grid)
    row, col = winner["cells"][0]
    no_winner[row][col] = 0
    assert gen.self_check(no_winner)

    second_winner = copy.deepcopy(grid)
    decoy = facts["decoys"][0]
    r1, c1, r2, c2 = decoy["bbox"]
    second_winner[r1][c1] = decoy["color"]
    second_winner[r1][c2] = decoy["color"]
    second_winner[r2][c1] = decoy["color"]
    second_winner[r2][c2] = decoy["color"]
    assert gen.self_check(second_winner)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 2, 3]],
        [[0.0, 2, 3]],
        [[-1, 2, 3]],
        [[10, 2, 3]],
    ],
)
def test_malformed_inputs_are_rejected_without_crashing(grid) -> None:
    assert gen.self_check(grid)


def test_declared_output_codomain_is_exact_and_fully_reachable() -> None:
    outputs = {
        tuple(tuple(row) for row in gen.rule_mirror(gen.generate(
            550_000 + height * 100 + width,
            height * 100 + width,
            difficulty="hard",
            scene_profile="canonical_corners",
            winner_height=height,
            winner_width=width,
        )))
        for height in range(3, 7)
        for width in range(3, 9)
    }
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 24
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN


def test_workspace_shortcut_probe_reports_clean_lesson_windows() -> None:
    probe_path = TARGET / "workspace" / "shortcut_probe.py"
    spec = importlib.util.spec_from_file_location("review_shortcut_probe", probe_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_census(seed=901_002, samples=15, difficulty="hard")
    assert report["generation_failures"] == []
    assert report["surviving_lesson_rivals"] == {}
    assert set(report["profile_counts"]) == set(gen.SCHEDULE_PROFILES)
    assert all(count > 0 for count in report["shortcut_witness_counts"].values())
    assert report["distinct_output_shapes"] >= 10
