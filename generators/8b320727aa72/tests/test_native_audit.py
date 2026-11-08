"""The bounded authoring audit retains private labels and safe first turns."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/check_native.py"


def load_audit():
    assert SOURCE.is_file(), "the reusable native audit runner must exist"
    spec = importlib.util.spec_from_file_location("native_disagreement_audit_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_audit_keeps_answers_private_and_rejects_serialized_leaks(tmp_path):
    audit = load_audit()
    destination = tmp_path / "audit"
    report = audit.run_audit(destination)
    assert report["status"] == "passed", report
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["selected_labels_checked"] == 42
    assert report["owner_accepted"] is False
    assert report["training_admitted"] is False
    assert len(report["episodes"]) == 6
    assert report["first_turn_checks"] == 6
    for row in report["episodes"]:
        private = json.loads((destination / row["private_path"]).read_bytes())
        assert len(private["train"]) == 3
        assert len(private["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in private["test"])
        assert private["program_solution"]
        public_path = destination / row["first_turn_path"]
        payload = public_path.read_bytes()
        public = json.loads(payload)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert public_path.stem == hashlib.sha256(payload).hexdigest()
    assert report["public_check"]["status"] == "passed"
    for name, code in (
        ("query_output", "public_schema"),
        ("boolean_cell", "public_grid"),
        ("duplicate_input", "duplicate_input"),
        ("wrong_count", "query_count"),
    ):
        negative = report["negative_public_checks"][name]
        assert negative["status"] == "failed"
        assert code in {finding["code"] for finding in negative["findings"]}
    assert report["rival_audit"]["episodes_checked"] == 2
    assert report["rival_audit"]["rivals_per_episode"] >= 9
    assert not report["rival_audit"]["survivors"]
    assert len(report["rival_audit"]["witnesses"]) >= 9
    assert (destination / "audit.json").is_file()
    with pytest.raises(FileExistsError):
        audit.run_audit(destination)
