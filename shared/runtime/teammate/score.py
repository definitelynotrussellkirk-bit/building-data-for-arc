#!/usr/bin/env python3
"""score.py — the other half of the loop: held-out evals + scoring, SAFE-only.

`make_data.py` gets you training rows; this closes the loop for BOTH styles
it emits:

  make-eval   build a family-disjoint held-out set from the SAFE pool:
              probes (demos + query input, NO answers) + a local answer key.
              Families are split by `split_group`, so nothing in the eval
              shares a family with what you train on at the same seed.
  score       score a predictions file against the answer key:
              grid predictions -> exact@1, pass@2, cell accuracy;
              program predictions -> executed through the real Racket bridge
              against the probe's demos AND the hidden test (pass@train,
              pass@test). Per-task and per-family breakdowns. Missing or
              malformed predictions are counted LOUDLY, never silently.

Examples:
  python3 teammate/score.py make-eval --count 50 --seed 7
  python3 teammate/score.py score --predictions preds.jsonl \
      --answers teammate/out/eval_seed7_answers.jsonl

Prediction rows (JSONL, one per probe `id`):
  {"id": ..., "output": [[...]]}                  one grid attempt
  {"id": ..., "attempts": [[[...]], [[...]]]}     up to N attempts (pass@2 uses 2)
  {"id": ..., "program": "(rule! (lambda (g) ...))"}   a Racket program

Deterministic (--seed), SAFE-pool-only, torch-free. Rules of this folder
apply: no flag relaxes the SAFE constraint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "scripts", ROOT / "teammate"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from make_data import CANONICAL, DEFAULT_POOL, load_canonical_index, load_pool  # noqa: E402


# ---------------------------------------------------------------------------
# make-eval
# ---------------------------------------------------------------------------

def _family_in_holdout(split_group: str, seed: int, frac: float) -> bool:
    """Deterministic family-level split: same family always lands on the
    same side for a given seed, so train/eval can never share a family."""
    digest = hashlib.sha256(f"eval-split:{seed}:{split_group}".encode()).digest()
    return (int.from_bytes(digest[:4], "big") % 10_000) < int(frac * 10_000)


def cmd_make_eval(args) -> int:
    from puzzle_generators.runner import run_batch
    from qwen9b.instance_rows import make_instance_row

    pool = load_pool(Path(args.pool))
    canonical = load_canonical_index(Path(args.canonical))
    tasks = sorted(t for t in pool if t in canonical)
    if not tasks:
        raise SystemExit("LOUD: no pool tasks have canonical rules")

    holdout = [t for t in tasks
               if _family_in_holdout(canonical[t].get("parent_hash")
                                     or canonical[t].get("content_hash") or t,
                                     args.seed, args.holdout_frac)]
    if not holdout:
        raise SystemExit(
            f"LOUD: holdout fraction {args.holdout_frac} selected 0 of "
            f"{len(tasks)} families — raise --holdout-frac")
    weights = [pool[t] for t in holdout]

    stem = ROOT / "teammate" / "out" / f"eval_seed{args.seed}"
    probes_path = Path(args.out_probes) if args.out_probes else Path(f"{stem}_probes.jsonl")
    answers_path = Path(args.out_answers) if args.out_answers else Path(f"{stem}_answers.jsonl")
    probes_path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    produced = rejected = 0
    seen_tasks: set[str] = set()
    with probes_path.open("w") as probes, answers_path.open("w") as answers:
        while produced < args.count:
            task_id = rng.choices(holdout, weights=weights, k=1)[0]
            seed = rng.getrandbits(31)
            try:
                instances = run_batch(task_id, 1, n_train=4, n_test=1,
                                      seed_start=seed)
            except Exception as exc:
                rejected += 1
                print(f"LOUD: rejected {task_id}: {type(exc).__name__}: {exc}",
                      file=sys.stderr, flush=True)
                continue
            for instance in instances:
                if produced >= args.count:
                    break
                raw = make_instance_row(task_id, canonical[task_id], instance,
                                        where=f"teammate-eval:{task_id}:{produced}")
                probe_id = f"{task_id}:{raw['seed']}:{raw['sample_index']}"
                probes.write(json.dumps({
                    "id": probe_id,
                    "task_id": task_id,
                    "split_group": raw["split_group"],
                    "train": raw["train"],
                    "test_input": raw["test"][0]["input"],
                }, separators=(",", ":")) + "\n")
                answers.write(json.dumps({
                    "id": probe_id,
                    "task_id": task_id,
                    "split_group": raw["split_group"],
                    "train": raw["train"],
                    "test": raw["test"],
                    "program_hash": raw["program_hash"],
                }, separators=(",", ":")) + "\n")
                produced += 1
                seen_tasks.add(task_id)

    print(json.dumps({
        "probes": str(probes_path),
        "answers": str(answers_path),
        "rows": produced,
        "holdout_families": len(holdout),
        "pool_tasks": len(tasks),
        "tasks_used": len(seen_tasks),
        "task_rejections": rejected,
        "seed": args.seed,
        "note": "train on the SAME seed's non-holdout side to stay family-disjoint",
    }, indent=1, sort_keys=True))
    return 0


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

def _is_grid(g) -> bool:
    return (isinstance(g, list) and g
            and all(isinstance(r, list) and r and
                    all(isinstance(v, int) and not isinstance(v, bool)
                        and 0 <= v <= 9 for v in r) for g_row in [g] for r in g)
            and len({len(r) for r in g}) == 1)


def _cell_accuracy(pred, truth) -> float:
    if (len(pred) != len(truth)
            or any(len(pr) != len(tr) for pr, tr in zip(pred, truth))):
        return 0.0
    total = sum(len(r) for r in truth)
    same = sum(1 for pr, tr in zip(pred, truth)
               for pv, tv in zip(pr, tr) if pv == tv)
    return same / total if total else 0.0


def cmd_score(args) -> int:
    answers: dict[str, dict] = {}
    for line in Path(args.answers).open():
        if line.strip():
            row = json.loads(line)
            answers[row["id"]] = row
    if not answers:
        raise SystemExit(f"LOUD: no answer rows in {args.answers}")

    preds: dict[str, dict] = {}
    malformed: list[str] = []
    for n, line in enumerate(Path(args.predictions).open(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            pid = row["id"]
        except Exception:
            malformed.append(f"line {n}")
            continue
        preds[pid] = row

    verifier = None
    per_task: dict[str, dict] = defaultdict(lambda: {"n": 0, "exact1": 0,
                                                     "pass2": 0, "cells": 0.0})
    program_rows = grid_rows = missing = 0
    program_train_pass = program_test_pass = 0
    unknown_ids = sorted(set(preds) - set(answers))

    for pid, ans in sorted(answers.items()):
        truth = ans["test"][0]["output"]
        stats = per_task[ans["task_id"]]
        stats["n"] += 1
        row = preds.get(pid)
        if row is None:
            missing += 1
            continue
        if row.get("program"):
            program_rows += 1
            from coder_synth_verify import ProgramVerifier
            if verifier is None:
                verifier = ProgramVerifier()
            res = verifier.score(row["program"], ans["train"], ans["test"])
            train_ok = res["train_pass"] == res["train_total"]
            test_ok = res["test_pass"] == res["test_total"] and res["test_total"] > 0
            program_train_pass += train_ok
            program_test_pass += test_ok
            stats["exact1"] += test_ok
            stats["pass2"] += test_ok
            stats["cells"] += 1.0 if test_ok else 0.0
            continue
        attempts = row.get("attempts")
        if attempts is None and row.get("output") is not None:
            attempts = [row["output"]]
        if not attempts or not all(_is_grid(a) for a in attempts):
            malformed.append(pid)
            continue
        grid_rows += 1
        stats["exact1"] += attempts[0] == truth
        stats["pass2"] += any(a == truth for a in attempts[:2])
        stats["cells"] += _cell_accuracy(attempts[0], truth)

    n = len(answers)
    exact1 = sum(s["exact1"] for s in per_task.values())
    pass2 = sum(s["pass2"] for s in per_task.values())
    cells = sum(s["cells"] for s in per_task.values())
    families = {ans["split_group"] for ans in answers.values()}

    report = {
        "probes": n,
        "answered": n - missing,
        "missing_predictions": missing,
        "malformed_predictions": sorted(malformed),
        "unknown_prediction_ids": unknown_ids,
        "grid_predictions": grid_rows,
        "program_predictions": program_rows,
        "exact_at_1": round(exact1 / n, 4),
        "pass_at_2": round(pass2 / n, 4),
        "mean_cell_accuracy": round(cells / n, 4),
        "program_pass_train": program_train_pass,
        "program_pass_test": program_test_pass,
        "per_task": {t: {"n": s["n"], "exact1": s["exact1"], "pass2": s["pass2"]}
                     for t, s in sorted(per_task.items())},
        "families": len(families),
    }
    if missing:
        print(f"LOUD: {missing} probes had no prediction (scored 0)",
              file=sys.stderr, flush=True)
    if malformed:
        print(f"LOUD: {len(malformed)} malformed prediction(s): "
              f"{sorted(malformed)[:5]}", file=sys.stderr, flush=True)
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n")
    print(text)
    return 0 if not malformed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_make = sub.add_parser("make-eval", help="build probes + answer key")
    p_make.add_argument("--count", type=int, default=50)
    p_make.add_argument("--seed", type=int, default=20260724)
    p_make.add_argument("--holdout-frac", type=float, default=0.2)
    p_make.add_argument("--pool", default=str(DEFAULT_POOL))
    p_make.add_argument("--canonical", default=str(CANONICAL))
    p_make.add_argument("--out-probes", default="")
    p_make.add_argument("--out-answers", default="")
    p_make.set_defaults(fn=cmd_make_eval)

    p_score = sub.add_parser("score", help="score predictions vs the answer key")
    p_score.add_argument("--predictions", required=True)
    p_score.add_argument("--answers", required=True)
    p_score.add_argument("--out", default="")
    p_score.set_defaults(fn=cmd_score)

    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
