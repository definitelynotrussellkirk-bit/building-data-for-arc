"""Live-Racket evidence writer checks for the task-local parametric prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The test's tree does not contain reviewer_support.py")

from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "31b8bedd699a"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
BUILDER = PARAMETRIC / "build_evidence.py"


def _load_builder():
    assert BUILDER.is_file(), f"parametric Racket evidence builder is missing: {BUILDER}"
    spec = importlib.util.spec_from_file_location(
        "parametric_token_tie_evidence_31b8bedd699a", BUILDER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_writer_builds_six_racket_verified_three_demo_four_query_episodes(tmp_path):
    builder = _load_builder()
    out = tmp_path / "evidence"
    summary = builder.write_evidence(
        out,
        seed=20261023,
        demo_count=3,
        query_count=4,
    )
    assert summary["status"] == "pass"
    assert summary["classification"] == "prototype_proposed_not_production_approved"
    assert summary["all_racket_outputs_match_stored"] is True
    assert summary["all_python_outputs_match_racket"] is True
    assert summary["all_demos_identify_selected_settings"] is True
    assert summary["all_queries_discriminate_some_alternative"] is True
    assert summary["all_public_challenges_masked"] is True
    assert summary["all_episode_verifiers_pass"] is True
    assert summary["known_shortcut_refuted_by_every_episode"] is True
    assert summary["shared_input_count"] == 7
    assert summary["cross_setting_witness"]["all_outputs_distinct"] is True
    assert summary["racket_runtime"]["protected"] is True

    execution = summary["execution"]
    assert set(execution) == {
        "3-horizontal",
        "3-vertical",
        "4-horizontal",
        "4-vertical",
        "5-horizontal",
        "5-vertical",
    }
    assert execution["4-horizontal"]["program_is_exact_canonical_text"] is True
    assert all(row["demo_count"] == 3 for row in execution.values())
    assert all(row["query_count"] == 4 for row in execution.values())
    assert all(row["racket_outputs_match_stored"] is True for row in execution.values())
    assert all(row["python_outputs_match_racket"] is True for row in execution.values())
    assert all(row["demos_identify_selected_setting"] is True for row in execution.values())
    assert all(row["query_shortcut_refutations"] >= 1 for row in execution.values())

    public_files = sorted((out / "public").glob("challenge-*.json"))
    assert len(public_files) == 6
    assert len({path.name for path in public_files}) == 6
    for path in public_files:
        public = json.loads(path.read_text())
        assert path.read_bytes() == public_challenge_bytes(public)
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = path.read_text()
        for hidden in ("token_size", "tie_policy", "program", "seed", "generator_seed"):
            assert hidden not in serialized

    private_rows = [
        json.loads(line)
        for line in (out / "private" / "episodes.jsonl").read_text().splitlines()
    ]
    assert len(private_rows) == 6
    assert all(len(row["train"]) == 3 and len(row["test"]) == 4 for row in private_rows)


def test_writer_rejects_duplicate_settings_and_nonempty_destination(tmp_path):
    builder = _load_builder()
    with pytest.raises(ValueError):
        builder.write_evidence(
            tmp_path / "duplicates",
            settings=((4, "horizontal"), (4, "horizontal")),
        )

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        builder.write_evidence(
            occupied,
            settings=((4, "horizontal"), (4, "vertical")),
        )
