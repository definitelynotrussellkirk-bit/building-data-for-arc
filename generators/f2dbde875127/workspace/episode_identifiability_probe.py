#!/usr/bin/env python3
"""Probe actual Racket-labeled episodes for public-lesson key identifiability.

The generator/runtime produce complete episodes, but this controller removes every
query output before calling ``lesson_key_gate.analyze_lesson``.  The gate sees only
visible demonstration pairs and query inputs.  A zero exit means all sampled
lessons passed the declared independent-key quarter-turn rival family; it is not a
claim of general ARC identifiability or model accuracy.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "f2dbde875127"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
WORKSPACE = Path(__file__).resolve().parent

sys.path.insert(0, str(WORKSPACE))
from lesson_key_gate import analyze_lesson  # noqa: E402


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def public_lesson(episode: dict) -> dict:
    """Deep-copy the public view and deliberately omit every test output."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _generator_examples_needed() -> int:
    """Read the literal contract without importing generator runtime dependencies."""
    value = 3
    tree = ast.parse((HOME / "generator.py").read_text())
    for statement in tree.body:
        targets = (statement.targets if isinstance(statement, ast.Assign) else
                   [statement.target] if isinstance(statement, ast.AnnAssign) else [])
        if any(isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED"
               for target in targets):
            value = ast.literal_eval(statement.value)
    if type(value) is not int or not 1 <= value <= 32:
        raise ValueError("EXAMPLES_NEEDED must be a literal integer in 1..32")
    return max(3, value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=32, help="consecutive episode seeds")
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=None)
    parser.add_argument("--n-test", type=int, default=2)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.count < 1 or args.start_seed < 0 or args.sample_index < 0 or args.n_test < 1:
        parser.error("count and n-test must be positive; seeds/indices must be nonnegative")
    n_train = _generator_examples_needed() if args.n_train is None else args.n_train
    if not 1 <= n_train <= 32 or args.timeout <= 0:
        parser.error("n-train must be in 1..32 and timeout must be positive")

    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog  # noqa: E402

    source_path = HOME / "generator.py"
    source_hash = _sha(source_path.read_bytes())
    episodes = Catalog(REPO).generate(
        TASK_ID,
        count=args.count,
        seed=args.start_seed,
        sample_index=args.sample_index,
        n_train=n_train,
        n_test=args.n_test,
        difficulty=args.difficulty,
        allow_unapproved=True,
        timeout=args.timeout,
    )

    failures: list[dict] = []
    summaries: list[dict] = []
    unique_inputs: set[str] = set()
    total_rejections = 0
    nonconsecutive = 0
    provenance_hashes: set[str] = set()
    executed_rule_hashes: set[str] = set()
    for offset, episode in enumerate(episodes):
        public = public_lesson(episode)
        diagnostic = analyze_lesson(public)
        for split in ("train", "test"):
            for pair in public[split]:
                unique_inputs.add(_sha(_canonical(pair["input"])))
        indices = episode.get("sample_indices", [])
        total_rejections += len(episode.get("rejections", []))
        expected = list(range(args.sample_index, args.sample_index + n_train + args.n_test))
        if indices != expected:
            nonconsecutive += 1
        provenance = episode.get("provenance", {})
        provenance_hashes.add(provenance.get("generator_sha256"))
        executed_rule_hashes.add(episode.get("executed_rule_hash"))
        item = {
            "seed": args.start_seed + offset,
            "sample_indices": indices,
            "rejection_count": len(episode.get("rejections", [])),
            "passed": diagnostic["passed"],
            "observed_key_frames": diagnostic["observed_key_frames"],
            "consistent_turns": diagnostic["consistent_turns"],
            "ambiguous_query_keys": diagnostic["ambiguous_query_keys"],
            "errors": diagnostic["errors"],
        }
        summaries.append(item)
        if not diagnostic["passed"]:
            failures.append({**item, "query_frames": diagnostic["query_frames"]})

    source_bound = provenance_hashes == {source_hash}
    passed = not failures and source_bound and len(episodes) == args.count
    report = {
        "schema": "actual-episode-key-identifiability-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "generator_provenance_hashes": sorted(x for x in provenance_hashes if x),
        "executed_rule_hashes": sorted(x for x in executed_rule_hashes if x),
        "probe_sha256": _sha(Path(__file__).read_bytes()),
        "lesson_gate_sha256": _sha((WORKSPACE / "lesson_key_gate.py").read_bytes()),
        "sampling": {
            "episode_seed_first": args.start_seed,
            "episode_seed_last": args.start_seed + args.count - 1,
            "episode_count": args.count,
            "sample_index": args.sample_index,
            "n_train": n_train,
            "n_test": args.n_test,
            "difficulty": args.difficulty,
        },
        "counts": {
            "episodes_returned": len(episodes),
            "episodes_passed": len(episodes) - len(failures),
            "episodes_failed": len(failures),
            "candidate_rejections": total_rejections,
            "episodes_with_nonconsecutive_indices": nonconsecutive,
            "unique_public_inputs": len(unique_inputs),
        },
        "source_bound": source_bound,
        "query_outputs_discarded_before_analysis": True,
        "query_answers_read_by_lesson_gate": False,
        "rival_family": "independent per-key quarter-turn maps with fixed crop and floor centering",
        "episodes": summaries,
        "failures": failures,
        "passed": passed,
        "training_admitted": False,
        "limitation": "finite sampled gate under a declared rival family; not general identifiability or model performance",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": source_hash,
        "sampling": report["sampling"],
        "counts": report["counts"],
        "source_bound": source_bound,
        "passed": passed,
    }, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
