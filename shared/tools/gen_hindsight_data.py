#!/usr/bin/env python3
"""Hindsight / mutation data generator — research recommendation #1 (CodeIt-style, the highest-
leverage fix for "grammar-not-semantics"). MUTATE a gold program, EXECUTE the mutation through the
Racket verifier on fresh demo inputs, and if it runs, emit the (demos-with-its-ACTUAL-outputs ->
mutated program) pair as a fully-valid <synth> training row (+ <exec> rows). Because the mutated
program genuinely PRODUCES those outputs, it's a correct (task, program) example — so every
executable mutation becomes dense semantic signal teaching the model what programs ACTUALLY DO, not
just gold-program syntax. Decoupled from the fast streamer (it runs Racket per mutation).

  python3 scripts/gen_hindsight_data.py --pool data/coder_dsl/stream_pool --shard-size 1000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from dsl_v2 import build_core_vocab, to_tokens, from_tokens, grid_to_tokens, io_example_tokens  # noqa: E402
from puzzle_generators.runner import run_batch  # noqa: E402
from gen_dsl_stream import corrupt_program, gold_programs, _RNG  # noqa: E402
from ground_facts import fed_facts  # noqa: E402  fact-scratchpad on the hindsight demos too
from coder_synth_verify import _grids_equal  # noqa: E402  robust str/int grid compare for the trace
from racket_style_check import check_program  # noqa: E402  never train on HARD-violating Racket


def _diff_mask(a, b):
    """A binary grid (a's shape): 1 where a and b differ, 0 where identical. Shape mismatch = all-1
    (maximally different). Dense per-cell target — the count is just its sum, so the mask subsumes it."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return [[1] * len(a[0]) for _ in a]
    return [[1 if x != y else 0 for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def _valid_grid(g) -> bool:
    if not (isinstance(g, list) and g and all(isinstance(r, list) and r for r in g)):
        return False
    if len({len(r) for r in g}) != 1 or len(g) > 30 or len(g[0]) > 30:
        return False
    return all(isinstance(c, int) and 0 <= c <= 9 for r in g for c in r)   # ints 0-9 only


def hindsight_rows(task_id, prog, inst, core, ver, n_mut):
    """Up to n_mut mutations of the gold program, executed on the instance's demos; the ones that
    run become valid <synth>+<exec> hindsight rows (demos with the mutation's REAL output)."""
    train = inst.get("train") or []
    if not train:
        return [], 0, 0
    try:
        base = to_tokens(prog, core)
    except Exception:
        return [], 0, 0
    rows, tried, kept = [], 0, 0
    for _ in range(n_mut):
        try:                                               # one bad mutation must not kill the run
            broken = corrupt_program(base, _RNG)
            if broken is None:
                continue
            tried += 1
            mutated = from_tokens(broken)
            if check_program(mutated)["hard"]:      # GATE: never feed HARD-violating Racket anywhere
                continue
            outs, ok = [], True
            for p in train:
                if not _valid_grid(p.get("input")):        # demo input must be a clean int grid too
                    ok = False; break
                try:
                    o = ver.apply(mutated, p["input"])
                except Exception:
                    ok = False; break
                if not _valid_grid(o):
                    ok = False; break
                outs.append(o)
            if not ok:
                continue
            kept += 1
            demos = []
            for p, o in zip(train, outs):
                demos += io_example_tokens(p["input"], o)  # the mutation's ACTUAL output (hindsight)
            ff = fed_facts([{"input": p["input"], "output": o} for p, o in zip(train, outs)])
            rows.append({"task_id": task_id, "task_type": "<synth>", "hindsight": True,
                         "input_tokens": ["<synth>"] + ff + demos, "program_tokens": broken})
            for p, o in zip(train, outs):
                rows.append({"task_id": task_id, "task_type": "<exec>", "hindsight": True,
                             "input_tokens": ["<exec>"] + ff + broken + ["<io>"] + grid_to_tokens(p["input"]),
                             "program_tokens": grid_to_tokens(o)})
            # <repair> REMOVED (2026-07-07): it was an ARTIFICIAL, mutation-induced repair. Per the
            # OWN-MISTAKES-ONLY rule, ALL correction data comes solely from the in-loop shard_fb
            # (the model's REAL decode errors) — never from synthetic corruptions.
            # <equiv>: predict the DIFF-MASK grid (1 where mutated program's output differs from gold
            # on this input, 0 where identical). Dense per-cell CE — same loss as <exec>/<predict>, and
            # subsumes the 0..900 count (= its sum). Sometimes all-0 (equivalent), often not.
            for p, o in zip(train, outs):
                rows.append({"task_id": task_id, "task_type": "<equiv>", "hindsight": True,
                             "input_tokens": ["<equiv>"] + base + ["<vs>"] + broken + ["<io>"]
                                             + grid_to_tokens(p["input"]),
                             "program_tokens": grid_to_tokens(_diff_mask(p["output"], o))})
        except Exception:
            continue
    return rows, tried, kept



def _next_shard_n(pool, prefix):
    """Collision-proof shard numbering: continue after the max existing index
    across the pool AND consumed/ (a fresh launch used to restart at 0 and
    silently OVERWRITE unconsumed shards)."""
    import re
    mx = -1
    for d in (pool, pool / "consumed"):
        if d.is_dir():
            for f in d.glob(prefix + "*.jsonl"):
                m = re.search(r"(\d+)\.jsonl$", f.name)
                if m:
                    mx = max(mx, int(m.group(1)))
    return mx + 1

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=str(ROOT / "data/coder_dsl/stream_pool"))
    ap.add_argument("--canonical", default=str(ROOT / "data/canonical/puzzles.jsonl"))
    ap.add_argument("--shard-size", type=int, default=1000)
    ap.add_argument("--per-task", type=int, default=2, help="fresh instances per task per visit")
    ap.add_argument("--n-mut", type=int, default=4, help="mutations attempted per instance")
    ap.add_argument("--max-pool-shards", type=int, default=40)
    ap.add_argument("--max-shards", type=int, default=0)
    a = ap.parse_args()
    from coder_synth_verify import ProgramVerifier
    ver = ProgramVerifier()
    _toks, core = build_core_vocab(0)
    gold = gold_programs(Path(a.canonical))
    pool = Path(a.pool); pool.mkdir(parents=True, exist_ok=True)
    import itertools
    order = itertools.cycle(list(gold.keys()))
    print(f"HINDSIGHT generator -> {pool} | {len(gold)} tasks", flush=True)
    buf, shard_n, made, seed_ctr, tried_t, kept_t = [], _next_shard_n(pool, "shard_h"), 0, 0, 0, 0
    while True:
        if a.max_pool_shards and len(list(pool.glob("shard_h*.jsonl"))) >= a.max_pool_shards:
            time.sleep(5); continue
        tid = next(order)
        if tid not in gold:
            continue
        try:
            insts = run_batch(tid, a.per_task, seed_start=seed_ctr)
        except Exception:
            seed_ctr += a.per_task; continue
        seed_ctr += a.per_task
        for inst in insts:
            r, tr, kp = hindsight_rows(tid, gold[tid], inst, core, ver, a.n_mut)
            buf += r; tried_t += tr; kept_t += kp
        while len(buf) >= a.shard_size:
            shard = pool / f"hind_{shard_n:06d}.jsonl"; tmp = shard.with_suffix(".tmp")
            with tmp.open("w") as f:
                for row in buf[:a.shard_size]:
                    f.write(json.dumps(row) + "\n")
            tmp.rename(pool / f"shard_h{shard_n:06d}.jsonl")     # shard_* so the trainer consumes it
            buf = buf[a.shard_size:]; shard_n += 1; made += 1
            print(f"wrote hindsight shard {made} (mutations kept {kept_t}/{tried_t} executed)", flush=True)
            if a.max_shards and made >= a.max_shards:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
