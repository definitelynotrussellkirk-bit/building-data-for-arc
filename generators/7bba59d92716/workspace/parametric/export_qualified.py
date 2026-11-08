"""Project native qualification episodes into separate, hash-named query views.

From the packet's outer directory:
  python3 review.py run python3 generators/7bba59d92716/workspace/parametric/export_qualified.py \
    --qualification ../checks/7bba59d92716/qualification/qualification.json \
    --out ../checks/7bba59d92716/projection

Only individual public/<sha256>.json files are model-visible. The private
manifest retains query order and complete source-bound episodes for the existing
consumer. This serializer implements no turn controller or training loop. It
checks native receipt/source integrity; it does not replay Racket or accept a
family, and cannot authenticate a maliciously rewritten qualification bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
for folder in (ROOT / "shared/runtime", ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from arcpuzzles.review_witness import _qualified
from arcpuzzles.runtime import validate_grid
from reviewer_support import public_challenge_bytes, public_challenge_id


def query_views(episode):
    """Return (public ID, exact bytes) for each query, without private context."""
    if type(episode) is not dict:
        raise ValueError("Expected a private episode object")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("Episodes need 2..6 demonstrations")
    if type(test) is not list or not 1 <= len(test) <= 4:
        raise ValueError("Episodes need 1..4 queries")
    inputs = []
    for pair in train + test:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("Private pairs require input and output grids")
        validate_grid(pair["input"])
        validate_grid(pair["output"])
        inputs.append(json.dumps(pair["input"], separators=(",", ":")))
    if len(set(inputs)) != len(inputs):
        raise ValueError("All demonstration and query inputs must be distinct")
    views = []
    for pair in test:
        visible = {"train": train, "test": [{"input": pair["input"]}]}
        views.append((public_challenge_id(visible), public_challenge_bytes(visible)))
    return views


def export_qualified(qualification, output, *, root=ROOT):
    """Validate current native evidence and publish a new private/public bundle."""
    output, qualification = Path(output), Path(qualification).resolve()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory: {output}")
    q, execution = _qualified(Path(root).resolve(), qualification)
    qualification_hash = hashlib.sha256(qualification.read_bytes()).hexdigest()
    public, private = {}, []
    for episode in execution["episodes"]:
        views = query_views(episode)
        for identifier, payload in views:
            if identifier in public:
                raise ValueError("Duplicate visible query payload in export")
            public[identifier] = payload
        private.append({"episode": episode, "public_ids": [identifier for identifier, _ in views]})
    manifest = {
        "status": "projected_qualification", "task_id": q["task_id"],
        "qualification_sha256": qualification_hash,
        "execution_sha256": q["execution"]["sha256"],
        "source_binding": q["source_binding"], "racket": execution["racket"],
        "episodes": private, "checks": execution["checks"],
        "owner_acceptance": "pending", "training_admitted": False,
        "limits": "Serialized native evidence/source checks only; no new Racket replay, owner acceptance or training admission.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".query-projection-", dir=output.parent) as temp:
        stage = Path(temp)
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for identifier in sorted(public):
            (stage / "public" / (identifier + ".json")).write_bytes(public[identifier])
        (stage / "private/manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        fresh_q, fresh_execution = _qualified(Path(root).resolve(), qualification)
        if (fresh_q != q or fresh_execution != execution
                or hashlib.sha256(qualification.read_bytes()).hexdigest() != qualification_hash):
            raise ValueError("Qualification changed during projection")
        output.mkdir(exist_ok=False)
        os.replace(stage / "public", output / "public")
        # The private manifest publishes last; partial output is not complete.
        os.replace(stage / "private", output / "private")
    return {"status": "projected_qualification", "output": str(output),
            "episodes": len(private), "public_files": len(public),
            "owner_acceptance": "pending", "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = export_qualified(args.qualification, args.out)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Projection refused: {error}\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
