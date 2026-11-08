"""Focused tests for the task-local public-focus and legend-selector prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge, RacketBridgeError
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "89ab40aedfe4"
PUBLIC_PARENT_ID = "d59b0160"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = TASK_HOME / "workspace" / "parametric"


def _load_optional(name: str, path: Path):
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PUBLIC = _load_optional("public_focus_89ab40aedfe4", PARAMETRIC / "public_focus.py")
PROTO = _load_optional("parametric_89ab40aedfe4", PARAMETRIC / "prototype.py")
GEN = _load_optional("generator_89ab40aedfe4_for_parametric", TASK_HOME / "generator.py")


def _public_task() -> dict:
    path = ROOT / "shared" / "data" / "raw" / "arc-agi_evaluation_challenges.json"
    return json.loads(path.read_text(encoding="utf-8"))[PUBLIC_PARENT_ID]


def _canonical_program() -> str:
    values = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            values.append(row["program_solution"])
    assert values and len(set(values)) == 1
    return values[0]


def _pattern(height: int, *foreground_rows: int) -> tuple[int, ...]:
    active = set(foreground_rows)
    return tuple(1 if row in active else 0 for row in range(height))


def _grid_from_patterns(patterns: tuple[tuple[int, ...], ...], fg: int = 6) -> list[list[int]]:
    height = len(patterns[0])
    assert all(len(pattern) == height for pattern in patterns)
    width = 3 * (len(patterns) - 1) + 2
    grid = [[0] * width for _ in range(height)]
    for index, pattern in enumerate(patterns):
        start = 3 * index
        for row in range(height):
            grid[row][start] = fg
            grid[row][start + 1] = fg if pattern[row] else 0
    return grid


def _racket_application(program: str, grid: list[list[int]]) -> str:
    stripped = program.strip()
    assert stripped.startswith("(rule!") and stripped.endswith(")")
    expression = stripped[len("(rule!") : -1].strip()
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"({expression} '({rows}))"


def _public_test_prediction() -> list[list[int]]:
    # Key colors are {2, 4, 5}.  The three four-connected external regions
    # containing all three are replaced by background 7; all others remain.
    return [
        [7,2,7,3,7,7,7,7,7,7,7,7,7,7,7,7],
        [7,7,5,3,7,7,7,7,7,7,0,0,0,0,0,7],
        [7,4,7,3,7,7,7,7,7,7,4,0,5,0,0,7],
        [3,3,3,3,7,7,7,7,7,7,4,0,8,0,0,7],
        [7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [9,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,8,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [6,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,7,7,7,7,7,7,7,7,7,0,0,0,0,0],
        [5,0,7,7,7,7,7,7,7,7,7,0,0,9,0,1],
        [0,0,7,7,7,7,7,7,7,7,7,1,0,4,0,0],
        [5,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
        [0,0,7,7,7,7,7,7,7,7,7,7,7,7,7,7],
    ]


def test_public_focus_rule_matches_all_demonstrations_and_predicts_query() -> None:
    assert PUBLIC is not None, "public_focus.py has not been implemented"
    task = _public_task()
    for pair in task["train"]:
        assert PUBLIC.apply_rule(pair["input"]) == pair["output"]
    assert PUBLIC.key_colors(task["test"][0]["input"]) == frozenset({2, 4, 5})
    assert PUBLIC.apply_rule(task["test"][0]["input"]) == _public_test_prediction()


def test_public_focus_uses_four_connectivity_not_diagonal_contact() -> None:
    assert PUBLIC is not None, "public_focus.py has not been implemented"
    grid = [[7] * 8 for _ in range(8)]
    for index in range(4):
        grid[3][index] = 3
        grid[index][3] = 3
    grid[0][0] = 1
    grid[0][1] = 2
    grid[5][5] = 1
    grid[6][6] = 2
    assert PUBLIC.apply_rule(grid) == grid


def test_default_program_is_exact_canonical_and_variant_is_distinct() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    canonical = _canonical_program()
    assert PROTO.program_for("all_slots", root=ROOT) == canonical
    assert PROTO.program_for("contains_key", root=ROOT) != canonical


def test_contains_key_sorts_only_matching_candidates_and_preserves_ties() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    height = 8
    key = _pattern(height, 0, 2, 5)
    selected_a = _pattern(height, 0, 1, 2, 4, 5)  # count 5
    unselected = _pattern(height, 0, 1, 2, 6)  # misses required row 5
    selected_c = _pattern(height, 0, 2, 3, 5, 7)  # count 5
    selected_d = _pattern(height, 0, 2, 5, 6)  # count 4
    grid = _grid_from_patterns((key, selected_a, unselected, selected_c, selected_d))

    expected_contains = _grid_from_patterns(
        (key, selected_d, unselected, selected_a, selected_c)
    )
    expected_all = _grid_from_patterns(
        (key, unselected, selected_d, selected_a, selected_c)
    )
    assert PROTO.apply_python(grid, "contains_key") == expected_contains
    assert PROTO.apply_python(grid, "all_slots") == expected_all
    assert expected_contains != expected_all


def test_contains_key_rejects_an_empty_body_key() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    height = 8
    key = _pattern(height, 0)
    a = _pattern(height, 0, 1, 2)
    b = _pattern(height, 0, 2, 3, 4)
    c = _pattern(height, 0, 1, 4, 5)
    grid = _grid_from_patterns((key, a, b, c))
    with pytest.raises(ValueError, match="key.*body"):
        PROTO.apply_python(grid, "contains_key")


def test_contains_key_racket_rejects_an_empty_body_key() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    height = 8
    grid = _grid_from_patterns((
        _pattern(height, 0),
        _pattern(height, 0, 1, 2),
        _pattern(height, 0, 2, 3, 4),
        _pattern(height, 0, 1, 4, 5),
    ))
    bridge = RacketBridge(timeout=30)
    try:
        with pytest.raises(RacketBridgeError, match="contains_key"):
            bridge.eval_text(_racket_application(PROTO.program_for("contains_key", root=ROOT), grid))
    finally:
        bridge.shutdown()


def test_contains_key_racket_rejects_fewer_than_two_matches() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    height = 8
    grid = _grid_from_patterns((
        _pattern(height, 0, 2, 5),
        _pattern(height, 0, 2, 5, 6),
        _pattern(height, 0, 2, 6),
        _pattern(height, 0, 1, 5),
    ))
    with pytest.raises(ValueError, match="at least two"):
        PROTO.apply_python(grid, "contains_key")
    bridge = RacketBridge(timeout=30)
    try:
        with pytest.raises(RacketBridgeError, match="contains_key"):
            bridge.eval_text(_racket_application(PROTO.program_for("contains_key", root=ROOT), grid))
    finally:
        bridge.shutdown()


def test_episode_is_fixed_distinguishing_and_has_four_distinct_queries() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    assert GEN is not None
    seed = 20261023
    for mode in PROTO.SELECTION_MODES:
        episode = PROTO.build_episode(
            seed,
            selection_mode=mode,
            demonstration_count=3,
            query_count=4,
            root=ROOT,
        )
        assert episode["parameter"] == {"selection_mode": mode}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        all_pairs = episode["train"] + episode["test"]
        for pair in all_pairs:
            assert GEN.self_check(pair["input"]) == []
            assert pair["output"] == PROTO.apply_python(pair["input"], mode)
            other = next(value for value in PROTO.SELECTION_MODES if value != mode)
            assert pair["output"] != PROTO.apply_python(pair["input"], other)
        query_inputs = {json.dumps(pair["input"], separators=(",", ":")) for pair in episode["test"]}
        assert len(query_inputs) == 4
        assert episode == PROTO.build_episode(
            seed,
            selection_mode=mode,
            demonstration_count=3,
            query_count=4,
            root=ROOT,
        )

        public = PROTO.public_challenge(episode)
        serialized = json.dumps(public, sort_keys=True)
        assert "selection_mode" not in serialized
        assert "program" not in serialized
        assert all("output" in pair for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])


def test_invalid_modes_and_episode_counts_fail_loudly() -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    with pytest.raises(ValueError, match="selection_mode"):
        PROTO.program_for("unknown", root=ROOT)
    with pytest.raises(ValueError, match="demonstration_count"):
        PROTO.build_episode(1, selection_mode="all_slots", demonstration_count=0, root=ROOT)
    with pytest.raises(ValueError, match="query_count"):
        PROTO.build_episode(1, selection_mode="all_slots", query_count=0, root=ROOT)


def test_verifier_executes_racket_and_materializes_masked_artifacts(tmp_path: Path) -> None:
    verify = PARAMETRIC / "verify.py"
    assert verify.is_file(), "verify.py has not been implemented"
    report_path = tmp_path / "report.json"
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    legacy_files = {"all-slots-public.json": b"legacy\n", "contains-key-public.json": b"legacy\n"}
    for name, body in legacy_files.items():
        (artifact_dir / name).write_bytes(body)
    (artifact_dir / "manifest.json").write_text(
        json.dumps({
            "schema": "89ab40aedfe4-legend-selector-materialization-v1",
            "files": {
                name: {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
                for name, body in legacy_files.items()
            },
        }),
        encoding="utf-8",
    )
    run = subprocess.run(
        [
            sys.executable,
            str(verify),
            "--seed",
            "20261023",
            "--out",
            str(report_path),
            "--artifact-dir",
            str(artifact_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stderr or run.stdout
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["counts"] == {
        "settings": 2,
        "train_pairs_per_setting": 3,
        "query_pairs_per_setting": 4,
        "episode_pairs": 14,
        "racket_executions": 28,
        "distinguishing_demonstrations": 6,
        "public_parent_train_pairs": 3,
    }
    assert report["input_uniqueness"] == {
        "all_slots": 7,
        "contains_key": 7,
        "paired_inputs_equal": True,
    }
    assert report["public_parent"]["task_id"] == PUBLIC_PARENT_ID
    assert report["public_parent"]["training_exact"] is True
    assert report["public_parent"]["test_prediction"] == _public_test_prediction()
    assert all(row["python_racket_match"] for row in report["checks"])
    assert all(row["settings_distinct"] for row in report["checks"])

    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    expected_files = {
        "all-slots.rkt",
        "all-slots-private.json",
        "contains-key.rkt",
        "contains-key-private.json",
    }
    expected_public_ids = {}
    for mode in PROTO.SELECTION_MODES:
        stem = mode.replace("_", "-")
        private = json.loads((artifact_dir / f"{stem}-private.json").read_text(encoding="utf-8"))
        public = PROTO.public_challenge(private)
        public_id = public_challenge_id(public)
        public_name = f"public-{public_id}.json"
        expected_public_ids[mode] = {"public_id": public_id, "path": public_name}
        expected_files.add(public_name)
        assert (artifact_dir / public_name).read_bytes() == public_challenge_bytes(public)
        serialized = json.dumps(public, sort_keys=True)
        assert "selection_mode" not in serialized
        assert "program" not in serialized
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
    assert set(manifest["files"]) == expected_files
    assert manifest["public"] == expected_public_ids
    assert {path.name for path in artifact_dir.iterdir()} == expected_files | {"manifest.json"}


def test_verifier_preserves_modified_prior_artifacts_and_fails(tmp_path: Path) -> None:
    assert PROTO is not None, "prototype.py has not been implemented"
    verify = PARAMETRIC / "verify.py"
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    name = "all-slots-public.json"
    expected = b"expected prior bytes\n"
    actual = b"modified outside the materializer\n"
    (artifact_dir / name).write_bytes(actual)
    (artifact_dir / "manifest.json").write_text(
        json.dumps({
            "schema": "89ab40aedfe4-legend-selector-materialization-v1",
            "files": {
                name: {"sha256": hashlib.sha256(expected).hexdigest(), "bytes": len(expected)}
            },
        }),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"
    run = subprocess.run(
        [
            sys.executable,
            str(verify),
            "--seed",
            "20261023",
            "--out",
            str(report_path),
            "--artifact-dir",
            str(artifact_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert run.returncode != 0
    assert "prior artifact hash/size mismatch" in (run.stderr + run.stdout)
    assert (artifact_dir / name).read_bytes() == actual
    assert not report_path.exists()


def test_verifier_preserves_manifest_named_foreign_files_and_fails(tmp_path: Path) -> None:
    verify = PARAMETRIC / "verify.py"
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    name = "important.txt"
    body = b"not a generated artifact\n"
    (artifact_dir / name).write_bytes(body)
    (artifact_dir / "manifest.json").write_text(
        json.dumps({
            "schema": "89ab40aedfe4-legend-selector-materialization-v1",
            "files": {
                name: {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
            },
        }),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.json"
    run = subprocess.run(
        [
            sys.executable,
            str(verify),
            "--seed",
            "20261023",
            "--out",
            str(report_path),
            "--artifact-dir",
            str(artifact_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert run.returncode != 0
    assert "unexpected prior artifact name" in (run.stderr + run.stdout)
    assert (artifact_dir / name).read_bytes() == body
    assert not report_path.exists()
