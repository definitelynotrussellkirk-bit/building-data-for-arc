"""Export and verify this task's proposed threshold episodes.

Public payloads and IDs use exactly reviewer_support.public_challenge_bytes.
Only index.json and public/ are model-visible; private/ retains labels, settings,
seeds, exact Racket text and source identities. Hash checks establish integrity,
not semantics. --verify DIR --replay additionally checks current source identity
and every private label by executing the matching current Racket rule.

From WORK/repo, with the included Racket environment configured::

    python3 generators/661dffbdf39a/workspace/parametric/export_challenges.py \
        --out ../checks/parametric/examples --seed 1729 --train-count 3 --query-count 4
    python3 generators/661dffbdf39a/workspace/parametric/export_challenges.py \
        --verify ../checks/parametric/examples --replay

This is a task-local prototype tool. It neither changes the production generator
API nor grants source, rule-variant, or training approval.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile


TASK_ID = "661dffbdf39a"
THRESHOLDS = ("1/3", "1/2", "2/3")
FORMAT = "arc-threshold-public-export-v1"
REPO = Path(__file__).resolve().parents[4]
TASK_RELATIVE = f"generators/{TASK_ID}"
PARAMETRIC_RELATIVE = f"{TASK_RELATIVE}/workspace/parametric"
SOURCE_PATHS = {
    "prototype": f"{PARAMETRIC_RELATIVE}/threshold_variant.py",
    "exporter": f"{PARAMETRIC_RELATIVE}/export_challenges.py",
    "canonical_generator": f"{TASK_RELATIVE}/generator.py",
    "public_projection_helper": "shared/runtime/reviewer_support.py",
}
CANONICAL_LEDGER = "shared/data/canonical/puzzles.jsonl"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _sha256(body):
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value):
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("export data must be finite, serializable JSON") from error


def _load_module(path, prefix):
    """Execute the bytes we hash, avoiding stale timestamp-based .pyc reuse."""
    body = path.read_bytes()
    digest = _sha256(body)
    name = prefix + "_" + digest
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(body, str(path), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    module._loaded_source_sha256 = digest
    return module


_SUPPORT = _load_module(REPO / SOURCE_PATHS["public_projection_helper"],
                        "_threshold_public_support")
public_challenge_bytes = _SUPPORT.public_challenge_bytes
public_challenge_id = _SUPPORT.public_challenge_id
_EXPORT_SOURCE_SHA256 = _sha256(Path(__file__).read_bytes())


def load_core():
    """Load this checkout's source-bound prototype only when it is needed."""
    core = _load_module(REPO / SOURCE_PATHS["prototype"], "_threshold_public_core")
    if tuple(core.THRESHOLDS) != THRESHOLDS:
        raise ValueError("prototype threshold domain differs from this export format")
    return core


def _canonical_program():
    programs = []
    with (REPO / CANONICAL_LEDGER).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row.get("program_solution"))
    if len(programs) != 1 or not isinstance(programs[0], str) or not programs[0]:
        raise ValueError("expected one exact canonical Racket authority for this task")
    return programs[0]


def source_provenance():
    """Return current hashes and canonical text, with repository-relative paths."""
    sources = {role: {"path": relative, "sha256": _sha256((REPO / relative).read_bytes())}
               for role, relative in SOURCE_PATHS.items()}
    if sources["exporter"]["sha256"] != _EXPORT_SOURCE_SHA256:
        raise ValueError("exporter source changed during this process")
    if sources["public_projection_helper"]["sha256"] != _SUPPORT._loaded_source_sha256:
        raise ValueError("public projection helper source changed during this process")
    canonical = _canonical_program().encode("utf-8")
    digest = _sha256(canonical)
    return {"sources": sources,
            "canonical_rule": {"ledger_path": CANONICAL_LEDGER, "task_id": TASK_ID,
                               "program_sha256": digest,
                               "reference_path": f"references/{digest}.rkt"}}, canonical


def _distinct_inputs(episode):
    seen = set()
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            signature = tuple(tuple(row) for row in pair["input"])
            if signature in seen:
                raise ValueError(f"duplicate input within demonstrations/queries at {split}[{index}]")
            seen.add(signature)


def _validated_episode(episode):
    public = public_challenge_bytes(episode)
    _distinct_inputs(episode)
    # Use the shared grid validator for private query labels as well. Projection
    # alone deliberately ignores test outputs, whereas an export retains them.
    public_challenge_bytes({"train": episode["train"] + episode["test"],
                            "test": episode["test"]})
    metadata = episode.get("metadata")
    required = {"threshold", "seed", "program", "program_sha256", "teaching"}
    if type(metadata) is not dict or not required.issubset(metadata):
        raise ValueError("private episode requires threshold, seed, program, hash and teaching metadata")
    if metadata["threshold"] not in THRESHOLDS or type(metadata["seed"]) is not int:
        raise ValueError("invalid private threshold or exact integer seed")
    if type(metadata["program"]) is not str or not metadata["program"]:
        raise ValueError("private episode requires exact Racket program text")
    program = metadata["program"].encode("utf-8")
    if metadata["program_sha256"] != _sha256(program):
        raise ValueError("private program hash does not match its exact text")
    if type(metadata["teaching"]) is not dict:
        raise ValueError("private teaching metadata must be an object")
    private = _json_bytes(episode)
    return public, private, program


def _empty_destination(destination):
    if destination.is_symlink():
        raise ValueError("export destination must not be a symlink")
    if destination.exists():
        if not destination.is_dir():
            raise ValueError("export destination must be a directory")
        if any(destination.iterdir()):
            raise ValueError("refusing nonempty export destination")


def write_batch(episodes, destination, *, expected_core_sha256=None):
    """Validate the complete batch, then publish once without overwriting files.

    This writer checks structural validity and provenance integrity, not whether
    labels are semantically correct. Synthetic projection tests may use it;
    only verify_export(..., replay=True) establishes executed label agreement.
    """
    destination = Path(destination).absolute()
    _empty_destination(destination)
    try:
        episodes = list(episodes)
    except TypeError as error:
        raise ValueError("episodes must be a nonempty iterable") from error
    if not episodes:
        raise ValueError("episodes must be nonempty")

    prepared = {}
    for episode in episodes:
        public, private, program = _validated_episode(episode)
        public_id = _sha256(public)
        if public_id in prepared:
            raise ValueError("duplicate public challenge payload in batch")
        prepared[public_id] = (episode, public, private, program)

    provenance, canonical_program = source_provenance()
    if (expected_core_sha256 is not None
            and provenance["sources"]["prototype"]["sha256"] != expected_core_sha256):
        raise ValueError("prototype source changed after episode generation")
    ids = sorted(prepared)
    files = {"index.json": _json_bytes({"public_challenge_ids": ids})}
    canonical_path = provenance["canonical_rule"]["reference_path"]
    files[f"private/{canonical_path}"] = canonical_program
    entries = []
    for public_id in ids:
        episode, public, private, program = prepared[public_id]
        metadata = episode["metadata"]
        program_hash = _sha256(program)
        episode_path = f"episodes/{public_id}.json"
        program_path = f"references/{program_hash}.rkt"
        files[f"public/{public_id}.json"] = public
        files[f"private/{episode_path}"] = private
        files[f"private/{program_path}"] = program
        entries.append({
            "public_challenge_id": public_id,
            "episode_path": episode_path, "episode_sha256": _sha256(private),
            "program_path": program_path, "program_sha256": program_hash,
            "threshold": metadata["threshold"], "seed": metadata["seed"],
            "train_count": len(episode["train"]), "query_count": len(episode["test"]),
        })
    files["private/manifest.json"] = _json_bytes({
        "format": FORMAT, "task_id": TASK_ID, "scope": "proposed_task_local_prototype",
        "provenance": provenance, "episodes": entries,
    })

    # Invalid batches have caused no directory or file writes up to this point.
    # A single rename publishes the prepared directory. POSIX rename refuses an
    # existing nonempty directory even if it appeared after the initial check.
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=".threshold-export-", dir=destination.parent))
    try:
        for relative, body in sorted(files.items()):
            path = staged / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(body)
        _empty_destination(destination)
        os.rename(staged, destination)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return {"status": "written", "episode_count": len(ids),
            "public_challenge_ids": ids, "label_replay": "not_run"}


def _json_load(body):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"nonfinite JSON value: {value}")

    return json.loads(body.decode("utf-8"), object_pairs_hook=unique_keys,
                      parse_constant=reject_constant)


def _keys(value, expected, message):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(message)


def _digest(value):
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError("expected a lowercase full SHA-256 identity")
    return value


def _read_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected a regular file: {path}")
    return path.read_bytes()


def _directory_names(path, expected, description):
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"expected a real {description} directory")
    children = list(path.iterdir())
    if any(entry.is_symlink() for entry in children):
        raise ValueError(f"symlink is not allowed in {description} directory")
    if {entry.name for entry in children} != set(expected):
        raise ValueError(f"unexpected {description} file set")


def _public_payload(body, public_id):
    challenge = _json_load(body)
    _keys(challenge, ("train", "test"), "public schema requires only train/test")
    for split, keys in (("train", {"input", "output"}), ("test", {"input"})):
        if type(challenge[split]) is not list:
            raise ValueError("public schema requires train/test lists")
        for pair in challenge[split]:
            _keys(pair, keys, f"public schema has unexpected {split} pair fields")
    canonical = public_challenge_bytes(challenge)
    _distinct_inputs(challenge)
    if body != canonical:
        raise ValueError("public payload is not the exact canonical bytes")
    if _sha256(body) != public_id:
        raise ValueError("public content ID does not match its exact bytes")
    return challenge


def _validate_provenance(provenance):
    _keys(provenance, ("sources", "canonical_rule"), "invalid private provenance schema")
    sources = provenance["sources"]
    _keys(sources, SOURCE_PATHS, "invalid source identity roles")
    for role, relative in SOURCE_PATHS.items():
        _keys(sources[role], ("path", "sha256"), "invalid source identity schema")
        if sources[role]["path"] != relative:
            raise ValueError("unexpected source identity path")
        _digest(sources[role]["sha256"])
    canonical = provenance["canonical_rule"]
    _keys(canonical, ("ledger_path", "task_id", "program_sha256", "reference_path"),
          "invalid canonical rule provenance schema")
    digest = _digest(canonical["program_sha256"])
    if (canonical["ledger_path"] != CANONICAL_LEDGER or canonical["task_id"] != TASK_ID
            or canonical["reference_path"] != f"references/{digest}.rkt"):
        raise ValueError("invalid canonical rule identity or reference path")


def verify_export(directory, *, replay=False):
    """Verify every retained file; optionally execute source-bound private labels.

    Default verification needs no Racket and does not import the prototype. It
    checks public bytes independently of private names or settings and rejects
    extra public fields/files. Replay requires the current checkout to match
    recorded hashes before it executes that checkout's expected rule programs.
    """
    directory = Path(directory).absolute()
    _directory_names(directory, ("index.json", "public", "private"), "export")
    index = _json_load(_read_file(directory / "index.json"))
    _keys(index, ("public_challenge_ids",), "invalid public index schema")
    ids = index["public_challenge_ids"]
    if type(ids) is not list or not ids:
        raise ValueError("public index must contain a nonempty ID list")
    for public_id in ids:
        _digest(public_id)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate public identity in index")
    if ids != sorted(ids):
        raise ValueError("public index is not sorted by content ID")
    _directory_names(directory / "public", [f"{public_id}.json" for public_id in ids], "public")
    public_bytes = {}
    seen_payloads = set()
    for public_id in ids:
        body = _read_file(directory / "public" / f"{public_id}.json")
        _public_payload(body, public_id)
        if body in seen_payloads:
            raise ValueError("duplicate public challenge payload")
        seen_payloads.add(body)
        public_bytes[public_id] = body

    private = directory / "private"
    _directory_names(private, ("manifest.json", "episodes", "references"), "private")
    manifest = _json_load(_read_file(private / "manifest.json"))
    _keys(manifest, ("format", "task_id", "scope", "provenance", "episodes"),
          "invalid private manifest schema")
    if (manifest["format"] != FORMAT or manifest["task_id"] != TASK_ID
            or manifest["scope"] != "proposed_task_local_prototype"):
        raise ValueError("unknown export format, task or prototype scope")
    provenance = manifest["provenance"]
    _validate_provenance(provenance)
    entries = manifest["episodes"]
    if type(entries) is not list or len(entries) != len(ids):
        raise ValueError("private episode mapping does not match public index")
    _directory_names(private / "episodes", [f"{public_id}.json" for public_id in ids], "episode")
    reference_hashes = {provenance["canonical_rule"]["program_sha256"]}
    retained_episodes = []
    for public_id, entry in zip(ids, entries):
        _keys(entry, ("public_challenge_id", "episode_path", "episode_sha256", "program_path",
                      "program_sha256", "threshold", "seed", "train_count", "query_count"),
              "invalid private episode mapping schema")
        program_hash = _digest(entry["program_sha256"])
        _digest(entry["episode_sha256"])
        if (entry["public_challenge_id"] != public_id
                or entry["episode_path"] != f"episodes/{public_id}.json"
                or entry["program_path"] != f"references/{program_hash}.rkt"):
            raise ValueError("private mapping paths or order do not match public index")
        body = _read_file(private / entry["episode_path"])
        if _sha256(body) != entry["episode_sha256"]:
            raise ValueError("private episode hash mismatch")
        episode = _json_load(body)
        projected, private_bytes, program = _validated_episode(episode)
        if private_bytes != body:
            raise ValueError("private episode is not canonical JSON bytes")
        if projected != public_bytes[public_id]:
            raise ValueError("private episode projection differs from public challenge")
        metadata = episode["metadata"]
        if (entry["threshold"] != metadata["threshold"]
                or type(entry["seed"]) is not int or entry["seed"] != metadata["seed"]
                or type(entry["train_count"]) is not int or entry["train_count"] != len(episode["train"])
                or type(entry["query_count"]) is not int or entry["query_count"] != len(episode["test"])
                or program_hash != metadata["program_sha256"]):
            raise ValueError("private mapping disagrees with episode metadata")
        reference = _read_file(private / entry["program_path"])
        if reference != program or _sha256(reference) != program_hash:
            raise ValueError("private Racket program hash/text mismatch")
        reference_hashes.add(program_hash)
        retained_episodes.append(episode)
    _directory_names(private / "references", [f"{digest}.rkt" for digest in reference_hashes],
                     "reference")
    canonical = provenance["canonical_rule"]
    if _sha256(_read_file(private / canonical["reference_path"])) != canonical["program_sha256"]:
        raise ValueError("canonical Racket reference hash mismatch")

    labels_checked = 0
    if replay:
        current, _ = source_provenance()
        if current != provenance:
            raise ValueError("recorded source hash or canonical rule differs from current checkout")
        core = load_core()
        if core._loaded_source_sha256 != provenance["sources"]["prototype"]["sha256"]:
            raise ValueError("prototype source hash changed before replay")
        for episode in retained_episodes:
            metadata = episode["metadata"]
            program = metadata["program"]
            if program != core.rule_program(metadata["threshold"]):
                raise ValueError("private program is not the current rule for its threshold")
            pairs = episode["train"] + episode["test"]
            outputs = core.run_racket(program, [pair["input"] for pair in pairs])
            if len(outputs) != len(pairs):
                raise ValueError("Racket replay returned a different label count")
            for index, (pair, output) in enumerate(zip(pairs, outputs)):
                if pair["output"] != output:
                    split = "train" if index < len(episode["train"]) else "test"
                    offset = index if split == "train" else index - len(episode["train"])
                    raise ValueError(f"Racket label mismatch at {split}[{offset}]")
                labels_checked += 1

    return {"status": "verified", "episode_count": len(ids), "public_challenge_ids": ids,
            "file_integrity": "passed", "current_sources": "matched" if replay else "not_checked",
            "label_replay": "passed" if replay else "not_run", "labels_checked": labels_checked,
            "scope": "proposed_task_local_prototype"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path, help="new or empty output directory")
    mode.add_argument("--verify", type=Path, help="verify an existing complete export")
    parser.add_argument("--replay", action="store_true", help="with --verify, check current sources and Racket labels")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--train-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--threshold", choices=THRESHOLDS, help="one setting; default exports all three")
    args = parser.parse_args(argv)
    try:
        if args.verify is not None:
            report = verify_export(args.verify, replay=args.replay)
        else:
            if args.replay:
                parser.error("--replay requires --verify")
            _empty_destination(args.out)
            core = load_core()
            settings = (args.threshold,) if args.threshold else THRESHOLDS
            episodes = [core.make_episode(args.seed, threshold=threshold,
                                          train_count=args.train_count, query_count=args.query_count)
                        for threshold in settings]
            report = write_batch(episodes, args.out,
                                 expected_core_sha256=core._loaded_source_sha256)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
