from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "line_span_policy_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hand_gap_grid() -> list[list[int]]:
    return [
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
        [7, 3, 7, 8, 8, 7, 7, 8, 8, 7, 3],
        [7, 7, 7, 8, 8, 7, 7, 8, 8, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
    ]


def test_rule_sources_keep_exact_default_and_alternative_executes_a_distinct_policy():
    mod = load_prototype()
    canonical = mod.canonical_program()

    assert mod.rule_source("foreground_only") == canonical
    assert mod.rule_source("entire_span") != canonical
    with pytest.raises(ValueError):
        mod.rule_source("ray_extend")

    grid = hand_gap_grid()
    assert mod.python_mirror(grid, "foreground_only")[2] == [
        7,
        3,
        7,
        3,
        3,
        7,
        7,
        3,
        3,
        7,
        3,
    ]
    assert mod.python_mirror(grid, "entire_span")[2] == [
        7,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
        3,
    ]


def test_rectangle_restoration_is_invariant_across_line_span_settings():
    mod = load_prototype()
    grid = [
        [7, 7, 7, 7, 7, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 2, 4, 4, 2, 7, 7],
        [7, 2, 4, 4, 2, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 7, 7, 7, 7, 7, 7],
    ]
    expected = [
        [7, 7, 7, 7, 7, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 2, 2, 2, 2, 7, 7],
        [7, 7, 7, 7, 7, 7, 7],
    ]

    assert mod.python_mirror(grid, "foreground_only") == expected
    assert mod.python_mirror(grid, "entire_span") == expected


def test_episode_sampling_is_deterministic_fresh_and_has_three_demos_four_queries():
    mod = load_prototype()
    first = mod.sample_episode(20261023, demo_count=3, query_count=4)
    second = mod.sample_episode(20261023, demo_count=3, query_count=4)

    assert first == second
    assert first is not second
    assert first["inputs"] is not second["inputs"]
    assert first["parameters"] == {
        "line_span_policy": mod.policy_for_seed(20261023)
    }
    assert first["demo_count"] == 3
    assert first["query_count"] == 4
    assert len(first["inputs"]) == 7
    assert len({json.dumps(grid, sort_keys=True) for grid in first["inputs"]}) == 7
    assert all(
        mod.python_mirror(grid, "foreground_only")
        != mod.python_mirror(grid, "entire_span")
        for grid in first["inputs"]
    )

    with pytest.raises(ValueError):
        mod.sample_episode(1, demo_count=0, query_count=4)
    with pytest.raises(ValueError):
        mod.sample_episode(1, demo_count=3, query_count=0)


def test_public_projection_has_opaque_visible_identity_and_omits_private_fields():
    mod = load_prototype()
    episode = mod.sample_episode(20261023, demo_count=3, query_count=4)
    policy = episode["parameters"]["line_span_policy"]
    pairs = [
        {"input": grid, "output": mod.python_mirror(grid, policy)}
        for grid in episode["inputs"]
    ]

    public = mod.public_challenge(pairs, demo_count=3)
    public_id = mod.public_id(public)
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(public_id) == 64

    serialized = json.dumps(public, sort_keys=True)
    assert policy not in serialized
    assert str(episode["seed"]) not in serialized
    assert "program" not in serialized

    changed_private_answers = deepcopy(pairs)
    for pair in changed_private_answers[3:]:
        pair["output"] = [[0]]
    assert mod.public_id(mod.public_challenge(changed_private_answers, demo_count=3)) == public_id


def test_rival_score_uses_demonstrations_only():
    mod = load_prototype()
    chosen = [[[1]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    rival_refuted = [[[2]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    result = mod.score_rival(
        {
            "foreground_only": chosen,
            "entire_span": rival_refuted,
        },
        chosen_policy="foreground_only",
        demo_count=3,
    )
    assert result["status"] == "refuted_by_demonstrations"
    assert result["demonstration_mismatches"] == [0]
    assert result["query_disagreements"] == []

    rival_ambiguous = [[[1]], [[1]], [[1]], [[2]], [[2]], [[2]], [[2]]]
    result = mod.score_rival(
        {
            "foreground_only": chosen,
            "entire_span": rival_ambiguous,
        },
        chosen_policy="foreground_only",
        demo_count=3,
    )
    assert result["status"] == "ambiguous_queries"
    assert result["demonstration_mismatches"] == []
    assert result["query_disagreements"] == [3, 4, 5, 6]


def test_evidence_builder_writes_two_complete_episodes_with_opaque_public_files(tmp_path):
    mod = load_prototype()

    def controlled_verifier(task, program, *, racket_path):
        policy = next(
            policy
            for policy in mod.ALLOWED_POLICIES
            if mod.rule_source(policy) == program
        )
        train_outputs = [
            mod.python_mirror(pair["input"], policy) for pair in task["train"]
        ]
        assert train_outputs == [pair["output"] for pair in task["train"]]
        return {
            "status": "pass",
            "backend": "racket",
            "error": None,
            "test_outputs": [
                mod.python_mirror(pair["input"], policy) for pair in task["test"]
            ],
        }

    out = tmp_path / "evidence"
    report = mod.run_evidence(
        out,
        base_seed=20261023,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=controlled_verifier,
    )

    assert report["status"] == "pass"
    assert report["summary"] == {
        "episodes": 2,
        "retained_inputs": 14,
        "racket_rule_applications": 28,
        "racket_canaries": 2,
        "python_mirror_matches": 28,
        "rival_checks": 2,
        "refuted_rivals": 2,
        "ambiguous_rivals": 0,
        "survived_rivals": 0,
        "query_disagreements": 8,
    }
    runtime_root = find_root(__file__)
    canonical_binding = canonical_path(runtime_root).relative_to(runtime_root).as_posix()
    assert set(report["source_sha256"]) >= {
        "generators/0b9e771d6ba5/generator.py",
        "generators/0b9e771d6ba5/tests/test_parametric_line_span_policy.py",
        "generators/0b9e771d6ba5/workspace/parametric/prototype.py",
        canonical_binding,
    }

    public_files = sorted((out / "public").glob("*.json"))
    assert len(public_files) == 2
    assert all(len(path.stem) == 64 for path in public_files)
    for path in public_files:
        challenge = json.loads(path.read_text())
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all("output" not in pair for pair in challenge["test"])
        text = path.read_text()
        assert "line_span_policy" not in text
        assert "foreground_only" not in text
        assert "entire_span" not in text
        assert "program" not in text
        assert "seed" not in text

    private_files = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(private_files) == 2
    assert {
        json.loads(path.read_text())["parameters"]["line_span_policy"]
        for path in private_files
    } == set(mod.ALLOWED_POLICIES)
    assert (out / "private" / "cross_setting_witness.json").is_file()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "pass"
    assert len(manifest["public_challenges"]) == 2
    assert manifest["public_challenges"] == sorted(manifest["public_challenges"])
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )
    assert len(manifest["private_evidence"]) == 2


def test_evidence_builder_fails_closed_and_retains_report_and_manifest(tmp_path):
    mod = load_prototype()

    def failing_verifier(task, program, *, racket_path):
        return {
            "status": "error",
            "backend": "racket",
            "error": "controlled failure",
            "test_outputs": [],
        }

    out = tmp_path / "failed-evidence"
    report = mod.run_evidence(
        out,
        base_seed=20261023,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=failing_verifier,
    )

    assert report["status"] == "error"
    assert report["error"]["type"] == "RuntimeError"
    assert "controlled failure" in report["error"]["message"]
    assert json.loads((out / "report.json").read_text())["status"] == "error"
    assert json.loads((out / "manifest.json").read_text())["status"] == "error"


def test_evidence_builder_physically_writes_public_files_in_visible_id_order(
    tmp_path, monkeypatch
):
    mod = load_prototype()

    def controlled_verifier(task, program, *, racket_path):
        policy = next(
            policy
            for policy in mod.ALLOWED_POLICIES
            if mod.rule_source(policy) == program
        )
        return {
            "status": "pass",
            "backend": "racket",
            "error": None,
            "test_outputs": [
                mod.python_mirror(pair["input"], policy) for pair in task["test"]
            ],
        }

    out = tmp_path / "evidence"
    public_writes: list[str] = []
    original_write_bytes = Path.write_bytes

    def recording_write_bytes(path: Path, data: bytes) -> int:
        if path.parent == out / "public":
            public_writes.append(path.stem)
        return original_write_bytes(path, data)

    monkeypatch.setattr(Path, "write_bytes", recording_write_bytes)
    report = mod.run_evidence(
        out,
        base_seed=20261023,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=controlled_verifier,
    )

    assert report["status"] == "pass"
    assert len(public_writes) == 2
    assert public_writes == sorted(public_writes)
    assert public_writes == [row["public_id"] for row in report["episodes"]]


def test_assignment_count_contract_is_two_to_six_demos_and_exactly_four_queries():
    mod = load_prototype()
    for demos, queries in ((1, 4), (7, 4), (3, 3), (3, 5), (True, 4)):
        with pytest.raises((TypeError, ValueError)):
            mod.sample_episode(20261024, demo_count=demos, query_count=queries)


def test_episode_sampling_includes_a_lawful_30_by_30_stress_case():
    mod = load_prototype()
    episode = mod.sample_episode(20261024, demo_count=3, query_count=4)
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in episode["inputs"])
    parent = mod._load_parent_generator()
    assert all(parent.self_check(grid) == [] for grid in episode["inputs"])
