"""Live-Racket evidence tests for the pass-budget prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "135219aecdb4"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
BUILDER = PARAMETRIC / "build_evidence.py"


def _load_builder():
    assert BUILDER.is_file(), "parametric Racket evidence builder is missing"
    spec = importlib.util.spec_from_file_location(
        "pass_budget_evidence_135219aecdb4", BUILDER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"missing canonical row {TASK_ID}")


def test_writer_builds_three_racket_verified_four_query_episodes(tmp_path):
    builder = _load_builder()
    out = tmp_path / "evidence"
    summary = builder.write_evidence(
        out,
        seed=17,
        pass_counts=(1, 2, 3),
        demo_count=2,
        query_count=4,
    )

    assert summary["status"] == "pass"
    assert summary["classification"] == "prototype_proposed_not_production_approved"
    assert summary["parameter"] == {
        "name": "pass_count",
        "allowed": [1, 2, 3],
        "default": 3,
        "selected_once_per_episode": True,
        "input_grammar_changed": False,
    }
    assert summary["all_racket_outputs_match_stored"] is True
    assert summary["all_python_outputs_match_racket"] is True
    assert summary["all_demos_refute_alternative_settings"] is True
    assert summary["all_queries_distinguish_alternative_settings"] is True
    assert summary["all_public_challenges_masked"] is True
    assert summary["unique_input_count"] == 6
    assert summary["racket_runtime"]["protected"] is True

    executions = summary["execution"]
    assert set(executions) == {"1", "2", "3"}
    for key, row in executions.items():
        assert row["pass_count"] == int(key)
        assert row["train_count"] == 2
        assert row["query_count"] == 4
        assert row["racket_outputs_match_stored"] is True
        assert row["python_outputs_match_racket"] is True
        assert row["all_demonstrations_refute_alternatives"] is True
        assert row["all_queries_distinguish_alternatives"] is True
        assert set(row["alternative_settings"]) == ({1, 2, 3} - {int(key)})
        program_path = out / row["program_file"]
        assert hashlib.sha256(program_path.read_bytes()).hexdigest() == row["program_sha256"]
    assert executions["3"]["program_is_exact_canonical_text"] is True
    assert (out / executions["3"]["program_file"]).read_text() == _canonical_program()

    public_files = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_files) == 3
    assert len({path.name for path in public_files}) == 3
    for path in public_files:
        assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name)
        challenge = json.loads(path.read_text())
        assert set(challenge) == {"train", "test"}
        assert len(challenge["train"]) == 2
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        encoded = path.read_text()
        for hidden in ("pass_count", "program", "seed", "query_output"):
            assert hidden not in encoded

    private_rows = [
        json.loads(line)
        for line in (out / "private" / "episodes.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert {row["parameter"]["pass_count"] for row in private_rows} == {1, 2, 3}
    assert all(len(row["test"]) == 4 for row in private_rows)
    assert all(all("output" in pair for pair in row["test"]) for row in private_rows)


def test_writer_rejects_duplicate_settings_and_nonempty_destination(tmp_path):
    builder = _load_builder()
    with pytest.raises(ValueError, match="duplicate pass_count"):
        builder.write_evidence(
            tmp_path / "dupe",
            seed=17,
            pass_counts=(1, 1),
            demo_count=2,
            query_count=4,
        )

    with pytest.raises(ValueError, match="at least two"):
        builder.write_evidence(
            tmp_path / "single",
            seed=17,
            pass_counts=(1,),
            demo_count=2,
            query_count=4,
        )

    with pytest.raises(ValueError, match="default pass_count=3"):
        builder.write_evidence(
            tmp_path / "missing-default",
            seed=17,
            pass_counts=(1, 2),
            demo_count=2,
            query_count=4,
        )

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "sentinel.txt").write_text("do not overwrite")
    with pytest.raises(FileExistsError, match="nonempty"):
        builder.write_evidence(
            occupied,
            seed=17,
            pass_counts=(1, 2, 3),
            demo_count=2,
            query_count=4,
        )
