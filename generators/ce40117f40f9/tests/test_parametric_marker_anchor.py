from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "ce40117f40f9"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "marker_anchor_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hand_anchor_grid() -> list[list[int]]:
    grid = [[0] * 8 for _ in range(8)]
    grid[5][5] = 4
    grid[5][6] = 4
    grid[6][5] = 4
    grid[3][3] = 9
    return grid


def colored_cells(grid: list[list[int]]) -> set[tuple[int, int, int]]:
    return {
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    }


def test_rule_sources_keep_exact_default_and_materialize_bottom_right_policy():
    mod = load_prototype()
    canonical = mod.canonical_program()

    assert mod.rule_source("top_left") == canonical
    assert mod.rule_source("bottom_right") != canonical
    assert "(rows (s6b-component-crop g cells))" in mod.rule_source("bottom_right")
    assert "(cols (s6b-component-crop g cells))" in mod.rule_source("bottom_right")
    with pytest.raises(ValueError):
        mod.rule_source("center")


def test_python_mirror_moves_the_same_crop_under_each_anchor_interpretation():
    mod = load_prototype()
    grid = hand_anchor_grid()

    top_left = mod.python_mirror(grid, "top_left")
    bottom_right = mod.python_mirror(grid, "bottom_right")

    assert colored_cells(top_left) == {(3, 3, 4), (3, 4, 4), (4, 3, 4)}
    assert colored_cells(bottom_right) == {(2, 2, 4), (2, 3, 4), (3, 2, 4)}
    assert top_left != bottom_right


@pytest.mark.parametrize("demo_count", [2, 3, 6])
def test_episode_sampling_is_deterministic_fresh_distinct_and_policy_separating(demo_count):
    mod = load_prototype()
    first = mod.sample_episode(20261024, demo_count=demo_count, query_count=4)
    second = mod.sample_episode(20261024, demo_count=demo_count, query_count=4)

    assert first == second
    assert first is not second
    assert first["inputs"] is not second["inputs"]
    assert first["parameters"] == {
        "marker_anchor": mod.policy_for_seed(20261024)
    }
    assert first["demo_count"] == demo_count
    assert first["query_count"] == 4
    assert len(first["inputs"]) == demo_count + 4
    assert len({json.dumps(grid, sort_keys=True) for grid in first["inputs"]}) == demo_count + 4
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in first["inputs"])
    assert all(
        mod.python_mirror(grid, "top_left")
        != mod.python_mirror(grid, "bottom_right")
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
    policy = episode["parameters"]["marker_anchor"]
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
    assert "marker_anchor" not in serialized

    changed_private_answers = deepcopy(pairs)
    for pair in changed_private_answers[3:]:
        pair["output"] = [[0]]
    assert mod.public_id(mod.public_challenge(changed_private_answers, demo_count=3)) == public_id


def test_rival_score_uses_demonstrations_only():
    mod = load_prototype()
    chosen = [[[1]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    rival_refuted = [[[2]], [[1]], [[1]], [[1]], [[1]], [[1]], [[1]]]
    result = mod.score_rival(
        {"top_left": chosen, "bottom_right": rival_refuted},
        chosen_policy="top_left",
        demo_count=3,
    )
    assert result["status"] == "refuted_by_demonstrations"
    assert result["demonstration_mismatches"] == [0]
    assert result["query_disagreements"] == []

    rival_ambiguous = [[[1]], [[1]], [[1]], [[2]], [[2]], [[2]], [[2]]]
    result = mod.score_rival(
        {"top_left": chosen, "bottom_right": rival_ambiguous},
        chosen_policy="top_left",
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
        "generators/ce40117f40f9/generator.py",
        "generators/ce40117f40f9/tests/test_parametric_marker_anchor.py",
        "generators/ce40117f40f9/workspace/parametric/prototype.py",
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
        assert "marker_anchor" not in text
        assert "top_left" not in text
        assert "bottom_right" not in text
        assert "program" not in text
        assert "seed" not in text

    private_files = sorted((out / "private" / "episodes").glob("*.json"))
    assert len(private_files) == 2
    assert {
        json.loads(path.read_text())["parameters"]["marker_anchor"]
        for path in private_files
    } == set(mod.ALLOWED_POLICIES)
    assert (out / "private" / "cross_setting_witness.json").is_file()
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "pass"
    assert manifest["public_challenges"] == sorted(manifest["public_challenges"])
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )


def test_evidence_builder_physically_writes_public_files_in_visible_id_order(
    tmp_path, monkeypatch
):
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
