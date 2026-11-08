#!/usr/bin/env python3
"""Family-aware generator-distribution gate (task #36; reviewers next375/376/380 repeated ask).

The existing gates (lint_generator/self_check/rule_smoke) verify STRUCTURE, PARITY and non-degeneracy,
but they do NOT check that a generator's INPUT distribution matches the CANONICAL task's own inputs by
STRUCTURAL metric. That gap let real drift ship (e.g. 1b7cbdffd485 generated median object-count 12 vs
canonical 2; f7ffd4a6769a 39 vs 6; cbf77aa253ac 2 vs 8) — "valid parity, wrong teaching signal".

This gate, per task_id: materialize N generated inputs, compute per-metric MEDIANS, compare to the
canonical train inputs' medians, and FLAG a metric whose generated median diverges beyond a ratio band.
Metrics (from distribution_audit.py): object count, median component size, palette size, largest-bbox
aspect, input area. It is advisory drift detection — it does not replace parity; it catches pedagogy drift.

  python3 scripts/generator_distribution_gate.py 1b7cbdffd485 cbf77aa253ac        # explicit ids
  python3 scripts/generator_distribution_gate.py 1b7cbdffd485 --seeds 40 --tol 0.6
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from distribution_audit import comps, pal, comp_size_median, largest_bbox_aspect, area, modal_bg  # noqa: E402
from scripts.generator_module_loader import load_module_from_path
from src.core.canonical_pairs import load_task_pairs

ROOT = "puzzle_generators/per_puzzle"
CANON = "data/canonical/puzzles.jsonl"


def load_gen(task_id):
    p = f"{ROOT}/{task_id}/generator.py"
    return load_module_from_path(f"g_{task_id}", p)


def canonical_inputs(ids):
    return {
        task_id: [
            pair["input"]
            for pair in load_task_pairs(
                task_id,
                REPO / CANON,
                splits=("train",),
            )
        ]
        for task_id in ids
    }


def _metrics(g):
    bg = modal_bg(g)
    return {
        "obj_count": comps(g, bg),
        "comp_size_med": comp_size_median(g, bg),
        "palette": pal(g),
        "bbox_aspect_x10": round(largest_bbox_aspect(g, bg) * 10),
        "area": area(g),
    }


def _median_metrics(grids):
    if not grids:
        return {}
    keys = _metrics(grids[0]).keys()
    per = {k: [] for k in keys}
    for g in grids:
        m = _metrics(g)
        for k in keys:
            per[k].append(m[k])
    return {k: median(v) for k, v in per.items()}


def _metric_values(grids):
    values = {}
    for grid in grids:
        for key, value in _metrics(grid).items():
            values.setdefault(key, []).append(value)
    return values


def gate_one(task_id, canon_in, seeds, bands, tol, max_crash_frac=0.05):
    """Return (flags, gen_med, canon_med). flags = list of (metric, gen, canon)."""
    try:
        m = load_gen(task_id)
    except Exception as e:
        return [("GEN_LOAD_FAIL", str(e)[:40], "")], {}, {}
    gen = []
    crashes = 0
    requested = 0
    for band in bands:
        for sd in range(1, seeds + 1):
            requested += 1
            try:
                gen.append(m.generate(sd, sd, difficulty=band))
            except Exception:
                crashes += 1
    # A generator judged only on its survivors is not a distribution match.
    # rule_smoke and defect-lint count generate() crashes; this gate silently
    # discarded them, letting a 95%-crashing generator pass on 5% survivors.
    if requested and crashes / requested > max_crash_frac:
        return [("generate_crashes", f"{crashes}/{requested}",
                 f"<= {max_crash_frac:.0%}")], {}, {}
    canon_med = _median_metrics(canon_in)
    gen_med = _median_metrics(gen)
    canon_values = _metric_values(canon_in)
    gen_values = _metric_values(gen)
    # Only flag SEVERE drift on PEDAGOGY-CRITICAL metrics. `area` (and larger palettes) are DELIBERATELY
    # widened for training diversity (see project_contest_distribution_gap) — reported, never flagged.
    # The real defect class is fragmentation: object count / component size off by a large RATIO in either
    # direction (over-fragmented pepper-noise, or under-complex single blobs). `tol` is the ratio band.
    # obj_count is the robust fragmentation signal (what reviewers actually caught: 12 vs 2, 39 vs 6, 2 vs 8);
    # comp_size_med is derivative + noisy on tasks with only 2-4 canonical examples, so it's reported not flagged.
    FLAG_METRICS = ("obj_count",)
    flags = []
    for k in FLAG_METRICS:
        cv, gv = canon_med.get(k, 0), gen_med.get(k, 0)
        hi = max(abs(cv), abs(gv), 1)
        lo = max(min(abs(cv), abs(gv)), 1)
        if hi / lo > tol:
            flags.append((k, gv, cv))
    # A broad aggregate median can look healthy while an authoritative color
    # role is literally unreachable. Treat canonical palette cardinalities
    # outside the generated range as a blocking distribution disagreement.
    generated_palette = gen_values.get("palette") or []
    canonical_palette = canon_values.get("palette") or []
    if generated_palette and canonical_palette:
        generated_range = (
            min(generated_palette),
            max(generated_palette),
        )
        # Extra generated distractor colors can intentionally broaden a
        # lesson. The blocking case is the opposite: canonical examples need
        # more simultaneous color roles than any generated input can express.
        unreachable = sorted(
            {value for value in canonical_palette if value > generated_range[1]}
        )
        if unreachable:
            flags.append(
                (
                    "canonical_palette_unreachable",
                    f"{generated_range[0]}..{generated_range[1]}",
                    ",".join(map(str, unreachable)),
                )
            )
    return flags, gen_med, canon_med


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--bands", default="easy,medium,hard")
    ap.add_argument("--tol", type=float, default=3.0,
                    help="max allowed RATIO between generated & canonical median on obj_count/comp_size "
                         "(either direction); default 3.0 = flag only >3x fragmentation drift")
    ap.add_argument("--max-crash-frac", type=float, default=0.05,
                    help="max allowed fraction of generate() crashes before flagging; default 0.05")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    ids = sorted(set(a.ids))
    bands = a.bands.split(",")
    canon = canonical_inputs(ids)
    flagged = {}
    for t in ids:
        if t not in canon or not canon[t]:
            print(f"  {t}: NO CANONICAL INPUTS [SKIP]", flush=True)
            continue
        flags, gm, cm = gate_one(t, canon[t], a.seeds, bands, a.tol, a.max_crash_frac)
        if flags:
            flagged[t] = flags
            desc = ", ".join(f"{k}: gen={gv} vs canon={cv}" for k, gv, cv in flags)
            print(f"  {t}: DRIFT [{desc}]", flush=True)
        else:
            # Scope honesty (worker ask WFB-001, batch v13-h): this gate compares
            # MORPHOLOGY MARGINALS only — it is not semantic/self-check/override
            # evidence, and a green line here must never be read as such.
            print(f"  {t}: OK (morphology-marginals only; gen≈canon: {cm})", flush=True)
    if a.json:
        json.dump({"flagged": {t: [list(f) for f in fs] for t, fs in flagged.items()}}, open(a.json, "w"), indent=2)
    print(f"\nscanned {len(ids)}; DRIFT-FLAGGED {len(flagged)}")
    # The per-task lines say "morphology-marginals only", but the SUMMARY line is
    # what a human reads and what gets pasted into a report — and it said nothing.
    # WFB-101 (b962e7deb312, 2026-07-25) came from exactly that gap: this gate
    # printed OK while the generator emitted ~10 objects against a canonical ~2
    # and a palette of ~8 against a canonical ~3, with 0/60 exact profile support.
    # A clean line here means "the marginals I check did not drift", never
    # "the distribution teaches the task".
    print("NOTE: DIAGNOSTIC-ONLY. This gate compares morphology MARGINALS. It "
          "cannot see task-linked component/palette drift, missing semantic "
          "contracts, or shortcut-teaching distributions — a clean result is "
          "not evidence of any of those.\n"
          "      For those, read: canonical_profile_gate.py (linked "
          "profile support), generator_semantic_gate.py --require-contract "
          "(does it teach the rule?), and the strict defect lint.")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
