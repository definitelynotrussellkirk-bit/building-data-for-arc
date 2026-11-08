#!/usr/bin/env python3
"""Distribution-space audit: are our generated data representative of the target?

Compares three corpora across measurable task-distribution axes:
  - OURS   = the live Qwen pool (actual generated grids the trainer streams)
  - RE-ARC = the ARC-1 procedural distribution (reference)
  - EVAL   = the 120 public eval tasks (the contest TARGET we must match)

Axes: input area, output area, size-relation, #components (4-conn, bg=0),
palette size. Flags axes where OURS diverges from EVAL.
"""
from __future__ import annotations
import json, glob, math, random, sys, types
from collections import deque, Counter
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parents[1]


def comps(g, bg=0):
    h, w = len(g), len(g[0]); seen = [[0]*w for _ in range(h)]; n = 0
    for r in range(h):
        for c in range(w):
            if g[r][c] != bg and not seen[r][c]:
                n += 1; dq = deque([(r, c)]); seen[r][c] = 1
                while dq:
                    y, x = dq.popleft()
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = y+dy, x+dx
                        if 0<=ny<h and 0<=nx<w and not seen[ny][nx] and g[ny][nx] != bg:
                            seen[ny][nx] = 1; dq.append((ny, nx))
    return n

def pal(g): return len({v for row in g for v in row})
def area(g): return len(g)*len(g[0])
def rel(i, o):
    ih, iw = len(i), len(i[0]); oh, ow = len(o), len(o[0])
    if (ih,iw)==(oh,ow): return "same"
    if oh<=ih and ow<=iw: return "shrink"
    if oh>=ih and ow>=iw: return "grow"
    return "mixed"


def modal_bg(g):
    """Most common color — a SEMANTIC background proxy. Many real eval tasks use a
    nonzero background, so measuring only `v != 0` confounds a dense colored
    background with actual object occupancy."""
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def density(g, bg=0):
    a = area(g)
    return sum(1 for row in g for v in row if v != bg) / a if a else 0.0


# ---- structural metrics (round-34: the 6 marginals are hygiene, not a difficulty proxy;
#      these capture STRUCTURE the model must actually reason about — symmetry, object size,
#      shape aspect — so we can see gen-vs-eval gaps the marginals miss). --------------------
def symmetries(g):
    """Which mirror symmetries the grid satisfies: lr, ud, 180-rot, diagonal (square only)."""
    h, w = len(g), len(g[0])
    lr = all(g[r][c] == g[r][w - 1 - c] for r in range(h) for c in range(w))
    ud = all(g[r][c] == g[h - 1 - r][c] for r in range(h) for c in range(w))
    r180 = all(g[r][c] == g[h - 1 - r][w - 1 - c] for r in range(h) for c in range(w))
    diag = (h == w) and all(g[r][c] == g[c][r] for r in range(h) for c in range(w))
    return lr, ud, r180, diag


def _components(g, bg):
    """4-conn non-bg components as lists of cells."""
    h, w = len(g), len(g[0]); seen = [[0] * w for _ in range(h)]; out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != bg and not seen[r][c]:
                cells = []; dq = deque([(r, c)]); seen[r][c] = 1
                while dq:
                    y, x = dq.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] != bg:
                            seen[ny][nx] = 1; dq.append((ny, nx))
                out.append(cells)
    return out


def comp_size_median(g, bg):
    sizes = [len(c) for c in _components(g, bg)]
    return median(sizes) if sizes else 0


def largest_bbox_aspect(g, bg):
    """max(h,w)/min(h,w) of the LARGEST non-bg component's bbox (1.0 = square/none)."""
    comps_ = _components(g, bg)
    if not comps_:
        return 1.0
    cells = max(comps_, key=len)
    rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
    bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
    return max(bh, bw) / min(bh, bw)


def feats(pairs):
    """pairs = list of (input, output). Return per-axis sample lists. Includes both
    the legacy bg=0 axes (in_comp, density_nonzero) AND modal-background-aware axes
    (in_comp_modal, density_nonmodal, zero_fraction, modal_bg_nonzero) so the
    dashboard can separate semantic occupancy from background-color convention."""
    f = {
        "in_area": [], "out_area": [], "in_comp": [], "in_comp_modal": [],
        "in_pal": [], "rel": [], "density_nonzero": [], "density_nonmodal": [],
        "zero_fraction": [], "modal_bg_nonzero": [],
        # structural (round-34)
        "out_sym_any": [], "out_sym_lr": [], "out_sym_ud": [], "out_sym_180": [],
        "in_obj_size_med": [], "in_bbox_aspect": [],
    }
    for i, o in pairs:
        bg = modal_bg(i)
        f["in_area"].append(area(i)); f["out_area"].append(area(o))
        f["in_comp"].append(comps(i, 0)); f["in_comp_modal"].append(comps(i, bg))
        f["in_pal"].append(pal(i)); f["rel"].append(rel(i, o))
        f["density_nonzero"].append(density(i, 0))
        f["zero_fraction"].append(1.0 - f["density_nonzero"][-1])
        f["density_nonmodal"].append(density(i, bg))
        f["modal_bg_nonzero"].append(1.0 if bg != 0 else 0.0)
        # structural: symmetry of the OUTPUT (completion/tiling tasks emit symmetric grids),
        # object-size + shape-aspect of the INPUT (what the model must segment/reason over).
        obg = modal_bg(o)
        lr, ud, r180, diag = symmetries(o)
        f["out_sym_lr"].append(1.0 if lr else 0.0)
        f["out_sym_ud"].append(1.0 if ud else 0.0)
        f["out_sym_180"].append(1.0 if r180 else 0.0)
        f["out_sym_any"].append(1.0 if (lr or ud or r180 or diag) else 0.0)
        f["in_obj_size_med"].append(comp_size_median(i, bg))
        f["in_bbox_aspect"].append(largest_bbox_aspect(i, bg))
    return f


def _parse_grid(s):
    return [[int(ch) for ch in line] for line in s.strip().split("\n") if line]

LIVE_POOL_GLOB = "/mnt/ai/scratch/qwen_run/pool/gen_*/*.jsonl"
BUNDLE_POOL_SAMPLE_GLOB = str(REPO / "data" / "pool_sample" / "*.jsonl")


def resolve_ours_shards(glob_pat=None):
    """Return (shards, source_glob, is_bundle_fallback).

    The bundled pool_sample is intentionally small and review-friendly; it is NOT
    the same thing as the natural live training mix. Keeping this explicit
    prevents an off-box fallback run from being logged as a live trajectory point.
    """
    requested = glob_pat or LIVE_POOL_GLOB
    shards = sorted(glob.glob(requested))
    if shards:
        return shards, requested, False
    if requested == LIVE_POOL_GLOB:
        shards = sorted(glob.glob(BUNDLE_POOL_SAMPLE_GLOB))
        if shards:
            return shards, BUNDLE_POOL_SAMPLE_GLOB, True
    return [], requested, False


def load_ours(n=2500, glob_pat=None):
    """Sample input/output pairs from pool rows (messages = u/a turns).

    Defaults to the live /mnt/ai pool, but when that isn't mounted (e.g. a review
    bundle on another machine) falls back to the bundled data/pool_sample/*.jsonl
    so the audit is SELF-CONTAINED and reproducible off-box.

    The sample is a deterministic RESERVOIR across ALL matching shards. Reading
    whole shards until n pairs are collected (the old behavior) made the sample a
    shard PREFIX — and since one per-puzzle shard is ~5000 rows, `--n-ours 4000`
    could measure a single large shard, making the reported "natural training
    proportion" depend on which filename got shuffled first. Reservoir replacement
    gives a uniform sample over pairs regardless of shard size."""
    shards, source_glob, is_fallback = resolve_ours_shards(glob_pat)
    if is_fallback:
        print(f"WARNING: live pool absent; using bundled pool_sample fallback {source_glob} "
              f"({len(shards)} shards), not the natural live training mix", file=sys.stderr)
    pairs, rng, seen = [], random.Random(0), 0
    rng.shuffle(shards)
    for sh in shards:
        try:
            fh = open(sh)
        except OSError:
            continue
        with fh:
            for ln in fh:
                try:
                    row = json.loads(ln); ms = row["messages"]
                    for k in range(0, len(ms) - 1, 2):
                        i = _parse_grid(ms[k]["content"]); o = _parse_grid(ms[k + 1]["content"])
                        if not (i and o):
                            continue
                        seen += 1
                        if len(pairs) < n:
                            pairs.append((i, o))
                        else:
                            j = rng.randrange(seen)   # reservoir: replace w.p. n/seen
                            if j < n:
                                pairs[j] = (i, o)
                except Exception:
                    continue
    return pairs

def load_rearc(per_key=2):
    sys.path.insert(0, str(REPO))
    from scripts.integrate_re_arc import load_re_arc, sample_bank
    gens, vers = load_re_arc("~/re-arc")
    pairs, rng = [], random.Random(0)
    for key in sorted(gens):
        if key not in vers: continue
        bank = sample_bank(gens[key], vers[key], per_key, rng)
        for ex in bank: pairs.append((ex["input"], ex["output"]))
    return pairs

def load_eval(include_test=True):
    """Eval target pairs: train demos, and (by default) the held-out test/query pairs.

    The distribution target is the grids the model must SOLVE, not only the demo
    grids — and eval test inputs skew larger, so train-only under-counts the real
    size target. The solutions file is bundled, so pair each test input with its
    official output (tolerating a debug challenge file that already inlines it).
    Pass include_test=False (--eval-target train) to reproduce the historical
    demo-only trajectory snapshots."""
    ch = json.load(open(REPO/"data/raw/arc-agi_evaluation_challenges.json"))
    sol_path = REPO/"data/raw/arc-agi_evaluation_solutions.json"
    sols = json.load(open(sol_path)) if include_test and sol_path.exists() else {}
    pairs = []
    for tid, t in ch.items():
        for p in t["train"]:
            pairs.append((p["input"], p["output"]))
        if not include_test:
            continue
        for qi, test in enumerate(t.get("test", [])):
            outs = sols.get(tid, [])
            if qi < len(outs):
                pairs.append((test["input"], outs[qi]))
            elif "output" in test:          # tolerant for local/debug challenge files
                pairs.append((test["input"], test["output"]))
    return pairs


def summary(name, f):
    n = len(f["in_area"])
    def q(xs, p):
        xs = sorted(xs)
        return xs[max(0, min(len(xs) - 1, math.ceil(p * len(xs)) - 1))] if xs else 0
    rc = Counter(f["rel"])
    print(f"\n[{name}]  n_pairs={n}")
    print(f"  in_area   mean={mean(f['in_area']):6.0f} med={median(f['in_area']):5.0f} p90={q(f['in_area'],.9):5.0f}")
    print(f"  out_area  mean={mean(f['out_area']):6.0f} med={median(f['out_area']):5.0f}")
    print(f"  in_comps  mean={mean(f['in_comp']):6.1f} med={median(f['in_comp']):5.0f} p90={q(f['in_comp'],.9):5.0f}  (bg=0)")
    print(f"  in_comps  mean={mean(f['in_comp_modal']):6.1f} med={median(f['in_comp_modal']):5.0f} p90={q(f['in_comp_modal'],.9):5.0f}  (bg=modal)")
    print(f"  in_pal    mean={mean(f['in_pal']):6.1f} med={median(f['in_pal']):5.0f}")
    # modal-bg-aware axes (round-1 M2): don't read the legacy bg=0 density as occupancy
    print(f"  density   zero-bg={mean(f['density_nonzero']):.3f}  non-modal={mean(f['density_nonmodal']):.3f}  "
          f"zero-frac={mean(f['zero_fraction']):.3f}  modal-bg-nonzero={100*mean(f['modal_bg_nonzero']):.0f}%")
    print(f"  size-rel  " + " ".join(f"{k}={100*v/n:.0f}%" for k,v in rc.most_common()))
    # structural axes (round-34) — the reasoning shape the 6 marginals miss
    print(f"  STRUCTURE out-symmetric any={100*mean(f['out_sym_any']):.0f}%  "
          f"lr={100*mean(f['out_sym_lr']):.0f}% ud={100*mean(f['out_sym_ud']):.0f}% 180={100*mean(f['out_sym_180']):.0f}%")
    print(f"            in-obj-size med={mean(f['in_obj_size_med']):.1f}  "
          f"in-bbox-aspect mean={mean(f['in_bbox_aspect']):.2f} (largest comp h:w)")
    return {"in_area_med": median(f["in_area"]), "in_comp_mean": mean(f["in_comp"]),
            "out_sym_any": mean(f["out_sym_any"]), "out_sym_lr": mean(f["out_sym_lr"]),
            "out_sym_ud": mean(f["out_sym_ud"]), "out_sym_180": mean(f["out_sym_180"]),
            "in_obj_size_med": mean(f["in_obj_size_med"]), "in_bbox_aspect": mean(f["in_bbox_aspect"]),
            "in_comp_modal_mean": mean(f["in_comp_modal"]),
            "in_pal_mean": mean(f["in_pal"]),
            "density_nonzero": mean(f["density_nonzero"]),
            "density_nonmodal": mean(f["density_nonmodal"]),
            "zero_fraction": mean(f["zero_fraction"]),
            "modal_bg_nonzero": mean(f["modal_bg_nonzero"]),
            "rel": {k: v/n for k,v in rc.items()}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours-glob", default=None,
                    help="pool JSONL glob; defaults to live /mnt/ai with a bundled pool_sample fallback")
    ap.add_argument("--skip-rearc", action="store_true",
                    help="skip the RE-ARC reference (needs ~/re-arc; absent off-box)")
    ap.add_argument("--eval-target", choices=["train", "full"], default="full",
                    help="train = historical eval demo/train pairs only; "
                         "full = demos plus official eval query/test solutions")
    ap.add_argument("--n-ours", type=int, default=2500,
                    help="number of OURS input/output pairs to reservoir-sample from the pool")
    a = ap.parse_args()
    print(f"loading EVAL (target={a.eval_target}) ..."); ev = feats(load_eval(include_test=(a.eval_target == "full")))
    print(f"loading OURS (pool, n={a.n_ours}) ...");   ou = feats(load_ours(n=a.n_ours, glob_pat=a.ours_glob))
    se = summary("EVAL  (TARGET)", ev)
    so = summary("OURS  (pool)", ou)
    # RE-ARC needs ~/re-arc, which a review bundle on another box won't have — make it optional.
    if not a.skip_rearc:
        try:
            print("loading RE-ARC ..."); ra = feats(load_rearc())
            summary("RE-ARC", ra)
        except Exception as e:
            print(f"  (RE-ARC skipped: {type(e).__name__}: {str(e)[:80]}; pass --skip-rearc to silence)")
    print("\n=== OURS vs EVAL gaps (target - ours) ===")
    print(f"  in_area  median: eval={se['in_area_med']:.0f}  ours={so['in_area_med']:.0f}  "
          f"-> ours {'SMALLER' if so['in_area_med']<se['in_area_med'] else 'ok'}")
    print(f"  in_comps mean (bg=0 legacy):     eval={se['in_comp_mean']:.1f}  ours={so['in_comp_mean']:.1f}")
    print(f"  in_comps mean (bg=modal target): eval={se['in_comp_modal_mean']:.1f}  ours={so['in_comp_modal_mean']:.1f}  "
          f"-> ours {'SPARSER' if so['in_comp_modal_mean']<se['in_comp_modal_mean'] else 'ok'}")
    print(f"  density non-modal: eval={se['density_nonmodal']:.3f}  ours={so['density_nonmodal']:.3f}")
    print(f"  modal-bg nonzero:  eval={100*se['modal_bg_nonzero']:.0f}%  ours={100*so['modal_bg_nonzero']:.0f}%")
    print(f"  zero fraction:     eval={se['zero_fraction']:.3f}  ours={so['zero_fraction']:.3f}")
    print(f"  in_pal   mean:     eval={se['in_pal_mean']:.1f}  ours={so['in_pal_mean']:.1f}")
    for k in ("same","grow","shrink","mixed"):
        e=se['rel'].get(k,0); o=so['rel'].get(k,0)
        print(f"  rel {k:6s}: eval={100*e:.0f}%  ours={100*o:.0f}%  {'<-- under' if o<e-0.05 else ''}")
