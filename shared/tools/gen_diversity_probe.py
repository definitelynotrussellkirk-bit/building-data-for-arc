#!/usr/bin/env python3
"""Sample each generator across seeds and measure how much its (input, output) pairs
actually vary. Low intra-generator diversity = the model sees near-duplicate examples
for that task -> overfit / wasted capacity. Reports per-generator diversity and flags
the worst offenders, plus *why* (shape-locked, palette-locked, content-duplicating).

Usage:
  python3 scripts/gen_diversity_probe.py --n-tasks 40 --episodes 6 --seed 1
  python3 scripts/gen_diversity_probe.py --task-id 0934a4d8 --episodes 12
  python3 scripts/gen_diversity_probe.py --task-id 0934a4d8 --episodes 12 --no-append
  python3 scripts/gen_diversity_probe.py --task-id 0934a4d8 --out checks/diversity.jsonl
"""
from __future__ import annotations
import argparse, hashlib, importlib, json, random, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from puzzle_generators import runner
from src.core.canonical_pairs import load_task_pairs


def gh(grid):
    return hashlib.sha1((";".join(",".join(map(str, r)) for r in grid)).encode()).hexdigest()[:10]


def shape(grid):
    return (len(grid), len(grid[0]) if grid else 0)


def palette(grid):
    return frozenset(v for r in grid for v in r)


def probe_task(task_id, episodes, base_seed, n_demos=4, n_queries=2):
    """Probe one task, always releasing the persistent Racket bridge.

    The probe used to leak the bridge subprocess: it printed its complete
    green summary and then never exited, so the enclosing battery looked like
    it hung *after* the diversity stage. That symptom was reported
    independently by ~8 generator workers (v13-x/v13-y) as "battery wrapper
    outlives a completed child". The child was this process.
    """
    bundle = runner._load_bundle(task_id)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        return _probe_with_bridge(
            task_id, episodes, base_seed, n_demos, n_queries,
            bundle, bridge, fn_name,
        )
    finally:
        try:
            bridge.shutdown()
        except Exception as exc:  # never mask the probe's own result/error
            print(f"LOUD: racket bridge shutdown failed for {task_id}: {exc}",
                  file=sys.stderr)


def _probe_with_bridge(task_id, episodes, base_seed, n_demos, n_queries,
                       bundle, bridge, fn_name):
    in_grids, out_grids = [], []
    fails = 0
    for ep in range(episodes):
        try:
            inst = runner.run_one(task_id, seed=base_seed + ep * 101, sample_index=0,
                                  n_train=n_demos, n_test=n_queries,
                                  bundle=bundle, bridge=bridge, fn_name=fn_name)
            for p in list(inst["train"]) + list(inst["test"]):
                in_grids.append(p["input"]); out_grids.append(p["output"])
        except Exception:
            fails += 1
    n = len(in_grids)
    if n == 0:
        return {"task_id": task_id, "pairs": 0, "fails": fails}
    in_h = {gh(g) for g in in_grids}; out_h = {gh(g) for g in out_grids}
    in_sh = {shape(g) for g in in_grids}; out_sh = {shape(g) for g in out_grids}
    canonical_in_shapes: set[tuple[int, int]] = set()
    canonical_out_shapes: set[tuple[int, int]] = set()
    try:
        for pair in load_task_pairs(task_id):
            canonical_in_shapes.add(shape(pair["input"]))
            if pair.get("output") is not None:
                canonical_out_shapes.add(shape(pair["output"]))
    except (OSError, ValueError):
        pass
    pals = {palette(g) for g in in_grids + out_grids}
    colors = set().union(*[palette(g) for g in in_grids + out_grids])
    # fraction of pairs where the rule left the grid unchanged (output == input).
    # A healthy transformation should be ~0 here; high values flag a no-op /
    # wrong-rule generator (the rule barely changes the generated inputs).
    identity = sum(1 for gi, go in zip(in_grids, out_grids) if gi == go)
    try:
        expected_codomain = getattr(
            importlib.import_module(
                f"puzzle_generators.per_puzzle.{task_id}.generator"
            ),
            "EXPECTED_OUTPUT_CODOMAIN",
            None,
        )
    except Exception:
        expected_codomain = None
    if (
        not isinstance(expected_codomain, int)
        or isinstance(expected_codomain, bool)
        or expected_codomain <= 0
    ):
        expected_codomain = None
    return {
        "task_id": task_id, "pairs": n, "fails": fails,
        "uniq_in": len(in_h) / n, "uniq_out": len(out_h) / n,
        # ABSOLUTE distinct-output count: the true "near-constant" signal. A
        # counting/classification rule legitimately has a small output alphabet
        # (one grid per count value) -> low uniq_out RATIO but many distinct
        # outputs; only n_distinct_out <= 2 means the model could learn a constant.
        "n_distinct_out": len(out_h),
        "in_shapes": len(in_sh), "out_shapes": len(out_sh),
        "canonical_in_shapes": len(canonical_in_shapes),
        "canonical_out_shapes": len(canonical_out_shapes),
        "shape_lock_in_intrinsic": (
            len(in_sh) == 1
            and bool(canonical_in_shapes)
            and in_sh == canonical_in_shapes
        ),
        "shape_lock_out_intrinsic": (
            len(out_sh) == 1
            and bool(canonical_out_shapes)
            and out_sh == canonical_out_shapes
        ),
        "n_colors": len(colors), "uniq_palettes": len(pals),
        "frac_identity": identity / n,
        "expected_output_codomain": expected_codomain,
        "output_codomain_coverage": (
            min(1.0, len(out_h) / expected_codomain)
            if expected_codomain
            else None
        ),
    }


def flags(r):
    f = []
    if r.get("pairs", 0) == 0:
        return ["DEAD(no pairs)"]
    if r["uniq_in"] < 0.5: f.append(f"dup-inputs({r['uniq_in']:.0%})")
    if (
        r["uniq_out"] < 0.5
        and r.get("output_codomain_coverage") != 1.0
    ):
        f.append(f"dup-outputs({r['uniq_out']:.0%})")
    if r["in_shapes"] == 1 and not r.get("shape_lock_in_intrinsic"):
        f.append("shape-locked-in")
    if r["out_shapes"] == 1 and not r.get("shape_lock_out_intrinsic"):
        f.append("shape-locked-out")
    if r["n_colors"] <= 2: f.append(f"palette-locked({r['n_colors']}c)")
    if r.get("frac_identity", 0) > 0.3:
        f.append(f"no-op({r['frac_identity']:.0%}=in)")
    return f


def informational_notes(r):
    notes = []
    if r.get("shape_lock_in_intrinsic"):
        notes.append("intrinsic-fixed-input-shape")
    if r.get("shape_lock_out_intrinsic"):
        notes.append("intrinsic-fixed-output-shape")
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=40)
    ap.add_argument("--episodes", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--task-id", action="append")
    output = ap.add_mutually_exclusive_group()
    output.add_argument(
        "--out",
        type=Path,
        help="append machine-readable rows to this path instead of the shared ledger",
    )
    output.add_argument(
        "--no-append",
        action="store_true",
        help="print the report without writing any machine-readable ledger",
    )
    args = ap.parse_args()

    paths = sorted((REPO / "puzzle_generators" / "per_puzzle").glob("*/generator.py"))
    all_ids = [p.parent.name for p in paths]
    out = args.out or REPO / "data" / "derived" / "gen_diversity_probe.jsonl"
    # Accumulate across loop iterations: skip generators already probed so each run
    # sweeps NEW ones (progressively covering all of them).
    covered = set()
    if not args.no_append and out.exists() and not args.task_id:
        for line in open(out):
            try: covered.add(json.loads(line)["task_id"])
            except Exception: pass
    if args.task_id:
        ids = args.task_id
    else:
        pool = [t for t in all_ids if t not in covered]
        if not pool:  # full sweep done — start a fresh pass
            print(f"full sweep complete ({len(covered)} covered); restarting pass\n", flush=True)
            pool = all_ids[:]
            covered = set()
        rng = random.Random(args.seed); rng.shuffle(pool); ids = pool[: args.n_tasks]
    print(f"probing {len(ids)} generators x {args.episodes} episodes "
          f"({len(covered)}/{len(all_ids)} already covered)\n", flush=True)

    rows, flagged = [], []
    for i, t in enumerate(ids):
        try:
            r = probe_task(t, args.episodes, args.seed)
        except Exception as e:
            r = {"task_id": t, "pairs": 0, "fails": -1, "err": f"{type(e).__name__}:{str(e)[:60]}"}
        rows.append(r); fl = flags(r); info = informational_notes(r)
        if fl:
            flagged.append((t, fl, r))
        if r.get("pairs"):
            print(f"{t}  pairs={r['pairs']:3d} uniqIn={r['uniq_in']:.0%} uniqOut={r['uniq_out']:.0%} "
                  f"inSh={r['in_shapes']} outSh={r['out_shapes']} colors={r['n_colors']} "
                  f"{' '.join(fl + info)}", flush=True)
        else:
            print(f"{t}  NO PAIRS {r.get('err','')}", flush=True)

    ok = [r for r in rows if r.get("pairs")]
    print(f"\n=== summary: {len(ok)}/{len(rows)} produced pairs; {len(flagged)} flagged ===")
    if ok:
        import statistics as st
        print(f"median uniq_in={st.median(r['uniq_in'] for r in ok):.0%} "
              f"median uniq_out={st.median(r['uniq_out'] for r in ok):.0%} "
              f"median colors={st.median(r['n_colors'] for r in ok):.0f}")
    print("\nworst offenders (low diversity):")
    for t, fl, r in sorted(flagged, key=lambda x: x[2].get("uniq_in", 1))[:25]:
        print(f"  {t}: {' '.join(fl)}")
    # Machine-readable dump. The historical default still appends so scheduled
    # coverage sweeps accumulate, while review/audit callers can be read-only.
    if args.no_append:
        print(f"\nno ledger written (--no-append); {len(rows)} rows reported")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"\nappended {len(rows)} rows -> {out}")


if __name__ == "__main__":
    raise SystemExit(main())
