#!/usr/bin/env python3
"""Build and verify compact, Racket-backed proposed marker-ray episodes."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "shared/runtime").is_dir())
for path in (HERE, ROOT / "src", ROOT / "shared/runtime"):
    if str(path) not in sys.path: sys.path.insert(0, str(path))
from core import enumerate_settings, params_dict, materialize_program, transform, TASK_ID
from episodes import lesson_certificate
from reviewer_support import public_challenge_bytes, public_challenge_id


def _sha(data): return hashlib.sha256(data).hexdigest()


def _json(value): return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def source_hashes():
    paths = [HERE / n for n in ("core.py", "episodes.py", "build.py", "adapter.py", "promotion.json", "canonical.rkt")]
    paths.append(HERE.parents[1] / "generator.py")
    return {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in paths}


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30 or any(type(row) is not list or len(row) != len(value[0])
            or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in value)):
        raise ValueError("invalid exact-integer ARC grid")
    return value


def write_export(episodes, destination, *, racket=None, racket_evaluations=0, command=None):
    """Serialize already-labeled episodes; verify_export checks their claims.

    Public names and bytes depend exclusively on visible examples. Private maps,
    hashes and source identity remain outside public/. Duplicate visible content
    fails before destination creation. An existing destination is never reused.
    """
    destination = Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    if type(episodes) is not list or not episodes: raise ValueError("nonempty episode list required")
    prepared, seen = [], set()
    for episode in episodes:
        visible = public_challenge_bytes(episode)
        identity = public_challenge_id(episode)
        if identity in seen: raise ValueError("duplicate visible challenge")
        seen.add(identity)
        for split in ("train", "test"):
            for pair in episode[split]: _grid(pair["input"]); _grid(pair["output"])
        prepared.append((identity, visible, deepcopy(episode)))
    prepared.sort(key=lambda item: item[0])
    destination.mkdir(parents=True)
    (destination / "public").mkdir()
    private, files = [], {}
    for identity, visible, episode in prepared:
        relative = "public/" + identity + ".json"
        (destination / relative).write_bytes(visible)
        files[relative] = _sha(visible)
        private.append({"public_id": identity, "episode": episode})
    data = _json(private)
    (destination / "private.json").write_bytes(data); files["private.json"] = _sha(data)
    manifest = {"schema": "marker-rays-prototype-export-v1", "status": "proposed",
                "task_id": TASK_ID, "episode_count": len(private),
                "demos": sum(len(x["episode"]["train"]) for x in private),
                "queries": sum(len(x["episode"]["test"]) for x in private),
                "files": files, "source_hashes": source_hashes(),
                "racket": racket, "racket_evaluations": racket_evaluations, "command": command,
                "scope": "Finite declared settings and saved seeds; no acceptance or training admission."}
    (destination / "manifest.json").write_bytes(_json(manifest))
    return manifest


def verify_export(destination, *, replay=False):
    """Validate bytes, source, projection, labels and lessons; optionally replay Racket."""
    destination = Path(destination)
    manifest = json.loads((destination / "manifest.json").read_bytes())
    if manifest.get("schema") != "marker-rays-prototype-export-v1": raise ValueError("unknown export schema")
    if manifest.get("task_id") != TASK_ID or manifest.get("status") != "proposed":
        raise ValueError("export task/status mismatch")
    if any(type(manifest.get(key)) is not int or manifest[key] < 1 for key in ("episode_count", "demos", "queries")):
        raise ValueError("manifest counts require positive exact integers")
    contract = json.loads((HERE / "promotion.json").read_bytes())
    if manifest.get("source_hashes") != source_hashes(): raise ValueError("prototype source drift")
    private = json.loads((destination / "private.json").read_bytes())
    if type(private) is not list or not private: raise ValueError("missing private episodes")
    identities = [row["public_id"] for row in private]
    if identities != sorted(set(identities)): raise ValueError("public IDs must be unique and sorted")
    expected_files = {"private.json"} | {"public/" + identity + ".json" for identity in identities}
    if set(manifest["files"]) != expected_files: raise ValueError("unexpected file inventory")
    if {p.name for p in (destination / "public").iterdir()} != {i + ".json" for i in identities}:
        raise ValueError("unexpected public file")
    for relative, digest in manifest["files"].items():
        path = destination / relative
        if not path.resolve().is_relative_to(destination.resolve()) or path.is_symlink():
            raise ValueError("export file escapes destination")
        if _sha(path.read_bytes()) != digest: raise ValueError("export byte hash mismatch: " + relative)
    bridge = None; runtime = None; evaluations = 0
    if replay:
        from arcpuzzles.parametric_worker import _real_evaluator
        apply, runtime, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        counts = {"demos": 0, "queries": 0}
        for row in private:
            ep = row["episode"]
            if type(ep.get("seed")) is not int or not 0 <= ep["seed"] <= 2**63 - 1:
                raise ValueError("episode seed requires an exact nonnegative integer")
            if type(ep.get("settings")) is not dict or set(ep["settings"]) != set(contract["parameters"]):
                raise ValueError("episode settings must name exactly the declared parameters")
            settings = params_dict(ep["settings"])
            for split, key in (("train", "demos"), ("test", "queries")):
                low, high = contract["limits"][key]
                if type(ep.get(split)) is not list or not low <= len(ep[split]) <= high:
                    raise ValueError("episode count outside declared " + key + " limits")
            if ep["program_solution"] != materialize_program(settings): raise ValueError("program mismatch")
            if "program_sha256" in ep and ep["program_sha256"] != _sha(ep["program_solution"].encode()):
                raise ValueError("private program hash mismatch")
            visible = public_challenge_bytes(ep)
            if row["public_id"] != _sha(visible): raise ValueError("public identifier includes nonvisible data")
            if (destination / "public" / (row["public_id"] + ".json")).read_bytes() != visible:
                raise ValueError("public/private projection mismatch")
            inputs = []
            for split, count in (("train", "demos"), ("test", "queries")):
                counts[count] += len(ep[split])
                for pair in ep[split]:
                    _grid(pair["input"]); _grid(pair["output"])
                    inputs.append(json.dumps(pair["input"]))
                    if transform(pair["input"], settings) != pair["output"]: raise ValueError("incorrect claimed label")
                    if replay:
                        evaluations += 1
                        if apply(ep["program_solution"], pair["input"]) != pair["output"]:
                            raise ValueError("Racket label mismatch")
            if len(set(inputs)) != len(inputs): raise ValueError("duplicate episode input")
            certificate = lesson_certificate(ep["train"], [p["input"] for p in ep["test"]])
            if _json(certificate) != _json(ep["certificate"]) or certificate["setting_survivors"] != [settings] or not certificate["identifiable"]:
                raise ValueError("invalid finite lesson certificate")
        if manifest["episode_count"] != len(private) or any(manifest[k] != v for k, v in counts.items()):
            raise ValueError("manifest counts mismatch")
    finally:
        if bridge is not None: bridge.close()
    return {"valid": True, "episodes": len(private), **counts, "racket_replayed": replay,
            "racket_evaluations": evaluations, "racket": runtime}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    gen.add_argument("--demos", type=int, default=3); gen.add_argument("--queries", type=int, default=4)
    gen.add_argument("--quarter-turns", type=int, choices=range(4)); gen.add_argument("--stride", type=int, choices=(1, 2))
    gen.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify"); verify.add_argument("path", type=Path); verify.add_argument("--replay", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "verify":
        print(json.dumps(verify_export(args.path, replay=args.replay), sort_keys=True)); return 0
    if args.out.exists(): raise FileExistsError(args.out)
    if len(set(args.seeds)) != len(args.seeds): raise ValueError("duplicate requested seeds")
    settings = [s for s in enumerate_settings() if (args.quarter_turns is None or s["quarter_turns"] == args.quarter_turns)
                and (args.stride is None or s["stride"] == args.stride)]
    jobs = [{"seed": seed, "settings": setting, "demos": args.demos, "queries": args.queries}
            for seed in args.seeds for setting in settings]
    contract = json.loads((HERE / "promotion.json").read_bytes())
    from arcpuzzles.parametric_worker import evaluate_contract
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    episodes = []
    for raw in result["episodes"]:
        ep = deepcopy(raw)
        ep["program_solution"] = ep.pop("program")
        ep["status"] = "proposed_parametric_prototype"; ep["reference"] = "proposed_parametric_prototype"
        ep["certificate"] = lesson_certificate(ep["train"], [pair["input"] for pair in ep["test"]])
        if not ep["certificate"]["identifiable"]: raise ValueError("shortcut ambiguity after Racket labeling")
        episodes.append(ep)
    manifest = write_export(episodes, args.out, racket=result["racket"],
                            racket_evaluations=result["racket_evaluations"], command=sys.argv)
    print(json.dumps({"out": str(args.out), "episodes": manifest["episode_count"], "demos": manifest["demos"],
                      "queries": manifest["queries"], "racket_evaluations": manifest["racket_evaluations"],
                      "verified": verify_export(args.out)["valid"], "status": "proposed"}, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
