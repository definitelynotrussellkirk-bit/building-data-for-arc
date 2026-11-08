#!/usr/bin/env python3
"""Rule-smoke: apply a task's REAL Racket rule to its generator's output.

`lint_generator.py` checks structure/AXES/diversity but never runs the rule, so
non-constructive (crashing) and output-degenerate generators pass lint while
producing garbage. This closes that gap: for each task it loads the canonical
`program_solution`, runs the generator across bands/seeds, applies the rule via
the Racket bridge, and reports crashes + distinct OUTPUTS + fired (non-trivial)
fraction. Flags CRASH>0 or distinct_outputs < --min-outputs.

  python3 scripts/rule_smoke.py 56a06c9b29a3 6c68e1b008a5      # explicit ids
  python3 scripts/rule_smoke.py --grep "find pair"            # by docstring
  python3 scripts/rule_smoke.py --grep "find pair" --seeds 6 --min-outputs 5
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import runpy
import shutil
import sys
import time
from pathlib import Path

# Make `arc_repl` importable when run as `python3 scripts/rule_smoke.py`
# (otherwise the RacketBridge import fails unless PYTHONPATH is set). Harvested
# from reviewer gpt55_pro_278.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from puzzle_generators.rule_wrap import wrap_rule
# Both the packet's shared/tools and staged scripts layouts ship this sibling.
# Load exact local bytes; do not borrow a scripts namespace or hide import errors.
load_module_from_path = runpy.run_path(
    str(Path(__file__).resolve().with_name("generator_module_loader.py"))
)["load_module_from_path"]

ROOT = "puzzle_generators/per_puzzle"
CANON = "data/canonical/puzzles.jsonl"


def load_rules(ids):
    """Load each task's executable rule using the same fallback order as the
    generator runner.  Canonical puzzles.jsonl is still preferred where present,
    but synthetic / review-bank generators can now be smoked when their only
    checked rule lives in solvers.grounded_rules or data/base/solutions.
    """
    want = set(ids)
    out = {}
    if os.path.exists(CANON):
        for line in open(CANON):
            r = json.loads(line)
            t = r.get("task_id")
            if t in want and r.get("program_solution"):
                out[t] = r["program_solution"]
    missing = want - set(out)
    if missing:
        try:
            from puzzle_generators.runner import _load_rule
        except Exception:
            _load_rule = None
        if _load_rule is not None:
            for t in sorted(missing):
                try:
                    src, _label = _load_rule(t)
                except Exception:
                    continue
                if src:
                    out[t] = src
    return out


def _norm_grid(g):
    if isinstance(g, list) and g and isinstance(g[0], str):
        return [[int(ch) for ch in row] for row in g]
    return g


def load_canonical_output_counts(ids):
    """task_id -> distinct canonical train outputs (reviewer gpt55pro_384).

    Some ARC tasks have intentionally tiny answer spaces (solid swatches, binary
    quadrant labels, categorical matrices). Those should not fail the generic
    diversity floor merely because the generator's outputs are as low-cardinality
    as the canonical demonstrations themselves."""
    want = set(ids)
    out = {}
    for line in open(CANON):
        r = json.loads(line)
        t = r.get("task_id")
        if t not in want:
            continue
        vals = set()
        for p in r.get("train") or []:
            if isinstance(p, dict) and "output" in p:
                vals.add(json.dumps(_norm_grid(p["output"]), sort_keys=True))
        out[t] = len(vals)
    return out


def load_canonical_identity_tasks(ids):
    """Return tasks whose own training set contains a lawful identity pair.

    Identity is normally a strong smoke failure, but some ARC tasks explicitly
    include an already-complete input.  A mixed curriculum for such a task must
    retain that demonstrated branch instead of deleting it merely to satisfy a
    generic no-op check.
    """
    want = set(ids)
    out = set()
    with open(CANON, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            task_id = row.get("task_id")
            if task_id not in want:
                continue
            for pair in row.get("train") or []:
                if not isinstance(pair, dict):
                    continue
                if (
                    "input" in pair
                    and "output" in pair
                    and _norm_grid(pair["input"]) == _norm_grid(pair["output"])
                ):
                    out.add(task_id)
                    break
    return out


def calibrated_identity_is_lawful(
    *, identity, applied, distinct_outputs, min_outputs, canonical_identity
):
    """Accept only a diverse mixed curriculum with a canonical identity branch."""
    return (
        canonical_identity
        and 0 < identity < applied
        and distinct_outputs >= min_outputs
    )


def _grid_sha16(grid):
    """Stable short digest of a grid, so a witness is replay-checkable."""
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()[:16]


def _percentile(values, pct):
    """Nearest-rank percentile; `values` need not be sorted. None if empty."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100.0 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def rule_body(src):
    """Return a bare-bridge expression that applies the canonical rule to `g`.

    Keep this gate on the same rule-source normalization path as the producer
    (`puzzle_generators.runner`).  The previous local parser only stripped `;;`
    comments and rebuilt a custom h/w wrapper; it could diverge from `wrap_rule`
    on dict literals, for-shorthand, bare callable forms, or future wrapper fixes.
    """
    return f"({wrap_rule(src)} g)"


def _grid_literal(grid):
    """Serialize one ARC grid as a quoted Racket list literal."""
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"'({rows})"


def rule_application(src, grid):
    """Apply one wrapped rule to an inline grid in a single bridge call."""
    return f"({wrap_rule(src)} {_grid_literal(grid)})"


def purity_body(src, first_grid, second_grid):
    """One atomic A→B→A probe, immune to bridge auto-restart boundaries."""
    wrapped = wrap_rule(src)
    first = _grid_literal(first_grid)
    second = _grid_literal(second_grid)
    return (
        f"(let* ([rule {wrapped}] [a {first}] [b {second}] "
        "[out-a1 (rule a)] [ignored (rule b)] [out-a2 (rule a)]) "
        "(list out-a1 out-a2 a))"
    )


def mirror_normalized(mout):
    """rule_mirror output normalized for exact comparison with the bridge's
    grid, or None when the mirror returned a non-grid (counted as mismatch)."""
    if isinstance(mout, list) and mout and isinstance(mout[0], list):
        return [[int(v) for v in row] for row in mout]
    return None


def load_gen(task_id):
    p = f"{ROOT}/{task_id}/generator.py"
    return load_module_from_path(f"g_{task_id}", p)


def arc_bounds_violation(out):
    """Non-None reason when an oracle output is not a lawful ARC grid.

    ARC grids are rectangular, 1..30 per dimension, values 0..9. A generator
    whose scene drives the oracle past these bounds produces untrainable rows
    (v13-x WFB: 18e652e005b1 shipped a lawful-looking scene with a 1x31
    output that no generic gate rejected).
    """
    if not isinstance(out, list) or not out or not all(isinstance(r, list) for r in out):
        return "not_a_grid"
    w = len(out[0])
    if any(len(r) != w for r in out):
        return "ragged"
    if not (1 <= len(out) <= 30) or not (1 <= w <= 30):
        return f"dims_{len(out)}x{w}"
    if any(not isinstance(v, int) or v < 0 or v > 9 for r in out for v in r):
        return "bad_value"
    return None


def trivial(out):
    return (not isinstance(out, list) or not out
            or all(all(v == 0 for v in row) for row in out))


def scalar_label(out):
    """A legitimate 1x1 label task has intrinsically tiny output cardinality."""
    return isinstance(out, list) and len(out) == 1 and isinstance(out[0], list) and len(out[0]) == 1


def finite_output_codomain(module):
    """Return a declared finite output codomain size, if the generator states one.

    Some ARC tasks are intrinsically low-cardinality: for example a rule may
    choose among exactly three fixed 3x3 labels.  The normal --min-outputs
    diversity floor should not flag such tasks once all declared labels are
    observed.  Generators can declare this with EXPECTED_OUTPUT_CODOMAIN as an
    integer or as a finite container/table.
    """
    v = getattr(module, "EXPECTED_OUTPUT_CODOMAIN", None)
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v if v > 0 else None
    if isinstance(v, (list, tuple, set, frozenset, dict)):
        return len(v) if len(v) > 0 else None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="task_ids to smoke")
    ap.add_argument("--grep", help="only generators whose docstring contains this string")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--bands", default="easy,medium,hard")
    ap.add_argument("--min-outputs", type=int, default=5)
    ap.add_argument("--min-scalar-outputs", type=int, default=2,
                    help="minimum distinct outputs for intrinsic 1x1 scalar-label tasks; "
                         "these should not be held to the normal grid-diversity floor")
    ap.add_argument("--limit", type=int, default=0, help="cap number of generators scanned")
    ap.add_argument("--json-out", help=(
        "write per-task structured evidence (timing p95, input-purity, bridge "
        "restarts, first-failure witness) to this path. The worker evidence "
        "contract requires these; without it every worker reimplements a "
        "private bridge harness (v13-z WFB-702, 30d3af94d21e WFB-001)."))
    args = ap.parse_args()

    ids = list(args.ids)
    if args.grep:
        for t in sorted(os.listdir(ROOT)):
            gp = f"{ROOT}/{t}/generator.py"
            if not os.path.exists(gp):
                continue
            try:
                head = open(gp).read(600)
            except Exception:
                continue
            if args.grep in head:
                ids.append(t)
    elif not ids and args.limit:
        # Make `rule_smoke.py --limit N` a useful smoke command. Previously
        # --limit only truncated an already-selected id list, so this natural
        # invocation printed "no task_ids selected" and exited before testing
        # anything. Do NOT default to all generators without --limit; that would
        # unexpectedly launch a multi-hour Racket job.
        for t in sorted(os.listdir(ROOT)):
            gp = f"{ROOT}/{t}/generator.py"
            if os.path.exists(gp):
                ids.append(t)
    ids = sorted(set(ids))
    if args.limit:
        ids = ids[: args.limit]
    if not ids:
        print("no task_ids selected")
        return 1

    rules = load_rules(ids)
    canonical_output_counts = load_canonical_output_counts(ids)
    canonical_identity_tasks = load_canonical_identity_tasks(ids)
    bands = args.bands.split(",")
    flagged = []
    evidence_rows = []

    # Discover missing rules BEFORE starting Racket — a missing-rule audit must not
    # require a Racket binary (CI / off-box), and an absent rule is a hard CI failure.
    runnable = []
    for t in ids:
        if t not in rules:
            print(f"  {t}: NO RULE in canonical [NO_RULE]", flush=True)
            flagged.append((t, "NO_RULE", 0, 0))
        else:
            runnable.append(t)

    if runnable and not shutil.which("racket"):
        # No silent garbage: if racket isn't on PATH the bridge can't evaluate
        # anything, so flag every runnable task explicitly instead of crashing
        # mid-loop. Harvested from reviewer gpt55_pro_278.
        print("  racket not on PATH — the parity gate cannot run. Install it once with:\n"
              "    bash scripts/setup_racket.sh\n"
              "  (rootless ~34 MB download; then re-run this command).", flush=True)
        for t in runnable:
            print(f"  {t}: RACKET MISSING [RACKET_MISSING]", flush=True)
            flagged.append((t, "RACKET_MISSING", 0, 0))
        runnable = []

    if runnable:
        from arc_repl.racket_bridge import RacketBridge
        # Restart the Racket child every few dozen evals: long smoke sweeps run
        # many grids through one bridge, and a bounded restart prevents slow
        # state/memory drift in a single child (reviewer 466).
        b = RacketBridge(max_calls_before_restart=48)
        try:
            for t in runnable:
                try:
                    m = load_gen(t)
                except Exception as e:
                    print(f"  {t}: GEN LOAD FAIL {str(e)[:50]} [GEN_LOAD_FAIL]", flush=True)
                    flagged.append((t, "GEN_LOAD_FAIL", 0, 0))
                    continue
                declared_codomain = finite_output_codomain(m)
                ok = crash = fired = scalar = identity = 0
                oob_outputs = 0
                input_mutations = stateful_replays = 0
                probe_grid = probe_output = None
                reentrant_checked = False
                outs = set(); out_areas = []
                # Structured evidence the worker contract asks for. `witness`
                # pins the FIRST crash/identity to a (band, seed, sample_index)
                # so a failure is replayable instead of being a bare count —
                # a worker had to hand-replay 120 draws to find hard/seed=17
                # (30d3af94d21e WFB-001).
                timings_ms = []
                restarts_before = getattr(b, "_restarts", 0)
                restart_skipped = 0
                witness = None
                # Python-mirror parity (adopted 2026-07-29, bf9e0959b8ce
                # WFB-001): a declared rule_mirror that silently disagrees with
                # the selected Racket authority (e.g. across palette-role
                # boundaries like color 0 in `mode`) trains tests against the
                # wrong semantics. When the generator exposes one, every
                # smoked grid is also run through the mirror and compared.
                mirror_fn = getattr(m, "rule_mirror", None)
                mirror_checked = mirror_mismatch = mirror_crash = 0
                mirror_witness = None
                for band in bands:
                    for sd in range(1, args.seeds + 1):
                        try:
                            g = m.generate(sd, sd, difficulty=band)
                        except Exception as exc:
                            crash += 1
                            if witness is None:
                                witness = {"kind": "generate_crash", "band": band,
                                           "seed": sd, "sample_index": sd,
                                           "error": f"{type(exc).__name__}: {exc}"[:200]}
                            continue
                        _t0 = time.perf_counter()
                        try:
                            out = b.eval_text(rule_application(rules[t], g))
                        except Exception as exc:
                            crash += 1
                            if witness is None:
                                witness = {"kind": "rule_crash", "band": band,
                                           "seed": sd, "sample_index": sd,
                                           "input_sha16": _grid_sha16(g),
                                           "error": f"{type(exc).__name__}: {exc}"[:200]}
                            continue
                        _elapsed_ms = (time.perf_counter() - _t0) * 1000.0
                        # A call that paid child-startup cost is not a
                        # steady-state latency sample; count it, don't time it.
                        if getattr(b, "restarted_last_call", False):
                            restart_skipped += 1
                        else:
                            timings_ms.append(_elapsed_ms)
                        if isinstance(out, list) and out and isinstance(out[0], list):
                            if probe_grid is None:
                                probe_grid = copy.deepcopy(g)
                                probe_output = copy.deepcopy(out)
                            elif not reentrant_checked and g != probe_grid:
                                # Evaluate the entire A→B→A probe in one Racket
                                # expression. If the bridge reaches its bounded
                                # auto-restart threshold, this expression is
                                # still self-contained and cannot lose `g`
                                # between separate calls.
                                try:
                                    probe = b.eval_text(
                                        purity_body(rules[t], probe_grid, g)
                                    )
                                except Exception:
                                    crash += 1
                                else:
                                    if (
                                        not isinstance(probe, list)
                                        or len(probe) != 3
                                    ):
                                        crash += 1
                                    else:
                                        first_out, replay_out, input_after = probe
                                        if input_after != probe_grid:
                                            input_mutations += 1
                                        if (
                                            first_out != probe_output
                                            or replay_out != probe_output
                                        ):
                                            stateful_replays += 1
                                reentrant_checked = True
                            if arc_bounds_violation(out) is not None:
                                oob_outputs += 1
                            if callable(mirror_fn):
                                try:
                                    mout = mirror_fn(copy.deepcopy(g))
                                except Exception as exc:
                                    mirror_crash += 1
                                    if mirror_witness is None:
                                        mirror_witness = {
                                            "kind": "mirror_crash", "band": band,
                                            "seed": sd, "sample_index": sd,
                                            "input_sha16": _grid_sha16(g),
                                            "error": f"{type(exc).__name__}: {exc}"[:200]}
                                else:
                                    mirror_checked += 1
                                    norm = mirror_normalized(mout)
                                    if norm != out:
                                        mirror_mismatch += 1
                                        if mirror_witness is None:
                                            mirror_witness = {
                                                "kind": "mirror_mismatch",
                                                "band": band, "seed": sd,
                                                "sample_index": sd,
                                                "input_sha16": _grid_sha16(g),
                                                "racket_sha16": _grid_sha16(out),
                                                "mirror_repr": repr(mout)[:200]}
                            ok += 1; outs.add(str(out)); out_areas.append(len(out) * len(out[0]))
                            if scalar_label(out):
                                scalar += 1
                            if out == g:
                                identity += 1        # no-op: rule left input unchanged (was masked as fired)
                                if witness is None:
                                    witness = {"kind": "identity", "band": band,
                                               "seed": sd, "sample_index": sd,
                                               "input_sha16": _grid_sha16(g),
                                               "output_sha16": _grid_sha16(out)}
                            elif not trivial(out):
                                fired += 1
                        else:
                            crash += 1
                            if witness is None:
                                witness = {"kind": "non_grid_output", "band": band,
                                           "seed": sd, "sample_index": sd,
                                           "input_sha16": _grid_sha16(g),
                                           "output_repr": repr(out)[:200]}
                status = "OK"
                all_scalar = ok > 0 and scalar == ok
                finite_low_cardinality = (
                    declared_codomain is not None
                    and declared_codomain < args.min_outputs
                    and len(outs) >= declared_codomain
                )
                if crash > 0:
                    status = "CRASH"
                elif oob_outputs > 0:
                    # Outputs outside the ARC 30x30/0..9 grid contract are
                    # untrainable rows even when the oracle executes cleanly.
                    status = "OOB_OUTPUT"
                elif input_mutations > 0:
                    status = "INPUT_MUTATION"
                elif stateful_replays > 0:
                    status = "STATEFUL"
                elif mirror_mismatch > 0 or mirror_crash > 0:
                    # A declared Python mirror must agree exactly with the
                    # Racket authority on every smoked grid; divergence means
                    # tests/self_check trained against the wrong semantics.
                    status = "MIRROR_MISMATCH"
                elif identity > 0:
                    if calibrated_identity_is_lawful(
                        identity=identity,
                        applied=ok,
                        distinct_outputs=len(outs),
                        min_outputs=args.min_outputs,
                        canonical_identity=t in canonical_identity_tasks,
                    ):
                        status = "OK_CANONICAL_IDENTITY"
                    else:
                        # No-op output without a demonstrated identity branch,
                        # or an all-/low-diversity identity curriculum.
                        status = "IDENTITY"
                elif all_scalar and len(outs) >= args.min_scalar_outputs:
                    status = "OK_SCALAR_LOW_CARDINALITY"
                elif finite_low_cardinality:
                    status = "OK_FINITE_CODOMAIN"
                elif out_areas and max(out_areas) <= 9 and len(outs) >= 4:
                    # Legit small categorical / relation-matrix tasks have only a handful of possible
                    # outputs; 4 distinct <=3x3 outputs proves it's not a constant/identity generator
                    # while preserving the default gate for larger outputs (reviewer 370).
                    status = "OK_SMALL_LOW_CARDINALITY"
                elif len(outs) < args.min_outputs and len(outs) >= max(1, canonical_output_counts.get(t, 0)):
                    # The generator is at least as diverse as the canonical task's OWN train outputs;
                    # some ARC tasks are intrinsically low-cardinality (reviewer gpt55pro_384).
                    status = "OK_CANONICAL_LOW_CARDINALITY"
                elif len(outs) < args.min_outputs:
                    status = "DEGENERATE"
                line = (f"  {t}: applied={ok} crash={crash} fired={fired} "
                        f"distinct_out={len(outs)}"
                        + (f" IDENTITY={identity}" if identity else "")
                        + (f" scalar_out={scalar}" if scalar else "")
                        + (f" finite_out={declared_codomain}" if declared_codomain is not None else "")
                        + (f" oob_out={oob_outputs}" if oob_outputs else "")
                        + (f" input_mutation={input_mutations}" if input_mutations else "")
                        + (f" stateful_replay={stateful_replays}" if stateful_replays else "")
                        + (" reentrant=A-B-A" if reentrant_checked else "")
                        + (f" mirror={mirror_checked - mirror_mismatch}/{mirror_checked}"
                           + (f" mirror_crash={mirror_crash}" if mirror_crash else "")
                           if callable(mirror_fn) else "")
                        + f" [{status}]")
                p95 = _percentile(timings_ms, 95)
                task_restarts = getattr(b, "_restarts", 0) - restarts_before
                # input-pure = applications that provably did not mutate the
                # input grid. The A→B→A probe is what establishes this.
                evidence = {
                    "task_id": t, "status": status,
                    "applied": ok, "crash": crash, "fired": fired,
                    "distinct_outputs": len(outs), "identity": identity,
                    "oob_outputs": oob_outputs,
                    "input_mutations": input_mutations,
                    "input_pure": input_mutations == 0 and reentrant_checked,
                    "stateful_replays": stateful_replays,
                    "reentrant_aba_checked": reentrant_checked,
                    "latency_ms": {
                        "p50": _percentile(timings_ms, 50),
                        "p95": p95,
                        "max": max(timings_ms) if timings_ms else None,
                        "timed_calls": len(timings_ms),
                        "restart_contaminated_calls_excluded": restart_skipped,
                    },
                    "bridge_restarts": task_restarts,
                    "first_failure_witness": witness,
                    "mirror_parity": (
                        {"checked": mirror_checked,
                         "mismatches": mirror_mismatch,
                         "crashes": mirror_crash,
                         "first_witness": mirror_witness}
                        if callable(mirror_fn) else None),
                }
                evidence_rows.append(evidence)
                if p95 is not None:
                    line += f" p95={p95:.2f}ms"
                if task_restarts:
                    line += f" restarts={task_restarts}"
                if witness is not None:
                    line += (f" first_{witness['kind']}=@{witness['band']}"
                             f"/seed={witness['seed']}")
                print(line, flush=True)
                if status not in {
                    "OK",
                    "OK_SCALAR_LOW_CARDINALITY",
                    "OK_FINITE_CODOMAIN",
                    "OK_CANONICAL_LOW_CARDINALITY",
                    "OK_SMALL_LOW_CARDINALITY",
                    "OK_CANONICAL_IDENTITY",
                }:
                    flagged.append((t, status, len(outs), crash))
        finally:
            b.shutdown()

    print(f"\nscanned {len(ids)}; FLAGGED {len(flagged)}:")
    for t, st, do, cr in flagged:
        print(f"  {t}: {st} (distinct_out={do} crash={cr})")
    if args.json_out:
        payload = {
            "seeds": args.seeds, "bands": bands,
            "scanned": len(ids), "flagged": len(flagged),
            "tasks": evidence_rows,
        }
        Path(args.json_out).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json_out} ({len(evidence_rows)} task record(s))")
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
