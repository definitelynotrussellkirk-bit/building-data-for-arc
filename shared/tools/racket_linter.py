#!/usr/bin/env python3
"""AST-aware Racket-rule linter — correctness gotchas + canonical-style checks.

Why a second linter when `lint_racket_style.py` exists: that one is pure regex.
A `for/or` regex flags EVERY `for/or`, but `(for/or ((x xs)) (pred? x))` is the
legitimate "does any element satisfy" use — only `(for/or ((x xs)) (if ... x #f))`
(value-search) is the bug. This linter parses the rule with the existing
`scripts.compactor.parser` and CLASSIFIES the `for/or`/`for/first` tail
expression, so it only flags the value-search shape. That cuts the false
positives the regex can't.

It is a library first (so the coder loop can lint model-emitted Racket before
executing it) and a CLI second (audit the canonical corpus / grounded rules).

Checks (kind / severity):
  CORRECTNESS
    for-or-value-search     warn   `for/or` whose tail returns a non-boolean
                                   VALUE — returns #t/#f, not the value. Use
                                   `find-first` / `(first (filter ...))`.
    for-first-value-search  warn   same bug: `for/first` stops on the first #f.
    (a broken single-paren `(for/X (v seq) ...)` binding is already caught by
     `parse-error` below — the parser rejects it before any detector runs.)
    empty-lambda            warn   `(lambda () ...)` — the bridge mangles `()`
                                   to `'()`; use `(define (f) ...)`.
  CANONICAL STYLE (mirror docs/CANONICAL_STYLE.md hard rules; warn)
    style-cell-at           warn   `(cell-at g r c)` → `(at g r c)`        (#3)
    style-not-eq            warn   `(not (= a b))` → `(!= a b)`            (#4)
    style-eq-zero           warn   `(= x 0)` / `(= 0 x)` → `(zero? x)`     (#5)
    style-when-not          warn   `(when (not X) Y)` → `(unless X Y)`     (#7)
    style-if-x-y-false      warn   `(if X Y #f)` → `(and X Y)`            (#8)
    style-outer-wrapper     warn   leftover `(rule! …)` / `(lambda (g) …)` (#1)
    dummy-let-binding       warn   `(let ((dummy 0)) …)` preamble          (#1)
    generated-helper-name   warn   codegen-prefixed name `e8b-list<` etc.
  SIZE
    oversized-rule          warn   body > RULE_SIZE_LIMIT chars.

Style findings should be near-zero after unwrapping the executable corpus wrapper;
they earn their keep on UN-compacted, model-generated Racket.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.compactor.parser import Sym, emit, parse  # noqa: E402

RULE_SIZE_LIMIT = 3000

# Compactor/codegen artifact: a helper whose head segment (before the first
# hyphen) is short AND mixes a digit with a letter — e.g. `e8b-list<`,
# `t10-norm-cells`, `t3b-overlay-op`. Real canonical primitives keep digits out
# of the head segment (`cell-at`, `obj-size`, `objects-8` has the digit AFTER the
# hyphen), so this stays specific to generated names.
_GENERATED_HELPER_HEAD = re.compile(r"^(?=[a-z]*\d)(?=\d*[a-z])[a-z0-9]{2,4}-")


def _is_generated_helper_name(name: str) -> bool:
    return bool(_GENERATED_HELPER_HEAD.match(name))

# Heads whose call provably yields a boolean (so a for/or tail using them is the
# legitimate "any element satisfies" use, NOT a value-search bug).
_BOOL_HEADS = {
    "=", "!=", "<", ">", "<=", ">=", "eq?", "eqv?", "equal?",
    "and", "or", "not", "zero?", "null?", "empty?", "even?", "odd?",
    "positive?", "negative?", "member", "memq", "memv", "assoc",
}


class Finding(NamedTuple):
    kind: str
    severity: str           # "error" | "warn"
    snippet: str            # offending sub-expression, emitted
    suggest: str


def _is_sym(node, name: str) -> bool:
    return isinstance(node, Sym) and node == name


def _head(node):
    return node[0] if isinstance(node, tuple) and node else None


# Forms that don't compute a value themselves — their result is the result of
# their TAIL sub-form. We reduce through them before classifying.
#   let/let*/letrec/parameterize: (head, bindings, body...)  → tail = body[-1]
#   begin/when/unless:            (head, expr...)            → tail = expr[-1]
#   for/or/for/and:               (head, clauses, body...)   → tail = body[-1],
#       AND the comprehension yields a boolean iff that tail is boolean.
_TAIL_REDUCE_HEADS = {"let", "let*", "letrec", "parameterize",
                      "begin", "when", "unless", "for/or", "for/and"}


def _is_boolean_expr(node) -> bool:
    """Best-effort: does evaluating `node` yield a boolean (vs a data value)?

    Used only to SUPPRESS legitimate boolean `for/or`/`for/first`. Conservative
    toward flagging: anything we can't prove boolean is treated as a value
    (so we never silence a real value-search bug)."""
    if isinstance(node, bool):
        return True
    if not isinstance(node, tuple) or not node:
        return False                       # bare var / number / string → value
    h = node[0]
    if not isinstance(h, Sym):
        return False
    if h.endswith("?"):
        return True                        # predicate call (foo?, hash-has-key?)
    if h in _BOOL_HEADS:
        return True
    if h in _TAIL_REDUCE_HEADS and len(node) >= 2:
        return _is_boolean_expr(node[-1])  # result is the tail sub-form's result
    if h == "if" and len(node) == 4:
        return _is_boolean_expr(node[2]) and _is_boolean_expr(node[3])
    if h == "cond":
        # boolean only if every clause's last expr is boolean
        for clause in node[1:]:
            if isinstance(clause, tuple) and len(clause) >= 2:
                if not _is_boolean_expr(clause[-1]):
                    return False
        return True
    return False                           # any other call → assume value


def _for_tail(node) -> object:
    """The return expression of a `(for/X (clauses) body...)` form."""
    # node = (Sym for/X, clauses, body0, body1, ...)
    if len(node) < 3:
        return None
    return node[-1]


def _tail_may_yield_false(tail) -> bool:
    """Does this `for/first` body short-circuit to #f on a non-match (the
    stop-on-first-#f footgun)? True for `(if C T #f)`/`(if C #f E)`, `(and …)`,
    `(when …)`/`(unless …)` — all of which can evaluate to #f/void."""
    if not isinstance(tail, tuple) or not tail or not isinstance(tail[0], Sym):
        return False
    h = tail[0]
    if h == "if" and len(tail) == 4:
        return tail[3] is False or tail[2] is False
    return h in ("and", "when", "unless")


def _walk(node):
    """Yield every tuple sub-node, depth-first."""
    if isinstance(node, tuple):
        yield node
        for c in node:
            yield from _walk(c)


def _strip_outer(node):
    """Unwrap a leading `(rule! BODY)` / `(lambda (g) BODY)` so we analyze the
    real body. Returns (inner, had_wrapper)."""
    had = False
    while isinstance(node, tuple) and node:
        h = node[0]
        if _is_sym(h, "rule!") and len(node) == 2:
            node = node[1]; had = True; continue
        if _is_sym(h, "lambda") and len(node) >= 3 and isinstance(node[1], tuple) \
                and len(node[1]) == 1 and isinstance(node[1][0], Sym) \
                and node[1][0] in ("g", "grid"):
            # (lambda (g) body...) → wrap remaining body forms in begin
            inner = node[2] if len(node) == 3 else (Sym("begin"), *node[2:])
            node = inner; had = True; continue
        break
    return node, had


def lint_rule(rule_text: str, *, canonical: bool = True) -> list[Finding]:
    """Lint one Racket rule string. `canonical=True` also flags a leftover
    outer wrapper (naked-body is the canonical form)."""
    out: list[Finding] = []
    if len(rule_text) > RULE_SIZE_LIMIT:
        out.append(Finding("oversized-rule", "warn", "",
                           f"body is {len(rule_text)} chars (> {RULE_SIZE_LIMIT})"))
    try:
        ast = parse(rule_text)
    except Exception as e:
        out.append(Finding("parse-error", "error", rule_text[:80].replace("\n", " "),
                           f"failed to parse: {e}"))
        return out

    body, had_wrapper = _strip_outer(ast)
    if had_wrapper and canonical:
        out.append(Finding("style-outer-wrapper", "warn", "",
                           "leftover (rule! …)/(lambda (g) …) wrapper — canonical "
                           "body sits naked (CANONICAL_STYLE #1)"))

    for n in _walk(body):
        h = _head(n)
        if not isinstance(h, Sym):
            continue

        # --- correctness: for/or value-search ---
        # `for/or` is the "does any element satisfy" idiom — fine when its tail
        # is boolean; a bug only when it returns a non-boolean VALUE.
        if h == "for/or":
            tail = _for_tail(n)
            if tail is not None and not _is_boolean_expr(tail):
                out.append(Finding(
                    "for-or-value-search", "warn", emit(n)[:120],
                    f"`for/or` tail returns a VALUE ({emit(tail)[:40]}) not a "
                    f"boolean — `for/or` yields #t/#f. Use `find-first` / "
                    f"`(first (filter pred lst))`."))

        # --- correctness: for/first stop-on-first-#f bug ---
        # `(for/first ((x xs) #:when pred) x)` is the CORRECT filter idiom (the
        # guard skips non-matches). The bug is doing the filter INSIDE the body
        # with an `if/and/when` that short-circuits to #f, so it returns #f from
        # the first non-match instead of continuing. Flag only that shape.
        if h == "for/first":
            clauses = n[1] if len(n) > 1 else ()
            tail = _for_tail(n)
            if "#:when" not in emit(clauses) and _tail_may_yield_false(tail):
                out.append(Finding(
                    "for-first-value-search", "warn", emit(n)[:120],
                    "`for/first` filters in its body and can short-circuit to "
                    "#f on the first non-match. Use a `#:when` guard or "
                    "`find-first`."))

        # --- correctness: empty-arg lambda ---
        if h == "lambda" and len(n) >= 2 and n[1] == ():
            out.append(Finding("empty-lambda", "warn", emit(n)[:80],
                               "`(lambda () …)` — bridge mangles `()`; use "
                               "`(define (f) …)`."))

        # --- style: cell-at → at ---
        if h == "cell-at":
            out.append(Finding("style-cell-at", "warn", emit(n)[:80],
                               "`(cell-at …)` → `(at …)` (CANONICAL_STYLE #3)"))

        # --- style: (not (= a b)) → (!= a b) ---
        if h == "not" and len(n) == 2 and _head(n[1]) == Sym("="):
            out.append(Finding("style-not-eq", "warn", emit(n)[:80],
                               "`(not (= a b))` → `(!= a b)` (CANONICAL_STYLE #4)"))

        # --- style: (= x 0) / (= 0 x) → (zero? x) ---
        if h == "=" and len(n) == 3 and (n[1] == 0 or n[2] == 0):
            out.append(Finding("style-eq-zero", "warn", emit(n)[:80],
                               "`(= x 0)` → `(zero? x)` (CANONICAL_STYLE #5)"))

        # --- style: (when (not X) Y) → (unless X Y) ---
        if h == "when" and len(n) >= 2 and _head(n[1]) == Sym("not"):
            out.append(Finding("style-when-not", "warn", emit(n)[:80],
                               "`(when (not X) …)` → `(unless X …)` (CANONICAL_STYLE #7)"))

        # --- style: (if X Y #f) → (and X Y) ---
        if h == "if" and len(n) == 4 and n[3] is False:
            out.append(Finding("style-if-x-y-false", "warn", emit(n)[:80],
                               "`(if X Y #f)` → `(and X Y)` (CANONICAL_STYLE #8)"))

        # --- style: dummy let-binding preamble ---
        # The compactor sometimes leaves `(let ((dummy 0)) …)` so the body has a
        # head form; canonical bodies are naked (CANONICAL_STYLE #1). Flag a
        # binding literally named `dummy`/`_dummy` bound to a literal.
        if h in ("let", "let*", "letrec") and len(n) >= 2 and isinstance(n[1], tuple):
            for b in n[1]:
                if (isinstance(b, tuple) and len(b) == 2 and isinstance(b[0], Sym)
                        and str(b[0]).lstrip("_") == "dummy"
                        and isinstance(b[1], (int, float, bool, str))):
                    out.append(Finding(
                        "dummy-let-binding", "warn", emit(n)[:80],
                        "dummy `(let ((dummy 0)) …)` preamble — drop it; the "
                        "canonical body sits naked (CANONICAL_STYLE #1)."))
                    break

        # --- style: generated helper names ---
        # `(define (e8b-list< …) …)` / `(let ((t3b-overlay-op …)) …)` carry
        # codegen-prefixed names that read as noise in training text. Flag the
        # introduced name; suggest a semantically meaningful rename.
        if h == "define" and len(n) >= 2:
            target = n[1]
            dname = (target[0] if isinstance(target, tuple) and target
                     and isinstance(target[0], Sym) else
                     target if isinstance(target, Sym) else None)
            if dname is not None and _is_generated_helper_name(str(dname)):
                out.append(Finding(
                    "generated-helper-name", "warn", str(dname),
                    f"`{dname}` is a codegen-prefixed helper name — rename to "
                    f"something semantic (CANONICAL_STYLE)."))
        if h in ("let", "let*", "letrec") and len(n) >= 2 and isinstance(n[1], tuple):
            for b in n[1]:
                if (isinstance(b, tuple) and b and isinstance(b[0], Sym)
                        and _is_generated_helper_name(str(b[0]))):
                    out.append(Finding(
                        "generated-helper-name", "warn", str(b[0]),
                        f"`{b[0]}` is a codegen-prefixed helper name — rename to "
                        f"something semantic (CANONICAL_STYLE)."))

    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _load_canonical() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            tid, rule = r.get("task_id"), r.get("program_solution") or ""
            if tid and rule:
                rows.append({"tid": tid, "rule": rule})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=("canonical", "grounded"), default="canonical")
    ap.add_argument(
        "--task-id",
        action="append",
        help="lint only this task ID (repeatable; fails if an ID is absent)",
    )
    ap.add_argument("--rule", help="lint a single rule string and exit")
    ap.add_argument("--file", help="lint a single .rkt/.txt file and exit")
    ap.add_argument("--only", help="comma-separated finding kinds to show")
    ap.add_argument("--errors-only", action="store_true",
                    help="exit nonzero if any error-severity finding")
    ap.add_argument(
        "--fail-on-style",
        action="store_true",
        help="strict candidate mode: exit nonzero on any finding",
    )
    ap.add_argument("--show-each", action="store_true")
    ap.add_argument("--json-out", help="write per-rule findings JSONL here")
    args = ap.parse_args()

    if args.rule or args.file:
        text = args.rule or Path(args.file).read_text()
        findings = lint_rule(text)
        for fnd in findings:
            print(f"  [{fnd.severity:5s}] {fnd.kind:24s} {fnd.suggest}")
            if fnd.snippet:
                print(f"           ↳ {fnd.snippet}")
        if args.fail_on_style and findings:
            sys.exit(1)
        if args.errors_only and any(
            finding.severity == "error" for finding in findings
        ):
            sys.exit(1)
        return

    if args.source == "grounded":
        from solvers.grounded_rules import GROUNDED_RULES
        rows = [{"tid": k, "rule": v} for k, v in GROUNDED_RULES.items()]
    else:
        rows = _load_canonical()

    if args.task_id:
        requested = set(args.task_id)
        rows = [row for row in rows if row["tid"] in requested]
        missing = sorted(requested - {row["tid"] for row in rows})
        if missing:
            ap.error(f"task ID(s) absent from {args.source}: {', '.join(missing)}")

    only = set(args.only.split(",")) if args.only else None
    by_kind = Counter()
    unique_oversized_rules: set[str] = set()
    flagged = []
    n_error = 0
    for r in rows:
        # The corpus stores executable `(rule! BODY)` strings; that wrapper is not a
        # useful finding when auditing the whole corpus.  Keep the wrapper warning for
        # one-off `--rule`/`--file` model outputs, where callers usually want a naked body.
        finds = lint_rule(r["rule"], canonical=False)
        if only:
            finds = [f for f in finds if f.kind in only]
        if finds:
            flagged.append({"tid": r["tid"], "findings": finds})
            for f in finds:
                by_kind[f.kind] += 1
                if f.kind == "oversized-rule":
                    unique_oversized_rules.add(" ".join(r["rule"].split()))
                if f.severity == "error":
                    n_error += 1

    print(f"\n=== racket_linter ({args.source}) ===")
    print(f"  rules scanned: {len(rows)}")
    print(f"  flagged:       {len(flagged)}")
    print(f"  errors:        {n_error}")
    for k, n in by_kind.most_common():
        if k == "oversized-rule" and len(unique_oversized_rules) != n:
            print(
                f"    {k:26s} {len(unique_oversized_rules)} unique "
                f"/ {n} locations"
            )
        else:
            print(f"    {k:26s} {n}")

    if args.show_each:
        for r in flagged[:40]:
            kinds = Counter(f.kind for f in r["findings"])
            print(f"  {r['tid']:14s}  {dict(kinds)}")

    if args.json_out:
        out = Path(args.json_out)
        with out.open("w") as f:
            for r in flagged:
                f.write(json.dumps({"tid": r["tid"],
                                    "findings": [f._asdict() for f in r["findings"]]}) + "\n")
        print(f"\nwrote {out}")

    if args.fail_on_style and flagged:
        sys.exit(1)
    if args.errors_only and n_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
