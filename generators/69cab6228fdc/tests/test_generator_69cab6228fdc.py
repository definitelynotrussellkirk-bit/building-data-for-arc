from __future__ import annotations

import copy
import importlib
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.69cab6228fdc.generator")
TASK_ID = "69cab6228fdc"
RUNTIME_ROOT = find_root(__file__)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=RUNTIME_ROOT, variant=0)


def test_rule_pin_and_canonical_pairs_are_exact_in_portable_runtime():
    assert gen.VERSION == "2.1.0"
    assert gen.RULE_HASH == "8fec6004f588"
    pairs = _canonical_pairs()
    assert [(pair["split"], pair["pair_index"]) for pair in pairs] == [
        ("train", 0),
        ("train", 1),
        ("train", 2),
        ("train", 3),
        ("test", 0),
    ]
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_override_boundaries_are_exact_observable_and_band_safe():
    cases = [
        {
            "grid_h": 7,
            "grid_w": 6,
            "n_pairs": 2,
            "legend_layout": "scattered",
            "body_profile": "sparse",
            "passthrough": "absent",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "n_pairs": 4,
            "legend_layout": "contiguous",
            "body_profile": "dense",
            "passthrough": "present",
        },
        {
            "grid_h": 9,
            "grid_w": 7,
            "n_pairs": 3,
            "legend_layout": "scattered",
            "body_profile": "medium",
            "passthrough": "present",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(
                1000 + index,
                20 + index,
                difficulty=difficulty,
                **requested,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_every_three_demo_schedule_window_identifies_the_query():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            examples = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(1701, sample_index, difficulty=difficulty)
                examples.append({"input": grid, "output": gen.rule_mirror(grid)})
            modes = [gen.observe_overrides(item["input"])["passthrough"] for item in examples[:3]]
            assert set(modes) == {"absent", "present"}
            assert gen.lesson_identifiable(examples[:3], examples[3]) == []



def _unmapped_body_colors(grid):
    sources = {source for source, _ in gen._pairs(grid)}
    return sorted(
        {value for row in grid[3:] for value in row if value and value not in sources}
    )


def test_present_schedule_teaches_two_unmapped_colors_and_refutes_one_only_rival():
    rival = gen.SEMANTIC_RIVALS["first_unmapped_only"]
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            if gen.schedule_profile(3107, sample_index, difficulty) != "present":
                continue
            grid = gen.generate(3107, sample_index, difficulty=difficulty)
            assert len(_unmapped_body_colors(grid)) == 2
            assert rival(grid) != gen.rule_mirror(grid)


def test_self_check_accepts_multiple_unmapped_colors_and_preserves_each_one():
    grid = [
        [1, 2, 0, 0, 0, 0],
        [3, 4, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 5, 6, 0, 0, 0],
        [2, 6, 5, 0, 0, 0],
        [1, 2, 5, 6, 0, 0],
        [2, 1, 6, 5, 0, 0],
    ]
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["passthrough"] == "present"
    assert gen.rule_mirror(grid) == [
        [3, 5, 6, 0, 0, 0],
        [4, 6, 5, 0, 0, 0],
        [3, 4, 5, 6, 0, 0],
        [4, 3, 6, 5, 0, 0],
    ]
    assert gen.SEMANTIC_RIVALS["first_unmapped_only"](grid) != gen.rule_mirror(grid)

def test_named_witnesses_really_refute_their_rivals():
    grids = [gen.generate(4200, index, difficulty="medium") for index in range(8)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        witness_grid = next(grid for grid in grids if witness(grid))
        answer = gen.rule_mirror(witness_grid)
        assert any(
            gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer
            for rival_name in rival_names
        )


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        9001,
        5,
        difficulty="medium",
        grid_h=9,
        grid_w=7,
        n_pairs=3,
        legend_layout="scattered",
        body_profile="medium",
        passthrough="present",
    )
    pair_columns = [c for c in range(len(base[0])) if base[0][c] and base[1][c]]

    fixtures: dict[str, list[list[int]]] = {}
    fixtures["separator_contaminated"] = copy.deepcopy(base)
    fixtures["separator_contaminated"][2][0] = 1

    fixtures["half_pair"] = copy.deepcopy(base)
    fixtures["half_pair"][1][pair_columns[0]] = 0

    fixtures["duplicate_source"] = copy.deepcopy(base)
    fixtures["duplicate_source"][0][pair_columns[1]] = fixtures["duplicate_source"][0][pair_columns[0]]

    fixtures["missing_source_evidence"] = copy.deepcopy(base)
    missing = fixtures["missing_source_evidence"][0][pair_columns[-1]]
    replacement = fixtures["missing_source_evidence"][0][pair_columns[0]]
    for row in fixtures["missing_source_evidence"][3:]:
        for c, value in enumerate(row):
            if value == missing:
                row[c] = replacement

    fixtures["target_leakage_as_passthrough"] = copy.deepcopy(base)
    passthrough = next(
        value
        for row in fixtures["target_leakage_as_passthrough"][3:]
        for value in row
        if value not in {0, *[fixtures["target_leakage_as_passthrough"][0][c] for c in pair_columns]}
    )
    target = fixtures["target_leakage_as_passthrough"][1][pair_columns[0]]
    for row in fixtures["target_leakage_as_passthrough"][3:]:
        for c, value in enumerate(row):
            if value == passthrough:
                row[c] = target

    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(20260726)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second



def _load_passthrough_probe():
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "workspace" / "passthrough_probe.py",
        RUNTIME_ROOT / "generators" / TASK_ID / "workspace" / "passthrough_probe.py",
        RUNTIME_ROOT / "workspace" / "passthrough_probe.py",
    ]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError(
            "passthrough probe not found in portable task-test snapshot: "
            + ", ".join(str(candidate) for candidate in candidates)
        )
    spec = importlib.util.spec_from_file_location("passthrough_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load probe at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_passthrough_probe_audits_schedule_rivals_and_exact_witness():
    probe = _load_passthrough_probe()
    report = probe.run_probe(
        generator=gen,
        canonical_pairs=_canonical_pairs(),
        per_band=8,
        seed=20261004,
    )

    assert report["schema"] == "arcpuzzles-passthrough-probe-v1"
    assert report["task_id"] == TASK_ID
    assert report["generator_version"] == gen.VERSION
    assert report["failures"] == []
    assert report["canonical_shortcuts"] == {
        "first_unmapped_only": {"fits": 5, "pairs": 5, "status": "fits_all"},
        "zero_unmapped": {"fits": 5, "pairs": 5, "status": "fits_all"},
    }
    for band in ("easy", "medium", "hard"):
        observed = report["bands"][band]
        assert observed["passthrough_cardinality"] == {"0": 4, "2": 4}
        assert observed["rival_refutations"] == {
            "first_unmapped_only": 4,
            "zero_unmapped": 4,
        }
        assert observed["lesson_windows_checked"] == 8
        assert observed["ambiguous_windows"] == 0

    witness = report["exact_witness"]
    assert witness["unmapped_colors"] == [5, 6]
    assert witness["self_check_errors"] == []
    assert witness["intended_output"] != witness["first_unmapped_only_output"]
