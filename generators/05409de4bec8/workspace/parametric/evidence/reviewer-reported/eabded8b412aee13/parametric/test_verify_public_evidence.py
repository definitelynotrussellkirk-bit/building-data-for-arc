from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
CHECKER_PATH = HERE / "verify_public_evidence.py"
EVIDENCE = HERE / "rectangle-policy-public-writer-v4"
VERIFIER = (
    WORK
    / "repo/generators/05409de4bec8/workspace/parametric/verify.py"
)


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "rectangle_policy_public_evidence_checker", CHECKER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load public-evidence checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_accepts_current_visible_only_evidence():
    checker = load_checker()
    receipt = checker.verify_evidence(EVIDENCE, VERIFIER)

    assert receipt["status"] == "passed"
    assert receipt["counts"] == {"demonstrations": 5, "queries": 4}
    assert receipt["settings"] == ["both", "longer"]
    assert receipt["public_ids"] == sorted(receipt["public_ids"])
    assert receipt["checks"]["exact_public_bytes_hash_to_full_id"] is True
    assert receipt["checks"]["public_projection_matches_private_episode"] is True
    assert receipt["checks"]["manifest_complete_and_exact"] is True


def test_checker_rejects_verifier_drift(tmp_path):
    checker = load_checker()
    drifted = tmp_path / "verify.py"
    drifted.write_bytes(VERIFIER.read_bytes() + b"\n# drift\n")

    with pytest.raises(AssertionError, match="verifier hash"):
        checker.verify_evidence(EVIDENCE, drifted)
