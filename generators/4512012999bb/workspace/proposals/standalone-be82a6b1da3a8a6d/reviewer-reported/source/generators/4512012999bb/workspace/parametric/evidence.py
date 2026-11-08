"""Bounded source-bound replay of an already generated parametric batch.

This is an authoring audit: it deliberately reads private programs/answers.
It is not a blind solver or evidence of a completed review intake.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("parametric_proposal", HERE / "prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def audit_batch(batch, *, canonical=None, max_pairs=64, timeout=30):
    """Replay at most max_pairs scenes, four programs each, plus five originals."""
    batch = Path(batch)
    if type(max_pairs) is not int or not 1 <= max_pairs <= 256:
        raise ValueError("max_pairs must be in 1..256")
    manifest_path = batch / "private/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "4512012999bb-parametric-proposal-v1":
        raise ValueError("unexpected proposal manifest schema")
    provenance = manifest["provenance"]
    source_sha = P.sha256((HERE / "prototype.py").read_bytes())
    if provenance["prototype_sha256"] != source_sha:
        raise ValueError("proposal source changed since batch generation; regenerate before replay")
    selected = HERE.parents[1] / "generator.py"
    selected_sha = P.sha256(selected.read_bytes())
    if provenance["selected_generator_sha256"] != selected_sha:
        raise ValueError("selected generator source changed since batch generation")
    canonical_row, canonical_path = P.load_canonical(canonical)
    if P.sha256(canonical_path.read_bytes()) != provenance["canonical_file_sha256"]:
        raise ValueError("canonical source file changed since batch generation")
    expected_programs = P.programs_from(canonical_row["program_solution"])
    programs = {}
    if set(manifest["program_sha256"]) != set(P.RIVALS):
        raise ValueError("the evidence must cover exactly the four declared programs")
    for name in P.RIVALS:
        raw = (batch / "private/programs" / f"{name}.rkt").read_bytes()
        if raw != expected_programs[name].encode() or P.sha256(raw) != manifest["program_sha256"][name]:
            raise ValueError(f"materialized {name} program differs from its bound source")
        programs[name] = raw.decode()
    ids = manifest["public_ids"]
    if (not ids or len(ids) > 2 or ids != sorted(set(ids))
            or any(not re.fullmatch(r"[0-9a-f]{64}", item) for item in ids)):
        raise ValueError("public IDs must be a sorted unique batch of one or two hashes")
    if sorted(p.name for p in (batch / "public").iterdir()) != [f"{item}.json" for item in ids]:
        raise ValueError("public directory must contain only the visible-content hash files")
    if [episode["public_id"] for episode in manifest["episodes"]] != ids:
        raise ValueError("private episodes are not aligned to the sorted public batch")
    P._add_runtime_path()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    challenges, seen = [], set()
    count = 0
    for episode in manifest["episodes"]:
        public_id = episode["public_id"]
        raw = (batch / "public" / f"{public_id}.json").read_bytes()
        challenge = json.loads(raw)
        if raw != public_challenge_bytes(challenge) or public_challenge_id(challenge) != public_id:
            raise ValueError("public file has extra fields, noncanonical bytes, or an invalid content ID")
        if episode["setting"] not in ("direct", "mirror"):
            raise ValueError("unknown selected policy")
        for split in ("train", "test"):
            if len(challenge[split]) != len(episode["scenes"][split]):
                raise ValueError("metadata scene count mismatch")
            for pair in challenge[split]:
                key = P.grid_key(pair["input"])
                if key in seen:
                    raise ValueError("input grid repeated across the batch")
                seen.add(key)
                if len(P.find_candidates(pair["input"])) != 1:
                    raise ValueError("scene does not have exactly one guide/crop candidate")
                count += 1
        challenges.append((episode, challenge))
    if count > max_pairs:
        raise ValueError(f"batch contains {count} scenes, above replay bound {max_pairs}")
    runner = P.RacketRunner(timeout=timeout)
    episode_evidence = []
    try:
        originals = list(canonical_row["train"])
        test = canonical_row.get("test", [])
        originals += [test] if isinstance(test, dict) else test
        labeled = [pair for pair in originals if "output" in pair]
        if len(labeled) != 5:
            raise ValueError("expected five labeled original pairs")
        for index, pair in enumerate(labeled):
            if runner.apply(programs["direct"], pair["input"]) != pair["output"]:
                raise AssertionError(f"canonical replay mismatch at pair {index}")
        for episode, challenge in challenges:
            predictions = {name: {"train": [], "test": []} for name in P.RIVALS}
            for split in ("train", "test"):
                for index, pair in enumerate(challenge[split]):
                    outputs = {name: runner.apply(programs[name], pair["input"]) for name in P.RIVALS}
                    scene = {"input": pair["input"], "meta": episode["scenes"][split][index]}
                    P._check_outputs(scene, outputs)
                    for name, output in outputs.items():
                        predictions[name][split].append(output)
            if predictions != episode["predictions"]:
                raise AssertionError("materialized prediction matrix failed live Racket replay")
            if predictions[episode["setting"]]["test"] != episode["query_answers"]:
                raise AssertionError("private query answers failed live Racket replay")
            certificate = P.identify_from_demos(challenge["train"], predictions)
            if (certificate != episode["certificate"] or certificate["survivors"] != [episode["setting"]]
                    or not all(query["identifiable"] for query in certificate["queries"])):
                raise AssertionError("demo-only finite-family certificate failed recomputation")
            episode_evidence.append({"public_id": episode["public_id"], "setting": episode["setting"],
                                     "train": len(challenge["train"]), "test": len(challenge["test"]),
                                     "certificate": certificate,
                                     "query_crop_shapes": [s["crop_shape"] for s in episode["scenes"]["test"]]})
        result = {"schema": "4512012999bb-parametric-replay-v1", "status": "pass",
                  "scope": "source-bound authoring replay; finite declared rivals only; not review intake",
                  "canonical_pairs_passed": len(labeled), "scenes_replayed": count,
                  "racket_evaluations": runner.calls, "max_scene_bound": max_pairs,
                  "public_ids": ids, "episodes": episode_evidence,
                  "source_sha256": {"prototype.py": source_sha,
                                    "evidence.py": P.sha256(Path(__file__).read_bytes()),
                                    "selected_generator.py": selected_sha,
                                    "canonical_file": P.sha256(canonical_path.read_bytes()),
                                    "private_manifest": P.sha256(manifest_path.read_bytes())},
                  "program_sha256": manifest["program_sha256"],
                  "runtime_identity": runner.bridge.runtime_identity}
    finally:
        runner.close()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new private evidence JSON file")
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--max-pairs", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        if args.out.exists():
            raise FileExistsError(f"evidence output already exists: {args.out}")
        result = audit_batch(args.batch, canonical=args.canonical, max_pairs=args.max_pairs, timeout=args.timeout)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (ValueError, KeyError, OSError, RuntimeError, AssertionError) as error:
        print(f"parametric replay failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"], "scenes_replayed": result["scenes_replayed"],
                      "racket_evaluations": result["racket_evaluations"], "public_ids": result["public_ids"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
