#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators/9a94379ed070/workspace/parametric/prototype.py"
RETAINED = ROOT.parent / "checks/parametric/9a94379ed070-rank-offset-v1"
OUT = Path(__file__).resolve().parent / "result.json"


def load_prototype():
    spec = importlib.util.spec_from_file_location("rank_offset_probe", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite_manifest_hash(tree: Path, relative: str) -> None:
    path = tree / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["files"][relative] = sha(tree / relative)
    path.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def expect_rejection(module, tree: Path, expected: str, bridge: RacketBridge) -> str:
    try:
        module.verify_tree(tree, root=ROOT, bridge=bridge)
    except ValueError as exc:
        message = str(exc)
        if expected not in message:
            raise AssertionError(f"expected rejection containing {expected!r}, got {message!r}")
        return message
    raise AssertionError("tampered tree was accepted")


def main() -> int:
    module = load_prototype()
    result: dict[str, object] = {
        "schema": "rank-offset-adversarial-probe-v1",
        "task_id": module.TASK_ID,
        "surfaces": {},
    }
    with RacketBridge(max_calls_before_restart=256) as bridge:
        # Boundary sampler: maximum supported query count, a large valid seed,
        # deterministic replay, distinct payloads, and live-Racket rival analysis.
        kwargs = {
            "rank_offset": 1,
            "n_train": 1,
            "n_test": 12,
            "root": ROOT,
            "bridge": bridge,
        }
        episode = module.make_episode(2**31 - 1, **kwargs)
        replay = module.make_episode(2**31 - 1, **kwargs)
        analysis = module.analyze_episode(episode, root=ROOT, bridge=bridge)
        input_hashes = [pair["input_sha256"] for pair in episode["pairs"]]
        sampler_passed = (
            episode == replay
            and len(episode["train"]) == 1
            and len(episode["test"]) == 12
            and len(input_hashes) == len(set(input_hashes)) == 13
            and analysis["passed"]
            and analysis["demonstrations_refuting_rival"] == 1
            and all(row["rival_query_differs"] for row in analysis["queries"])
        )
        if not sampler_passed:
            raise AssertionError("maximum-query boundary episode failed")
        result["surfaces"]["sampler_boundary"] = {
            "status": "pass",
            "seed": 2**31 - 1,
            "rank_offset": 1,
            "demonstrations": 1,
            "queries": 12,
            "distinct_inputs": 13,
            "tile_sizes": sorted({pair["tile_size"] for pair in episode["pairs"]}),
            "racket_replay": analysis["racket_replay"],
            "python_parity": analysis["python_parity"],
            "queries_refuting_rival": sum(
                row["rival_query_differs"] for row in analysis["queries"]
            ),
        }

        # Verifier hardening: alter bytes and then update the manifest hash, so
        # rejection must come from semantic/exact-source checks rather than the
        # outer checksum alone.
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            program_tree = temp_root / "program"
            shutil.copytree(RETAINED, program_tree)
            program_rel = "programs/rank-offset-1.rkt"
            with (program_tree / program_rel).open("a", encoding="utf-8") as handle:
                handle.write("\n;; adversarial mutation\n")
            rewrite_manifest_hash(program_tree, program_rel)
            program_message = expect_rejection(
                module, program_tree, "program bytes differ", bridge
            )

            public_tree = temp_root / "public"
            shutil.copytree(RETAINED, public_tree)
            manifest = json.loads((public_tree / "manifest.json").read_text())
            public_rel = manifest["entries"]["1"]["public_challenge"]
            public_path = public_tree / public_rel
            public_payload = json.loads(public_path.read_text(encoding="utf-8"))
            public_payload["test"][0]["input"][0][0] = (
                public_payload["test"][0]["input"][0][0] + 1
            ) % 10
            public_path.write_text(
                json.dumps(public_payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            rewrite_manifest_hash(public_tree, public_rel)
            public_message = expect_rejection(
                module, public_tree, "public bytes mismatch", bridge
            )

        result["surfaces"]["verifier_rejection"] = {
            "status": "pass",
            "program_tamper_with_updated_manifest": program_message,
            "public_tamper_with_updated_manifest": public_message,
        }

    result["status"] = "pass"
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
