#!/usr/bin/env python3
"""CI gate: grammar admissibility + operator-callable inventory (task #56).

Catches the recurring "runtime-callable drift" class automatically, before review. The failure mode
it guards: a gold `program_solution` calls a real Racket/prelude helper in operator position (e.g.
`pair?`, `hash-copy`, `hash-remove!`) that is NOT yet in the grammar's admissible-callable universe.
The constrained decoder would then be UNABLE to emit that gold program — a silent
grammar-completeness regression that has been re-discovered by reviewers three times.

Two checks, both must pass (exit non-zero + LOUD on any failure):

  1. ADMISSIBILITY (authoritative): feed every gold program through the constrained grammar
     (`dsl_grammar._validate`). It must accept 100% — a reject means the grammar is too strict for a
     real program (the exact drift symptom). This is what prints `accepted 4349/4349`.

  2. OPERATOR-CALLABLE INVENTORY (diagnostic): independently parse every gold program, extract every
     identifier used in OPERATOR position, and assert each resolves to one of:
       - a special form (lambda/let/cond/for*/... , `rule!`)
       - an atomic core head (dsl_vocab heads)
       - a prelude callable / macro (arc-prelude.rkt defines)
       - a Racket builtin / EXTRA_RUNTIME_CALLABLE (the runtime allowlist)
       - a lexically-bound local (lambda/define/let/for binding in scope)
     Anything left over is named explicitly, with an example task_id and the exact one-line fix
     ("add '<name>' to EXTRA_RUNTIME_CALLABLES in scripts/dsl_v2.py"). More actionable than the
     grammar's token-index reject.

Run standalone (`python3 scripts/grammar_gate.py`) or as a wired check in kaggle/pre_push_check.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import json  # noqa: E402

from dsl_v2 import (SPECIAL_FORMS, core_heads, runtime_callables, CANONICAL, _ATOM)  # noqa: E402
import dsl_grammar  # noqa: E402

# Binding special forms whose sub-structure introduces lexical names that may then appear in
# operator position as locals (a call to a locally-bound function value).
_LET_FORMS = {"let", "let*", "letrec"}
_LOOP_FORMS = {"for", "for/list", "for/sum", "for/fold", "for/or", "for/and", "for/first",
               "for*", "for*/list", "for*/fold", "for/set", "for/hash", "for/product",
               "for/max", "for/min", "for*/sum", "for*/or", "for*/and", "for*/first"}
# Prelude binding MACROS whose numbered argument is a bare `(name ...)` binding list, not a call
# (mirrors dsl_grammar's PARAMLIST special-cases). value = the 1-based arg index of the bind list.
_BIND_MACROS = {"with-bbox": 2, "build-grid": 3, "cellmap": 2}


def _strip_comments(src: str) -> str:
    """Remove Racket `#| ... |#` block comments and `;`-to-EOL line comments (respecting string
    literals, so a `;` inside a "..." string is preserved). Beautified gold carries `;; alt:` prose
    that must not be mistaken for operator-position identifiers."""
    src = re.sub(r"#\|.*?\|#", " ", src, flags=re.S)
    out = []
    for line in src.splitlines():
        in_str = False; buf = []
        for ch in line:
            if ch == '"':
                in_str = not in_str; buf.append(ch)
            elif ch == ";" and not in_str:
                break
            else:
                buf.append(ch)
        out.append("".join(buf))
    return "\n".join(out)


def _read_forms(src: str):
    """Minimal s-expression reader -> nested lists of string tokens. `[` is treated like `(`.
    Strings/atoms stay as raw tokens; good enough to locate operator heads and binding names."""
    toks = _ATOM.findall(_strip_comments(src))
    pos = [0]

    def parse():
        pos[0] += 1                       # consume the opener
        lst = []
        while pos[0] < len(toks) and toks[pos[0]] not in (")", "]"):
            t = toks[pos[0]]
            if t in ("(", "["):
                lst.append(parse())
            else:
                lst.append(t); pos[0] += 1
        pos[0] += 1                        # consume the closer
        return lst

    forms = []
    while pos[0] < len(toks):
        if toks[pos[0]] in ("(", "["):
            forms.append(parse())
        else:
            pos[0] += 1
    return forms


def _is_literal(t: str) -> bool:
    return (not t) or t[0] in "\"#" or bool(re.fullmatch(r"-?\d+(\.\d+)?", t)) or t[0] == "'"


def _param_names(node):
    """Names bound by a lambda/define parameter spec: a symbol (rest-arg) or a list of symbols."""
    if isinstance(node, str):
        return {node}
    out = set()
    for x in node:
        if isinstance(x, str) and not _is_literal(x) and x != ".":
            out.add(x)
        elif isinstance(x, list):
            out |= _param_names(x)
    return out


def _binding_names(clauses):
    """Names bound by a let/for clause list `((a e) (b e) ...)` -> {a, b, ...}."""
    out = set()
    if not isinstance(clauses, list):
        return out
    for cl in clauses:
        if isinstance(cl, list) and cl and isinstance(cl[0], str) and not _is_literal(cl[0]):
            out.add(cl[0])
        elif isinstance(cl, list) and cl and isinstance(cl[0], list):
            out |= _param_names(cl[0])            # e.g. ((r c) ...) destructured loop vars
    return out


def _walk(node, scope: set, universe: set, unknown: dict, all_bound: set, tid):
    """Collect operator-position identifiers not resolvable via universe or lexical scope."""
    if not isinstance(node, list) or not node:
        return
    head = node[0]

    # `quote`d data is not code — do not descend into operator analysis.
    if head == "quote":
        return

    child_scope = set(scope)
    # extend scope with names bound by this form (over-approximate: also feed the global safety net)
    if isinstance(head, str):
        if head == "lambda" and len(node) >= 2:
            child_scope |= _param_names(node[1])
        elif head == "define" and len(node) >= 2:
            tgt = node[1]
            if isinstance(tgt, list):
                child_scope |= _param_names(tgt)          # (define (f x y) ...)
                scope |= _param_names(tgt)                # f visible in enclosing scope too
            elif isinstance(tgt, str):
                scope.add(tgt); child_scope.add(tgt)
        elif head in _LET_FORMS and len(node) >= 2:
            idx = 1
            if isinstance(node[1], str):                  # named let: (let loop (...) ...)
                child_scope.add(node[1]); idx = 2
            if len(node) > idx:
                child_scope |= _binding_names(node[idx])
        elif head in _LOOP_FORMS:
            for part in node[1:3]:                        # accumulator + iteration clause lists
                if isinstance(part, list):
                    child_scope |= _binding_names(part)
    # prelude binding macros: their bind-list arg introduces names but is NOT a call to recurse into
    skip = None
    if isinstance(head, str) and head in _BIND_MACROS:
        bi = _BIND_MACROS[head]
        if len(node) > bi and isinstance(node[bi], list):
            child_scope |= _param_names(node[bi]); skip = bi
    all_bound |= child_scope

    # classify the head if it is an operator-position identifier
    if isinstance(head, str) and not _is_literal(head) and head not in SPECIAL_FORMS:
        if head not in universe and head not in child_scope:
            unknown.setdefault(head, tid)

    for i, child in enumerate(node[1:], start=1):
        if i == skip:
            continue
        _walk(child, child_scope, universe, unknown, all_bound, tid)


def check() -> int:
    # ---- check 1: admissibility (authoritative) ----
    rc_admit = dsl_grammar._validate(0, 0)

    # ---- check 2: operator-callable inventory (diagnostic) ----
    universe = set(SPECIAL_FORMS) | set(core_heads(0)) | runtime_callables()
    unknown: dict[str, str] = {}
    all_bound: set[str] = set()
    n = 0
    for line in CANONICAL.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = (r.get("program_solution") or "").strip()
        if not p:
            continue
        n += 1
        for form in _read_forms(p):
            _walk(form, set(), universe, unknown, all_bound, r.get("task_id"))
    # a head that is bound *somewhere* in a program is a local value call, never a missing callable
    unknown = {k: v for k, v in unknown.items() if k not in all_bound}

    print(f"operator-callable inventory: scanned {n} gold programs, universe={len(universe)} names, "
          f"{len(unknown)} unaccounted operator callable(s)")
    if unknown:
        print("LOUD: operator-position callables not in the admissible universe (grammar cannot emit these):")
        for name, tid in sorted(unknown.items()):
            print(f"  '{name}'  (e.g. task {tid})  -> add to EXTRA_RUNTIME_CALLABLES in scripts/dsl_v2.py")
    rc_inv = 1 if unknown else 0

    ok = (rc_admit == 0) and (rc_inv == 0)
    print("GRAMMAR GATE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def check_rule_text(text: str, label: str = "<rule>") -> bool:
    """Admissibility + operator-inventory check for ONE rule's text.

    Intake use (contract v14): every worker-returned Racket rule patch is fed
    through this BEFORE merging into canonical/grounded — a rule that executes
    but is grammar-inadmissible would silently shrink the constrained-decode
    training set. LOUD on reject; returns True when admissible."""
    from dsl_grammar import DSLGrammar, to_tokens

    text = text.strip()
    if not text:
        print(f"LOUD: {label}: empty rule text")
        return False
    g = DSLGrammar(0)
    g.reset()
    toks = to_tokens(text, g.core)
    for i, t in enumerate(toks):
        if not g.step(t):
            print(f"LOUD: {label}: grammar REJECTS token {i} {t!r} "
                  f"(context ...{' '.join(toks[max(0, i - 4):i + 1])})")
            return False
    if not g.complete():
        print(f"LOUD: {label}: grammar left INCOMPLETE at end of program")
        return False

    universe = set(SPECIAL_FORMS) | set(core_heads(0)) | runtime_callables()
    unknown: dict[str, str] = {}
    all_bound: set[str] = set()
    for form in _read_forms(text):
        _walk(form, set(), universe, unknown, all_bound, label)
    unknown = {k: v for k, v in unknown.items() if k not in all_bound}
    if unknown:
        print(f"LOUD: {label}: operator callables outside the admissible "
              f"universe: {sorted(unknown)} "
              "(add to EXTRA_RUNTIME_CALLABLES in scripts/dsl_v2.py if real)")
        return False
    print(f"{label}: admissible ({len(toks)} tokens)")
    return True


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--extra-rule", action="append", default=[],
                    metavar="FILE",
                    help="validate ONE rule's text (a file containing a single "
                         "(rule! ...) program, e.g. a staged worker patch "
                         "result) instead of the full corpus gate; repeatable")
    a = ap.parse_args()
    if a.extra_rule:
        ok = True
        for path in a.extra_rule:
            text = Path(path).read_text()
            ok = check_rule_text(text, label=path) and ok
        print("GRAMMAR GATE (extra rules):", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
