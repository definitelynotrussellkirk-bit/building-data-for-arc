"""Project qualified reviewer evidence into separate, single-query challenges.

Run through the packet launcher with --qualification PATH --out NEWDIR.
Only public/*.json is model-visible. private/manifest.json preserves the four
query order and labels for the existing consumer; this tool is no controller.
Receipt/source verification is static and does not replay Racket or accept a
family. Native owner acceptance and training admission remain separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from arcpuzzles import Catalog
from arcpuzzles import parametric_promotion as native
from arcpuzzles.runtime import validate_grid
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "5c9fd75979d1"
ROOT = Path(__file__).resolve().parents[4]
SCHEMA = "arcpuzzles-qualified-query-projection-v1"


def project_query(episode, query_index):
    """Return (visible-content ID, bytes); hidden/future data cannot affect it."""
    tests = episode.get("test")
    if (not isinstance(tests, list) or type(query_index) is not int
            or not 0 <= query_index < len(tests)):
        raise ValueError("query_index must select one existing query")
    challenge = {"train": episode.get("train"), "test": [tests[query_index]]}
    return public_challenge_id(challenge), public_challenge_bytes(challenge)


def _load_qualified(path):
    raw = path.read_bytes()
    qualification = json.loads(raw)
    if (not isinstance(qualification, dict)
            or qualification.get("schema") != native.QUALIFICATION
            or qualification.get("status") != "qualified"
            or qualification.get("task_id") != TASK_ID):
        raise ValueError("Expected a successful native qualification for " + TASK_ID)
    execution_path = path.with_name("execution.json")
    execution_bytes = execution_path.read_bytes()
    execution_hash = hashlib.sha256(execution_bytes).hexdigest()
    if qualification.get("execution") != {"path": "execution.json", "sha256": execution_hash}:
        raise ValueError("Qualification execution path or digest differs")
    execution = json.loads(execution_bytes)
    if not isinstance(execution, dict):
        raise ValueError("Native execution must be an object")
    contract, binding = native._ready(Catalog(ROOT), TASK_ID)
    if (native._raw(qualification.get("source_binding")) != native._raw(binding)
            or native._raw(qualification.get("contract")) != native._raw(contract)):
        raise ValueError("Qualification differs from current source binding or contract")
    jobs = qualification.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("Qualification has no jobs")
    coverage = {}
    try:
        for job in jobs:
            native._jobs(contract, seed=job["seed"], count=1, demos=job["demos"],
                         queries=job["queries"], settings=job["settings"])
            native._integer("MAIN demonstrations", job["demos"], 2, 6)
            native._integer("MAIN queries", job["queries"], 4, 4)
            seeds = coverage.setdefault(native._raw(job["settings"]), set())
            if job["seed"] in seeds:
                raise ValueError("Duplicate qualification seed for one setting")
            seeds.add(job["seed"])
        if (set(coverage) != {native._raw(s) for s in native.settings_space(contract)}
                or any(not 2 <= len(seeds) <= 8 for seeds in coverage.values())):
            raise ValueError("Qualification must cover every setting on two to eight seeds")
        programs = native._check_execution(execution, jobs, binding, contract)
        if programs != qualification.get("programs"):
            raise ValueError("Qualification program map differs from execution")
        for episode in execution["episodes"]:
            inputs = []
            for split in ("train", "test"):
                for pair in episode[split]:
                    validate_grid(pair["input"])
                    validate_grid(pair["output"])
                    inputs.append(native._raw(pair["input"]))
            if len(inputs) != len(set(inputs)):
                raise ValueError("Demonstration and query inputs must be distinct")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed native qualification or execution evidence") from error
    return qualification, execution, raw, execution_bytes


def export_qualification(qualification, output):
    """Validate pinned evidence and publish a reviewer-only query projection."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    path = Path(qualification)
    q, execution, qualification_bytes, execution_bytes = _load_qualified(path)
    public, hidden = {}, []
    for index, episode in enumerate(execution["episodes"]):
        identifiers = []
        for query_index in range(len(episode["test"])):
            identifier, payload = project_query(episode, query_index)
            if identifier in public:
                raise ValueError("Duplicate visible query challenge in the batch")
            public[identifier] = payload
            identifiers.append(identifier)
        # Native worker evidence uses an accepted_parametric reference label
        # before acceptance; do not propagate that label into this export.
        hidden.append({
            "qualification_episode_index": index,
            **{key: episode[key] for key in ("task_id", "seed", "settings", "program",
                                             "program_sha256", "train", "test")},
            "public_ids": identifiers,
        })
    manifest = {
        "schema": SCHEMA, "status": "reviewer_projection", "task_id": TASK_ID,
        "owner_acceptance": "not_performed", "training_admitted": False,
        "qualification_sha256": hashlib.sha256(qualification_bytes).hexdigest(),
        "execution_sha256": hashlib.sha256(execution_bytes).hexdigest(),
        "source_binding": q["source_binding"], "contract": q["contract"],
        "reported_racket_runtime": execution["racket"],
        "public_files": [{"path": f"public/{identifier}.json", "sha256": identifier}
                         for identifier in sorted(public)],
        "episodes": hidden,
        "limits": "Static projection of source-bound qualification evidence; no fresh Racket replay, owner acceptance, or training admission.",
    }
    # Validate the entire batch before creating the destination. Publication
    # places the private manifest last so interrupted output is incomplete.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".qualified-projection-", dir=output.parent) as temporary:
        stage = Path(temporary)
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for identifier in sorted(public):
            (stage / "public" / f"{identifier}.json").write_bytes(public[identifier])
        (stage / "private/manifest.json").write_bytes(native._raw(manifest))
        if (path.read_bytes() != qualification_bytes
                or path.with_name("execution.json").read_bytes() != execution_bytes
                or native._ready(Catalog(ROOT), TASK_ID) != (q["contract"], q["source_binding"])):
            raise ValueError("Qualified evidence or current source changed during export")
        output.mkdir(exist_ok=False)
        os.replace(stage / "public", output / "public")
        os.replace(stage / "private", output / "private")
    return {
        "status": "reviewer_projection", "episodes": len(hidden), "public_queries": len(public),
        "output": str(output.resolve()), "private_manifest": str((output / "private/manifest.json").resolve()),
        "owner_acceptance": "not_performed", "training_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = export_qualification(args.qualification, args.out)
    except (ValueError, OSError) as error:
        print(f"Qualified projection failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
