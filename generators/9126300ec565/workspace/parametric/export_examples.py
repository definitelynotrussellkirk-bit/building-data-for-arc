"""Write private labeled episodes and exact-byte public projections.

Run through review.py run. Only adapter.generate supplies actual labels. The
writer/verifier check serialization and privacy; they do not execute a rule.
Serve one privately ordered turns/public file at a time, after each answer.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id


SCHEMA = "arcpuzzles-parametric-review-examples-v1"
AXES = ("vertical", "horizontal", "long_axis")


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _materialize(episodes):
    if type(episodes) is not list or not episodes:
        raise ValueError("Supply a nonempty list of labeled episodes")
    files, records, turn_answers = {}, [], {}
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        # Reuse the strict grid checker for private query labels as well.
        public_challenge_bytes({"train": episode["test"], "test": episode["test"]})
        inputs = [_raw(pair["input"]) for split in ("train", "test") for pair in episode[split]]
        if len(inputs) != len(set(inputs)):
            raise ValueError("Demonstration and query inputs must all be distinct")
        public = "public/" + public_challenge_id(episode) + ".json"
        if public in files:
            raise ValueError("Duplicate visible full challenge")
        files[public] = raw
        turns = []
        for pair in episode["test"]:
            visible = {"train": episode["train"], "test": [{"input": pair["input"]}]}
            path = "turns/public/" + public_challenge_id(visible) + ".json"
            if path in turn_answers and turn_answers[path] != pair["output"]:
                raise ValueError("Identical visible turns have conflicting private answers")
            turn_answers[path] = pair["output"]
            files[path] = public_challenge_bytes(visible)
            turns.append(path)
        records.append({"episode": episode, "public": public, "turns": turns})
    index = {"schema": SCHEMA, "episodes": records,
             "verification_scope": "Projection and exact visible bytes only; labels are not re-executed here."}
    return files, _raw(index)


def write_examples(output, episodes):
    """Publish already labeled episodes into a new directory, without changing labels.

    Public filenames hash only exact visible challenge bytes. The private index
    retains all episode metadata and turn order; public turns retain only the
    original demonstrations and the next query input, with no sequence hints.
    """
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    files, private = _materialize(episodes)  # Validate everything before publishing.
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(raw)
    with (output / "private.json").open("xb") as handle:
        handle.write(private)  # Publish the private inventory last.
    return verify_examples(output)


def verify_examples(output):
    """Check strict grids, paths, file inventory and public/private projections.

    This is not a label oracle or an independent authentication of a rewritten
    private index. Native qualification provides the separate Racket evidence.
    """
    output = Path(output)
    try:
        index = json.loads((output / "private.json").read_bytes())
        if index.get("schema") != SCHEMA:
            raise ValueError("Unexpected private example schema")
        files, private = _materialize([record["episode"] for record in index["episodes"]])
        if index != json.loads(private):
            raise ValueError("Private paths or ordered turns differ from their visible projections")
        actual = set()
        for path in output.rglob("*"):
            if path.is_symlink():
                raise ValueError("Example files must be regular files")
            if path.is_file():
                actual.add(path.relative_to(output).as_posix())
        if actual != set(files) | {"private.json"}:
            raise ValueError("Example file inventory differs")
        for name, expected in files.items():
            if (output / name).read_bytes() != expected:
                raise ValueError("Public bytes, hash name or projection differ: " + name)
    except (KeyError, TypeError, AttributeError, OSError) as error:
        raise ValueError("Invalid example export: " + str(error)) from error
    return {"status": "verified_projection", "output": str(output.resolve()),
            "episodes": len(index["episodes"]),
            "turns": sum(len(record["turns"]) for record in index["episodes"]),
            "label_verification": "not_performed"}


def _load_adapter():
    path = Path(__file__).resolve().with_name("adapter.py")
    name = "_frame_export_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--axis", choices=AXES, help="Omit to export all three settings")
    args = parser.parse_args(argv)
    try:
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError(args.out)
        adapter = _load_adapter()
        episodes = []
        for axis in (args.axis,) if args.axis else AXES:
            settings = {"axis": axis}
            generated = adapter.generate(args.seed, settings, args.demos, args.queries)
            episodes.append(dict(generated, seed=args.seed, settings=settings))
        print(json.dumps(write_examples(args.out, episodes), sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError) as error:
        print("export_examples: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
