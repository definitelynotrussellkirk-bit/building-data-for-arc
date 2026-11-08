"""Verify final prototype evidence and preservation of the earlier bundle."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
OUT = HERE / "evidence-final"
OLD = HERE / "evidence"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def verify_manifest(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, record in manifest["files"].items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory.resolve()), name
        data = path.read_bytes()
        assert len(data) == record["bytes"], name
        assert digest(data) == record["sha256"], name
    return len(manifest["files"])


def main():
    final_count = verify_manifest(OUT)
    old_count = verify_manifest(OLD)
    report = json.loads((OUT / "report.json").read_text())
    old_report = json.loads((OLD / "report.json").read_text())
    for name, expected in report["source_sha256"].items():
        assert digest((ROOT / name).read_bytes()) == expected, name
    assert all(r["status"] == "pass" for r in report["execution_records"])
    executed = {(r["program_sha256"], r["input_sha256"], r["output_sha256"])
                for r in report["execution_records"]}
    verified_outputs = 0
    for metadata in report["episodes"]:
        private = json.loads((OUT / metadata["private_path"]).read_text())
        public = json.loads((OUT / metadata["public_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(p) == {"input", "output"} for p in public["train"])
        assert all(set(p) == {"input"} for p in public["test"])
        assert public["train"] == private["pairs"][:-1]
        assert public["test"] == [{"input": private["pairs"][-1]["input"]}]
        assert private["identifiability"]["status"] == "pass"
        assert (OUT / metadata["public_path"]).read_bytes() == (OLD / metadata["public_path"]).read_bytes()
        for metric, outputs in private["outputs_by_metric"].items():
            program_hash = report["programs"][metric]["sha256"]
            for pair, output in zip(private["pairs"], outputs):
                assert (program_hash, grid_hash(pair["input"]), grid_hash(output)) in executed
                verified_outputs += 1
    for filename in ("witness.json", "boundary-cases.json"):
        cases = json.loads((OUT / "private" / filename).read_text())
        if isinstance(cases, dict):
            cases = [cases]
        for case in cases:
            for metric, output in case["outputs"].items():
                program_hash = report["programs"][metric]["sha256"]
                assert (program_hash, grid_hash(case["input"]), grid_hash(output)) in executed
                verified_outputs += 1
    assert report["programs"] == old_report["programs"]
    result = {
        "status": "pass",
        "manifest_members": final_count,
        "preserved_before_fix_manifest_members": old_count,
        "source_bindings": len(report["source_sha256"]),
        "retained_output_occurrences_with_racket_receipts": verified_outputs,
        "all_racket_execution_records": len(report["execution_records"]),
        "programs_unchanged_from_before_fix": True,
        "public_challenges_unchanged_from_before_fix": True,
        "coverage": report["coverage"],
        "source_sha256": report["source_sha256"],
        "verification_script_sha256": digest(Path(__file__).read_bytes()),
    }
    (HERE / "retained-verification-final.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
