"""Replay verifier contract for retained border-policy prototype evidence."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "36275402c6b2"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    assert path.is_file(), f"{path.name} is not implemented"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return _load("parametric_border_policy_for_verifier", PARAMETRIC / "prototype.py")


@cache
def verifier():
    return _load("parametric_border_policy_evidence_verifier", PARAMETRIC / "verify_evidence.py")


def _evidence(tmp_path: Path) -> Path:
    out = tmp_path / "evidence"
    prototype().write_evidence(
        out,
        seeds=[0, 1],
        demo_count=2,
        query_count=2,
        root=ROOT,
    )
    return out


def test_verifier_replays_rules_inputs_and_privacy_boundary(tmp_path: Path) -> None:
    """Catches a verifier that trusts reports instead of deterministic replay."""
    result = verifier().verify_evidence(_evidence(tmp_path), root=ROOT)
    assert result == {
        "task_id": TASK_ID,
        "status": "verified",
        "episodes": 2,
        "demonstrations": 4,
        "queries": 4,
        "policies": {"preserve": 1, "recolour": 1},
        "covered_border_sides": ["bottom", "left", "right", "top"],
        "canonical_pairs": 5,
    }


def test_verifier_rejects_public_extra_fields_even_when_visible_pairs_are_unchanged(
    tmp_path: Path,
) -> None:
    """Catches private metadata leakage hidden behind permissive JSON parsing."""
    out = _evidence(tmp_path)
    public_path = next((out / "public").glob("*.json"))
    data = json.loads(public_path.read_text(encoding="utf-8"))
    data["seed"] = 0
    public_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canonical visible bytes"):
        verifier().verify_evidence(out, root=ROOT)


def test_verifier_rejects_hash_valid_private_answer_tamper(tmp_path: Path) -> None:
    """Catches a verifier that checks structure but not Racket-backed replay."""
    out = _evidence(tmp_path)
    private_path = next((out / "private" / "episodes").glob("*.json"))
    data = json.loads(private_path.read_text(encoding="utf-8"))
    data["query_answers"][0][0][0] = (data["query_answers"][0][0][0] + 1) % 10
    private_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="private episode replay mismatch"):
        verifier().verify_evidence(out, root=ROOT)


def test_verifier_rejects_manifest_rows_not_sorted_by_public_id(tmp_path: Path) -> None:
    """Catches hidden seed order reintroduced after public files are materialized."""
    out = _evidence(tmp_path)
    manifest_path = out / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["episodes"] = list(reversed(data["episodes"]))
    manifest_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="sorted by public ID"):
        verifier().verify_evidence(out, root=ROOT)
