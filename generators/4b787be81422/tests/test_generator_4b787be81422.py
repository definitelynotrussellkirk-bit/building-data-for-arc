"""Focused semantic and regression tests for generator 4b787be81422."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "4b787be81422"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _episode(seed: int, start: int, band: str) -> list[dict]:
    episode = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty=band)
        episode.append({"input": grid, "output": gen.rule_mirror(grid)})
    return episode


def test_rule_pin_and_all_canonical_pairs() -> None:
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "4a60caa6e208"
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 2

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 8
    assert {pair["output"][0][0] for pair in pairs} == {1, 7}
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        frozen = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == frozen


def test_every_sliding_four_demo_window_is_identifiable() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            episode = _episode(71_000 + start, start, band)
            assert gen.lesson_identifiable(episode[:-1], episode[-1]) == []

            demos = episode[:-1]
            labels = {demo["output"][0][0] for demo in demos}
            assert labels == {1, 7}
            analyses = [gen._analysis(demo["input"]) for demo in demos]
            assert len({item["fg_color"] for item in analyses}) >= 2
            assert any(
                left["foreground_count"] == right["foreground_count"]
                and demos[i]["output"] != demos[j]["output"]
                for i, left in enumerate(analyses)
                for j, right in enumerate(analyses)
                if i < j
            )


def test_named_witnesses_fire_and_refute_named_rivals() -> None:
    grids = [
        gen.generate(181, sample_index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for sample_index in range(32)
    ]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(
                rival(grid) != gen.rule_mirror(grid) for grid in hits
            ), (witness_name, rival_name)

    assert set(gen.SCHEDULE_PROFILES) == {
        gen.schedule_profile(5, index, difficulty="medium")
        for index in range(4)
    }


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_boundary_overrides_are_exact_observable_and_band_safe(band: str) -> None:
    cases = [
        {"grid_h": 3},
        {"grid_h": 8},
        {"grid_w": 3},
        {"grid_w": 8},
        {"fg_color": 1},
        {"fg_color": 9},
        {"symmetric": False},
        {"symmetric": True},
        {
            "grid_h": 8,
            "grid_w": 8,
            "fg_color": 9,
            "symmetric": False,
        },
        {
            "grid_h": 3,
            "grid_w": 3,
            "fg_color": 1,
            "symmetric": True,
        },
    ]
    for case_index, overrides in enumerate(cases):
        grid = gen.generate(
            9_100 + case_index,
            case_index,
            difficulty=band,
            **overrides,
        )
        assert gen.self_check(
            grid, difficulty=band, meta={"overrides": overrides}
        ) == []
        observed = gen.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value


def test_override_contract_rejects_unknown_invalid_and_out_of_range_values() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(TypeError, match="grid_h"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises(TypeError, match="symmetric"):
        gen.generate(1, 0, symmetric=1)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=2)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_w=9)
    with pytest.raises(ValueError):
        gen.generate(1, 0, fg_color=0)
    with pytest.raises(ValueError):
        gen.generate(1, 0, fg_color=10)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_self_check_rejects_explicit_mutation_impostors() -> None:
    valid = gen.generate(404, 5, difficulty="medium")
    assert gen.self_check(valid) == []
    h, w = len(valid), len(valid[0])
    fg = gen.observe_overrides(valid)["fg_color"]
    second = 1 if fg != 1 else 2

    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]
    monochrome_zero = [[0] * w for _ in range(h)]
    monochrome_fg = [[fg] * w for _ in range(h)]
    singleton = [[0] * w for _ in range(h)]
    singleton[h // 2][w // 2] = fg
    horizontal_line = [[0] * w for _ in range(h)]
    for col in range(min(4, w)):
        horizontal_line[h // 2][col] = fg
    solid_2x2 = [[0] * w for _ in range(h)]
    for row in range(2):
        for col in range(2):
            solid_2x2[row][col] = fg
    three_color = copy.deepcopy(valid)
    three_color[0][0] = second
    too_small = [row[:2] for row in valid[:2]]
    bool_cell = copy.deepcopy(valid)
    bool_cell[0][0] = True

    for name, impostor in {
        "ragged": ragged,
        "monochrome_zero": monochrome_zero,
        "monochrome_foreground": monochrome_fg,
        "singleton": singleton,
        "horizontal_line": horizontal_line,
        "solid_2x2": solid_2x2,
        "three_color": three_color,
        "too_small": too_small,
        "boolean_cell": bool_cell,
    }.items():
        assert gen.self_check(impostor), name


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(52711)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="hard")
    second = gen.generate(17, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 0 if first[0][0] else 9
    assert first != second
    assert second == gen.generate(17, 9, difficulty="hard")
    assert second != gen.generate(17, 10, difficulty="hard")


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(bad_sample_index) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(991, bad_sample_index, difficulty="easy")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, "1"])
def test_generate_rejects_noninteger_seed_scalars(bad_seed) -> None:
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


def test_top_bottom_shortcut_counterexample_is_source_bound() -> None:
    path = Path(__file__).resolve().parents[1] / "counterexamples" / "top_bottom_shortcut.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    grid = payload["input"]

    assert payload["ordinary_generation"] == {
        "seed": 0,
        "sample_index": 3,
        "difficulty": "medium",
        "overrides": {},
    }
    assert gen.generate(0, 3, difficulty="medium") == grid
    analysis = gen._analysis(grid)
    assert analysis["top_bottom_symmetric"] is True
    assert analysis["symmetric"] is False
    assert gen._rival_top_bottom(grid) == [[1]]
    assert gen.rule_mirror(grid) == [[7]]
    assert payload["authoritative_output"] == [[7]]
