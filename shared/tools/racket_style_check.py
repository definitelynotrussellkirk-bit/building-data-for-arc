#!/usr/bin/env python3
"""Racket style/quality linter — encodes the CANONICAL_STYLE hard rules + the RACKET_DSL gotchas so we
(a) GATE training targets (never train on malformed/anti-pattern Racket) and (b) produce a CODE-REVIEW
report of the corpus so reviewers improve expression elegance.

HARD violations are bugs/crashers (a program with one is broken or silently wrong) -> gate them out of
training data. SOFT violations are style/elegance (the compactor would fix them) -> surface for review.

Usage:
  python3 scripts/racket_style_check.py --corpus            # ranked report over canonical
  from racket_style_check import check_program              # {"hard":[...], "soft":[...]}
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _forms(prog: str, head: str):
    """Yield the arg-count of every top-level `(head ...)` form (paren-aware)."""
    i = 0
    key = "(" + head
    while True:
        idx = prog.find(key, i)
        if idx < 0:
            return
        j = idx + len(key)
        if j < len(prog) and prog[j] not in " \t\n(":   # not a real head (e.g. (-> vs (-)
            i = idx + 1; continue
        depth, args, in_atom = 1, 0, False
        while j < len(prog) and depth > 0:
            ch = prog[j]
            if ch == "(":
                if depth == 1 and not in_atom:
                    args += 1
                depth += 1; in_atom = False
            elif ch == ")":
                depth -= 1
                if depth == 1:
                    in_atom = False
            elif depth == 1 and ch not in " \t\n":
                if not in_atom:
                    args += 1; in_atom = True
            elif depth == 1:
                in_atom = False
            j += 1
        yield args
        i = idx + 1


def check_program(prog: str) -> dict:
    """Return {"hard": [msgs], "soft": [msgs]} for one Racket program string."""
    hard, soft = [], []
    # ---- HARD: crashers / silently-wrong ----
    if re.search(r"\(lambda\s*\(\s*\)", prog):
        hard.append("empty (lambda () ...) — the bridge mangles the empty arg list; use (define (f) ...)")
    # NOTE: 3-arg `-` is VALID in the Racket bridge (228 verified corpus rules use it) — NOT gated.
    if re.search(r"\(for/or\s+\([^)]*\)\s*\(if\b[^)]*\s#f\)", prog):
        hard.append("for/or value-search — returns #t not the value; use find-first / filter-then-first")
    if re.search(r"\(for/first\s+\([^)]*\)\s*\(if\b[^)]*\s#f\)", prog):
        hard.append("for/first with a failing-first branch — stops on the first #f; use find-first")
    # ---- SOFT: style / elegance (compactor would fix) ----
    if "cell-at" in prog:
        soft.append("cell-at -> at (canonical alias)")
    if re.search(r"\(not\s+\(=\s", prog):
        soft.append("(not (= a b)) -> (!= a b)")
    if re.search(r"\(=\s+\S+\s+0\)", prog) or re.search(r"\(=\s+0\s+\S+\)", prog):
        soft.append("(= x 0) -> (zero? x)")
    if re.search(r"\(let\s+\(", prog):
        soft.append("let -> let* (canonical; flatten nested lets)")
    return {"hard": hard, "soft": soft}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="store_true", help="lint every canonical program_solution")
    ap.add_argument("--canonical", default=str(ROOT / "data/canonical/puzzles.jsonl"))
    ap.add_argument("--report", default="", help="write a markdown report to this path")
    a = ap.parse_args()
    if not a.corpus:
        ap.error("pass --corpus")
    rows = [json.loads(l) for l in open(a.canonical)]
    hard_hits, soft_hits, from_rule = {}, {}, {}
    n_clean = 0
    for r in rows:
        p = (r.get("program_solution") or "").strip()
        if not p:
            continue
        res = check_program(p)
        if not res["hard"] and not res["soft"]:
            n_clean += 1
        for m in res["hard"]:
            hard_hits[m] = hard_hits.get(m, 0) + 1
            from_rule.setdefault(m, []).append(r.get("task_id"))
        for m in res["soft"]:
            soft_hits[m] = soft_hits.get(m, 0) + 1
    lines = ["# Racket code-review — canonical corpus style report", ""]
    lines.append(f"- programs linted: {len(rows)} | clean: {n_clean} "
                 f"({100*n_clean/max(1,len(rows)):.1f}%)")
    lines.append(f"- HARD (bug/crasher) kinds: {len(hard_hits)} | SOFT (elegance) kinds: {len(soft_hits)}")
    lines.append("")
    lines.append("## HARD violations (should never train on these — gated)")
    for m, c in sorted(hard_hits.items(), key=lambda kv: -kv[1]):
        ex = ", ".join(str(t) for t in from_rule[m][:5])
        lines.append(f"- **{c}×** {m}  \n  e.g. {ex}")
    if not hard_hits:
        lines.append("- none — corpus is crasher-clean ✓")
    lines.append("")
    lines.append("## SOFT / elegance (reviewers: tighten these expressions)")
    for m, c in sorted(soft_hits.items(), key=lambda kv: -kv[1]):
        lines.append(f"- **{c}×** {m}")
    if not soft_hits:
        lines.append("- none — corpus is compactor-clean ✓")
    report = "\n".join(lines)
    print(report)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(report + "\n")
        print(f"\nwrote report -> {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
