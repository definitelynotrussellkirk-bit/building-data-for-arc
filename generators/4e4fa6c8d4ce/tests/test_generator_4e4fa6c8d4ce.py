from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "4e4fa6c8d4ce"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BASE_AUTHORITIES = (
    ROOT / "shared" / "data" / "base" / "solutions" / "training" / "6ecd11f4__4e4fa6c8d4ce.json",
    ROOT / "shared" / "data" / "base" / "solutions" / "augmented" / "6ecd11f4__3eb7b3d6e0ab.json",
)
BANDS = ("easy", "medium", "hard")

sys.path.insert(0, str(ROOT / "shared" / "runtime"))
from puzzle_generators import base as gen_base  # noqa: E402


def _load():
    name = f"review_{TASK_ID}_generator"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_rows() -> list[dict]:
    rows = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def _canonical_source() -> str:
    return next(row["program_solution"] for row in _canonical_rows())


def _canonical_pairs() -> list[dict]:
    pairs: list[dict] = []
    for row in _canonical_rows():
        pairs.extend(row.get("train", []))
        pairs.extend(row.get("test", []))
    return pairs


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(module, seed: int, sample_index: int, band: str) -> dict:
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": module.rule_mirror(grid)}


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_canonical_acceptance_and_python_mirror() -> None:
    module = _load()
    assert module.RULE_HASH == _normalized_rule_hash(_canonical_source()) == "adb72b5aa400"
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        assert module.self_check(copy.deepcopy(pair["input"])) == []
        assert module.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert module.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_selected_racket_authorities_are_exactly_synchronized() -> None:
    canonical = _canonical_source()
    for path in BASE_AUTHORITIES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["racket_target"]["target_code"] == canonical, path


def test_declared_override_cross_product_round_trips_and_unknowns_reject() -> None:
    module = _load()
    cases = (
        {
            "palette_size": 3,
            "block_size": 3,
            "layout": "below",
            "gap": 0,
            "palette_profile": "seven_nonshape",
            "mask_profile": "connected",
        },
        {
            "palette_size": 4,
            "block_size": 5,
            "layout": "right",
            "gap": 1,
            "palette_profile": "shape_filled",
            "mask_profile": "disconnected",
        },
        {
            "palette_size": 4,
            "block_size": 4,
            "layout": "below",
            "gap": 1,
            "palette_profile": "eight_nonshape",
            "mask_profile": "connected",
        },
    )
    for band_index, band in enumerate(BANDS):
        for index, requested in enumerate(cases):
            grid = module.generate(
                8100 + 100 * band_index + index,
                index,
                difficulty=band,
                **requested,
            )
            assert module.self_check(grid) == []
            assert module.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        module.generate(0, 0, unknown_axis=1)
    with pytest.raises(ValueError):
        module.generate(0, 0, palette_size=2)
    with pytest.raises(ValueError):
        module.generate(0, 0, palette_profile="shape_only")


def test_default_keyed_draws_round_trip_through_observer() -> None:
    module = _load()
    captured = []
    gen_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(BANDS):
            for sample_index in range(16):
                grid = module.generate(
                    8200 + band_index,
                    sample_index,
                    difficulty=band,
                )
                ctx = captured[-1]
                recorded = ctx.recorded_draws()
                assert set(recorded) == set(module.AXES)
                assert {axis: recorded[axis] for axis in module.AXES} == module.observe_overrides(grid)
    finally:
        gen_base.set_ctx_observer(None)


def test_four_slot_schedule_matches_canonical_profiles_and_covers_witnesses() -> None:
    module = _load()
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    assert canonical_profiles == {
        (27, 25, 9),
        (27, 21, 9),
        (22, 22, 10),
        (21, 24, 10),
    }
    assert module.EXAMPLES_NEEDED == 3
    assert tuple(module.SCHEDULE_PROFILES) == (
        "canonical_27x25",
        "canonical_27x21",
        "canonical_22x22",
        "canonical_21x24",
    )

    for band_index, band in enumerate(BANDS):
        produced = [
            module.generate(8300 + band_index, index, difficulty=band)
            for index in range(4)
        ]
        assert {_profile(grid) for grid in produced} == canonical_profiles
        assert all(module.strict_canonical_like(grid) == [] for grid in produced)
        assert module.SEMANTIC_WITNESSES["shape_color_survives"](produced[1])
        assert module.SEMANTIC_WITNESSES["shape_color_survives"](produced[2])
        assert module.SEMANTIC_WITNESSES["four_by_four_output"](produced[2])
        assert module.SEMANTIC_WITNESSES["disconnected_mask"](produced[1])


def test_every_three_demo_window_refutes_all_named_rivals() -> None:
    module = _load()
    for band_index, band in enumerate(BANDS):
        for start in range(8):
            lesson = [
                _pair(
                    module,
                    8400 + band_index * 100 + start,
                    start + offset,
                    band,
                )
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            assert module.lesson_identifiable(lesson[:3], lesson[3]) == []


def test_named_witnesses_kill_their_rivals_and_generator_kills_canonical_shortcut() -> None:
    module = _load()
    candidates = [module.generate(8500, index, difficulty="medium") for index in range(4)]
    for witness_name, rival_names in module.WITNESS_RIVALS.items():
        firing = next(
            grid for grid in candidates if module.SEMANTIC_WITNESSES[witness_name](grid)
        )
        expected = module.rule_mirror(firing)
        for rival_name in rival_names:
            assert module.SEMANTIC_RIVALS[rival_name](firing) != expected

    shortcut = module.CANONICAL_SHORTCUTS["drop_shape_color"]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]
    firing = next(
        grid
        for grid in candidates
        if module.SEMANTIC_WITNESSES["shape_color_survives"](grid)
    )
    assert shortcut(firing) != module.rule_mirror(firing)



def test_difficulty_bands_change_within_profile_randomness() -> None:
    module = _load()
    for sample_index in range(8):
        grids = [
            module.generate(8800, sample_index, difficulty=band)
            for band in BANDS
        ]
        assert len({repr(grid) for grid in grids}) == len(BANDS)
        assert len({_profile(grid) for grid in grids}) == 1

def test_strict_census_is_diverse_deterministic_and_global_rng_neutral() -> None:
    module = _load()
    for band_index, band in enumerate(BANDS):
        grids = [
            module.generate(8600 + band_index, index, difficulty=band)
            for index in range(80)
        ]
        assert all(module.self_check(grid) == [] for grid in grids)
        assert all(module.strict_canonical_like(grid) == [] for grid in grids)
        assert len({repr(grid) for grid in grids}) >= 76
        assert len({repr(module.rule_mirror(grid)) for grid in grids}) >= 70

    random.seed(20261002)
    state = random.getstate()
    first = module.generate(8700, 7, difficulty="hard")
    assert random.getstate() == state
    second = module.generate(8700, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


@pytest.mark.parametrize(
    ("axis", "value"),
    (
        ("palette_size", 3.5),
        ("block_size", 4.25),
        ("gap", 1.75),
        ("gap", True),
    ),
)
def test_integer_override_axes_reject_non_integer_scalars(axis: str, value: object) -> None:
    module = _load()
    with pytest.raises(TypeError, match="override must be an integer"):
        module.generate(8900, 0, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("difficulty", ("__invalid_difficulty__", 0.5, True))
def test_generate_rejects_invalid_difficulty(difficulty: object) -> None:
    module = _load()
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        module.generate(8901, 0, difficulty=difficulty)


@pytest.mark.parametrize("seed", (True, False, 1.0, 1.75, "1"))
def test_generate_rejects_non_integer_seed(seed: object) -> None:
    module = _load()
    with pytest.raises((TypeError, ValueError), match="seed"):
        module.generate(seed, 0, difficulty="medium")


@pytest.mark.parametrize("sample_index", (True, False, 1.0, 1.75, "1", -1))
def test_generate_rejects_invalid_sample_index(sample_index: object) -> None:
    module = _load()
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        module.generate(8902, sample_index, difficulty="medium")
