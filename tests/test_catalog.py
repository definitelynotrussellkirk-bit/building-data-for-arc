import json

import pytest

from arcpuzzles import Catalog
from arcpuzzles.cli import main


def test_filters_combine_and_alias_resolves(library):
    catalog = Catalog(library)
    result = catalog.query(approved=True, source="training", difficulty="easy", skill="REFLECTION", primitive="flip-lr")
    assert [r["id"] for r in result] == ["aaaa00000001"]
    assert catalog.get("old-first")["id"] == "aaaa00000001"
    assert len(catalog.query(source="bank")) == 1
    assert catalog.query(search="absent") == []
    assert len(catalog.query(approved=False)) == 1


def test_approval_is_revoked_when_source_or_rule_changes(library):
    catalog = Catalog(library)
    assert catalog.describe("aaaa00000001")["approved"]
    generator = library / "generators/aaaa00000001/generator.py"
    generator.write_text(generator.read_text() + "# change\n")
    assert "generator_changed_since_review" in catalog.describe("aaaa00000001")["approval_reasons"]
    path = library / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["program_solution"] = "(rule! (flip-lr g))"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    assert "rule_changed_since_review" in catalog.describe("aaaa00000002")["approval_reasons"]


@pytest.mark.parametrize("field,value,reason", [
    ("semantic_veto", True, "active_semantic_veto"),
    ("mix_weight", 0, "nonpositive_mix_weight"),
    ("mix_weight", float("nan"), "nonpositive_mix_weight"),
    ("reviewed_generator_sha256", None, "missing_reviewed_generator_hash"),
    ("reviewed_rule_hash", None, "missing_reviewed_rule_hash"),
    ("train_safety", "reviewed_unsafe", "not_reviewed_safe"),
])
def test_approval_does_not_silently_broaden(library, field, value, reason):
    catalog = Catalog(library)
    catalog._records["aaaa00000001"][field] = value
    assert reason in catalog.describe("aaaa00000001")["approval_reasons"]
    assert not catalog.describe("aaaa00000001")["approved"]


def test_missing_generator_and_duplicate_rule_are_not_approved(library):
    catalog = Catalog(library)
    (library / "generators/aaaa00000001/generator.py").unlink()
    assert "missing_generator" in catalog.describe("aaaa00000001")["approval_reasons"]
    path = library / "shared/data/canonical/puzzles.jsonl"
    with path.open("a") as handle:
        handle.write(json.dumps({"task_id": "aaaa00000002", "program_solution": "(rule! flip-lr)"}) + "\n")
    assert "ambiguous_canonical_rule" in catalog.describe("aaaa00000002")["approval_reasons"]


def test_challenge_omits_query_answers_rules_and_summary(library):
    challenge = Catalog(library).challenge("aaaa00000001")
    assert challenge == {"id": "aaaa00000001", "variant": 0,
                         "train": [{"input": [[1]], "output": [[2]]}], "test": [{"input": [[3]]}]}


def test_paging_sampling_and_empty_results(library):
    catalog = Catalog(library)
    assert catalog.query(limit=0) == []
    assert catalog.query(offset=99) == []
    assert catalog.query(sample=2, seed=7) == catalog.query(sample=2, seed=7)
    assert len(catalog.query(sample=99)) == 3
    with pytest.raises(ValueError):
        catalog.query(offset=-1)
    with pytest.raises(KeyError):
        catalog.get("../../secret")


def test_cli_machine_outputs_and_nonzero_errors(library, capsys):
    assert main(["--library", str(library), "list", "--approved", "--format", "json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert main(["--library", str(library), "list", "--approved", "--count"]) == 0
    assert capsys.readouterr().out.strip() == "2"
    assert main(["--library", str(library), "list", "--offset", "-1"]) == 1
    assert "nonnegative" in capsys.readouterr().err
    assert main(["--library", str(library), "show", "missing"]) == 1


def test_returned_records_do_not_mutate_catalog(library):
    catalog = Catalog(library)
    row = catalog.get("aaaa00000001")
    row["skills"].clear()
    row["variants"][0]["test"][0]["output"][0][0] = 9
    assert catalog.get("aaaa00000001")["skills"] == ["reflection"]
    assert catalog.get("aaaa00000001")["variants"][0]["test"][0]["output"] == [[4]]


def test_challenge_normalizes_row_strings_and_rejects_partial_pairs(library):
    path = library / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["train"] = [{"input": ["01", "23"], "output": ["45", "67"]}]
    rows[0]["test"] = {"input": ["89"], "output": ["99"]}
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    catalog = Catalog(library)
    result = catalog.challenge("aaaa00000001")
    assert result["test"] == [{"input": [[8, 9]]}]
    assert result["train"][0]["input"] == [[0, 1], [2, 3]]
    rows[0]["train"].append({"input": [[1]]})
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="malformed pairs"):
        catalog.challenge("aaaa00000001")


def test_original_id_alias_file_and_ambiguous_alias(library):
    (library / "catalog/aliases.json").write_text(json.dumps({"old": ["aaaa00000001"],
        "ambiguous": ["aaaa00000001", "aaaa00000002"]}))
    catalog = Catalog(library)
    assert catalog.resolve("old") == "aaaa00000001"
    assert "old" in catalog.describe("old")["aliases"]
    with pytest.raises(ValueError, match="Ambiguous"):
        catalog.resolve("ambiguous")


def test_official_lineage_is_bound_to_generator_and_unambiguous(library):
    (library / "catalog/aliases.json").write_text(json.dumps({"1234abcd": ["aaaa00000001"]}))
    catalog = Catalog(library)
    evidence = {"generator_id": "aaaa00000001", "mapping_status": "verified",
                "source_split": "training", "source_task_id": "1234abcd",
                "source_hashes": {"generator_sha256": catalog.describe("aaaa00000001")["generator_sha256"]}}
    path = library / "shared/data/derived/official_generator_lineage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence) + "\n")
    assert catalog.lineage("1234abcd")["family_id"] == "official:training:1234abcd"
    assert catalog.lineage("1234abcd")["verified"]
    generator = library / "generators/aaaa00000001/generator.py"
    generator.write_text(generator.read_text() + "\n# changed after mapping\n")
    assert "lineage_generator_hash_changed" in catalog.lineage("1234abcd")["reasons"]
    path.write_text((json.dumps(evidence) + "\n") * 2)
    assert catalog.lineage("1234abcd")["reasons"] == ["missing_or_ambiguous_lineage"]
