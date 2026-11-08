"""Strict content-addressed export and replay for the proposed stencil family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath

from reviewer_support import public_challenge_bytes

_spec = importlib.util.spec_from_file_location(
    "_stencil_export_impl", Path(__file__).resolve().with_name("prototype.py"))
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)

SCHEMA = "arcpuzzles-stencil-export-v1"


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def turn_bytes(episode, index):
    """Only demonstrations and one input; no totals, ordinals, or future queries."""
    prototype.integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})


def _snapshot(episodes):
    files, records = {}, []
    seen = set()
    for episode in episodes:
        controller = public_challenge_bytes(episode)
        visible_id = _sha(controller)
        if visible_id in seen:
            raise ValueError("duplicate controller challenge")
        seen.add(visible_id)
        controller_path = f"controller/{visible_id}.json"
        files[controller_path] = controller
        private_path = f"private/{visible_id}.json"
        files[private_path] = _bytes(episode)
        turns = []
        for index in range(len(episode["test"])):
            raw = turn_bytes(episode, index)
            name = f"public/{_sha(raw)}.json"
            if name in files and files[name] != raw:
                raise ValueError("inconsistent public bytes")
            files[name] = raw
            turns.append(name)
        records.append({"controller": controller_path, "private": private_path, "turns": turns})
    manifest = {"schema": SCHEMA, "task_id": prototype.TASK_ID, "episodes": records,
                "files": {name: {"sha256": _sha(raw), "bytes": len(raw)} for name, raw in sorted(files.items())},
                "public_usage": "Serve only the next public/ file listed in each private turn order.",
                "controller_usage": "controller/ holds all future inputs; it is not a model prompt.",
                "variant_approved": False, "training_admitted": False}
    return files, manifest


def write_export(episodes, output, *, engine=None):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if type(episodes) is not list or not episodes:
        raise ValueError("export requires at least one episode")
    # Recompute labels/teaching rather than trusting an attached certificate.
    with prototype._engine(engine) as runtime:
        for episode in episodes:
            prototype.verify_episode(episode, engine=runtime)
    files, manifest = _snapshot(episodes)
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(files.items()):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    # Manifest is written last; incomplete output cannot pass verify_export.
    (output / "manifest.json").write_bytes(_bytes(manifest))
    return manifest


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite JSON number: " + value)


def _json(raw):
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _member(root, name):
    if type(name) is not str:
        raise ValueError("manifest path must be a string")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
        raise ValueError("unsafe export member")
    result = root / path
    if any(p.is_symlink() for p in (result, *result.parents)):
        raise ValueError("symlinks are not export members")
    if not result.is_file() or not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("export member is missing or outside destination")
    return result


def verify_export(output, *, engine=None):
    """Rehash serialized members, reproject visibility, and replay actual Racket.

    This detects corruption and false labels; an editable archive is not a signed
    authority. This never grants qualification, acceptance, or training admission.
    """
    output = Path(output)
    if output.is_symlink() or not output.is_dir():
        raise ValueError("export must be a regular directory")
    manifest = _json(_member(output, "manifest.json").read_bytes())
    if (type(manifest) is not dict or manifest.get("schema") != SCHEMA
            or manifest.get("task_id") != prototype.TASK_ID
            or type(manifest.get("files")) is not dict
            or type(manifest.get("episodes")) is not list or not manifest["episodes"]):
        raise ValueError("invalid export manifest")
    raw_files = {}
    for name, claim in manifest["files"].items():
        raw = _member(output, name).read_bytes()
        if (type(claim) is not dict or set(claim) != {"sha256", "bytes"}
                or type(claim["bytes"]) is not int or claim["bytes"] != len(raw)
                or claim["sha256"] != _sha(raw)):
            raise ValueError("member hash or size mismatch")
        raw_files[name] = raw
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlinks are not export members")
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
    if actual != set(raw_files) | {"manifest.json"}:
        raise ValueError("unlisted or missing export member")
    episodes = []
    for record in manifest["episodes"]:
        if (type(record) is not dict or set(record) != {"controller", "private", "turns"}
                or type(record["turns"]) is not list):
            raise ValueError("malformed episode manifest row")
        try:
            episode = _json(raw_files[record["private"]])
            episodes.append(episode)
        except (KeyError, TypeError) as error:
            raise ValueError("missing private episode") from error
    with prototype._engine(engine) as runtime:
        for episode in episodes:
            prototype.verify_episode(episode, engine=runtime)
    expected_files, expected_manifest = _snapshot(episodes)
    if raw_files != expected_files or manifest != expected_manifest:
        raise ValueError("export schema, public identity, visibility, or turn projection mismatch")
    return {"schema": "arcpuzzles-stencil-export-check-v1", "status": "passed",
            "episodes": len(episodes), "public_turns": len(list((output / "public").glob("*.json"))),
            "racket_labels_checked": True, "teaching_fit": "demonstrations_only",
            "variant_approved": False, "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--demos", type=int, default=3)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--direction", choices=["both", *prototype.DIRECTIONS], default="both")
    verify = commands.add_parser("verify")
    verify.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    if args.command == "build":
        directions = prototype.DIRECTIONS if args.direction == "both" else (args.direction,)
        with prototype.RacketEngine() as engine:
            episodes = [prototype.generate(args.seed, {"direction": d}, args.demos, args.queries,
                                            engine=engine) for d in directions]
            write_export(episodes, args.out, engine=engine)
            result = verify_export(args.out, engine=engine)
    else:
        result = verify_export(args.path)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
