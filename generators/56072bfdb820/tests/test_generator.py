"""Regression and semantic-contract tests for ARC generator 56072bfdb820."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from itertools import combinations
import json
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "56072bfdb820"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
TILES = tuple((r, c) for r in range(3) for c in range(3))
PAIR_SPACE = tuple(combinations(TILES, 2))
DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))


def _symbols(grid):
    found = []
    for tr, tc in TILES:
        values = [
            grid[tr * 4 + dr][tc * 4 + dc]
            for dr in range(3)
            for dc in range(3)
            if grid[tr * 4 + dr][tc * 4 + dc] not in (6, 7)
        ]
        if values:
            found.append((tr, tc, values[0]))
    return found


def _independent_rule(grid):
    """Small independent translation of the selected Racket authority."""
    symbols = _symbols(grid)
    if any(color != 2 for _, _, color in symbols):
        return [[7] * 16 for _ in range(16)]

    twos = [(r, c) for r, c, color in symbols if color == 2]
    assert len(twos) == 2
    (r1, c1), (r2, c2) = twos
    if c1 == c2:
        r, c = min(r1, r2) - 1, c1
        extras = ((r, c - 1, 5), (r, c + 1, 8))
    elif r1 == r2:
        r, c = r1, min(c1, c2) - 1
        extras = ((r - 1, c, 8), (r + 1, c, 5))
    elif c2 < c1:
        extras = ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    else:
        extras = ((r2, c2 + 1, 8), (r2 + 1, c2, 5))

    items = list(symbols) + [
        item for item in extras if 0 <= item[0] < 3 and 0 <= item[1] < 3
    ]
    lookup = {(r, c): color for r, c, color in reversed(items)}
    # The Racket find-first gives observed symbols priority over extras.
    for r, c, color in symbols:
        lookup[(r, c)] = color

    output = [[7] * 11 for _ in range(11)]
    for row in (3, 7):
        output[row] = [6] * 11
    for col in (3, 7):
        for row in range(11):
            output[row][col] = 6
    for (tr, tc), color in lookup.items():
        for dr, dc in DIAMOND:
            output[tr * 4 + dr][tc * 4 + dc] = color
    return output


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_contract_metadata_is_pinned_and_minimal():
    assert gen.RULE_HASH == "5eec51381abd"
    assert gen.VERSION == "5.0.0"
    assert set(gen.AXES) == {"pair_index", "bad_mask"}
    assert gen.EXAMPLES_NEEDED == 5
    assert len(gen.SCHEDULE_PROFILES) == 6
    assert gen.MIN_STRICT_FRAC == 1.0
    assert gen.ALLOW_IDENTITY_OUTPUT is True
    assert gen.AXES["bad_mask"]["default"] == "schedule 0,0,3,1,2,0"


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_every_canonical_pair_is_accepted_and_replayed(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert _independent_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_joint_exact_override_is_realized_in_every_band(band):
    for pair_index in range(36):
        for bad_mask in range(4):
            requested = {"pair_index": pair_index, "bad_mask": bad_mask}
            grid = gen.generate(17, 9, difficulty=band, **requested)
            assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
            assert gen.observe_overrides(grid) == requested
            assert gen.rule_mirror(grid) == _independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"pair_index": -1},
        {"pair_index": 36},
        {"bad_mask": -1},
        {"bad_mask": 4},
        {"pair_index": True},
        {"pair_index": 1.0},
        {"pair_index": "1"},
        {"bad_mask": False},
        {"bad_mask": 2.0},
    ],
)
def test_unknown_or_invalid_overrides_raise(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_all_valid_pair_placements_are_supported_with_expected_clip_census():
    counts = {0: 0, 1: 0, 2: 0}
    seen = set()
    for pair_index in range(36):
        grid = gen.generate(101, 0, pair_index=pair_index, bad_mask=0)
        assert gen.observe_overrides(grid) == {"pair_index": pair_index, "bad_mask": 0}
        output = gen.rule_mirror(grid)
        extras = sum(color in (5, 8) for _, _, color in _symbols(output))
        counts[extras] += 1
        seen.add(_freeze(grid))
    assert counts == {0: 20, 1: 12, 2: 4}
    assert len(seen) == 36


def test_declared_shortcuts_fit_every_canonical_pair_but_are_wrong_rules():
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS), name
        assert any(
            shortcut(gen.generate(77, index)) != gen.rule_mirror(gen.generate(77, index))
            for index in range(6)
        ), name


def test_every_six_position_schedule_block_has_rotation_safe_five_demo_lessons():
    for band in (None, "easy", "medium", "hard"):
        for start in range(6):
            labelled = []
            profiles = []
            for offset in range(6):
                index = start + offset
                grid = gen.generate(123, index, difficulty=band)
                assert gen.self_check(grid, difficulty=band) == []
                labelled.append({"input": grid, "output": gen.rule_mirror(grid)})
                profiles.append(gen.schedule_profile(123, index, band))
            assert set(profiles) == set(gen.SCHEDULE_PROFILES)
            for query_index in range(6):
                query = labelled[query_index]
                demos = labelled[:query_index] + labelled[query_index + 1 :]
                assert len(demos) == gen.EXAMPLES_NEEDED
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_every_witness_fires_in_every_band_and_its_claimed_rivals_disagree():
    for band in (None, "easy", "medium", "hard"):
        grids = [gen.generate(901, index, difficulty=band) for index in range(6)]
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            hits = [grid for grid in grids if witness(grid)]
            assert hits, (band, witness_name)
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                rival = gen.SEMANTIC_RIVALS[rival_name]
                assert any(rival(grid) != gen.rule_mirror(grid) for grid in hits), (
                    band,
                    witness_name,
                    rival_name,
                )


def test_difficulty_bands_change_default_stream_without_changing_contract():
    streams = {
        band: tuple(_freeze(gen.generate(311, index, difficulty=band)) for index in range(18))
        for band in ("easy", "medium", "hard")
    }
    assert len(set(streams.values())) == 3
    for stream in streams.values():
        assert len(set(stream)) >= 6


def test_self_check_rejects_malformed_shape_dividers_and_diamonds():
    grid = gen.generate(4, 0)
    assert gen.self_check(grid) == []

    ragged = deepcopy(grid)
    ragged[0].pop()
    assert gen.self_check(ragged)

    broken_divider = deepcopy(grid)
    broken_divider[3][5] = 7
    assert gen.self_check(broken_divider)

    broken_diamond = deepcopy(grid)
    r, c, _ = _symbols(broken_diamond)[0]
    broken_diamond[r * 4][c * 4 + 1] = 7
    assert gen.self_check(broken_diamond)

    stray = deepcopy(grid)
    stray[0][0] = 2
    assert gen.self_check(stray)


def test_generation_is_repeatable_and_keyed():
    first = gen.generate(712, 31, difficulty="hard")
    for index in range(100):
        gen.generate(index, index * 7, difficulty="easy")
    assert gen.generate(712, 31, difficulty="hard") == first


def test_default_probe_exhausts_the_nonidentity_17_grid_output_codomain():
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 17
    grids = [
        gen.generate(episode * 101, sample_index)
        for episode in range(24)
        for sample_index in range(6)
    ]
    outputs = {_freeze(gen.rule_mirror(grid)) for grid in grids}
    assert len(outputs) == gen.EXPECTED_OUTPUT_CODOMAIN
    assert all(gen.rule_mirror(grid) != grid for grid in grids)
    assert any(len({value for row in grid for value in row}) == 5 for grid in grids)


def test_seed_rotates_profiles_at_fixed_sample_index_without_breaking_blocks():
    fixed_index_profiles = {
        gen.schedule_profile(seed, 0, None) for seed in range(40)
    }
    assert fixed_index_profiles == set(gen.SCHEDULE_PROFILES)
    fixed_index_inputs = {
        _freeze(gen.generate(seed, 0)) for seed in range(40)
    }
    assert len(fixed_index_inputs) >= 12


def test_equal_seed_index_gate_cohort_visits_all_profiles_and_stays_distinct():
    for band in ("easy", "medium", "hard"):
        profiles = {
            gen.schedule_profile(seed, seed, band) for seed in range(1, 21)
        }
        assert profiles == set(gen.SCHEDULE_PROFILES)
        grids = [gen.generate(seed, seed, difficulty=band) for seed in range(1, 21)]
        assert len({_freeze(grid) for grid in grids}) / len(grids) >= 0.70


def test_workspace_reference_probe_exhausts_override_domain_independently():
    tool = TASK_HOME / "workspace" / "reference_probe.py"
    assert tool.is_file()
    spec = importlib.util.spec_from_file_location("reference_probe_56072bfdb820", tool)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    result = probe.run_probe(TASK_HOME / "generator.py")
    assert result["status"] == "pass"
    assert result["cases"] == 36 * 4 * 4
    assert result["unique_inputs"] == 36 * 4
    assert result["unique_outputs"] == 37
    assert result["default_probe_unique_outputs"] == gen.EXPECTED_OUTPUT_CODOMAIN
    assert result["valid_extra_census"] == {"0": 20, "1": 12, "2": 4}
    assert result["mismatches"] == []


def test_workspace_reference_probe_writes_apply_sized_chunks(tmp_path):
    tool = TASK_HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("reference_probe_chunks_56072bfdb820", tool)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    chunks = tmp_path / "apply-inputs"
    result = probe.run_probe(TASK_HOME / "generator.py", inputs_dir=chunks)
    assert result["status"] == "pass"
    manifest = json.loads((chunks / "manifest.json").read_text())
    sizes = []
    for filename in manifest["files"]:
        payload = json.loads((chunks / filename).read_text())
        sizes.append(len(payload["inputs"]))
    assert sizes == [64, 64, 16]
    assert sum(sizes) == 144


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_and_schedule_reject_non_integer_seed_scalars(bad_seed):
    with pytest.raises(ValueError, match="seed must be an integer"):
        gen.schedule_profile(bad_seed, 0)
    with pytest.raises(ValueError, match="seed must be an integer"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_sample_index", [True, False, -1, 0.0, 1.5, "1"])
def test_generate_and_schedule_reject_invalid_sample_index_scalars(bad_sample_index):
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        gen.schedule_profile(0, bad_sample_index)
    with pytest.raises(ValueError, match="sample_index must be a nonnegative integer"):
        gen.generate(0, bad_sample_index)
