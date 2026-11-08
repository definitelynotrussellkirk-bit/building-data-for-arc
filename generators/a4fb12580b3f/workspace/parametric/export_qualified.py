"""Export native qualified episodes as private authoring data and one public turn.

Run through the packet's ``review.py run python3`` with ``--qualification`` and
``--out``. Only public.jsonl and public/*.json are model-visible. Everything
else is private controller/authoring metadata. This is a serialization helper,
not a controller, native acceptance operation, or training admission mechanism.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import parametric_promotion as native
from arcpuzzles import review_witness
from arcpuzzles.parametric_worker import _grid
import reviewer_support
from reviewer_support import public_challenge_bytes, public_challenge_id

LIMITS = ("Authoring only. Uses an existing native qualification and checks its exact "
          "current source/contract and execution hash; does not replay Racket, accept "
          "the family, independently authenticate receipts, or admit training data. "
          "Only the first query is published; future reveal policy is downstream.")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(episode):
    if not isinstance(episode, dict):
        raise ValueError("episode must contain nonempty train/test lists")
    result = {}
    for split in ("train", "test"):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError("episode must contain nonempty train/test lists")
        try:
            result[split] = [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                             for pair in pairs]
        except (KeyError, TypeError) as error:
            raise ValueError("episode pairs require input/output grids") from error
    return result


def reveal(episode, query_index):
    """Return copied demonstrations and exactly one query input, with no metadata.

    ``episode`` is a complete private native episode. Validate all its grids,
    including private answers, but publish only the selected query input. No
    count, query index, setting, seed, program or future query enters the result.
    The caller owns reveal order; this function has no controller state.
    """
    if (not isinstance(episode, dict) or type(episode.get("test")) is not list
            or type(query_index) is not int
            or not 0 <= query_index < len(episode["test"])):
        raise ValueError("query index must select an existing query; bool is forbidden")
    pairs = _pairs(episode)
    challenge = {"train": pairs["train"],
                 "test": [{"input": pairs["test"][query_index]["input"]}]}
    # Use the same strict, canonical visible projection as native exports.
    return json.loads(public_challenge_bytes(challenge))


def _same_checkout(root):
    expected = ((native.__file__, root / "src/arcpuzzles/parametric_promotion.py"),
                (review_witness.__file__, root / "src/arcpuzzles/review_witness.py"),
                (reviewer_support.__file__, root / "shared/runtime/reviewer_support.py"))
    if any(Path(actual).resolve() != wanted.resolve() for actual, wanted in expected):
        raise ValueError("Native qualification and public helpers must use the same checkout")


def _write_new(path, data):
    with path.open("xb") as handle:
        handle.write(data)


def export_qualified(root, qualification, output):
    """Write a new authoring export from an exact-current native qualification.

    public.jsonl contains one bare challenge per private episode, byte-for-byte
    identical to its public/<sha256>.json file. Duplicate visible challenges
    share the same file, while private rows retain their original correspondence.
    Receipt hashes, source bindings and all native jobs/checks remain private.
    Existing destinations (including dangling symlinks) are always refused.
    """
    root, qualification, output = Path(root).resolve(), Path(qualification).resolve(), Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory: {output}")
    _same_checkout(root)
    execution_path = qualification.with_name("execution.json")
    qualification_bytes, execution_bytes = qualification.read_bytes(), execution_path.read_bytes()
    receipt, execution = review_witness._qualified(root, qualification)
    if (qualification.read_bytes() != qualification_bytes
            or execution_path.read_bytes() != execution_bytes):
        raise ValueError("Qualification or execution changed during validation")
    if not execution["episodes"]:
        raise ValueError("Qualification must contain at least one episode")

    public_lines, private_lines, public_files = [], [], {}
    for index, (episode, job, check) in enumerate(zip(
            execution["episodes"], receipt["jobs"], execution["checks"])):
        challenge = reveal(episode, 0)
        visible = public_challenge_bytes(challenge)
        identity = public_challenge_id(challenge)
        public_path = f"public/{identity}.json"
        public_files[public_path] = visible
        public_lines.append(visible)
        private_episode = deepcopy(episode)
        # The native qualification worker uses this reference value even before
        # acceptance. Preserve its provenance privately without claiming acceptance.
        worker_reference = private_episode.pop("reference", None)
        private_episode["reference"] = "qualified_authoring_only"
        private_lines.append(_raw({"schema": "arcpuzzles-authoring-controller-payload-v1",
            "episode_index": index, "public_id": identity, "public_path": public_path,
            "first_query_index": 0, "query_order": list(range(len(episode["test"]))),
            "episode": private_episode, "native_worker_reference": worker_reference,
            "job": deepcopy(job), "check": deepcopy(check),
            "training_admitted": False, "owner_acceptance": "not_performed"}))

    public_bytes, private_bytes = b"".join(public_lines), b"".join(private_lines)
    files = {**public_files, "public.jsonl": public_bytes, "private.jsonl": private_bytes}
    manifest = {"schema": "arcpuzzles-qualified-authoring-export-v1",
        "status": "authoring_only", "task_id": receipt["task_id"],
        "training_admitted": False, "owner_acceptance": "not_performed",
        "source_binding": deepcopy(receipt["source_binding"]),
        "contract": deepcopy(receipt["contract"]), "programs": deepcopy(receipt["programs"]),
        "qualification": {"path": str(qualification), "sha256": _sha(qualification_bytes),
                          "status": receipt["status"], "schema": receipt["schema"]},
        "execution": {"path": str(execution_path), "sha256": _sha(execution_bytes),
                      "racket": deepcopy(execution["racket"]),
                      "racket_evaluations": execution["racket_evaluations"]},
        "episodes": len(public_lines), "first_turn_queries_per_episode": 1,
        "files": {name: {"sha256": _sha(data), "bytes": len(data)}
                  for name, data in sorted(files.items())}, "limits": LIMITS}
    # Fail source/receipt drift before publication, then write the completion
    # manifest last. A write failure leaves no apparently complete manifest.
    if review_witness._qualified(root, qualification) != (receipt, execution):
        raise ValueError("Qualified source or receipt changed before export")
    if (qualification.read_bytes() != qualification_bytes
            or execution_path.read_bytes() != execution_bytes):
        raise ValueError("Qualification or execution bytes changed before export")
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    for name, data in files.items():
        _write_new(output / name, data)
    _write_new(output / "manifest.private.json", _raw(manifest))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = export_qualified(args.library, args.qualification, args.out)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Authoring export refused: {error}\n")
    print(json.dumps({"status": result["status"], "training_admitted": False,
                      "owner_acceptance": "not_performed",
                      "private_manifest": str((args.out / "manifest.private.json").resolve())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
