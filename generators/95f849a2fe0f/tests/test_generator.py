"""Focused semantic regressions for ARC generator 95f849a2fe0f."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap: works in the review packet and staged arcpuzzles runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "95f849a2fe0f"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _independent_xor(grid):
    shapes = []
    for color in (2, 3):
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        assert cells
        shapes.append(_normalize(cells))
    xor = shapes[0] ^ shapes[1]
    if not xor:
        return [[0]]
    height = max(r for r, _ in xor) + 1
    width = max(c for _, c in xor) + 1
    return [[8 if (r, c) in xor else 0 for c in range(width)] for r in range(height)]


def _recrop_nonzero(output):
    cells = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in output[r0:r1 + 1]]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def test_rule_pin_and_contract_are_declared():
    assert gen.RULE_HASH == "0aa57664563a"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert set(gen.RECROP_WITNESS_PROFILES) == {"leading_row", "leading_col", "leading_both"}
    assert set(gen.SEMANTIC_WITNESSES) == {"leading_blank_frame"}
    assert set(gen.SEMANTIC_RIVALS) == {"recrop_xor"}
    assert gen.WITNESS_RIVALS == {"leading_blank_frame": ["recrop_xor"]}
    assert set(gen.CANONICAL_SHORTCUTS) == {"recrop_xor"}
    assert set(gen.LESSON_COMPETITORS) == {"recrop_xor"}


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert _independent_xor(source) == pair["output"]
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_public_profiles_reproduce_the_three_canonical_inputs_exactly():
    for profile, pair in zip(PUBLIC_PROFILES, PAIRS):
        generated = gen.generate(999, 777, difficulty="hard", scene_profile=profile)
        assert generated == pair["input"]
        assert gen.canonical_profile_signature(generated) == profile
        assert gen.observe_overrides(generated) == {"scene_profile": profile}


def test_recrop_shortcut_really_fits_every_canonical_pair():
    for pair in PAIRS:
        assert _recrop_nonzero(_independent_xor(pair["input"])) == pair["output"]
        assert gen.recrop_xor_rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_profile_is_exactly_observable_and_lawful(band):
    for index, profile in enumerate(gen.SCENE_PROFILES):
        for seed in range(4):
            grid = gen.generate(10_000 + seed, index * 17 + seed, difficulty=band,
                                scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.rule_mirror(grid) == _independent_xor(grid)
            assert (len(grid), len(grid[0])) in {(7, 12), (7, 13), (8, 14)}
            assert {value for row in grid for value in row} == {0, 2, 3}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_witness_profile_refutes_recropping_in_every_band(band):
    for index, profile in enumerate(gen.RECROP_WITNESS_PROFILES):
        for seed in range(12):
            grid = gen.generate(seed, 100 + index * 31 + seed, difficulty=band,
                                scene_profile=profile)
            assert gen.SEMANTIC_WITNESSES["leading_blank_frame"](grid) is True
            assert gen.rule_mirror(grid) != gen.recrop_xor_rival(grid)


def test_default_schedule_survives_every_four_pair_query_rotation():
    witness_profiles = set(gen.RECROP_WITNESS_PROFILES)
    assert set(gen.SCHEDULE_PROFILES) == set(gen.GENERAL_PROFILES)
    period = len(gen.DEFAULT_SCHEDULE)
    for seed in (0, 1, 17, 991):
        for start in range(period * 3):
            profiles = [gen.schedule_profile(seed, start + offset, difficulty="medium")
                        for offset in range(4)]
            assert sum(profile in witness_profiles for profile in profiles) >= 2
            for held_out in range(4):
                demos = profiles[:held_out] + profiles[held_out + 1:]
                assert any(profile in witness_profiles for profile in demos)


def test_lesson_identifiability_reports_the_actual_recrop_ambiguity():
    anchored = gen.generate(17, 0, scene_profile="anchored")
    witness = gen.generate(17, 1, scene_profile="leading_both")
    anchored_query = gen.generate(17, 2, scene_profile="anchored")

    # A witness demonstration refutes the rival, regardless of query profile.
    assert gen.lesson_identifiable([_pair(witness)], _pair(anchored_query)) == []

    # With only canonical-like anchored evidence, the recrop rival fits the
    # demonstration but predicts a different answer on a leading-blank query.
    reasons = gen.lesson_identifiable([_pair(anchored)], _pair(witness))
    assert reasons
    assert any("recrop_xor" in reason for reason in reasons)


def test_default_distribution_is_deterministic_diverse_and_counterexample_rich():
    inputs = set()
    outputs = set()
    witness_count = 0
    random.seed(20261007)
    global_state = random.getstate()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(80):
            seed = 50_000 + band_index * 10_000 + sample_index
            first = gen.generate(seed, sample_index, difficulty=band)
            second = gen.generate(seed, sample_index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert gen.self_check(first) == []
            inputs.add(tuple(map(tuple, first)))
            output = gen.rule_mirror(first)
            outputs.add(tuple(map(tuple, output)))
            witness_count += int(output != gen.recrop_xor_rival(first))
    assert random.getstate() == global_state
    assert len(inputs) >= 210
    assert len(outputs) >= 35
    assert witness_count >= 115


def test_difficulty_bands_affect_realized_inputs_without_changing_the_domain():
    differing = 0
    for sample_index in range(30):
        grids = [gen.generate(8080, sample_index, difficulty=band)
                 for band in ("easy", "medium", "hard")]
        differing += int(len({tuple(map(tuple, grid)) for grid in grids}) > 1)
    assert differing >= 25


def test_invalid_controls_and_malformed_grids_are_rejected():
    for kwargs in (
        {"scene_profile": "not-a-profile"},
        {"texture": "default"},
        {"grid_h": 7},
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 2, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty="extreme")

    valid = gen.generate(3, 4, scene_profile="anchored")
    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    illegal = copy.deepcopy(valid)
    illegal[0][0] = 9
    boolean = copy.deepcopy(valid)
    boolean[0][0] = True
    missing_color = [[0 for _ in row] for row in valid]
    disconnected = copy.deepcopy(valid)
    first_two = [(r, c) for r, row in enumerate(disconnected)
                 for c, value in enumerate(row) if value == 2]
    r, c = first_two[-1]
    disconnected[r][c] = 0
    disconnected[-1][-1] = 2
    wrong_size = copy.deepcopy(valid)
    r, c = next((r, c) for r, row in enumerate(wrong_size)
                for c, value in enumerate(row) if value == 2)
    wrong_size[r][c] = 0
    for grid in ([], ragged, illegal, boolean, missing_color, disconnected, wrong_size):
        errors = gen.self_check(grid)
        assert errors
        assert all(isinstance(error, str) and error for error in errors)


def test_racket_authority_matches_python_mirror_on_generated_conflicts():
    from arcpuzzles import Catalog

    grids = [
        gen.generate(91_000 + band_index * 100 + index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(8)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [gen.rule_mirror(grid) for grid in grids]


def test_workspace_lesson_probe_runs_portably_and_reports_schedule_support():
    import json
    import subprocess

    probe = GENERATOR_PATH.parent / "workspace" / "lesson_probe.py"
    result = subprocess.run(
        [sys.executable, str(probe), "--per-band", "2"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "ok"
    assert report["generator_sha256"] == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assert report["canonical"]["pairs"] == 3
    assert report["canonical"]["shortcut_fits"] == {"recrop_xor": True}
    assert report["schedule"]["rotations_checked"] == 72
    assert report["schedule"]["ambiguous_rotations"] == 0
    assert all(stats["draws"] == 2 for stats in report["sampling"].values())
