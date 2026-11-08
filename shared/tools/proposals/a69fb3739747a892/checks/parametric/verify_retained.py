"""Check persisted prototype evidence against current source and serialized files."""
from pathlib import Path
import hashlib
import json
import sys


HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
EVIDENCE = HERE / (sys.argv[1] if len(sys.argv) > 1 else "evidence-final")
REPO = WORK / "repo"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read(relative):
    return json.loads((EVIDENCE / relative).read_text())


report = read("report.json")
assert report["status"] == "pass"
assert "json_hash_algorithm" in report
sources = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() == value
           for name, value in report["source_sha256"].items()}
assert all(sources.values())
programs = {name: hashlib.sha256((EVIDENCE / row["path"]).read_bytes()).hexdigest() == row["sha256"]
            for name, row in report["programs"].items()}
assert all(programs.values())
assert hashlib.sha256((REPO / "shared/data/canonical/puzzles.jsonl").read_bytes()).hexdigest() == report["canonical"]["ledger_sha256"]
for row in report["episodes"]:
    episode, public, audit = read(row["private_path"]), read(row["public_path"]), read(row["audit_path"])
    assert digest(episode) == row["episode_sha256"]
    assert digest(public) == row["public_sha256"]
    assert digest(audit) == row["audit_sha256"]
    for name, relative in (("public", row["public_path"]), ("episode", row["private_path"]), ("audit", row["audit_path"])):
        assert hashlib.sha256((EVIDENCE / relative).read_bytes()).hexdigest() == row["file_sha256"][name]
    assert public == {"train": episode["train"], "test": [{"input": pair["input"]} for pair in episode["test"]]}
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert episode["parameters"] == row["parameters"]
    key = episode["parameters"]["axis"] + "__" + episode["parameters"]["order"]
    assert episode["program"] == (EVIDENCE / report["programs"][key]["path"]).read_text()
    assert hashlib.sha256(episode["program"].encode()).hexdigest() == episode["program_sha256"]
    assert audit["episode_pairs_sha256"] == digest({"train": episode["train"], "test": episode["test"]})
    assert audit["program_sha256"] == {name: item["sha256"] for name, item in report["programs"].items()}
    assert audit["reference_labels_match"] is True
    assert audit["status"] == "no_ambiguity_found" and audit["parameters_identified"] is True
    for score in [audit["production"], *audit["rotations"]]:
        assert len(score["rivals"]) == 3
        assert all(rival["status"] == "refuted_by_demonstrations" for rival in score["rivals"].values())
    pairs = episode["train"] + episode["test"]
    assert len({digest(pair["input"]) for pair in pairs}) == 4
    for pair in pairs:
        assert len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30
for row in report["diagnostics"]:
    fixture = read(row["path"])
    assert digest(fixture) == row["sha256"]
    assert hashlib.sha256((EVIDENCE / row["path"]).read_bytes()).hexdigest() == row["file_sha256"]
    assert fixture["audit"]["status"] == "ambiguous"
    assert sum(rotation["status"] == "ambiguous" for rotation in fixture["audit"]["rotations"]) == 1
summary = {
    "status": "pass",
    "evidence_path": str(EVIDENCE),
    "source_bindings_match": sources,
    "program_files_match": programs,
    "public_files_verified": len(report["episodes"]),
    "private_episode_audit_hashes_verified": len(report["episodes"]),
    "public_isolation_passed": True,
    "racket_executions": report["racket_executions"],
    "runtime_backend": report["runtime"]["backend"],
    "canonical_pairs": report["canonical"]["pair_count"],
    "boundary_output_shapes": [row["output_shape"] for row in report["boundaries"]],
    "total_bytes": sum(path.stat().st_size for path in HERE.rglob("*") if path.is_file()),
    "summary": report["summary"],
}
(HERE / "verification-final.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
