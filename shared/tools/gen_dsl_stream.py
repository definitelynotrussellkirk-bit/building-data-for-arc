#!/usr/bin/env python3
"""Streaming UNIQUE DSL data generator — never re-uses an example (no epochs).

Our data principle is always-unique: instead of 3 epochs over a fixed 19,813-row corpus, mint
FRESH validated instances from the 3,889 per-puzzle generators (via puzzle_generators.runner.
run_batch — each instance has its own seed → unique grids) and tokenize them to the closed DSL
vocab. Runs forever, appending shards to a pool dir; the trainer (train_dsl.py --stream-dir)
consumes each shard exactly once.

Emits all four modes from each fresh instance:
  <synth>   demos -> gold program        (RACKET OUTPUT)
  <predict> demos + test input -> output (ARRAY OUTPUT)
  <exec>    gold program + input -> output (reads RACKET, ARRAY OUTPUT)

  python3 scripts/gen_dsl_stream.py --pool data/coder_dsl/stream_pool --shard-size 2000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from dsl_v2 import build_core_vocab, to_tokens, grid_to_tokens, io_example_tokens  # noqa: E402
from puzzle_generators.runner import run_batch, _load_generator_module  # noqa: E402
from ground_facts import fed_facts, fact_tokens  # noqa: E402  fact-scratchpad (auto_scan/suggest)

_SC_CACHE: dict = {}


def _self_check_fn(task_id):
    """The generator's self_check (cached). None if it has none."""
    if task_id not in _SC_CACHE:
        try:
            _SC_CACHE[task_id] = getattr(_load_generator_module(task_id), "self_check", None)
        except Exception:
            _SC_CACHE[task_id] = None
    return _SC_CACHE[task_id]


def _instance_clean(task_id, inst) -> bool:
    """POOL GATE (reviewer rec): reject an instance if any of its grids fails the generator's
    self_check — so a generator defect can't poison the training data regardless of fix status."""
    fn = _self_check_fn(task_id)
    if fn is None:
        return True   # no self_check -> can't gate (counted separately)
    # self_check validates the GENERATOR'S INPUT grid (its invariants); the output is the rule's
    # result (different structure) — running it on outputs false-rejects valid data.
    for p in (inst.get("train") or []) + (inst.get("test") or []):
        grid = p.get("input")
        if grid is None:
            continue
        try:
            if fn(grid):          # non-empty error list -> defective input
                return False
        except Exception:
            return False
    return True


def gold_programs(canonical: Path) -> dict:
    """task_id -> gold program_solution (for <synth>/<exec> targets)."""
    out = {}
    for line in canonical.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = (r.get("program_solution") or "").strip()
        if p and r.get("task_id"):
            out[r["task_id"]] = p
    return out


import random  # noqa: E402
_RNG = random.Random(20260630)
_DIGITS = {str(d) for d in range(10)}


# A real model error is usually a plausible WRONG PRIMITIVE, not a typo — repairing these teaches
# SEMANTIC recovery (the verifiable generate->repair loop a small model relies on), not token fixes.
_PRIM_CONFUSIONS = {
    "flip-lr": "flip-ud", "flip-ud": "flip-lr",
    "rotate-cw": "rotate-ccw", "rotate-ccw": "rotate-cw", "rotate-180": "rotate-cw",
    "flip-cells-lr": "flip-cells-ud", "flip-cells-ud": "flip-cells-lr",
    "rotate-cells-cw": "rotate-cells-ccw", "rotate-cells-ccw": "rotate-cells-cw",
    "hconcat": "vconcat", "vconcat": "hconcat",
    "top-half": "bottom-half", "bottom-half": "top-half",
    "left-half": "right-half", "right-half": "left-half",
    "grid-and": "grid-or", "grid-or": "grid-and", "grid-xor": "grid-or",
    "objects": "objects-8", "objects-8": "objects", "objects-multicolor": "objects",
    "min": "max", "max": "min", "first": "second", "second": "first",
    "rows": "cols", "cols": "rows", "cell-up": "cell-down", "cell-down": "cell-up",
    "cell-left": "cell-right", "cell-right": "cell-left",
}


def corrupt_program(toks, rng):
    """Inject ONE plausible model-style error into a gold program so the <repair> target (the gold) is
    a real fix. Two SEMANTIC errors (wrong primitive, dropped sub-expression) are drawn twice as often
    as the four token-level typos, because the model's real failures are semantic, not typos. Returns
    None if it couldn't change the program."""
    if len(toks) < 4:
        return None
    t = list(toks)
    # weight the semantic corruptions (4,5) heavier than the typo ones (0-3)
    k = rng.choice([0, 1, 2, 3, 4, 4, 5, 5])
    if k == 0:                                   # wrong literal (color/int)
        ds = [i for i, x in enumerate(t) if x in _DIGITS]
        if not ds:
            return None
        i = rng.choice(ds); t[i] = str((int(t[i]) + 1 + rng.randrange(8)) % 10)
    elif k == 1:                                 # drop a token (structural break)
        del t[rng.randrange(len(t))]
    elif k == 2:                                 # duplicate a token
        i = rng.randrange(len(t)); t.insert(i, t[i])
    elif k == 3:                                 # swap adjacent
        i = rng.randrange(len(t) - 1); t[i], t[i + 1] = t[i + 1], t[i]
    elif k == 4:                                 # WRONG PRIMITIVE (semantic): swap an op for a confusable
        cands = [i for i, x in enumerate(t) if x in _PRIM_CONFUSIONS]
        if not cands:
            return None
        i = rng.choice(cands); t[i] = _PRIM_CONFUSIONS[t[i]]
    else:                                        # DROP A SUB-EXPRESSION (semantic/structural)
        opens = [i for i, x in enumerate(t) if x in ("(", "[")]
        if not opens:
            return None
        i = rng.choice(opens); close = {"(": ")", "[": "]"}[t[i]]; depth = 0; j = i
        while j < len(t):
            if t[j] in ("(", "["): depth += 1
            elif t[j] in (")", "]"):
                depth -= 1
                if depth == 0: break
            j += 1
        if j >= len(t) or not (2 <= j - i <= len(t) - 3):   # keep a proper inner sub-expr, not the whole thing
            return None
        del t[i:j + 1]
    return t if t != list(toks) else None


def _flip_cells(g, rng, frac_lo, frac_hi):
    h, w = len(g), len(g[0]); n = h * w
    k = max(1, int(round(rng.uniform(frac_lo, frac_hi) * n)))
    for (r, c) in rng.sample([(r, c) for r in range(h) for c in range(w)], min(k, n)):
        g[r][c] = rng.choice([v for v in range(10) if v != g[r][c]])


def corrupt_grid(grid, rng, frac_lo=0.12, frac_hi=0.55):
    """Produce a WRONG draft for <refine> to FIX. Mixes random noise with STRUCTURED corruptions
    that mimic REAL model mistakes — localized region errors, color-mapping slips, off-by-(dr,dc)
    position shifts, over-fills. Random flips alone taught the model only to undo noise (refine
    rescue measured 0% on real errors); structured corruption makes the abundant offline <refine>
    signal TRANSFER to the model's own structured first-prediction errors. Returns None if unchanged.
    (The closed-loop form — draft = the model's own real wrong output — is the exact complement.)"""
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    orig = [list(row) for row in grid]
    g = [list(row) for row in grid]
    colors = sorted({v for row in grid for v in row})

    def rect():
        r1 = rng.randint(0, h - 1); r2 = rng.randint(r1, h - 1)
        c1 = rng.randint(0, w - 1); c2 = rng.randint(c1, w - 1)
        return r1, c1, r2, c2

    mode = rng.choice(["flip", "flip", "partial", "region_fill", "color_swap", "region_shift"])
    if mode == "partial":                            # corrupt ONE region (model often gets most right)
        r1, c1, r2, c2 = rect()
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if rng.random() < 0.6:
                    g[r][c] = rng.choice([v for v in range(10) if v != g[r][c]])
    elif mode == "region_fill":                      # over-fill a region with one color
        r1, c1, r2, c2 = rect(); fill = rng.randint(0, 9)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                g[r][c] = fill
    elif mode == "color_swap" and len(colors) >= 2:  # wrong color mapping (swap two colors globally)
        a, b = rng.sample(colors, 2)
        for r in range(h):
            for c in range(w):
                if g[r][c] == a: g[r][c] = b
                elif g[r][c] == b: g[r][c] = a
    elif mode == "region_shift":                     # off-by-(dr,dc) position error
        dr, dc = rng.randint(-2, 2), rng.randint(-2, 2)
        if dr or dc:
            bg = orig[0][0]
            g = [[bg] * w for _ in range(h)]
            for r in range(h):
                for c in range(w):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        g[nr][nc] = orig[r][c]
    else:                                            # "flip" (+ any degenerate branch): random noise
        _flip_cells(g, rng, frac_lo, frac_hi)
    return g if g != orig else None


# DATA-MIX weights per mode. weight < 1 = keep-PROBABILITY (drop); weight >= 1 = REPLICATION factor.
# OWN-MISTAKES-ONLY (2026-07-07): the offline ARTIFICIAL <repair> (corrupt a gold program then fix it)
# and <refine> (corrupt a grid then fix it) are REMOVED (weight 0). Fixing SYNTHETIC errors taught
# recovery of fake mistakes and — replicated 3-4x — MEMORIZED the fixed program set (synth loss 0.04,
# comp 0). Corrections now come SOLELY from the in-loop shard_fb: the model's OWN real errors.
# Everything is <=1 (NO replication) so no row repeats -> capacity goes to BREADTH across all 3889
# generators, not re-memorizing. External data unaffected (EXT_MODE_WEIGHTS, all <=1).
# SYNTH-FOCUS (2026-07-07): <synth> (demos->program, the DEPLOYMENT task) is the priority. It's 1
# row/task, so to make it DOMINATE ours-dsl we keep it at 1.0 and thin the read modes hard (exec is
# per-demo-pair so it floods at even moderate weight). No replication (all <=1) so synth is majority
# by PROPORTION, not by repeating rows. predict kept slightly (it's the 13%-IID grid path).
DEFAULT_MODE_WEIGHTS = {"<synth>": 0.2, "<repair>": 0.0, "<exec>": 0.15,
                        "<predict>": 1.0, "<invert>": 0.3, "<pred_facts>": 0.1,
                        "<refine>": 0.0}   # EXEC-GROUNDING (2026-07-08, reviewer gpt55pro_2_481): <exec>
                        # (gold program + input -> output) is the HIGHEST-value objective — it teaches
                        # actual primitive semantics. Ramped 0.0 -> 0.15 keep-prob (exec is per-demo-pair
                        # so it floods; 0.15 lands a meaningful share without swamping the <predict> IID
                        # anchor — monitor the mix and tune toward the reviewer's exec 35-45% target).
                        # PREDICT-FOCUS (2026-07-07 pivot): predict is the 70% target —
                        # it's where the model has signal (13% IID; synth was 0/30). synth kept at 0.2 so
                        # the model doesn't forget it (we return to synth later). ours-dsl + concept are now
                        # predict-heavy; external RE-ARC/ARC-GEN are predict too (eval-like real-ARC).


def instance_rows(task_id, prog_toks, inst, core, max_prog_tokens=0, weights=None):
    """Turn one fresh instance (train/test pairs) into DSL rows for each mode. max_prog_tokens>0 is
    a CURRICULUM cap: skip the tasks where the model GENERATES a program (<synth>/<repair>) when the
    gold program exceeds the cap — so early training sees only short, terminating programs and learns
    to emit <eos> (fixes the rambling: gold programs are median ~388 tokens). Phase the cap up over
    training. <exec>/<predict>/<invert> are unaffected (the program is only read, not generated)."""
    rows = []
    train = inst.get("train") or []
    test = inst.get("test") or []
    if not train:
        return rows
    # prog_toks is None for EXTERNAL datasets (RE-ARC/ARC-GEN: input/output pairs, no gold Racket
    # program). Those emit only the program-FREE modes (<predict>/<invert>/<pred_facts>); the
    # program-dependent modes (<synth>/<exec>/<repair>) are skipped. Behavior with a real program
    # is byte-identical (the guards below are all no-ops when prog_toks is a list).
    has_prog = prog_toks is not None
    prog_ok = has_prog and ((max_prog_tokens <= 0) or (len(prog_toks) <= max_prog_tokens))  # curriculum gate
    demos = []
    for p in train:
        demos += io_example_tokens(p["input"], p["output"])
    # FACT-SCRATCHPAD: deterministic auto_scan/suggest grounding, FED right after the mode tag so the
    # model writes on top of verified perception (props+ratings). demo-derived -> no test leakage.
    ff = fed_facts(train)
    # <synth>: fresh demos -> gold program  (gated by the length curriculum)
    if prog_ok:
        rows.append({"task_id": task_id, "task_type": "<synth>",
                     "input_tokens": ["<synth>"] + ff + demos, "program_tokens": prog_toks})
    # <predict>: demos + each test input -> test output
    for p in test:
        if p.get("input") and p.get("output"):
            rows.append({"task_id": task_id, "task_type": "<predict>",
                         "input_tokens": ["<predict>"] + ff + demos + ["<io>"] + grid_to_tokens(p["input"]),
                         "program_tokens": grid_to_tokens(p["output"])})
    # <exec>: gold program + each demo input -> demo output (reads racket, emits array)
    if has_prog:
        for p in train:
            rows.append({"task_id": task_id, "task_type": "<exec>",
                         "input_tokens": ["<exec>"] + ff + prog_toks + ["<io>"] + grid_to_tokens(p["input"]),
                         "program_tokens": grid_to_tokens(p["output"])})
    # <repair>: demos + a CORRUPTED program -> the gold program (learn to fix broken programs)
    broken = corrupt_program(prog_toks, _RNG) if has_prog else None
    if broken is not None and prog_ok:                  # curriculum gate (generates a program)
        rows.append({"task_id": task_id, "task_type": "<repair>",
                     "input_tokens": ["<repair>"] + ff + demos + ["<io>"] + broken,
                     "program_tokens": prog_toks})
    # <invert>: demos + a TEST OUTPUT grid -> a valid TEST INPUT (reverse task; the held-out test
    # pair is not in the demos, so no leakage; the real input is one valid answer — may be non-unique
    # but is validity-checkable by running it through the gold program).
    for p in test:
        if p.get("input") and p.get("output"):
            rows.append({"task_id": task_id, "task_type": "<invert>",
                         "input_tokens": ["<invert>"] + ff + demos + ["<io>"] + grid_to_tokens(p["output"]),
                         "program_tokens": grid_to_tokens(p["input"])})
    # <refine> (DEEP SUPERVISION, grid form): demos + test input + a WRONG draft output -> the correct
    # output. Teaches the model to fix its own answer; at inference apply iteratively (predict -> feed
    # as draft -> re-predict). Control token is <repair> (in-vocab; the model disambiguates program- vs
    # grid-repair by content). Works for program-FREE data too (RE-ARC/ARC-GEN get refinement as well).
    for p in test:
        if p.get("input") and p.get("output"):
            draft = corrupt_grid(p["output"], _RNG)
            if draft is not None:
                rows.append({"task_id": task_id, "task_type": "<refine>",
                             "input_tokens": ["<repair>"] + ff + demos + ["<io>"]
                             + grid_to_tokens(p["input"]) + grid_to_tokens(draft),
                             "program_tokens": grid_to_tokens(p["output"])})
    # <pred_facts> (~10%): demos -> the property ratings. The small PERCEPTION aux (graded) so the
    # model learns to compute the facts itself, not only read the fed ones. Body = facts w/o delimiters.
    fbody = fact_tokens(train)
    if fbody and _RNG.random() < 0.10:
        rows.append({"task_id": task_id, "task_type": "<pred_facts>",
                     "input_tokens": ["<pred_facts>"] + demos, "program_tokens": fbody})
    # PROVENANCE (task #20): every row traces back to its generator instance {generator_version, seed,
    # sample_index} so a bad generator's rows are identifiable and the own-mistake loop can't silently fail.
    prov = {"gv": inst.get("generator_version", "?"), "seed": inst.get("seed"),
            "si": inst.get("sample_index", 0)}
    for r in rows:
        r["prov"] = prov
    # DATA-MIX subsample: keep each row with its mode's weight (rebalances toward <synth>).
    w = weights if weights is not None else DEFAULT_MODE_WEIGHTS
    out = []
    for r in rows:
        wt = w.get(r["task_type"], 1.0)
        n = int(wt) + (1 if _RNG.random() < (wt - int(wt)) else 0)   # keep-prob when wt<1; replicate when wt>=1
        out.extend([r] * n)
    return out



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

def _apply_blacklist(task_ids, canonical_path, *, who=""):
    """Filter out generators on data/derived/generator_blacklist.txt (hard quarantine). Shared by every
    producer so a known-bad generator (no-rule / rule-raises / malformed / zero-valid) cannot re-enter the
    live pool. Absent file => return unchanged. LOUD on any exclusion (never silent)."""
    bl_path = Path(canonical_path).resolve().parent.parent / "derived" / "generator_blacklist.txt"
    if not bl_path.exists():
        return task_ids
    blacklist = {ln.split("\t")[0].strip() for ln in bl_path.read_text().splitlines()
                 if ln.strip() and not ln.startswith("#")}
    if not blacklist:
        return task_ids
    kept = [t for t in task_ids if t not in blacklist]
    n_excl = len(task_ids) - len(kept)
    if n_excl:
        print(f"QUARANTINE[{who}]: excluded {n_excl} blacklisted generators "
              f"({len(kept)} remain) per {bl_path}", flush=True)
    return kept


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=str(ROOT / "data/coder_dsl/stream_pool"))
    ap.add_argument("--canonical", default=str(ROOT / "data/canonical/puzzles.jsonl"))
    ap.add_argument("--shard-size", type=int, default=2000, help="rows per shard")
    ap.add_argument("--per-task", type=int, default=8, help="fresh instances per task per visit")
    ap.add_argument("--max-shards", type=int, default=0, help="0 = run forever")
    ap.add_argument("--max-pool-shards", type=int, default=40,
                    help="backpressure: pause if the pool has this many unconsumed shards")
    ap.add_argument("--max-prog-tokens", type=int, default=0,
                    help="CURRICULUM: skip <synth>/<repair> rows whose gold program exceeds N tokens "
                         "(0=off). Start small (~120) so the model learns to terminate; phase up.")
    ap.add_argument("--mode-weights", default="",
                    help="DATA-MIX keep-probs, e.g. '<synth>=1.0,<exec>=0.45,<predict>=0.7'. "
                         "Empty = DEFAULT_MODE_WEIGHTS (synth-shifted).")
    ap.add_argument("--seed-start", type=int, default=0,
                    help="first generator seed for this run; use a disjoint range for every durable pool")
    ap.add_argument("--rng-seed", type=int, default=20260630,
                    help="seed for task tie-breaking, row thinning, and within-shard shuffle")
    ap.add_argument("--generation-id", default="",
                    help="immutable dated generation ID recorded on every row and manifest entry")
    ap.add_argument("--curriculum-stage", default="",
                    help="human-readable mastery stage recorded on every row and manifest entry")
    ap.add_argument("--generation-created-utc", default="",
                    help="ISO-8601 creation time for the generation (defaults to process start)")
    ap.add_argument("--source-snapshot", default="",
                    help="content fingerprint for the frozen generator source snapshot")
    ap.add_argument("--manifest", default="",
                    help="append one dated/hash-verified JSON record per completed shard")
    ap.add_argument("--generator-weights", default="",
                    help="frozen generator_weights.json for this stage (default: live repository file)")
    ap.add_argument("--task-ids", default="",
                    help="optional frozen one-task-id-per-line allowlist for this stage")
    a = ap.parse_args()
    _RNG.seed(a.rng_seed)
    weights = dict(DEFAULT_MODE_WEIGHTS)
    for kv in a.mode_weights.split(","):                 # override defaults from the CLI
        if "=" in kv:
            k, v = kv.split("=", 1); weights[k.strip()] = float(v)
    print(f"mode-weights: {weights}", flush=True)

    pool = Path(a.pool); pool.mkdir(parents=True, exist_ok=True)
    _toks, core = build_core_vocab(0)
    gold = gold_programs(Path(a.canonical))
    prog_tok_cache = {}
    task_ids = list(gold.keys())
    if a.task_ids:
        frozen_ids = {line.strip() for line in Path(a.task_ids).read_text().splitlines()
                      if line.strip() and not line.startswith("#")}
        task_ids = [task_id for task_id in task_ids if task_id in frozen_ids]
        print(f"CURRICULUM: frozen allowlist keeps {len(task_ids)}/{len(gold)} program tasks", flush=True)
    # HARD QUARANTINE (reviewers gpt55pro 20260707 + (10), unanimous "biggest missing lever"): exclude
    # blacklisted generators (execute.no_rule / rule_raised / malformed / zero-valid) from the LIVE pool.
    # generator_stats.py writes generator_blacklist.txt; the producer treats it as a first-class input so a
    # known-bad generator cannot silently re-enter training. Absent file => no quarantine (graceful).
    task_ids = _apply_blacklist(task_ids, Path(a.canonical), who="ours-dsl")
    # DEFICIT ROUND-ROBIN by ROWS (task #19): each generator's target share of EMITTED ROWS is
    # proportional to its train_weight (generator_weights.json, strata from generator_stats). Uniform
    # task-shuffle gave row share ∝ rows-per-pick (a chatty generator got 2x the training diet); deficit
    # picking self-corrects that AND guarantees rare-but-valuable generators their floor: a never-picked
    # generator's deficit grows every pick until it wins. Weights file absent -> uniform (LOUD).
    gw_path = (Path(a.generator_weights) if a.generator_weights else
               Path(__file__).resolve().parent.parent / "data/derived/generator_weights.json")
    try:
        _gw = json.loads(gw_path.read_text())
    except OSError:
        _gw = {}
        print(f"LOUD: {gw_path} missing — deficit sampler falls back to UNIFORM weights", flush=True)
    task_w = {t: float(_gw.get(t, 1.0)) for t in task_ids}
    task_ids = [t for t in task_ids if task_w[t] > 0]      # weight-0 (broken) never sampled
    if len(task_w) != len(task_ids):
        print(f"QUARANTINE[weights]: {len(task_w) - len(task_ids)} zero-weight generators excluded "
              f"({len(task_ids)} remain)", flush=True)
    _w_sum = sum(task_w[t] for t in task_ids)
    emitted = {t: 0 for t in task_ids}                     # ROWS emitted per generator this run
    emitted_total = 0

    def _next_deficit_tid():
        # deficit_i = target share of the diet so far - actually served; argmax wins. Tiny seeded
        # jitter breaks cold-start ties randomly instead of alphabetically.
        return max(task_ids, key=lambda t: (task_w[t] / _w_sum) * (emitted_total + 1)
                   - emitted[t] + _RNG.random() * 1e-6)

    print(f"streaming pool -> {pool} | {len(task_ids)} tasks | shard={a.shard_size}", flush=True)
    buf = []
    shard_n = _next_shard_n(pool, "shard_")
    made = 0; gated = 0
    seed_ctr = a.seed_start
    generation_created = (a.generation_created_utc or
                          datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    generation_meta = None
    if a.generation_id or a.curriculum_stage or a.source_snapshot:
        generation_meta = {
            "id": a.generation_id,
            "stage": a.curriculum_stage,
            "created_utc": generation_created,
            "source": a.source_snapshot,
        }
    manifest_path = Path(a.manifest) if a.manifest else None
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
    skipped = 0
    while True:
        # backpressure: don't outrun the trainer
        unconsumed = len(list(pool.glob("shard_[0-9]*.jsonl")))   # own prefix only
        if a.max_pool_shards and unconsumed >= a.max_pool_shards:
            time.sleep(5); continue
        tid = _next_deficit_tid()
        if tid not in gold:
            emitted[tid] += 1           # never earns rows -> bump so the deficit loop can't spin on it
            continue
        if tid not in prog_tok_cache:
            prog_tok_cache[tid] = to_tokens(gold[tid], core)
        try:
            insts = run_batch(tid, a.per_task, seed_start=seed_ctr)
        except Exception as e:
            skipped += 1
            emitted[tid] += a.per_task  # charge the failure so a crashing generator can't spin the loop
            emitted_total += a.per_task
            if skipped <= 5 or skipped % 200 == 0:
                print(f"LOUD: run_batch failed for {tid}: {str(e)[:80]} (skipped={skipped})", flush=True)
            seed_ctr += a.per_task
            continue
        seed_ctr += a.per_task
        _before = len(buf)
        for inst in insts:
            if not _instance_clean(tid, inst):      # POOL GATE: drop self_check failures
                gated += 1
                continue
            new_rows = instance_rows(tid, prog_tok_cache[tid], inst, core,
                                     a.max_prog_tokens, weights)
            if generation_meta is not None:
                for row in new_rows:
                    row["generation"] = generation_meta
            buf.extend(new_rows)
        _got = len(buf) - _before
        emitted[tid] += max(1, _got)    # by ROWS; min 1 so a zero-row pick still rotates
        emitted_total += max(1, _got)
        if len(buf) >= a.shard_size:
            _RNG.shuffle(buf)           # PROPER SAMPLING: mix the ~40 tasks accumulated in buf so each
        while len(buf) >= a.shard_size: # shard is a random task MIX, not consecutive per-task clusters
            shard = pool / f"shard_{shard_n:06d}.jsonl"
            tmp = shard.with_suffix(".tmp")
            shard_rows = buf[:a.shard_size]
            with tmp.open("w") as f:
                for row in shard_rows:
                    f.write(json.dumps(row) + "\n")
            tmp.rename(shard)            # atomic: trainer never reads a half-written shard
            if manifest_path:
                digest = hashlib.sha256()
                with shard.open("rb") as sf:
                    for chunk in iter(lambda: sf.read(1024 * 1024), b""):
                        digest.update(chunk)
                seeds = [row.get("prov", {}).get("seed") for row in shard_rows]
                seeds = [seed for seed in seeds if isinstance(seed, int)]
                record = {
                    "generation_id": a.generation_id,
                    "curriculum_stage": a.curriculum_stage,
                    "generation_created_utc": generation_created,
                    "shard_created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "source_snapshot": a.source_snapshot,
                    "file": shard.name,
                    "rows": len(shard_rows),
                    "bytes": shard.stat().st_size,
                    "sha256": digest.hexdigest(),
                    "seed_min": min(seeds) if seeds else None,
                    "seed_max": max(seeds) if seeds else None,
                    "task_count": len({row.get("task_id") for row in shard_rows}),
                    "task_types": dict(sorted(Counter(row.get("task_type") for row in shard_rows).items())),
                }
                with manifest_path.open("a") as mf:
                    mf.write(json.dumps(record, sort_keys=True) + "\n")
                    mf.flush()
            buf = buf[a.shard_size:]
            shard_n += 1; made += 1
            print(f"wrote {shard.name} (total made={made}, gated(self_check)={gated}, skipped_tasks={skipped})", flush=True)
            if made % 20 == 0 and emitted_total:   # SHARE LOG (task #19): deficit-sampler health
                served = sorted(task_ids, key=lambda t: emitted[t] - (task_w[t] / _w_sum) * emitted_total)
                lo = [(t, emitted[t]) for t in served[:3]]
                hi = [(t, emitted[t]) for t in served[-3:]]
                n_cold = sum(1 for t in task_ids if emitted[t] == 0)
                print(f"SHARES: rows={emitted_total} cold={n_cold}/{len(task_ids)} "
                      f"under={lo} over={hi}", flush=True)
            if a.max_shards and made >= a.max_shards:
                return 0


if __name__ == "__main__":
    raise SystemExit(main())
