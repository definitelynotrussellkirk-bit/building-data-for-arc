#!/usr/bin/env python3
"""Racket-rule style + correctness lint.

Checks each `program_solution` in canonical for known anti-patterns.

Findings:
  for-or-value-search    `for/or` is in the rule. Per CLAUDE.md, this
                         returns #t/#f, not the matching value — almost
                         always a bug when used to PICK a value. ≥11
                         grounded rules have been repaired for this.
  for-first-value-search `for/first` has the same bug as `for/or`
                         (stops on first #f even if a later iteration
                         would succeed). Use `find-first` or `(first
                         (filter ...))` instead.
  oversized-rule         Rule body > 3000 chars after Phase 1 cleanup.
                         May still have over-elaborate logic that could
                         be compacted.

Severity: warn. Doesn't fail the lint suite — these are signals to
investigate, not all true positives. The for/or check in particular
needs human review per occurrence (some uses are genuinely boolean).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


_PATTERNS = [
    ("for-or-value-search", re.compile(r"\bfor/or\b"),
     "uses `for/or` — returns #t/#f, NOT the matching value. "
     "Use `find-first` or `(first (filter pred lst))` to pick a value."),
    ("for-first-value-search", re.compile(r"\bfor/first\b"),
     "uses `for/first` — stops on first #f even if a later iteration "
     "would succeed. Use `find-first` instead."),
]
# Single-paren binding `(for/or (var seq) body)` is invalid in Racket — needs
# `((var seq))` (double parens / one bracket-clause per binding). These rules
# fail to parse when actually evaluated. ERROR severity, not warn.
_BROKEN_BINDING_RE = re.compile(r"\bfor/(?:or|first|sum|list)\s+\(([a-zA-Z_][\w-]*)\s")
RULE_SIZE_LIMIT = 3000


def lint_one(rule_text: str) -> list[dict]:
    findings = []
    for kind, pat, msg in _PATTERNS:
        for m in pat.finditer(rule_text):
            findings.append({
                "kind": kind,
                "severity": "warn",
                "match": m.group(0),
                "offset": m.start(),
                "suggest": msg,
            })
    for m in _BROKEN_BINDING_RE.finditer(rule_text):
        findings.append({
            "kind": "for-comprehension-broken-binding",
            "severity": "error",
            "match": m.group(0),
            "offset": m.start(),
            "suggest": f"single-paren binding `(for/... ({m.group(1)} ...))` is "
                       f"invalid Racket — wrap in extra parens: `((  {m.group(1)} ...))`. "
                       f"This rule fails to parse at runtime.",
        })
    if len(rule_text) > RULE_SIZE_LIMIT:
        findings.append({
            "kind": "oversized-rule",
            "severity": "warn",
            "match": "",
            "offset": 0,
            "suggest": f"rule body is {len(rule_text)} chars (> {RULE_SIZE_LIMIT}); "
                       f"likely still has over-elaborate logic post-Phase-1 cleanup",
        })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-each", action="store_true")
    args = ap.parse_args()

    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            tid = r.get("task_id")
            rule = r.get("program_solution") or ""
            if tid and rule:
                rows.append({"tid": tid, "rule": rule})

    by_kind = Counter()
    flagged = []
    for r in rows:
        f = lint_one(r["rule"])
        if f:
            flagged.append({"tid": r["tid"], "findings": f})
            for finding in f:
                by_kind[finding["kind"]] += 1

    print(f"\n=== summary ===")
    print(f"  rules scanned: {len(rows)}")
    print(f"  flagged:       {len(flagged)}")
    for k, n in by_kind.most_common():
        print(f"  {k:30s} {n}")

    if args.show_each:
        for r in flagged[:30]:
            kinds = Counter(f["kind"] for f in r["findings"])
            print(f"  {r['tid']:55s}  {dict(kinds)}")
    else:
        print(f"\nfirst 15 flagged (by tid):")
        for r in flagged[:15]:
            kinds = Counter(f["kind"] for f in r["findings"])
            print(f"  {r['tid']:55s}  {dict(kinds)}")

    out = Path("/tmp/racket_style_lint.jsonl")
    with out.open("w") as f:
        for r in flagged:
            f.write(json.dumps(r) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
