"""Retain explicit historical rules without inheriting approval or bypassing checks."""
import shutil

import pytest

from arcpuzzles import Catalog
from arcpuzzles.catalog import jsonl
from arcpuzzles.datasets import _identity, verify_dataset


# Measured in the full v0.3 census against the retained original runner.
HISTORICAL_PAIRS = {
    "7c7796f15a18": "4976ceb768c02dd60064e23b54f8794a95d0a95206e09f2a14da8f3ed486e9e1",
    "defba1ab4f90": "8b35cf5d019df0dad8364813e07e7cc53beb0889c77864f66251e5b4b16cfbe0",
    "83edd318e70a": "c816f9a410672908daba04df47ed85e33ccf13c86e7504df2aa1eec0cb839425",
    "9d46a0f24d04": "c53abb53a188e6c5b734424d2ed2afe7e7a1aa8a9d774e9c74ced5752881be3f",
}


def test_archival_reference_requires_explicit_unapproved_research(tmp_path):
    catalog = Catalog()
    with pytest.raises(ValueError, match="allow_unapproved"):
        catalog.generate("6c68e1b008a5", reference="archival")
    output = tmp_path / "not-created"
    with pytest.raises(ValueError, match="allow_unapproved"):
        catalog.export(output, count=1, reference="archival")
    assert not output.exists()


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
@pytest.mark.parametrize("task_id,expected", HISTORICAL_PAIRS.items())
def test_archival_rule_access_matches_measured_historical_pairs(task_id, expected):
    row, = Catalog().generate(task_id, seed=17, difficulty="medium", n_train=1, n_test=1,
                             allow_unapproved=True, reference="archival")
    assert _identity({"train": row["train"], "test": row["test"]}) == expected
    assert row["provenance"]["rule_hash"] == row["executed_rule_hash"]
    assert row["provenance"]["reference"] == "archival"
    assert row["provenance"]["approved"] is False


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
@pytest.mark.parametrize("task_id", ["c55491432288", "d982cffd80f8"])
def test_archival_rules_still_enforce_generator_self_checks(task_id):
    catalog = Catalog()
    row, = catalog.generate(task_id, seed=17, difficulty="medium", n_train=1, n_test=1,
                             allow_unapproved=True, reference="archival")
    assert any("self_check:" in r["reason"] for r in row["rejections"])
    assert 0 not in row["sample_indices"]
    if catalog.describe(task_id)["train_safety"] == "unsafe":
        assert row["provenance"]["train_safety"] == "unsafe"


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_canonical_approval_never_transfers_to_archival_execution():
    catalog = Catalog()
    row, = catalog.generate("6c68e1b008a5", seed=17, n_train=1, n_test=1,
                             allow_unapproved=True, reference="archival")
    assert catalog.describe("6c68e1b008a5")["approved"]
    assert row["provenance"]["catalog_approved"] is True
    assert row["provenance"]["approved"] is False
    assert row["provenance"]["train_safety"] == "unverified"


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime required")
def test_archival_export_retains_actual_rule_and_private_boundary(tmp_path):
    output = tmp_path / "archival"
    result = Catalog().export(output, count=1, seed=17, task_ids=["7c7796f15a18"],
                               n_train=1, n_test=1, sampling="uniform", reference="archival",
                               allow_unapproved=True, style="native")
    assert result["status"] == "complete" and verify_dataset(output) == result
    public, = jsonl(output / "public.jsonl")
    native, = jsonl(output / "data.private.jsonl")
    episode, = jsonl(output / "episodes.private.jsonl")
    assert public["episode_id"] == native["episode_id"] == episode["episode_id"]
    assert set(public["test"][0]) == {"input"}
    assert native["source_provenance"]["approved"] is False
    assert native["source_provenance"]["rule_hash"] == episode["executed_rule_hash"]
    assert native["source_provenance"]["catalog_rule_hash"] is None
