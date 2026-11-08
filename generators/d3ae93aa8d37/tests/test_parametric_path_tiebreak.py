from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "d3ae93aa8d37"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "path_tiebreak_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hand_tie_grid() -> list[list[int]]:
    grid = [[0] * 6 for _ in range(6)]
    grid[4][1] = 2
    grid[1][4] = 3
    grid[2][2] = 5
    grid[2][3] = 5
    grid[3][2] = 5
    grid[3][3] = 5
    return grid


def cyan_cells(grid):
    return {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 8
    }


def endpoint_distance(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    green = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
    return abs(red[0] - green[0]) + abs(red[1] - green[1])


def test_rule_sources_keep_exact_default_and_change_only_neighbor_order():
    mod = load_prototype()
    canonical = mod.canonical_program()

    assert mod.rule_source("canonical_udlr") == canonical
    alternative = mod.rule_source("horizontal_first")
    assert alternative != canonical
    assert "(list (list 0 -1) (list 0 1) (list -1 0) (list 1 0))" in alternative
    assert alternative.count("cardinal-deltas") == 0
    with pytest.raises(ValueError):
        mod.rule_source("random")


def test_python_mirror_selects_distinct_equal_length_shortest_paths_on_a_tie():
    mod = load_prototype()
    grid = hand_tie_grid()
    canonical = mod.python_mirror(grid, "canonical_udlr")
    horizontal = mod.python_mirror(grid, "horizontal_first")

    assert cyan_cells(canonical) == {(3, 1), (2, 1), (1, 1), (1, 2), (1, 3)}
    assert cyan_cells(horizontal) == {(4, 2), (4, 3), (4, 4), (3, 4), (2, 4)}
    assert canonical != horizontal
    assert mod.shortest_path_length(grid, "canonical_udlr") == endpoint_distance(grid)
    assert mod.shortest_path_length(grid, "horizontal_first") == endpoint_distance(grid)


@pytest.mark.parametrize("demo_count", [2, 3, 6])
def test_episode_sampling_is_deterministic_fresh_distinct_and_tie_separating(demo_count):
    mod = load_prototype()
    first = mod.sample_episode(20261024, demo_count=demo_count, query_count=4)
    second = mod.sample_episode(20261024, demo_count=demo_count, query_count=4)

    assert first == second
    assert first is not second
    assert first["inputs"] is not second["inputs"]
    assert first["parameters"] == {
        "path_tiebreak": mod.policy_for_seed(20261024)
    }
    assert first["demo_count"] == demo_count
    assert first["query_count"] == 4
    assert len(first["inputs"]) == demo_count + 4
    assert len({json.dumps(grid, sort_keys=True) for grid in first["inputs"]}) == demo_count + 4
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in first["inputs"])
    assert all(
        mod.python_mirror(grid, "canonical_udlr")
        != mod.python_mirror(grid, "horizontal_first")
        for grid in first["inputs"]
    )
    assert all(
        mod.shortest_path_length(grid, "canonical_udlr") == endpoint_distance(grid)
        == mod.shortest_path_length(grid, "horizontal_first")
        for grid in first["inputs"]
    )

    parent, _path, _sha = load_selected_generator(TASK_ID, root=find_root(__file__))
    assert all(parent.self_check(grid) == [] for grid in first["inputs"])


def test_count_contract_is_two_to_six_demonstrations_and_exactly_four_queries():
    mod = load_prototype()
    for demos, queries in ((1, 4), (7, 4), (3, 3), (3, 5), (True, 4)):
        with pytest.raises((TypeError, ValueError)):
            mod.sample_episode(1, demo_count=demos, query_count=queries)


def test_public_projection_has_opaque_identity_and_omits_private_fields():
    mod = load_prototype()
    episode = mod.sample_episode(20261024, demo_count=3, query_count=4)
    policy = episode["parameters"]["path_tiebreak"]
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
    assert "path_tiebreak" not in serialized

    changed_private_answers = deepcopy(pairs)
    for pair in changed_private_answers[3:]:
        pair["output"] = [[0]]
    assert mod.public_id(mod.public_challenge(changed_private_answers, demo_count=3)) == public_id


def test_rival_score_uses_demonstrations_only():
    mod = load_prototype()
    chosen = [[[1]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    rival_refuted = [[[2]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    result = mod.score_rival(
        {"canonical_udlr": chosen, "horizontal_first": rival_refuted},
        chosen_policy="canonical_udlr",
        demo_count=3,
    )
    assert result["status"] == "refuted_by_demonstrations"
    assert result["demonstration_mismatches"] == [0]
    assert result["query_disagreements"] == []

    rival_ambiguous = [[[1]], [[1]], [[1]], [[2]], [[2]], [[2]], [[2]]]
    result = mod.score_rival(
        {"canonical_udlr": chosen, "horizontal_first": rival_ambiguous},
        chosen_policy="canonical_udlr",
        demo_count=3,
    )
    assert result["status"] == "ambiguous_queries"
    assert result["demonstration_mismatches"] == []
    assert result["query_disagreements"] == [3, 4, 5, 6]


def controlled_verifier(mod):
    def verify(task, program, *, racket_path):
        policy = next(
            policy
            for policy in mod.ALLOWED_POLICIES
            if mod.rule_source(policy) == program
        )
        train_outputs = [mod.python_mirror(pair["input"], policy) for pair in task["train"]]
        assert train_outputs == [pair["output"] for pair in task["train"]]
        return {
            "status": "pass",
            "backend": "racket",
            "error": None,
            "test_outputs": [mod.python_mirror(pair["input"], policy) for pair in task["test"]],
        }

    return verify


def test_evidence_builder_writes_complete_source_bound_episodes(tmp_path):
    mod = load_prototype()
    out = tmp_path / "evidence"
    report = mod.run_evidence(
        out,
        base_seed=20261024,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=controlled_verifier(mod),
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
        "generators/d3ae93aa8d37/generator.py",
        "generators/d3ae93aa8d37/tests/test_parametric_path_tiebreak.py",
        "generators/d3ae93aa8d37/workspace/parametric/prototype.py",
        canonical_binding,
    }

    public_files = sorted((out / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        challenge = json.loads(path.read_text())
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all("output" not in pair for pair in challenge["test"])
        text = path.read_text()
        assert "path_tiebreak" not in text
        assert "canonical_udlr" not in text
        assert "horizontal_first" not in text
        assert "program" not in text
        assert "seed" not in text

    private_files = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(private_files) == 2
    assert {
        json.loads(path.read_text())["parameters"]["path_tiebreak"]
        for path in private_files
    } == set(mod.ALLOWED_POLICIES)
    assert (out / "private" / "cross_setting_witness.json").is_file()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "pass"
    assert manifest["public_challenges"] == sorted(manifest["public_challenges"])
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )


def test_evidence_builder_physically_writes_public_files_in_visible_id_order(tmp_path, monkeypatch):
    mod = load_prototype()
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
        base_seed=20261024,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=controlled_verifier(mod),
    )
    assert report["status"] == "pass"
    assert public_writes == sorted(public_writes)
    assert public_writes == [row["public_id"] for row in report["episodes"]]


def test_evidence_builder_fails_closed_and_retains_report(tmp_path):
    mod = load_prototype()

    def failing_verifier(task, program, *, racket_path):
        return {
            "status": "fail",
            "backend": "racket",
            "error": {"code": "controlled", "message": "controlled failure"},
            "test_outputs": [],
        }

    out = tmp_path / "failed-evidence"
    report = mod.run_evidence(
        out,
        base_seed=20261024,
        demo_count=3,
        query_count=4,
        racket_path=Path("/bin/true"),
        verifier=failing_verifier,
    )
    assert report["status"] == "error"
    assert "controlled failure" in report["error"]["message"]
    assert json.loads((out / "report.json").read_text())["status"] == "error"
    assert json.loads((out / "manifest.json").read_text())["status"] == "error"
