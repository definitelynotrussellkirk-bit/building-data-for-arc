from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "db63430eeffa"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)
GENERATOR, _GENERATOR_PATH, _GENERATOR_SHA = load_selected_generator(
    TASK_ID, root=ROOT
)


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), f"missing proposed prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_parametric_prototype",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger_program() -> str:
    matches = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    assert len(set(matches)) == 1
    return matches[0]


def test_canonical_policy_is_exact_ledger_source():
    prototype = load_prototype()
    source = ledger_program()
    assert prototype.PATH_POLICIES == (
        "both",
        "diagonal_first",
        "straight_first",
    )
    assert prototype.canonical_program(root=ROOT) == source
    assert prototype.program_for("both", root=ROOT) == source


def test_one_path_programs_remove_only_the_opposite_guarded_loop():
    prototype = load_prototype()
    source = ledger_program()
    diagonal = prototype.program_for("diagonal_first", root=ROOT)
    straight = prototype.program_for("straight_first", root=ROOT)

    assert source.count(prototype.DIAGONAL_FIRST_BLOCK) == 1
    assert source.count(prototype.STRAIGHT_FIRST_BLOCK) == 1
    assert prototype.DIAGONAL_FIRST_BLOCK in diagonal
    assert prototype.STRAIGHT_FIRST_BLOCK not in diagonal
    assert prototype.STRAIGHT_FIRST_BLOCK in straight
    assert prototype.DIAGONAL_FIRST_BLOCK not in straight
    assert diagonal == prototype.derive_program(source, "diagonal_first")
    assert straight == prototype.derive_program(source, "straight_first")


def test_program_derivation_rejects_invalid_policy_and_source_drift():
    prototype = load_prototype()
    source = ledger_program()
    for invalid in (None, True, "", "diagonal", "Both"):
        with pytest.raises(ValueError, match="path_policy"):
            prototype.derive_program(source, invalid)
    drifted = source.replace("(rows g)", "(rows  g)", 1)
    with pytest.raises(ValueError, match="canonical source"):
        prototype.derive_program(drifted, "both")



@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge() as bridge:
        yield bridge


def test_canonical_racket_program_matches_every_labeled_fixture(racket_bridge):
    prototype = load_prototype()
    source = prototype.program_for("both", root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert (
            prototype.evaluate_racket(source, pair["input"], bridge=racket_bridge)
            == pair["output"]
        )


def test_three_policies_are_distinct_on_a_noncoincident_input(racket_bridge):
    prototype = load_prototype()
    grid = GENERATOR.generate(
        12,
        4,
        grid_h=11,
        grid_w=14,
        row_gap=2,
        col_gap=10,
        orientation="right_to_left",
    )
    outputs = {
        policy: prototype.evaluate_racket(
            prototype.program_for(policy, root=ROOT),
            grid,
            bridge=racket_bridge,
        )
        for policy in prototype.PATH_POLICIES
    }
    assert len({json.dumps(value) for value in outputs.values()}) == 3
    assert outputs["both"] == GENERATOR.rule_mirror(grid)


@pytest.mark.parametrize(
    "endpoints",
    [((1, 1), (7, 4)), ((1, 7), (7, 4)),
     ((1, 1), (4, 7)), ((1, 7), (4, 1))],
)
def test_path_policies_preserve_endpoints_and_both_is_the_path_union(
    endpoints, racket_bridge,
):
    import copy

    prototype = load_prototype()
    grid = [[0] * 9 for _ in range(9)]
    for row, col in endpoints:
        grid[row][col] = 8
    before = copy.deepcopy(grid)
    outputs = {
        policy: prototype.evaluate_racket(
            prototype.program_for(policy, root=ROOT), grid, bridge=racket_bridge,
        )
        for policy in prototype.PATH_POLICIES
    }
    assert grid == before
    assert len({json.dumps(output) for output in outputs.values()}) == 3
    for row in range(9):
        for col in range(9):
            cells = {policy: output[row][col] for policy, output in outputs.items()}
            if (row, col) in endpoints:
                assert set(cells.values()) == {8}
            else:
                assert set(cells.values()) <= {0, 3}
                expected = 3 if 3 in (
                    cells["diagonal_first"], cells["straight_first"],
                ) else 0
                assert cells["both"] == expected


@pytest.fixture(scope="module")
def prototype_module():
    return load_prototype()


@pytest.fixture(scope="module")
def complete_episodes(prototype_module, racket_bridge):
    return {
        policy: prototype_module.build_episode(
            1000 + index,
            policy,
            root=ROOT,
            bridge=racket_bridge,
        )
        for index, policy in enumerate(prototype_module.PATH_POLICIES)
    }


def _all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_complete_episode_for_every_setting_is_identifiable_and_four_query(
    prototype_module,
    complete_episodes,
    racket_bridge,
):
    for policy, episode in complete_episodes.items():
        assert episode["status"] == "proposed_unapproved"
        assert episode["approved"] is False
        assert episode["parameters"] == {"path_policy": policy}
        assert episode["selection_scope"] == "once_per_episode"
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        assert episode["racket_evaluation_count"] == 21
        assert len({json.dumps(grid) for grid in _all_inputs(episode)}) == 7
        assert {row["path_policy"] for row in episode["parameter_rivals"]} == (
            set(prototype_module.PATH_POLICIES) - {policy}
        )
        for rival in episode["parameter_rivals"]:
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["demonstration_mismatch_indices"]
            assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
        verification = prototype_module.verify_episode(
            episode,
            root=ROOT,
            bridge=racket_bridge,
        )
        assert verification["passed"] is True
        assert verification["racket_evaluation_count"] == 21

def test_demo_and_query_counts_are_independent(prototype_module, racket_bridge):
    episode = prototype_module.build_episode(
        2026,
        "both",
        demonstration_count=4,
        query_count=4,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert len(episode["train"]) == 4
    assert len(episode["test"]) == 4
    assert episode["racket_evaluation_count"] == 24
    assert len({json.dumps(grid) for grid in _all_inputs(episode)}) == 8


def test_seed_selected_setting_is_deterministic_and_fixed(prototype_module):
    for seed in (0, 1, 2, 99, 10_000):
        selected = prototype_module.select_path_policy(seed)
        assert selected in prototype_module.PATH_POLICIES
        assert selected == prototype_module.select_path_policy(seed)


def test_episode_controls_reject_invalid_scalars_before_racket(prototype_module):
    invalid_calls = [
        {"seed": True, "path_policy": "both"},
        {"seed": -1, "path_policy": "both"},
        {"seed": 0, "path_policy": True},
        {"seed": 0, "path_policy": "bogus"},
        {"seed": 0, "path_policy": "both", "demonstration_count": True},
        {"seed": 0, "path_policy": "both", "demonstration_count": 1},
        {"seed": 0, "path_policy": "both", "demonstration_count": 7},
        {"seed": 0, "path_policy": "both", "query_count": 0},
        {"seed": 0, "path_policy": "both", "query_count": 3},
        {"seed": 0, "path_policy": "both", "query_count": 5},
        {"seed": 0, "path_policy": "both", "query_count": 9},
        {"seed": 0, "path_policy": "both", "difficulty": "extreme"},
    ]
    for kwargs in invalid_calls:
        with pytest.raises(ValueError):
            prototype_module.build_episode(**kwargs, root=ROOT)


def test_public_projection_depends_only_on_visible_bytes(
    prototype_module,
    complete_episodes,
):
    import copy

    episode = complete_episodes["diagonal_first"]
    original_bytes = prototype_module.public_bytes(episode)
    original_id = prototype_module.public_id(episode)
    original_name = prototype_module.public_filename(episode)
    assert original_name == f"challenge-{original_id}.json"
    assert "diagonal" not in original_name
    public = prototype_module.public_challenge(episode)
    assert all(set(pair) == {"input"} for pair in public["test"])

    hidden = copy.deepcopy(episode)
    hidden["seed"] = 999_999
    hidden["parameters"]["path_policy"] = "straight_first"
    hidden["program"] = "private mutation"
    hidden["test"][0]["output"][0][0] = (
        hidden["test"][0]["output"][0][0] + 1
    ) % 10
    assert prototype_module.public_bytes(hidden) == original_bytes
    assert prototype_module.public_id(hidden) == original_id
    assert prototype_module.public_filename(hidden) == original_name

    visible_demo = copy.deepcopy(episode)
    visible_demo["train"][0]["output"][0][0] = (
        visible_demo["train"][0]["output"][0][0] + 1
    ) % 10
    assert prototype_module.public_id(visible_demo) != original_id

    visible_query = copy.deepcopy(episode)
    visible_query["test"][0]["input"][0][0] = (
        visible_query["test"][0]["input"][0][0] + 1
    ) % 10
    assert prototype_module.public_id(visible_query) != original_id


def test_public_batch_is_sorted_and_rejects_duplicate_visible_payloads(
    prototype_module,
    complete_episodes,
    tmp_path,
):
    episodes = list(reversed(list(complete_episodes.values())))
    paths = prototype_module.write_public_batch(episodes, tmp_path / "public")
    assert [path.name for path in paths] == sorted(path.name for path in paths)
    for path in paths:
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in payload["test"])

    with pytest.raises(ValueError, match="duplicate visible"):
        prototype_module.write_public_batch(
            [complete_episodes["both"], complete_episodes["both"]],
            tmp_path / "duplicates",
        )


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_bounded_sampler_shares_inputs_across_policies_and_keeps_public_ids_private(
    difficulty, prototype_module, racket_bridge,
):
    import copy
    import hashlib

    signatures = set()
    public_ids = set()
    for seed in (0, 17):
        per_policy_inputs = []
        for policy in prototype_module.PATH_POLICIES:
            episode = prototype_module.build_episode(
                seed, policy, difficulty=difficulty, root=ROOT, bridge=racket_bridge,
            )
            pairs = episode["train"] + episode["test"]
            signature = tuple(json.dumps(pair["input"]) for pair in pairs)
            assert len(set(signature)) == 7
            per_policy_inputs.append(signature)
            for rival in episode["parameter_rivals"]:
                assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
                assert rival["query_mismatch_indices"] == [0, 1, 2, 3]
            public = prototype_module.public_challenge(episode)
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            visible_id = prototype_module.public_id(episode)
            assert hashlib.sha256(prototype_module.public_bytes(episode)).hexdigest() == visible_id
            assert visible_id not in public_ids
            public_ids.add(visible_id)
            hidden = copy.deepcopy(episode)
            hidden["seed"] += 100_000
            hidden["program"] = "private replacement"
            hidden["parameters"]["path_policy"] = "private replacement"
            for pair in hidden["test"]:
                pair["output"] = [[9]]
            assert prototype_module.public_id(hidden) == visible_id
        assert len(set(per_policy_inputs)) == 1
        signatures.add(per_policy_inputs[0])
    assert len(signatures) == 2
    assert len(public_ids) == 6


def load_verifier():
    path = PROTOTYPE_PATH.with_name("verify.py")
    assert path.is_file(), f"missing reusable verifier: {path}"
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_parametric_verifier",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reusable_verifier_writes_private_public_and_manifest_evidence(tmp_path, racket_bridge):
    verifier = load_verifier()
    destination = tmp_path / "evidence"
    report = verifier.run_verification(
        destination,
        seed_base=7000,
        root=ROOT,
        bridge=racket_bridge,
    )
    assert report["passed"] is True
    assert report["settings_verified"] == 3
    assert report["generated_racket_evaluation_count"] == 63
    assert report["verification_racket_evaluation_count"] == 63
    assert report["sequential_witness_racket_evaluation_count"] == 2
    assert report["total_racket_evaluation_count"] == 128
    assert report["sequential_dependency"]["differing_cell_count"] > 0
    assert all(
        row["shortcut_survivors"] == []
        for row in report["episodes"].values()
    )
    assert (destination / "report.json").is_file()
    assert (destination / "sequential-dependency.json").is_file()
    assert (destination / "manifest.json").is_file()
    private = sorted((destination / "private").glob("*.json"))
    public = sorted((destination / "public").glob("*.json"))
    assert len(private) == 3
    assert len(public) == 3
    assert all(path.name.startswith("challenge-") for path in public)
    assert all("both" not in path.name for path in public)
    manifest = json.loads((destination / "manifest.json").read_text())
    assert manifest["file_count"] == 8
    assert len(manifest["files"]) == 8


def test_reusable_verifier_rejects_invalid_seed_before_writing(tmp_path):
    verifier = load_verifier()
    destination = tmp_path / "invalid"
    with pytest.raises(ValueError, match="seed_base"):
        verifier.run_verification(destination, seed_base=True, root=ROOT)
    assert not destination.exists()
