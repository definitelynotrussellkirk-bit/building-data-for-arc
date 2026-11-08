"""Read-only audit of a retained v2 height suite and its public projection."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(suite, repo):
    manifest_path = suite / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    errors = []
    for relative, expected in manifest["files_sha256"].items():
        path = suite / relative
        if not path.is_file() or digest(path) != expected:
            errors.append(f"artifact hash mismatch: {relative}")
    for relative, expected in manifest["sources_sha256"].items():
        if digest(repo / relative) != expected:
            errors.append(f"live source differs from retained run: {relative}")

    export = json.loads((suite / "private/public-export.json").read_text())
    index = json.loads((suite / "public/index.json").read_text())
    mapping = export["mapping"]
    if set(index) != {"challenges"}:
        errors.append("public index has metadata beyond the filename list")
    names = index["challenges"]
    if len(names) != len(set(names)) or len(names) != manifest["episode_count"]:
        errors.append("public index has incorrect count or duplicate names")
    if names != [row["public_filename"] for row in mapping]:
        errors.append("private mapping does not match public index order")
    public_files = {path.name for path in (suite / "public").iterdir()}
    if public_files != set(names) | {"index.json"}:
        errors.append("unexpected or missing public file")
    inputs_by_seed = defaultdict(dict)
    for position, row in enumerate(mapping):
        filename = row["public_filename"]
        if not re.fullmatch(r"[0-9a-f]{32}\.json", filename):
            errors.append(f"public filename is not an opaque 128-bit identifier: {filename}")
        if row["public_index_position"] != position:
            errors.append("private mapping has an incorrect public position")
        public_path = suite / "public" / filename
        challenge = json.loads(public_path.read_text())
        if digest(public_path) != row["public_sha256"]:
            errors.append(f"public content hash mismatch: {filename}")
        if set(challenge) != {"train", "test"}:
            errors.append(f"public top-level metadata leak: {filename}")
        if any(set(pair) != {"input", "output"} for pair in challenge["train"]):
            errors.append(f"unexpected demonstration fields: {filename}")
        if any(set(pair) != {"input"} for pair in challenge["test"]):
            errors.append(f"query metadata or answer leak: {filename}")
        episode = json.loads((suite / "private/episodes" / (row["private_episode_id"] + ".json")).read_text())
        expected = {"train": episode["pairs"][:-1], "test": [{"input": episode["pairs"][-1]["input"]}]}
        if challenge != expected:
            errors.append(f"public projection differs from its private episode: {filename}")
        if episode["parameter_selection"] != "explicit":
            errors.append("suite derived hidden parameters from a recoverable input seed")
        setting = tuple(sorted(episode["parameters"].items()))
        inputs = json.dumps([pair["input"] for pair in episode["pairs"]])
        inputs_by_seed[episode["seed"]][setting] = inputs
    for seed, settings in inputs_by_seed.items():
        if len(settings) != 16 or len(set(settings.values())) != 1:
            errors.append(f"input seed {seed} is not crossed identically with all 16 settings")

    return {"status": "passed" if not errors else "failed",
            "suite": str(suite), "manifest_sha256": digest(manifest_path),
            "files_verified": len(manifest["files_sha256"]),
            "public_challenges_verified": len(names),
            "live_source_files_verified": len(manifest["sources_sha256"]),
            "matched_input_seed_replicas": len(inputs_by_seed),
            "errors": errors,
            "scope": "Artifact hashes; source binding; public filename/index/schema/projection checks; every input seed shared by all settings. Random-ID freshness is covered by the focused regression."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.suite, args.repo)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)
