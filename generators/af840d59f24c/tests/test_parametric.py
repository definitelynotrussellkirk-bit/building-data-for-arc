"""Prototype-only contracts; these do not approve the canonical generator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "af840d59f24c"
gen, source, _ = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE = source.parent / "workspace/parametric/prototype.py"
if not PROTOTYPE.is_file():
    PROTOTYPE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("zero_rank_parametric", PROTOTYPE)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)


def witness():
    grid = [[9] * 8 for _ in range(8)]
    for row, column in ((0, 6), (1, 0), (1, 2), (3, 2), (3, 4),
                        (4, 0), (4, 2), (4, 4), (4, 6)):
        grid[row][column] = 0
    return grid


@pytest.fixture(scope="module")
def exact_execution():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    grids = [witness(), *[pair["input"] for pair in pairs]]
    programs = {setting.key: p.emit_program(setting, root=ROOT) for setting in p.SETTINGS}
    return pairs, p.execute_programs(programs, grids, root=ROOT)


def test_default_emits_the_unchanged_selected_canonical_program():
    authority = p.canonical_authority(ROOT)
    assert p.emit_program(p.DEFAULT, root=ROOT) == authority["program"]
    assert authority["normalized_rule_hash"] == gen.RULE_HASH


@pytest.mark.parametrize("axis,direction", [
    ("diagonal", "forward"), ("rows", "up"), (None, "forward"),
    (True, "forward"), ("columns", 1),
])
def test_parameters_reject_unsupported_or_coerced_values(axis, direction):
    with pytest.raises((TypeError, ValueError)):
        p.Parameters(axis, direction)


@pytest.mark.parametrize("seed", [-1, True, 1.0, "1"])
def test_episode_seed_is_a_nonnegative_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        p.choose_parameters(seed)


def test_seed_choice_is_deterministic_and_covers_the_declared_settings():
    values = [p.choose_parameters(seed) for seed in range(64)]
    assert values == [p.choose_parameters(seed) for seed in range(64)]
    assert set(values) == set(p.SETTINGS)


def test_shared_input_sampler_preserves_both_oriented_domains():
    first = p.sample_inputs(17, root=ROOT)
    assert first == p.sample_inputs(17, root=ROOT)
    assert len(first["grids"]) == 5
    assert len({p.json_sha256(grid) for grid in first["grids"]}) == 5
    assert {row["scene_profile"] for row in first["draws"]} == set(p.INPUT_PROFILES)
    for grid in first["grids"]:
        assert gen.self_check(grid) == []
        assert gen.self_check([list(row) for row in zip(*grid)]) == []


@pytest.mark.parametrize("setting,expected_ranks", [
    (p.Parameters("columns", "forward"), [4, 1, 2, 2, 3, 1, 2, 3, 4]),
    (p.Parameters("columns", "reverse"), [1, 4, 3, 3, 2, 4, 3, 2, 1]),
    (p.Parameters("rows", "forward"), [1, 2, 2, 3, 3, 4, 4, 4, 4]),
    (p.Parameters("rows", "reverse"), [4, 3, 3, 2, 2, 1, 1, 1, 1]),
])
def test_each_emitted_racket_program_has_the_expected_global_ranks(
    exact_execution, setting, expected_ranks
):
    _, execution = exact_execution
    grid = witness()
    output = execution["outputs"][setting.key][0]
    assert [output[r][c] for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 0] == expected_ranks
    assert all(output[r][c] == value for r, row in enumerate(grid)
               for c, value in enumerate(row) if value != 0)


def test_canonical_default_racket_matches_all_canonical_labels(exact_execution):
    pairs, execution = exact_execution
    assert execution["outputs"][p.DEFAULT.key][1:] == [pair["output"] for pair in pairs]


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    out = tmp_path_factory.mktemp("parametric") / "evidence"
    report = p.build_evidence(out, seed=17, root=ROOT)
    return out, report


def test_complete_episodes_are_seed_fixed_and_refute_every_parameter_rival(bundle):
    out, report = bundle
    assert report["summary"]["episodes"] == 4
    assert report["summary"]["parameter_rivals_refuted"] == 12
    assert report["summary"]["production_ambiguities"] == 0
    assert report["summary"]["rotation_ambiguities"] == 0
    private = json.loads((out / "episodes.private.json").read_text())
    for episode in private:
        assert episode["parameters"] == p.choose_parameters(episode["seed"]).as_dict()
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 1
        assert episode["program"] == p.emit_program(p.Parameters(**episode["parameters"]), root=ROOT)


def test_public_challenges_contain_only_demos_and_unanswered_queries(bundle):
    out, _ = bundle
    private = json.loads((out / "episodes.private.json").read_text())
    for index, episode in enumerate(private):
        public = json.loads((out / "public" / f"challenge-{index:02d}.json").read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public == p.public_challenge(episode)


def test_public_file_order_does_not_encode_the_fixed_parameter_enumeration(bundle):
    out, _ = bundle
    private = json.loads((out / "episodes.private.json").read_text())
    assert [episode["seed"] for episode in private] == sorted(episode["seed"] for episode in private)
    assert [episode["parameters"] for episode in private] != [setting.as_dict() for setting in p.SETTINGS]


def test_saved_bundle_replays_through_racket(bundle):
    out, _ = bundle
    replay = p.verify_evidence(out, root=ROOT)
    assert replay["status"] == "passed"
    assert replay["all_outputs_identical"]
    assert replay["source_hashes_match"]


def test_replay_rejects_a_modified_public_file_before_execution(bundle):
    out, _ = bundle
    path = out / "public/challenge-00.json"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n")
        with pytest.raises(ValueError, match="asset hash mismatch"):
            p.verify_evidence(out, root=ROOT)
    finally:
        path.write_bytes(original)
