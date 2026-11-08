"""Build, inspect and replay this proposed family using the packet's Racket.

Run through review.py run.  Public batch files contain all masked query inputs;
the sequential consumer uses one hash-named turns/ file via the private map.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
SCHEMA = "arcpuzzles-stop-short-export-v1"
_adapter_path = Path(__file__).with_name("adapter.py").resolve()
_adapter_name = "_stop_short_" + hashlib.sha256(str(_adapter_path).encode()).hexdigest()
_adapter_spec = importlib.util.spec_from_file_location(_adapter_name, _adapter_path)
adapter = importlib.util.module_from_spec(_adapter_spec)
sys.modules[_adapter_name] = adapter
_adapter_spec.loader.exec_module(adapter)


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def _validate(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    program = adapter.program(settings)
    if episode.get("program_solution") != program:
        raise ValueError("program does not match episode settings")
    for split, low, high in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{split} count is outside {low}..{high}")
        for pair in pairs:
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                raise ValueError("private pairs require exactly input/output")
            reasons = adapter.validate_input(pair["input"])
            if reasons:
                raise ValueError("input outside admitted grammar: " + "; ".join(reasons))
            adapter._grid(pair["output"])
            if adapter.transform(pair["input"], settings["stop_short"]) != pair["output"]:
                raise ValueError("incorrect claimed output")
    inputs = [_bytes(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("duplicate demonstration/query input")
    certificate = adapter.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
    if (certificate["surviving_settings"] != [settings] or certificate["surviving_shortcuts"]
            or certificate["ambiguous_queries"]):
        raise ValueError("unidentified or ambiguous lesson")
    if _bytes(episode.get("certificate")) != _bytes(certificate):
        raise ValueError("stored certificate does not match demonstrations")
    if episode.get("status") != "proposed" or episode.get("training_admitted") is not False:
        raise ValueError("prototype must remain proposed and not training-admitted")
    return certificate


def _execute(episodes):
    """Execute every setting on demos and chosen labels on all queries."""
    from arcpuzzles.parametric_worker import _real_evaluator
    canonical = {row["program_solution"] for line in canonical_path(ROOT).read_text().splitlines()
                 if (row := json.loads(line)).get("task_id") == adapter.TASK_ID}
    if canonical != {adapter.program({"stop_short": 0})}:
        raise ValueError("default Racket source drifted from canonical")
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0
    try:
        for episode in episodes:
            stop = episode["settings"]["stop_short"]
            for setting in adapter.SETTINGS:
                program = adapter.program({"stop_short": setting})
                for pair in episode["train"]:
                    actual = apply(program, pair["input"])
                    evaluations += 1
                    if actual != adapter.transform(pair["input"], setting):
                        raise ValueError("Racket/Python demonstration disagreement")
            for pair in episode["test"]:
                actual = apply(episode["program_solution"], pair["input"])
                evaluations += 1
                if actual != pair["output"]:
                    raise ValueError("Racket query label disagreement")
    finally:
        bridge.close()
    return {"racket": identity, "racket_evaluations": evaluations}


def write_export(episodes, out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    if type(episodes) is not list or not episodes:
        raise ValueError("at least one episode required")
    payloads, records, public_ids, turns = {}, [], [], {}
    for episode in episodes:
        _validate(episode)
        raw = public_challenge_bytes(episode)
        identity = _hash(raw)
        if identity in public_ids:
            raise ValueError("duplicate visible episode")
        public_ids.append(identity)
        payloads[f"public/{identity}.json"] = raw
        turn_ids = []
        for index in range(len(episode["test"])):
            visible = adapter.visible_turn(episode, index)
            turn_raw = public_challenge_bytes(visible)
            turn_id = _hash(turn_raw)
            turn_ids.append(turn_id)
            turns[turn_id] = turn_raw
        records.append({"public_id": identity, "turn_ids": turn_ids, "episode": copy.deepcopy(episode)})
    execution = _execute(episodes)
    records.sort(key=lambda r: r["public_id"])
    payloads["private.jsonl"] = b"".join(_bytes(row) for row in records)
    payloads.update({f"turns/{identity}.json": raw for identity, raw in turns.items()})
    manifest = {"schema": SCHEMA, "status": "proposed", "training_admitted": False,
                "public_ids": sorted(public_ids), "turn_ids": sorted(turns),
                "files": {name: _hash(raw) for name, raw in sorted(payloads.items())}, **execution}
    # Validate and execute before creating the destination; publish manifest last.
    out.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(payloads.items()):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (out / "manifest.json").write_bytes(_bytes(manifest))
    return manifest


def verify_export(out, *, replay=False):
    out = Path(out)
    if out.is_symlink() or not out.is_dir():
        raise ValueError("export must be a regular directory")
    manifest_path = out / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("missing regular manifest")
    manifest = _json(manifest_path.read_bytes())
    if (type(manifest) is not dict or manifest.get("schema") != SCHEMA
            or manifest.get("status") != "proposed" or manifest.get("training_admitted") is not False):
        raise ValueError("invalid proposed-export manifest")
    for key in ("public_ids", "turn_ids"):
        ids = manifest.get(key)
        if (type(ids) is not list or not ids or any(type(v) is not str or not re.fullmatch(r"[0-9a-f]{64}", v) for v in ids)
                or ids != sorted(set(ids))):
            raise ValueError("invalid/sorted/unique content IDs")
    expected = {"private.jsonl"} | {f"public/{v}.json" for v in manifest["public_ids"]} | {f"turns/{v}.json" for v in manifest["turn_ids"]}
    if type(manifest.get("files")) is not dict or set(manifest["files"]) != expected:
        raise ValueError("manifest inventory disagrees with content IDs")
    actual = set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlinks are not admitted")
        if path.is_file():
            actual.add(path.relative_to(out).as_posix())
        elif path.relative_to(out).as_posix() not in {"public", "turns"}:
            raise ValueError("unexpected directory")
    if actual != expected | {"manifest.json"}:
        raise ValueError("unexpected or missing export member")
    for name in expected:
        raw = (out / name).read_bytes()
        if _hash(raw) != manifest["files"][name]:
            raise ValueError("file hash mismatch: " + name)
        if name != "private.jsonl":
            visible = _json(raw)
            if _hash(raw) != Path(name).stem or public_challenge_bytes(visible) != raw:
                raise ValueError("public bytes/schema/identifier mismatch")
    records = [_json(line) for line in (out / "private.jsonl").read_bytes().splitlines()]
    if any(type(row) is not dict or set(row) != {"public_id", "turn_ids", "episode"} for row in records):
        raise ValueError("invalid private row")
    if [row["public_id"] for row in records] != manifest["public_ids"]:
        raise ValueError("private/public identity mismatch")
    used_turns = set()
    for row in records:
        episode = row["episode"]
        _validate(episode)
        if public_challenge_bytes(episode) != (out / "public" / (row["public_id"] + ".json")).read_bytes():
            raise ValueError("private/public projection mismatch")
        turn_ids = []
        for i in range(len(episode["test"])):
            visible = adapter.visible_turn(episode, i)
            identity = public_challenge_id(visible)
            turn_ids.append(identity)
            if identity not in manifest["turn_ids"] or (out / "turns" / (identity + ".json")).read_bytes() != public_challenge_bytes(visible):
                raise ValueError("sequential turn projection mismatch")
        if row["turn_ids"] != turn_ids:
            raise ValueError("private turn ordering mismatch")
        used_turns.update(turn_ids)
    if used_turns != set(manifest["turn_ids"]):
        raise ValueError("unreferenced turn")
    result = {"status": "passed", "episodes": len(records), "turns": len(used_turns),
              "racket_replayed": replay, "training_admitted": False,
              "limits": "Local integrity and finite-family evidence; no external authenticity, exhaustive induction or owner acceptance."}
    if replay:
        result.update(_execute([r["episode"] for r in records]))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--seed", type=int, default=17)
    export.add_argument("--demos", type=int, default=3)
    export.add_argument("--queries", type=int, default=4)
    verify = commands.add_parser("verify")
    verify.add_argument("directory", type=Path)
    verify.add_argument("--replay", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "export":
        episodes = [adapter.generate(args.seed, {"stop_short": s}, args.demos, args.queries) for s in adapter.SETTINGS]
        result = write_export(episodes, args.out)
        print(json.dumps({"status": "written", "episodes": len(episodes), "turns": len(result["turn_ids"]),
                          "racket_evaluations": result["racket_evaluations"], "training_admitted": False}, sort_keys=True))
    else:
        print(json.dumps(verify_export(args.directory, replay=args.replay), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
