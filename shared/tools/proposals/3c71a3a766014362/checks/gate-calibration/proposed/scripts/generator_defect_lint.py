"""Generic generator-DEFECT linter — auto-catch the recurring reviewer-found defects.

The per-puzzle generators keep failing in a SMALL set of generic ways that need NO
per-task knowledge to detect. v2 (2026-07-02) automates exactly what human reviewers
kept confirming by hand, round after round:

  1. CANONICAL COVERAGE — the canonical task's own train inputs must be
     IN-DISTRIBUTION for the generator. If the real task has ~166 objects and the
     generator tops out at 8 (4977f1fc4c50), or area 12 vs generated 80+
     (346d774eda9b), the generator is teaching the WRONG task. Multi-feature,
     anchored on the canonical demos — not hand thresholds per task.
  2. TRANSFORMATION FINGERPRINT — the rule's EFFECT on generated inputs must match
     its effect on canonical demos (size relation, colors introduced, changed-cell
     fraction). Catches semantic mismatches like wrong wall/portal colors
     (41860bce2569) where inputs look plausible but the rule barely fires.
  3. AXIS HONESTY — GenCtx draw provenance (bounds actually passed to draw_int)
     is compared against the declared AXES `valid` ranges. Catches metadata lies
     like `grid_w` drawn with the height bounds (346d774eda9b) and declared-but-
     untapped ranges.
  4. HASHSEED DETERMINISM — generate() re-run in subprocesses under different
     PYTHONHASHSEED values must produce identical grids. Catches set/dict
     iteration-order dependence (the ffaca7acb482 data-poisoning class), which
     same-process determinism checks CANNOT see.
  5. SELF-CHECK POWER — mutation-tests each generator's self_check(): structure-
     destroying mutations (cell shuffle, transpose, block stomp, color swap) of its
     own accepted instances should be REJECTED. A self_check that accepts nearly
     all mutations is toothless (the "loose even-area test" class).
  6. SELF-CALIBRATION — every per-pair detector first runs on the canonical train
     pairs themselves; if it fires there, the property is part of the TASK, not a
     defect, and the detector is disabled for that task. This replaces the
     hand-exemption treadmill (solid-label, scalar-label, ... FPs) structurally.

Per the spec, a generator emits `input`; the OUTPUT is derived by piping that input
through the puzzle's canonical Racket rule (one source of truth). So each detector
sees, per seed: (input, output, canonical_train_pairs, has_self_check, all_outputs).

### Severity model
ERROR-level findings flag the generator (exit summary FLAGGED count, gate-blocking).
WARN-level findings are printed + JSON'd but do not flag (elevate with --strict).

### Extending it (reviewers: this is the ask)
Add a detector: write `def my_detector(ctx) -> list[str]` returning zero or more
human-readable issue strings, then append `("my_name", my_detector)` to
PAIR_DETECTORS (runs once per generated pair; auto-calibrated on canonical pairs)
or TASK_DETECTORS (runs once per task with the full sample). Keep detectors
GENERIC (no per-task constants) and FAIL-LOUD.

  python3 scripts/generator_defect_lint.py <task_id> [...]   # lint specific ids
  python3 scripts/generator_defect_lint.py --all [--limit N] # sweep the corpus
  python3 scripts/generator_defect_lint.py <id> --seeds 12 --json report.json
  python3 scripts/generator_defect_lint.py <id> --generator-file /path/gen.py
                                          # lint a CANDIDATE file (patch review /
                                          # old-version regression) against <id>
  python3 scripts/generator_defect_lint.py --all --fast      # skip subprocess probes

Degrades gracefully without racket (static detectors like missing_self_check still
run; rule-dependent detectors are skipped + reported, never silently dropped).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.generator_module_loader import load_module_from_path

GEN_ROOT = REPO / "puzzle_generators" / "per_puzzle"
GENERIC_ROOT = REPO / "puzzle_generators" / "generic" / "concepts"
CANON = REPO / "data" / "canonical" / "puzzles.jsonl"


# ----- shared helpers (DRY: same shapes rule_smoke/verify use) ---------------
def _is_grid(g):
    return (isinstance(g, list) and g and isinstance(g[0], list)
            and g[0] and all(isinstance(r, list) for r in g))


def _dims(g):
    return (len(g), len(g[0])) if _is_grid(g) else (0, 0)


def _palette(g):
    return {v for row in g for v in row} if _is_grid(g) else set()


def _majority(g):
    c = Counter(v for row in g for v in row) if _is_grid(g) else Counter()
    return c.most_common(1)[0][0] if c else 0


def _object_stats(g, bg=None):
    """(component_count, max_component_size) over non-bg cells, 4-connected."""
    if not _is_grid(g):
        return 0, 0
    from collections import deque
    bg = _majority(g) if bg is None else bg
    H, W = _dims(g); seen = set(); n = 0; biggest = 0
    for sr in range(H):
        for sc in range(W):
            if (sr, sc) in seen or g[sr][sc] == bg:
                continue
            n += 1; size = 0
            col = g[sr][sc]; q = deque([(sr, sc)]); seen.add((sr, sc))
            while q:
                r, c = q.popleft(); size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen and g[nr][nc] == col:
                        seen.add((nr, nc)); q.append((nr, nc))
            biggest = max(biggest, size)
    return n, biggest


def _n_objects(g, bg=None):
    return _object_stats(g, bg)[0]


def _norm(g):
    # tolerate row-string grids ("000" -> [0,0,0]); mirror coder_synth_verify._norm_grid
    if isinstance(g, list) and g and isinstance(g[0], str):
        return [[int(ch) for ch in row] for row in g]
    return g


def _features(g):
    """Cheap interpretable per-grid features for canonical-coverage comparison."""
    h, w = _dims(g)
    cnt = Counter(v for row in g for v in row)
    modal, modal_n = cnt.most_common(1)[0] if cnt else (0, 0)
    n_obj, max_obj = _object_stats(g, bg=modal)
    return {"h": h, "w": w, "area": h * w, "n_colors": len(cnt),
            "modal_color": modal, "modal_frac": modal_n / max(1, h * w),
            "obj_count": n_obj, "max_obj": max_obj}


def _fingerprint(gin, gout):
    """Transformation signature of one (input, output) pair."""
    ih, iw = _dims(gin); oh, ow = _dims(gout)
    same = (ih, iw) == (oh, ow)
    if same:
        size = "same"
    elif oh <= ih and ow <= iw:
        size = "shrink"
    elif oh >= ih and ow >= iw:
        size = "grow"
    else:
        size = "reshape"
    pin, pout = _palette(gin), _palette(gout)
    changed = None
    if same:
        diff = sum(1 for r in range(ih) for c in range(iw) if gin[r][c] != gout[r][c])
        changed = diff / max(1, ih * iw)
    return {"size": size, "identity": gin == gout, "changed": changed,
            "added": frozenset(pout - pin), "removed": frozenset(pin - pout)}


# =====================================================================
# DETECTOR REGISTRY — each takes a ctx dict, returns list[str] of issues.
# ctx keys: input, output, train (canonical task train pairs as (in,out) tuples),
#           has_self_check (bool), all_outputs (list of every seed's output),
#           all_inputs (list of every seed's input), task_id
# PAIR_DETECTORS run once per generated pair and are SELF-CALIBRATED: any pair
# detector that fires on the canonical train pairs themselves is disabled for
# that task (the property is the task, not a defect). TASK_DETECTORS run once.
# Keep detectors GENERIC + fail-loud. Append new ones below.
# =====================================================================
def d_identity_demo(ctx):
    """Invisible/identity demo: the rule changed NOTHING (output == input)."""
    g, o = ctx["input"], ctx["output"]
    if _is_grid(g) and _is_grid(o) and g == o:
        return ["identity demo: canonical rule left the input unchanged "
                "(output == input) — the transformation is not demonstrated"]
    return []


def d_all_background_output(ctx):
    """Output is a LARGE single-color grid — a likely no-op.

    Skip two generic false-positive classes: intrinsically small/scalar outputs,
    and tasks whose own canonical training examples already include a large
    single-color output (for example crop-and-scale tasks where the selected
    component can be a solid rectangle). Those tasks may still be bad if *all*
    generated outputs collapse; the low-diversity detector covers that corpus
    signal without mislabeling individual valid examples.
    """
    o = ctx["output"]
    if not (_is_grid(o) and len(_palette(o)) == 1 and _dims(o)[0] * _dims(o)[1] >= 9):
        return []
    if min(_dims(o)) == 1:
        return []   # thin 1xN/Nx1 solid bar — a deliberate COUNT encoding, not a no-op (reviewers 425/430)
    justification = str(
        ctx.get("solid_output_justification") or ""
    ).strip()
    if ctx.get("has_self_check") and len(justification) >= 30:
        return []
    for _inp, canon_out in (ctx.get("train") or []):
        co = _norm(canon_out)
        # Area >=4 distinguishes genuine crop/scale solid examples from scalar-label tasks.
        if _is_grid(co) and len(_palette(co)) == 1 and _dims(co)[0] * _dims(co)[1] >= 4:
            return []
    return [f"degenerate output: a single solid color {next(iter(_palette(o)))} "
            f"({_dims(o)[0]}x{_dims(o)[1]}) — likely a no-op / wrong input; "
            "a lawful endpoint needs SOLID_OUTPUT_JUSTIFICATION (at least 30 characters) "
            "explaining the selected canonical rule, plus self_check; verify both "
            "against source-bound examples"]


def d_low_output_diversity(ctx):
    """Near-constant outputs across seeds (overlaps rule_smoke; corpus-wide here).

    This detector is rule-output dependent.  When Racket is unavailable, the rule is
    missing, or every bridge call failed, ``all_outputs`` is a list of ``None`` values.
    Only score diversity once we actually have a representative set of grid outputs.
    """
    grid_outs = [_norm(o) for o in ctx["all_outputs"] if _is_grid(_norm(o))]
    if len(grid_outs) >= 6:
        distinct = len({json.dumps(o) for o in grid_outs})
        expected = ctx.get("expected_codomain")   # generator's declared EXPECTED_OUTPUT_CODOMAIN
        if isinstance(expected, int) and expected > 0 and distinct >= expected:
            return []   # finite-codomain generator (e.g. always emits color-N grids), fully covered — not a defect
        # Don't demand more diversity than the canonical task's OWN train outputs show: some ARC tasks
        # are intrinsically low-cardinality (solid swatches, quadrant labels, matrices) (reviewer gpt55pro_384).
        canon_outs = [_norm(p[1]) for p in (ctx.get("train") or []) if _is_grid(_norm(p[1]))]
        canon_distinct = len({json.dumps(o) for o in canon_outs})
        if canon_distinct and distinct >= canon_distinct:
            return []
        # Small categorical / relation-matrix tasks can have a genuinely tiny output space. Don't flag a
        # non-constant <=3x3 task once it exercises >=4 distinct outputs (proves it's not constant/identity),
        # while preserving the default gate for larger structured outputs (reviewer 370).
        areas = [_dims(o)[0] * _dims(o)[1] for o in grid_outs]
        if max(areas or [0]) <= 9 and distinct >= 4:
            return []
        # Count-bar tasks: every output is a thin solid 1xN/Nx1 bar but they DO vary in length.
        # That's a legitimate finite-ish encoding, not a collapsed generator (reviewers 425/430).
        if (all(len(_palette(o)) == 1 and min(_dims(o)) == 1 for o in grid_outs)
                and distinct > max(3, len(grid_outs) // 8)):
            return []
        if distinct <= max(2, len(grid_outs) // 4):
            suffix = f"; declared finite codomain {expected}" if isinstance(expected, int) and expected > 0 else ""
            return [f"low output diversity: only {distinct} distinct outputs over "
                    f"{len(grid_outs)} evaluated seeds — generator likely too constrained / constant{suffix}; "
                    "justify EXPECTED_OUTPUT_CODOMAIN from the selected canonical rule "
                    "and verify sampled outputs cover that entire alphabet; "
                    "a collapsed sample is not a justification"]
    return []


def d_invalid_input(ctx):
    """Generated input is not a legal ARC grid (rectangular, 1..30 per side,
    ints 0..9). Found live: fa5bb24054bc emitted 31-wide grids — the runner's
    is_well_formed rejects these at build time, silently shrinking the stream,
    and any consumer skipping the runner ships them to the model."""
    g = ctx["input"]
    if _is_grid(g) and not _valid_arc_grid(g):
        h, w = _dims(g)
        vals = {
            v
            for row in g
            for v in row
            if not (
                isinstance(v, int)
                and not isinstance(v, bool)
                and 0 <= v <= 9
            )
        }
        why = (f"{h}x{w} exceeds 30" if (h > 30 or w > 30)
               else f"bad values {sorted(map(str, vals))[:4]}" if vals
               else "ragged rows")
        return [f"generated input is not a legal ARC grid ({why})"]
    return []


def d_duplicate_inputs(ctx):
    """High duplicate-INPUT rate across different seeds. The data principle is
    always-unique streaming; a generator that re-mints the same input grids
    under different seeds quietly shrinks the effective dataset (the 40-47%%
    duplicate-input generators found during the catalog effort). Distinct
    OUTPUTS are covered by d_low_output_diversity; this is the input side."""
    bands = ctx.get("in_bands")
    if not bands or len(bands) != len(ctx["all_inputs"]):
        return []
    # dedup WITHIN each band only: the same seed across overlapping difficulty
    # bands legitimately yields identical grids (that's the dead-bands probe's
    # territory, not a duplicate-input defect).
    per_band: dict = {}
    for g, b in zip(ctx["all_inputs"], bands):
        if _is_grid(g):
            per_band.setdefault(b, []).append(json.dumps(g))
    total = distinct = 0
    for rows in per_band.values():
        if len(rows) < 4:
            return []
        total += len(rows)
        distinct += len(set(rows))
    if total >= 12 and distinct / total < 0.7:
        return [f"duplicate_inputs: only {distinct}/{total} sampled inputs are "
                f"distinct within their difficulty band ({distinct/total:.0%}) — "
                f"different seeds re-mint the same grids, shrinking the effective "
                f"stream"]
    return []


def d_missing_self_check(ctx):
    """No executable self_check() — the only per-task safety net is absent."""
    if not ctx["has_self_check"]:
        checker = (
            "self_check_task()"
            if str(ctx.get("task_id") or "").startswith("generic_")
            else "self_check()"
        )
        return [
            f"no {checker}: generator has no executable per-task invariant; "
            "the exact-count/structural defects can only be caught by hand here"
        ]
    return []


def d_distribution_drift(ctx):
    """Generator's instances look structurally NOTHING like the canonical task's own
    train pairs — the signature of the 'wrong task / motif-gallery' rewrites.

    Compares median object-count, palette-size and grid-area of the GENERATED inputs
    vs the canonical task's ORIGINAL train inputs. Flags only large, robust drift."""
    train = ctx.get("train") or []
    ins = [g for g in ctx["all_inputs"] if _is_grid(g)]
    canon_in = [_norm(p[0]) for p in train if _is_grid(_norm(p[0]))]
    if len(ins) < 4 or len(canon_in) < 1:
        return []
    def med(xs):
        xs = sorted(xs); return xs[len(xs) // 2] if xs else 0
    g_obj = med([_n_objects(g) for g in ins]); c_obj = med([_n_objects(g) for g in canon_in])
    g_pal = med([len(_palette(g)) for g in ins]); c_pal = med([len(_palette(g)) for g in canon_in])
    g_area = med([_dims(g)[0] * _dims(g)[1] for g in ins])
    c_area = med([_dims(g)[0] * _dims(g)[1] for g in canon_in])
    issues = []
    # palette is the most reliable task-identity signal; objects next.
    if c_pal and (g_pal > 2.5 * c_pal or g_pal * 2.5 < c_pal):
        issues.append(f"distribution drift: generated palette-size ~{g_pal} vs canonical "
                      f"task ~{c_pal} — generator may be emitting the WRONG task")
    if c_obj and (g_obj > 3 * max(1, c_obj) or g_obj * 3 < max(1, c_obj)):
        issues.append(f"distribution drift: generated object-count ~{g_obj} vs canonical "
                      f"task ~{c_obj}")
    if c_area and (g_area > 4 * c_area or g_area * 4 < c_area):
        issues.append(f"distribution drift: generated grid-area ~{g_area} vs canonical "
                      f"task ~{c_area}")
    return issues


def d_canonical_coverage(ctx):
    """The canonical demos must be reachable by the generator (coverage, not just
    central-tendency drift). For every structural feature, the canonical median must
    fall inside the generated sample's [min, max] envelope (with tolerance). A
    canonical value the generator can NEVER produce means the model trains on a
    different task than it is evaluated on — the #1 confirmed reviewer defect class
    (4977f1fc4c50 obj 166 vs <=8; 346d774eda9b area 12 vs 80+; 501c7f0770eb obj 8
    vs <=3; bbdb31b935f8 obj 23 vs ~7)."""
    train = ctx.get("train") or []
    gen_in = [g for g in ctx["all_inputs"] if _is_grid(g)]
    canon_in = [_norm(p[0]) for p in train if _is_grid(_norm(p[0]))]
    if len(gen_in) < 6 or not canon_in:
        return []
    gf = [_features(g) for g in gen_in]
    cf = [_features(g) for g in canon_in]
    issues = []
    # Task-identity features only — component-SIZE residuals (max_obj) live in
    # d_canonical_coverage_soft at WARN level (field calibration 2026-07-02: all
    # post-fix max_obj hits were real-but-mild residual gaps, not wrong-task).
    for f in ("area", "h", "w", "n_colors", "obj_count"):
        # Some imported panel banks intentionally exceed ARC's 30x30 exchange
        # envelope. Per-puzzle generators are rejected by the runner if they
        # reproduce that oversized dimension, so do not demand an impossible
        # exact dimension from an otherwise faithful compressed lesson.
        if f in {"h", "w"}:
            canonical_median = sorted(x[f] for x in cf)[len(cf) // 2]
            generated_max = max(x[f] for x in gf)
            if canonical_median > 30 and generated_max <= 30:
                continue
        issue = _coverage_gap(f, gf, cf)
        if issue:
            issues.append(issue)
    # Background identity: if every clear-background canonical demo uses modal colors
    # the generator never produces, the visual prior (background color) is wrong.
    c_modals = {x["modal_color"] for x in cf if x["modal_frac"] >= 0.45}
    g_modals = {x["modal_color"] for x in gf}
    if c_modals and not (c_modals & g_modals):
        issues.append(f"canonical-coverage: canonical background/modal color(s) {sorted(c_modals)} "
                      f"never generated (generated modal colors: {sorted(g_modals)}) — wrong "
                      f"background prior")
    return issues


def _coverage_gap(f, gf, cf):
    gv = sorted(x[f] for x in gf)
    cv = sorted(x[f] for x in cf)
    cmed = cv[len(cv) // 2]
    lo, hi = gv[0], gv[-1]
    tol = max(1, int(0.25 * (hi - lo)) + 1, int(0.15 * hi) + 1)
    if cmed < lo - tol or cmed > hi + tol:
        return (f"canonical-coverage: canonical {f} median {cmed} outside generated "
                f"range [{lo}, {hi}] (tol {tol}) — the generator cannot produce inputs "
                f"like the real task's demos")
    return None


def d_canonical_coverage_soft(ctx):
    """WARN-level coverage residuals: component-size (max_obj) gaps are real but in
    practice post-fix leftovers (e.g. canonical wall structures larger than any the
    generator emits), not wrong-task signals — surface, don't gate."""
    train = ctx.get("train") or []
    gen_in = [g for g in ctx["all_inputs"] if _is_grid(g)]
    canon_in = [_norm(p[0]) for p in train if _is_grid(_norm(p[0]))]
    if len(gen_in) < 6 or not canon_in:
        return []
    gf = [_features(g) for g in gen_in]
    cf = [_features(g) for g in canon_in]
    issue = _coverage_gap("max_obj", gf, cf)
    return [issue] if issue else []


def d_transformation_drift(ctx):
    """The RULE's behavior on generated inputs must match its behavior on the
    canonical demos. Same generator inputs can be individually valid yet
    systematically fail to exercise the transformation (wrong marker/wall colors,
    missing trigger structures) — the rule then no-ops or degenerates and the model
    learns the wrong mapping (41860bce2569 class). Canonical-anchored, so tasks
    whose rule legitimately barely changes cells are never flagged."""
    train = ctx.get("train") or []
    pairs = [(_norm(i), _norm(o)) for i, o in zip(ctx["all_inputs"], ctx["all_outputs"])
             if _is_grid(_norm(i)) and _is_grid(_norm(o))]
    canon = [(_norm(p[0]), _norm(p[1])) for p in train
             if _is_grid(_norm(p[0])) and _is_grid(_norm(p[1]))]
    if len(pairs) < 6 or not canon:
        return []
    gfp = [_fingerprint(i, o) for i, o in pairs]
    cfp = [_fingerprint(i, o) for i, o in canon]
    issues = []
    # 1. size relation: a class the canonical task never exhibits dominating generated pairs
    c_sizes = {f["size"] for f in cfp}
    bad_size = [f for f in gfp if f["size"] not in c_sizes]
    if len(bad_size) >= max(2, 0.3 * len(gfp)):
        got = Counter(f["size"] for f in bad_size).most_common(1)[0][0]
        issues.append(f"transformation-drift: {len(bad_size)}/{len(gfp)} generated pairs have size "
                      f"relation '{got}' the canonical task never shows (canonical: {sorted(c_sizes)})")
    # 2. colors the rule introduces on EVERY canonical demo must appear on generated pairs
    always_added = frozenset.intersection(*[f["added"] for f in cfp])
    if always_added:
        lacking = [f for f in gfp if not (always_added & f["added"])]
        if len(lacking) >= max(2, 0.5 * len(gfp)):
            issues.append(f"transformation-drift: the rule introduces color(s) {sorted(always_added)} on "
                          f"every canonical demo but on {len(gfp)-len(lacking)}/{len(gfp)} generated pairs "
                          f"— generated inputs likely lack the structures the rule acts on")
    # 3. rule fires strongly on every canonical demo but barely on generated inputs
    c_changed = [f["changed"] for f in cfp if f["changed"] is not None]
    g_changed = [f["changed"] for f in gfp if f["changed"] is not None]
    if len(c_changed) == len(cfp) and c_changed and g_changed and min(c_changed) > 0:
        floor = min(c_changed) / 5
        weak = [x for x in g_changed if x < floor]
        if len(weak) >= max(2, 0.3 * len(g_changed)):
            issues.append(f"transformation-drift: rule changes >= {min(c_changed):.0%} of cells on every "
                          f"canonical demo but < {floor:.0%} on {len(weak)}/{len(g_changed)} generated pairs "
                          f"— the transformation is barely demonstrated")
    return issues


# Reviewers: append ("name", fn) when you find a new GENERIC defect pattern.
PAIR_DETECTORS = [
    ("invalid_input", d_invalid_input),
    ("identity_demo", d_identity_demo),
    ("all_background_output", d_all_background_output),
]
TASK_DETECTORS = [
    ("low_output_diversity", d_low_output_diversity),
    ("duplicate_inputs", d_duplicate_inputs),
    ("missing_self_check", d_missing_self_check),
    ("distribution_drift", d_distribution_drift),
    ("canonical_coverage", d_canonical_coverage),
    ("canonical_coverage_soft", d_canonical_coverage_soft),
    ("transformation_drift", d_transformation_drift),
]
DETECTORS = PAIR_DETECTORS + TASK_DETECTORS   # public registry (docs/spec reference)

# WARN-level findings are reported but do not FLAG (see --strict). Everything else
# is ERROR-level. New heuristics start at WARN and get promoted once field-proven.
WARN_DETECTORS = {"transformation_drift", "canonical_coverage_soft",
                  "selfcheck-power", "axis-span", "duplicate_inputs"}


# ----- probes (need the live module / subprocesses, not just pairs) ----------
_VALID_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*$")


def _parse_valid(v):
    if not isinstance(v, str):
        return None
    m = _VALID_RANGE_RE.match(v)
    if m:
        return ("range", int(m.group(1)), int(m.group(2)))
    if "|" in v:
        return ("enum", {s.strip() for s in v.split("|")})
    return None


def probe_axis_honesty(module, ctxs):
    """Compare declared AXES `valid` metadata against the DRAW PROVENANCE recorded
    by GenCtx during sampling (bounds passed to draw_int / options to draw_choice).

    ERROR: draws use bounds/values OUTSIDE the declared valid range — the metadata
           lies about the training distribution (the 346d774eda9b fake-width class).
    WARN:  a wide declared range whose drawn envelope covers <1/3 of it — declared-
           but-untapped variation (feeds the known small-inputs-vs-eval gap)."""
    axes = getattr(module, "AXES", None)
    if not isinstance(axes, dict) or not ctxs:
        return [], []
    bounds, drawn, options, int_options = {}, {}, {}, {}
    for ctx in ctxs:
        # Public GenCtx provenance API (contract v14); fall back to the raw
        # stores for any pre-API ctx object a bundled generator might build.
        bounds_map = (ctx.draw_bounds_store if hasattr(ctx, "draw_bounds_store")
                      else getattr(ctx, "_draw_bounds", {}))
        drawn_map = (ctx.recorded_draws() if hasattr(ctx, "recorded_draws")
                     else getattr(ctx, "_drawn", {}))
        options_map = (ctx.draw_options_store if hasattr(ctx, "draw_options_store")
                       else getattr(ctx, "_draw_options", {}))
        for label, (lo, hi) in bounds_map.items():
            cur = bounds.get(label)
            bounds[label] = (min(lo, cur[0]), max(hi, cur[1])) if cur else (lo, hi)
        for label, v in drawn_map.items():
            if isinstance(v, (int, str)) and not isinstance(v, bool):
                drawn.setdefault(label, set()).add(v)
        for label, opts in options_map.items():
            options.setdefault(label, set()).update(str(o) for o in opts)
            int_options.setdefault(label, set()).update(
                o for o in opts if isinstance(o, int) and not isinstance(o, bool))
    errors, warns = [], []
    for key, spec in axes.items():
        parsed = _parse_valid(spec.get("valid") if isinstance(spec, dict) else None)
        if parsed is None:
            continue
        if parsed[0] == "range":
            a, b = parsed[1], parsed[2]
            envelope = bounds.get(key)
            choice_ints = int_options.get(key, set())
            if choice_ints:
                choice_bounds = (min(choice_ints), max(choice_ints))
                envelope = ((min(envelope[0], choice_bounds[0]),
                             max(envelope[1], choice_bounds[1]))
                            if envelope is not None else choice_bounds)
            if envelope is not None:
                lo, hi = envelope
                if lo < a or hi > b:
                    errors.append(f"axis-honesty: axis {key!r} declared valid {a}..{b} but the "
                                  f"generator draws from [{lo}, {hi}] — AXES metadata lies about "
                                  f"the distribution")
                elif (b - a + 1) >= 6 and (hi - lo + 1) < (b - a + 1) / 3:
                    warns.append(f"axis-span: axis {key!r} declared {a}..{b} but sampling only ever "
                                 f"draws within [{lo}, {hi}] — most of the declared range is untapped")
            ints_out = {v for v in drawn.get(key, set())
                        if isinstance(v, int) and not (a <= v <= b)}
            if ints_out:
                errors.append(f"axis-honesty: axis {key!r} drew value(s) {sorted(ints_out)} outside "
                              f"declared valid {a}..{b}")
        elif parsed[0] == "enum":
            allowed = parsed[1]
            bad = {v for v in drawn.get(key, set()) if isinstance(v, str) and v not in allowed}
            if bad:
                errors.append(f"axis-honesty: axis {key!r} drew value(s) {sorted(bad)} outside the "
                              f"declared enum {sorted(allowed)}")
    return errors, warns


_HASHSEED_SNIPPET = """
import json, sys
sys.path.insert(0, {repo!r})
from scripts.generator_module_loader import load_module_from_path
m = load_module_from_path("g_probe", {path!r})
rows = []
for sd in (1, 2, 3):
    for band in ("easy", "medium", "hard"):
        try:
            rows.append(m.generate(sd, sd, difficulty=band))
        except Exception as e:
            rows.append(["__RAISED__", type(e).__name__])
print(json.dumps(rows))
"""


def probe_hashseed(gen_path):
    """generate() must be independent of the interpreter hash seed. Same-process
    determinism checks (generator_selfcheck) CANNOT catch set/dict iteration-order
    dependence because the hash seed is fixed within a process — this poisoned
    ffaca7acb482's task data. Two subprocesses, different PYTHONHASHSEED, exact
    grid comparison."""
    code = _HASHSEED_SNIPPET.format(repo=str(REPO), path=str(gen_path))
    outs = []
    for hs in ("0", "1"):
        env = dict(os.environ, PYTHONHASHSEED=hs)
        try:
            r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                               text=True, timeout=90, env=env)
        except subprocess.TimeoutExpired:
            return [f"hashseed-determinism: probe timed out under PYTHONHASHSEED={hs}"]
        if r.returncode != 0:
            return [f"hashseed-determinism: probe failed under PYTHONHASHSEED={hs}: "
                    f"{(r.stderr or '').strip()[:140]}"]
        outs.append(r.stdout)
    if outs[0] != outs[1]:
        return ["hashseed-determinism: generate() output CHANGES with the interpreter hash "
                "seed — set/dict iteration-order dependence (the ffaca7acb482 poisoning "
                "class); sort before iterating unordered collections"]
    return []


def probe_rule_hash(module, task_id, rules):
    """RULE STALENESS PIN. Generators may declare RULE_HASH (sha256[:12] of the
    whitespace-normalized canonical program_solution at authoring time). Every
    wrong-task defect this corpus has seen (3d9d2f9baa4e, 646eeb47599b,
    46c02325ed3b, d47d91bc30d0, f6b13494be37) had one root cause: the canonical
    rule was REPLACED and the generator silently went stale. A mismatched pin
    is an ERROR; an absent pin is a note (pins are added as generators are
    touched). Rule beautifications must re-verify the generator and re-pin —
    that re-check is the point, not an inconvenience."""
    from scripts.canonical_profile_gate import normalized_rule_hash
    src = rules.get(task_id)
    if not src:
        return [], ["rule-hash: no canonical rule available to compare"]
    actual = normalized_rule_hash(src)
    declared = getattr(module, "RULE_HASH", None)
    if declared is None:
        return [], [f"rule-hash: no RULE_HASH pin (current rule hash: {actual})"]
    if declared != actual:
        return ([f"rule-hash: generator pinned RULE_HASH={declared} but the canonical "
                 f"rule is now {actual} — the rule changed since this generator was "
                 f"written (the wrong-task staleness class); re-verify and re-pin"], [])
    return [], []


def probe_dead_bands(all_in, n_bands, seeds):
    """DEAD DIFFICULTY KNOB. If every (seed, index) produces byte-identical
    instances across easy/medium/hard, the difficulty axis does nothing —
    usually the band never entered any draw (the 8127b8dce4c5 class)."""
    if n_bands < 2 or len(all_in) != n_bands * seeds:
        return []
    for sd in range(seeds):
        base = all_in[sd]
        if any(all_in[b * seeds + sd] != base for b in range(1, n_bands)):
            return []
    return ["dead-bands: easy/medium/hard produce byte-identical instances for "
            "every sampled seed — the difficulty knob never enters any draw"]


def _minimal_impostors(g):
    """Named tiny shapes on the accepted grid's own modal background."""
    h, w = _dims(g)
    flat = [v for row in g for v in row]
    modal = _majority(g)
    nz = sorted(c for c in _palette(g) if c != modal)
    if not nz:
        return []
    fg = nz[0]
    out = [
        ("all_background", [[modal] * w for _ in range(h)]),
        ("full_one_color", [[fg] * w for _ in range(h)]),
    ]
    for name, cells in (
        ("singleton", [(h // 2, w // 2)]),
        (
            "solid_2x2",
            [
                (r, c)
                for r in range(min(2, h))
                for c in range(min(2, w))
            ],
        ),
        ("short_line", [(h // 2, c) for c in range(min(4, w))]),
    ):
        mutated = [[modal] * w for _ in range(h)]
        for r, c in cells:
            mutated[r][c] = fg
        out.append((name, mutated))
    return out


def _mutations(g, rng):
    """Structure-destroying-but-plausible mutations for self_check testing."""
    h, w = _dims(g)
    flat = [v for row in g for v in row]
    sh = flat[:]
    rng.shuffle(sh)
    yield [sh[r * w:(r + 1) * w] for r in range(h)]                      # cell shuffle
    if h == w and h > 1:
        yield [[g[c][r] for c in range(h)] for r in range(w)]            # transpose
    modal = _majority(g)
    nz = sorted(c for c in _palette(g) if c != modal)
    if nz:
        col = rng.choice(nz)
        m2 = [row[:] for row in g]
        r0, c0 = rng.randrange(h), rng.randrange(w)
        for dr in range(2):
            for dc in range(2):
                m2[min(h - 1, r0 + dr)][min(w - 1, c0 + dc)] = col
        yield m2                                                          # 2x2 stomp
    if len(nz) >= 2:
        a, b = nz[0], nz[1]
        yield [[b if v == a else a if v == b else v for v in row] for row in g]   # color swap
    # Minimal impostors catch shape-blind early-return exceptions. These are
    # recurring false accepts: a named degenerate branch checks only
    # palette/count and accidentally accepts arbitrary tiny shapes.
    for _, mutation in _minimal_impostors(g):
        yield mutation


def probe_rule_source_parity(task_id, rules):
    """RULE-SOURCE DIVERGENCE. The training stream + defect lint read the rule
    from CANONICAL, but the generator runner (run_one/run_batch — what
    lint_generator --validate and the SFT builders use) resolves it from
    data/base/solutions/*.json. When canonical is updated without the base file
    (the 2026-07-02 wrong-task class: 7 stale files across 5 tasks), the two
    pipelines silently apply DIFFERENT rules to the same generator."""
    src = rules.get(task_id)
    if not src:
        return []
    try:
        from puzzle_generators.runner import _load_rule
        base_src, base_file = _load_rule(task_id)
    except Exception:
        return []                     # no resolvable base rule — runner falls back
    def _h(s):
        return hashlib.sha256(" ".join(s.split()).encode()).hexdigest()[:12]
    if _h(base_src) != _h(src):
        return [(f"rule-source-divergence: {base_file} carries a different rule "
                 f"text than canonical ({_h(base_src)} vs {_h(src)}). "
                 "Canonical program_solution is active authority; align selected target_code "
                 "only after review, preserving archival raw_code. Non-applying proposal: "
                 f"arcpuzzles authority-sync {task_id} --selected-only; then check "
                 "authority_sync and rule_smoke. Semantic edits are refused.", base_src)]
    return []


def _valid_arc_grid(g):
    """Full ARC validity: rectangular, 1..30 per side, every value an int 0..9."""
    if not _is_grid(g):
        return False
    h, w = len(g), len(g[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return False
    return all(
        len(row) == w
        and all(
            isinstance(v, int)
            and not isinstance(v, bool)
            and 0 <= v <= 9
            for v in row
        )
        for row in g
    )


def probe_texture_domain_overlap(module) -> list[str]:
    """Reject textures advertised as both ordinary-valid and degenerate.

    ``DEGENERATE_TEXTURES`` are negative fixtures, not members of the training
    distribution.  Putting the same spelling in ``AXES['texture'].valid``
    makes override tooling treat an intentionally invalid fixture as lawful.
    ``LAWFUL_DEGENERATE_TEXTURES`` remains the explicit edge-but-valid escape.
    """
    axes = getattr(module, "AXES", None)
    if not isinstance(axes, dict):
        return []
    spec = axes.get("texture")
    if not isinstance(spec, dict):
        return []
    raw_valid = spec.get("valid")
    if isinstance(raw_valid, str):
        valid = {item.strip() for item in raw_valid.split("|") if item.strip()}
    elif isinstance(raw_valid, (list, tuple, set, frozenset)):
        valid = {str(item) for item in raw_valid}
    else:
        return []
    degenerate = set(getattr(module, "DEGENERATE_TEXTURES", ()) or ())
    lawful = set(getattr(module, "LAWFUL_DEGENERATE_TEXTURES", ()) or ())
    overlap = sorted((valid & degenerate) - lawful)
    if not overlap:
        return []
    return [
        "texture-domain-overlap: AXES['texture'].valid includes degenerate "
        f"negative fixture(s) {overlap!r}; remove them from the ordinary valid "
        "domain or explicitly classify a genuinely lawful edge case in "
        "LAWFUL_DEGENERATE_TEXTURES"
    ]


def probe_texture_overrides(module, seeds=tuple(range(1, 9))):
    """DECLARED-BUT-BROKEN TEXTURE OVERRIDES. DEGENERATE_TEXTURES / HELPFUL_TEXTURES
    advertise `generate(..., texture=name)` branches, but no gate ever CALLS them —
    a crashing, invalid, or dead branch (byte-identical to the un-textured draw for
    every seed) ships silently and would poison/abort any consumer that finally uses
    it. Every declared name is invoked here. Returns (warns, notes).

    Probe uses 8 seeds: with only 3, a texture equal to one of N random
    palette/variant choices false-positives as "dead" whenever all 3 hashed
    seeds coincidentally pick that choice (≈N^-2 per generator — dozens of
    false warnings corpus-wide; found live on a631936f7715)."""
    warns, notes = [], []
    axes = getattr(module, "AXES", None)
    has_texture_axis = isinstance(axes, dict) and "texture" in axes
    # DEGENERATE_TEXTURES historically served two incompatible roles: names
    # accepted by generate(..., texture=...) and labels for negative fixtures
    # produced by make_degenerate(). Only the former belong in this override
    # probe, and only when the module actually declares a texture axis.
    degen = (
        tuple(getattr(module, "DEGENERATE_TEXTURES", ()) or ())
        if has_texture_axis else ()
    )
    helpful = tuple(getattr(module, "HELPFUL_TEXTURES", ()) or ())
    lawful_degenerate = set(
        getattr(module, "LAWFUL_DEGENERATE_TEXTURES", ()) or ()
    )
    if not degen and not helpful:
        return warns, notes
    base = {}
    for sd in seeds:
        try:
            base[sd] = _norm(module.generate(sd, sd, difficulty="medium"))
        except Exception:
            return warns, notes            # baseline broken — reported elsewhere
    sc = getattr(module, "self_check", None)
    for kind, names in (("degenerate", degen), ("helpful", helpful)):
        for name in names:
            outs = []
            for sd in seeds:
                try:
                    g = module.generate(sd, sd, difficulty="medium", texture=name)
                except Exception as e:
                    warns.append(f"texture-crash: declared {kind} texture {name!r} "
                                 f"raises {e!r}"[:220])
                    outs = None
                    break
                if not _valid_arc_grid(g):
                    warns.append(f"texture-invalid: {kind} texture {name!r} returns a "
                                 f"non-grid / ragged / out-of-range result")
                    outs = None
                    break
                outs.append(_norm(g))
            if not outs:
                continue
            if all(o == base[sd] for o, sd in zip(outs, seeds)):
                warns.append(f"texture-dead: {kind} texture {name!r} is byte-identical "
                             f"to the un-textured draw for every sampled seed — the "
                             f"override is silently ignored")
                continue
            if callable(sc):
                fails = 0
                for o in outs:
                    try:
                        fails += bool(_call_self_check(sc, o, "medium"))
                    except Exception:
                        fails += 1
                # A HELPFUL texture must stay in-distribution; a DEGENERATE one is
                # EXPECTED to trip the mirror (that is its purpose).
                if kind == "helpful" and fails:
                    warns.append(f"texture-offdist: helpful texture {name!r} fails "
                                 f"self_check on {fails}/{len(outs)} draws — a "
                                 f"'helpful' variant must stay rule-valid")
                if kind == "degenerate" and fails == 0:
                    message = (
                        f"degenerate texture {name!r} passes self_check on all "
                        "sampled draws"
                    )
                    if name in lawful_degenerate:
                        notes.append(
                            message
                            + " (explicitly exempted as lawful edge-but-valid)"
                        )
                    else:
                        warns.append(
                            message
                            + " — declare it in LAWFUL_DEGENERATE_TEXTURES "
                            "only if this is intentional"
                        )
    return warns, notes


def _call_self_check(sc, grid, band):
    try:
        return sc(grid, difficulty=band)
    except TypeError:
        return sc(grid)


def probe_selfcheck_power(module, inputs, bands):
    """Mutation-test self_check(): destroy the structure of its own ACCEPTED
    instances and count rejections. A self_check that accepts nearly every
    shuffle/stomp/swap verifies nothing (the 'loose even-area test' class the
    reviewers keep strengthening by hand)."""
    sc = getattr(module, "self_check", None)
    if not callable(sc):
        return []
    import random as _random
    rejected = total = used = 0
    for g, band in zip(inputs, bands):
        if not _is_grid(g) or used >= 6:
            continue
        try:
            if _call_self_check(sc, g, band):
                continue                      # baseline instance doesn't pass — skip
        except Exception:
            continue
        used += 1
        rng = _random.Random(0xC0FFEE + used)
        for mut in _mutations(g, rng):
            total += 1
            try:
                if _call_self_check(sc, mut, band):
                    rejected += 1
            except Exception:
                rejected += 1                 # raising on garbage counts as a reject
    if total >= 8 and rejected / total < 0.30:
        return [f"selfcheck-power: self_check rejected only {rejected}/{total} structure-"
                f"destroying mutations of its own accepted instances — the invariant is "
                f"likely toothless (includes all-background/full, singleton, solid-2x2, "
                f"and short-line impostors, not only shuffle/transpose)"]
    return []


def probe_mutation_fixtures(module):
    """Task-local structural-mutation hook (worker ask WFB-002, batch v13-h).

    A generator may declare its own must-reject impostors — the task-semantic
    near-misses generic mutations can't construct (rank-selection aliasing,
    malformed distractor topology, ...):

        def mutation_fixtures():
            return [("two_component_rank_alias", grid), ...]

    Every declared fixture that self_check ACCEPTS is an ERROR: the author
    declared it malformed, so acceptance is a broken invariant, not a style
    issue. No hook declared -> no findings (fully optional)."""
    fixtures_fn = getattr(module, "mutation_fixtures", None)
    sc = getattr(module, "self_check", None)
    if not callable(fixtures_fn) or not callable(sc):
        return []
    try:
        fixtures = list(fixtures_fn())
    except Exception as e:
        return [f"mutation-fixtures: mutation_fixtures() raised {e!r} — fix or remove the hook"]
    findings = []
    for entry in fixtures:
        try:
            name, grid = entry
        except Exception:
            findings.append(f"mutation-fixtures: malformed entry {entry!r} (want (name, grid))")
            continue
        try:
            errors = _call_self_check(sc, grid, None)
        except Exception:
            continue                          # raising on garbage counts as a reject
        if not errors:
            findings.append(
                f"mutation-fixtures: self_check ACCEPTED declared impostor {name!r} "
                "— the task-local must-reject contract is broken"
            )
    return findings
    return []


def _canonical_minimal_kinds(train):
    """Minimal probe kinds directly witnessed by canonical training inputs.

    A generic tiny-shape heuristic must not flag the task's literal grammar
    (for example, a lone marker on a uniform field).  Keep the exemption
    evidence-based: only exact canonical input geometry can calibrate it.
    """
    lawful = set()
    for pair in train or ():
        grid = _norm(pair[0]) if isinstance(pair, (list, tuple)) and pair else None
        if not _is_grid(grid):
            continue
        modal = _majority(grid)
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value != modal]
        if len(cells) == 1:
            lawful.add("singleton")
        # Calibrate additional named shapes only when the exact probe grid
        # itself is witnessed by a canonical input. Acceptance of another
        # grammar must not blanket-disable unrelated minimal mutations.
        for name, mutation in _minimal_impostors(grid):
            if name in {"solid_2x2", "short_line"} and mutation == grid:
                lawful.add(name)
    return lawful


def probe_selfcheck_minimal_impostors(module, inputs, bands, canonical_train=None):
    """Name every minimal impostor accepted on the task's real background.

    The aggregate power ratio can look healthy while one dangerous exception
    remains (for example, four mutations reject but a marker-only singleton
    passes). Keep this a separate detector so an old generic
    ``selfcheck-power: fixed`` disposition cannot waive the new evidence.
    """
    sc = getattr(module, "self_check", None)
    if not callable(sc):
        return []
    accepted = Counter()
    totals = Counter()
    used = 0
    for grid, band in zip(inputs, bands):
        if not _is_grid(grid) or used >= 6:
            continue
        try:
            if _call_self_check(sc, grid, band):
                continue
        except Exception:
            continue
        used += 1
        for name, mutation in _minimal_impostors(grid):
            totals[name] += 1
            try:
                rejected = bool(_call_self_check(sc, mutation, band))
            except Exception:
                rejected = True
            if not rejected:
                accepted[name] += 1
    canonical_lawful = _canonical_minimal_kinds(canonical_train)
    bad = [
        f"{name} {accepted[name]}/{totals[name]}"
        for name in sorted(accepted)
        if accepted[name] and name not in canonical_lawful
    ]
    if not bad:
        return []
    return [
        "selfcheck-minimal-impostor: self_check accepted "
        + ", ".join(bad)
        + " probes built on its own modal background; narrow the named "
          "degenerate grammar or give task-semantic evidence that each shape "
          "is lawful"
    ]


# ----- machinery -------------------------------------------------------------
def _load_module(path: Path, name: str):
    return load_module_from_path(name, path)


def _load_gen(task_id, gen_file=None):
    p = Path(gen_file) if gen_file else GEN_ROOT / task_id / "generator.py"
    return _load_module(p, f"g_{task_id}"), p


def _generic_path(task_id: str) -> Path:
    """Map generic_dense_field_gen2 -> generic/concepts/dense_field/gen2.py."""
    tail = task_id[len("generic_"):]
    family, sep, gen = tail.rpartition("_")
    if not sep or not family or not gen.startswith("gen"):
        raise ValueError(f"generic task id must look like generic_<family>_genN: {task_id}")
    return GENERIC_ROOT / family / f"{gen}.py"


def _calibrate_pair_detectors(train):
    """Run each pair detector on the canonical pairs themselves; a detector that
    fires there measures the TASK, not a defect — disable it for this task."""
    disabled, notes = set(), []
    canon = [(_norm(p[0]), _norm(p[1])) for p in (train or [])
             if _is_grid(_norm(p[0])) and _is_grid(_norm(p[1]))]
    if not canon:
        return disabled, notes
    c_ins = [p[0] for p in canon]
    c_outs = [p[1] for p in canon]
    for name, fn in PAIR_DETECTORS:
        for gin, gout in canon:
            ctx = {"input": gin, "output": gout, "train": train, "has_self_check": True,
                   "all_outputs": c_outs, "all_inputs": c_ins, "task_id": "__calibration__"}
            try:
                fired = fn(ctx)
            except Exception:
                fired = []
            if fired:
                disabled.add(name)
                notes.append(f"calibrated-out: {name} fires on the canonical task itself "
                             f"— property is the task, not a defect")
                break
    return disabled, notes


def _run_detectors(
    task_id,
    *,
    has_sc,
    all_in,
    all_out,
    train,
    expected_codomain=None,
    solid_output_justification="",
    in_bands=None,
):
    """Run the registry over prepared examples; returns (issue_counter, notes)."""
    issues = Counter()
    disabled, notes = _calibrate_pair_detectors(train)
    for name, fn in PAIR_DETECTORS:
        if name in disabled:
            continue
        for i in range(len(all_in)):
            ctx = {"input": all_in[i], "output": all_out[i] if i < len(all_out) else None,
                   "train": train, "has_self_check": has_sc, "expected_codomain": expected_codomain,
                   "solid_output_justification": solid_output_justification,
                   "all_outputs": all_out, "all_inputs": all_in, "task_id": task_id,
                   "in_bands": in_bands}
            try:
                found = fn(ctx)
            except Exception as e:
                found = [f"[detector {name} crashed: {e!r}]"]
            for msg in found:
                issues[f"{name}: {msg}"] += 1
    for name, fn in TASK_DETECTORS:
        ctx = {"input": all_in[0] if all_in else None,
               "output": all_out[0] if all_out else None,
               "train": train, "has_self_check": has_sc, "expected_codomain": expected_codomain,
               "solid_output_justification": solid_output_justification,
               "all_outputs": all_out, "all_inputs": all_in, "task_id": task_id,
               "in_bands": in_bands}
        try:
            found = fn(ctx)
        except Exception as e:
            found = [f"[detector {name} crashed: {e!r}]"]
        for msg in found:
            issues[f"{name}: {msg}"] += 1
    return issues, notes


def _split_severity(issues):
    """Counter of 'name: msg' -> (error list, warn list) of {issue, count} dicts."""
    errs, warns = [], []
    for k, v in issues.most_common():
        name = k.split(":", 1)[0]
        (warns if name in WARN_DETECTORS else errs).append({"issue": k, "count": v})
    return errs, warns


def lint_generic(task_id, *, seeds, bands):
    """Lint generic concept generators, which emit full task dicts not bare grids.

    They have no canonical per-puzzle Racket row, so use the generated task's own
    train/test pair outputs for identity/diversity checks and skip canonical-
    anchored detectors (``train`` is None). Module-level probes (axis honesty,
    hashseed, selfcheck power) target the per-puzzle GenCtx contract and are
    skipped here — reported, not silent."""
    p = _generic_path(task_id)
    m = _load_module(p, f"g_{task_id}")
    gen_task = getattr(m, "generate_task", None)
    if not callable(gen_task):
        return {"task_id": task_id, "error": "generic generator has no generate_task()",
                "issues": [], "warnings": [], "notes": []}
    has_sc = callable(getattr(m, "self_check_task", None))
    all_in, all_out = [], []
    for band in bands:
        for sd in range(1, seeds + 1):
            try:
                task = gen_task(sd, difficulty=band)
            except Exception as e:
                return {"task_id": task_id, "error": f"generate_task() raised: {e!r}"[:160],
                        "issues": [], "warnings": [], "notes": []}
            for pair in list(task.get("train") or []) + list(task.get("test") or []):
                all_in.append(_norm(pair.get("input")))
                all_out.append(_norm(pair.get("output")))
    issues, notes = _run_detectors(task_id, has_sc=has_sc, all_in=all_in, all_out=all_out,
                                   train=None,
                                   expected_codomain=getattr(m, "EXPECTED_OUTPUT_CODOMAIN", None),
                                   solid_output_justification=getattr(
                                       m, "SOLID_OUTPUT_JUSTIFICATION", ""
                                   ))
    errs, warns = _split_severity(issues)
    notes.append("probes skipped (generic generator: no per-puzzle GenCtx/AXES contract)")
    return {"task_id": task_id, "error": None, "has_self_check": has_sc,
            "racket": False, "issues": errs, "warnings": warns, "notes": notes}


def _decode_grid(g):
    """Canonical stores some grids as digit-string rows ('002050'); 609 tasks
    ship that way and used to silently skip every canonical-anchored detector
    (rows failed _is_grid). Decode to list-of-int-lists; pass real grids through."""
    if isinstance(g, list) and g and isinstance(g[0], str):
        try:
            return [[int(ch) for ch in row] for row in g]
        except ValueError:
            return g
    return g


def _load_canon():
    """task_id -> list[(input, output)] train pairs from canonical."""
    out = {}
    if not CANON.exists():
        return out
    for line in open(CANON):
        try:
            r = json.loads(line)
        except Exception:
            continue
        t = r.get("task_id")
        tr = r.get("train") or []
        if isinstance(tr, dict):
            tr = [tr]
        if t and tr:
            out[t] = [(_decode_grid(p.get("input")), _decode_grid(p.get("output")))
                      for p in tr]
    return out


def _rule_body(src):
    """Apply the canonical rule to grid `g` via the SAME normalization as the
    generator runner (puzzle_generators.rule_wrap.wrap_rule) — not a divergent
    local copy that missed dict literals, for/X shorthand, and the h/w-in-lambda
    fix (reviewer gpt55pro(10): diagnostic-vs-production normalizer drift)."""
    from puzzle_generators.rule_wrap import wrap_rule
    return f"({wrap_rule(src)} g)"


def lint_one(task_id, *, rules, canon, bridge, seeds, bands, gen_file=None, fast=False):
    if task_id.startswith("generic_"):
        return lint_generic(task_id, seeds=seeds, bands=bands)
    m, gen_path = _load_gen(task_id, gen_file)
    has_sc = callable(getattr(m, "self_check", None))
    all_in, all_out, in_bands = [], [], []
    rule_body = _rule_body(rules[task_id]) if (bridge and task_id in rules) else None

    # Capture GenCtx draw provenance during the sampling loop (axis-honesty probe).
    ctxs = []
    observer_ok = False
    try:
        from puzzle_generators import base as gen_base
        gen_base.set_ctx_observer(ctxs.append)
        observer_ok = True
    except Exception:
        pass
    import time as _time
    steady_timings = []
    restart_timings_skipped = 0
    crash_idx = []
    try:
        for band in bands:
            for sd in range(1, seeds + 1):
                try:
                    g = m.generate(sd, sd, difficulty=band)
                except Exception as e:
                    return {"task_id": task_id, "error": f"generate() raised: {e!r}"[:160],
                            "issues": [], "warnings": [], "notes": []}
                all_in.append(_norm(g))
                in_bands.append(band)
                o = None
                if rule_body is not None:
                    t0 = _time.time()
                    define_restarted = False
                    eval_restarted = False
                    try:
                        bridge.define_grid("g", g)
                        define_restarted = bool(
                            getattr(bridge, "restarted_last_call", False)
                        )
                        o = _norm(bridge.eval_text(rule_body))
                        eval_restarted = bool(
                            getattr(bridge, "restarted_last_call", False)
                        )
                    except Exception:
                        o = None
                        crash_idx.append(len(all_out))
                        eval_restarted = bool(
                            getattr(bridge, "restarted_last_call", False)
                        )
                    elapsed = _time.time() - t0
                    # Startup/restart cost measures the bridge lifecycle, not
                    # the Racket rule. rule_smoke uses the same exclusion and
                    # reports restarts separately.
                    if define_restarted or eval_restarted:
                        restart_timings_skipped += 1
                    else:
                        steady_timings.append(elapsed)
                all_out.append(o)
    finally:
        if observer_ok:
            gen_base.set_ctx_observer(None)

    issues, notes = _run_detectors(task_id, has_sc=has_sc, all_in=all_in, all_out=all_out,
                                   train=canon.get(task_id),
                                   expected_codomain=getattr(m, "EXPECTED_OUTPUT_CODOMAIN", None),
                                   solid_output_justification=getattr(
                                       m, "SOLID_OUTPUT_JUSTIFICATION", ""
                                   ),
                                   in_bands=in_bands)
    errs, warns = _split_severity(issues)

    from review_diagnostics import compare_structure, scalar_override_probes
    structure = compare_structure(canon.get(task_id) or [],
                                  [{"input":i,"output":o} for i,o in zip(all_in,all_out) if o is not None])
    structure["generator_sha256"] = hashlib.sha256(Path(gen_path).read_bytes()).hexdigest()
    structure["rule_source_sha256"] = hashlib.sha256(rules.get(task_id, "").encode()).hexdigest()
    if structure["status"] == "advisory_mismatch":
        warns.append({"issue":"generator/authority structural mismatch: " + ", ".join(structure["disjoint_features"]), "count":1})
    scalar_findings = scalar_override_probes(m)
    for finding in scalar_findings:
        warns.append({"issue":"strict-scalar: " + str(finding), "count":1})

    # Module-level probes (ERROR/WARN strings appended directly).
    ax_errs, ax_warns = probe_axis_honesty(m, ctxs)
    errs += [{"issue": e, "count": 1} for e in ax_errs]
    warns += [{"issue": w, "count": 1} for w in ax_warns]
    warns += [{"issue": w, "count": 1} for w in probe_selfcheck_power(m, all_in, in_bands)]
    errs += [{"issue": e, "count": 1} for e in probe_mutation_fixtures(m)]
    warns += [
        {"issue": w, "count": 1}
        for w in probe_selfcheck_minimal_impostors(
            m, all_in, in_bands, canonical_train=canon.get(task_id)
        )
    ]
    rh_errs, rh_notes = probe_rule_hash(m, task_id, rules)
    errs += [{"issue": e, "count": 1} for e in rh_errs]
    notes += rh_notes
    for msg, base_src in probe_rule_source_parity(task_id, rules):
        # textual divergence found — decide severity BEHAVIORALLY: apply the
        # base-file rule to the sampled inputs and compare with canonical's out.
        sem = None
        if bridge is not None:
            base_body = _rule_body(base_src)
            sem, checked = False, 0
            for g_in, o in zip(all_in, all_out):
                if o is None or checked >= 6:
                    continue
                checked += 1
                try:
                    bridge.define_grid("g", g_in)
                    bo = _norm(bridge.eval_text(base_body))
                except Exception:
                    sem = True
                    break
                if bo != o:
                    sem = True
                    break
            if not checked:
                sem = None
        if sem:
            errs.append({"issue": msg + " — and the two rules BEHAVE differently "
                                        "on sampled inputs (wrong-task class)",
                         "count": 1})
        elif sem is False:
            warns.append({"issue": msg + " — behavior matches on sampled inputs "
                                         "(unsynced beautification)", "count": 1})
        else:
            warns.append({"issue": msg + " (no bridge — semantic equivalence "
                                         "unchecked)", "count": 1})
    warns += [{"issue": w, "count": 1}
              for w in probe_dead_bands(all_in, len(bands), seeds)]
    errs += [
        {"issue": message, "count": 1}
        for message in probe_texture_domain_overlap(m)
    ]
    tx_warns, tx_notes = probe_texture_overrides(m)
    warns += [{"issue": w, "count": 1} for w in tx_warns]
    notes += tx_notes
    slowest = max(steady_timings, default=0.0)
    if restart_timings_skipped:
        notes.append(
            "rule-performance: excluded "
            f"{restart_timings_skipped} startup/restart-contaminated call(s) "
            "from steady-state latency"
        )
    if rule_body is not None and slowest > 5.0:
        warns.append({"issue": f"rule-performance: slowest rule application took "
                               f"{slowest:.1f}s — a Kaggle/timeout hazard on this "
                               f"generator's inputs", "count": 1})
    if crash_idx:
        warns.append({"issue": f"rule-crash: {len(crash_idx)}/{len(all_out)} rule "
                               f"applications crashed (rule_smoke gates this)", "count": 1})
        if has_sc:
            sc = getattr(m, "self_check")
            blind = 0
            for i in crash_idx:
                try:
                    accepted = not _call_self_check(sc, all_in[i], in_bands[i])
                except Exception:
                    accepted = False
                blind += int(accepted)
            if blind:
                warns.append({"issue": f"selfcheck-blindspot: self_check ACCEPTED "
                                       f"{blind}/{len(crash_idx)} inputs the rule crashes "
                                       f"on — the safety net misses a real failure mode",
                              "count": 1})
    # Same blind-spot angle for NO-OP instances: only when identity_demo actually
    # fired (self-calibration keeps intentionally-identity tasks out of here).
    if has_sc and any(it["issue"].startswith("identity_demo") for it in errs):
        sc = getattr(m, "self_check")
        id_idx = [i for i, (gi, go) in enumerate(zip(all_in, all_out)) if go == gi]
        blind = 0
        for i in id_idx:
            try:
                blind += int(not _call_self_check(sc, all_in[i], in_bands[i]))
            except Exception:
                pass
        if blind:
            warns.append({"issue": f"selfcheck-blindspot: self_check ACCEPTED "
                                   f"{blind}/{len(id_idx)} inputs the rule NO-OPS on "
                                   f"— it does not mirror the rule's trigger "
                                   f"preconditions", "count": 1})
    if fast:
        notes.append("hashseed probe skipped (--fast)")
    else:
        errs += [{"issue": e, "count": 1} for e in probe_hashseed(gen_path)]
    if not observer_ok:
        notes.append("axis probe skipped: gen_base observer unavailable")

    return {"task_id": task_id, "error": None, "has_self_check": has_sc,
            "racket": rule_body is not None, "structure_diagnostic": structure,
            "strict_scalar_probes": scalar_findings,
            "strict_scalar_scope": "Request-contract diagnostics on accepted control calls: seed/index/difficulty and exact integer/color override endpoints in easy/default/hard bands. Rejected controls or unavailable domains are unknown coverage, not proof of valid scalar handling or semantic correctness.",
            "issues": errs, "warnings": warns, "notes": notes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--bands", default="easy,medium,hard")
    ap.add_argument("--json", "--json-out", dest="json", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="WARN-level findings also FLAG (default: printed only)")
    ap.add_argument("--fast", action="store_true",
                    help="skip subprocess probes (hashseed) for bulk sweeps")
    ap.add_argument("--generator-file", default=None,
                    help="lint this candidate generator FILE against the (single) given "
                         "task_id — for patch review / old-version regression runs")
    a = ap.parse_args()

    ids = list(a.ids)
    if a.all:
        ids = sorted(p.name for p in GEN_ROOT.iterdir()
                     if (p / "generator.py").exists())
    if a.limit:
        ids = ids[:a.limit]
    if not ids:
        print("no task_ids (give ids or --all)"); return 1
    if a.generator_file and len(ids) != 1:
        print("--generator-file requires exactly one task_id"); return 1

    canon = _load_canon()
    rules = {}
    for line in (open(CANON) if CANON.exists() else []):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("task_id") in set(ids) and r.get("program_solution"):
            rules[r["task_id"]] = r["program_solution"]

    bridge = None
    racket_skipped_reason = ""
    if shutil.which("racket"):
        try:
            from arc_repl.racket_bridge import RacketBridge
            bridge = RacketBridge(max_calls_before_restart=48)
        except Exception as e:
            racket_skipped_reason = f"racket present but bridge init failed: {e!r}"
            print(f"  {racket_skipped_reason} — static detectors only")
    else:
        racket_skipped_reason = "racket not on PATH"
        print("  racket not on PATH — rule-dependent detectors skipped "
              "(run scripts/setup_racket.sh). Static detectors still run.")
    # --strict promises the FULL battery: a green exit with rule-dependent
    # detectors silently disabled is a false green (worker WFB: EWF batch
    # v13-d, r01). In strict mode an incomplete run must fail loud.
    if a.strict and racket_skipped_reason:
        print(f"LOUD: --strict but rule-dependent detectors are UNAVAILABLE "
              f"({racket_skipped_reason}); refusing to report a clean strict "
              "run on static detectors alone.")
        return 2

    reports, flagged = [], 0
    try:
        for t in ids:
            try:
                rep = lint_one(t, rules=rules, canon=canon, bridge=bridge,
                               seeds=a.seeds, bands=a.bands.split(","),
                               gen_file=a.generator_file, fast=a.fast)
            except Exception as e:
                rep = {"task_id": t, "error": f"lint crashed: {e!r}"[:160],
                       "issues": [], "warnings": [], "notes": []}
            reports.append(rep)
            errs = rep.get("issues") or []
            warns = rep.get("warnings") or []
            is_flagged = bool(rep.get("error") or errs or (a.strict and warns))
            if is_flagged:
                flagged += 1
            if rep.get("error") or errs or warns:
                head = rep.get("error") or f"{len(errs)} issue(s), {len(warns)} warning(s)"
                print(f"\n{t}: {head}")
                for it in errs:
                    print(f"    [{it['count']:>3}x] {it['issue']}")
                for it in warns:
                    print(f"    [{it['count']:>3}x] WARN {it['issue']}")
                for note in rep.get("notes") or []:
                    print(f"          note: {note}")
    finally:
        if bridge is not None:
            try:
                bridge.shutdown()
            except Exception:
                pass
    print(f"\nscanned {len(ids)}; FLAGGED {flagged}")
    # corpus rollup
    cat = Counter()
    for rep in reports:
        for it in (rep.get("issues") or []) + (rep.get("warnings") or []):
            cat[it["issue"].split(":", 1)[0]] += 1
    if cat:
        print("by detector:", dict(cat.most_common()))
    if a.json:
        json.dump(reports, open(a.json, "w"), indent=1)
        print(f"-> {a.json}")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
