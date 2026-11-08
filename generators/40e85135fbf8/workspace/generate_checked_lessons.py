#!/usr/bin/env python3
"""Generate and validate this task's complete ordered lessons through Catalog.

From the packet root:
  python3 run_with_racket.py python3 \
    generators/40e85135fbf8/workspace/generate_checked_lessons.py \
    --count 2 --seed 0 --difficulty medium --allow-unapproved \
    --out ../checks/checked-lessons.jsonl

Only this entrypoint enforces EXAMPLES_NEEDED and checks accepted lessons after
materialization. Generic generate/API/export defaults remain unchanged. Labels
come from the canonical Racket runtime; Python checks never replace them.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)


def load_generator():
    source = next(path for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ) if path.is_file())
    raw = source.read_bytes()
    spec = importlib.util.spec_from_file_location("checked_lesson_generator", source)
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(source), "exec"), gen.__dict__)
    return gen, source, hashlib.sha256(raw).hexdigest()


def write_checked(episodes, out, *, gen, source, source_hash, count, n_test):
    """Validate the complete materialized population before creating its file."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output already exists: {out}")
    if not isinstance(episodes, list) or len(episodes) != count:
        raise ValueError(f"expected {count} materialized episodes")
    for index, episode in enumerate(episodes):
        if not isinstance(episode, dict) or episode.get("task_id") != TASK_ID:
            raise ValueError(f"episode {index}: wrong task identity")
        provenance = episode.get("provenance", {})
        if provenance.get("generator_sha256") != source_hash:
            raise ValueError(f"episode {index}: wrong generator source hash")
        if provenance.get("reference") != "canonical" or episode.get("executed_rule_hash") != gen.RULE_HASH:
            raise ValueError(f"episode {index}: wrong executed canonical rule")
        train, queries = episode.get("train"), episode.get("test")
        if not isinstance(train, list) or len(train) != gen.EXAMPLES_NEEDED:
            raise ValueError(f"episode {index}: expected {gen.EXAMPLES_NEEDED} demonstrations")
        if not isinstance(queries, list) or len(queries) != n_test:
            raise ValueError(f"episode {index}: expected {n_test} queries")
        for query_index, query in enumerate(queries):
            if not isinstance(query, dict) or "input" not in query or "output" not in query:
                raise ValueError(f"episode {index}: missing labeled query {query_index}")
            reasons = gen.lesson_identifiable(train, query)
            reasons += gen.strict_canonical_like(query["input"])
            if not reasons and gen.rule_mirror(query["input"]) != query["output"]:
                reasons.append("query label disagrees with the rule mirror")
            if reasons:
                raise ValueError(f"episode {index}, query {query_index}: " + "; ".join(reasons))
    if hashlib.sha256(Path(source).read_bytes()).hexdigest() != source_hash:
        raise ValueError("generator source changed during materialization")
    payload = "".join(json.dumps(episode, allow_nan=False) + "\n" for episode in episodes)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main():
    from arcpuzzles import Catalog

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=positive_int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--test", "--n-test", dest="n_test", type=positive_int, default=1)
    parser.add_argument("--allow-unapproved", action="store_true",
                        help="explicit research opt-in passed to the public Catalog API")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    gen, source, source_hash = load_generator()
    episodes = Catalog(ROOT).generate(
        TASK_ID, count=args.count, seed=args.seed, difficulty=args.difficulty,
        n_train=gen.EXAMPLES_NEEDED, n_test=args.n_test, reference="canonical",
        allow_unapproved=args.allow_unapproved)
    write_checked(episodes, args.out, gen=gen, source=source, source_hash=source_hash,
                  count=args.count, n_test=args.n_test)
    print(json.dumps({"out": str(args.out), "episodes": len(episodes),
                      "train_per_episode": gen.EXAMPLES_NEEDED, "test_per_episode": args.n_test,
                      "generator_sha256": source_hash, "rule_hash": gen.RULE_HASH,
                      "labels": "canonical Racket execution",
                      "allow_unapproved": args.allow_unapproved,
                      "policy": "validate accepted ordered lessons; rotations not checked"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
