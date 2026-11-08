#!/usr/bin/env python3
"""GUIDE self-check: keep the DSL manual honest.

Two jobs:

1. ``--inventory``: regenerate ``07-prelude-inventory.md`` from the prelude
   source, so the "if it's not here it doesn't exist" list can never drift.

2. default run: extract every fenced ```scheme block from the GUIDE markdown
   files and execute the testable ones against the real Racket bridge.
   - Blocks that are full rules (start with ``(rule!``) are applied to a
     probe grid via ProgramVerifier — they must at least EXECUTE and return
     a rectangular grid (worked examples are landed corpus rules, so
     correctness is already proven upstream).
   - Blocks made of top-level ``(define ...)`` forms are evaluated one form
     at a time in a session with ``g``/``h``/``w`` and common stub
     dependencies bound.
   - Blocks containing metavariables/ellipses (``...``, ``BODY``, ``H W``,
     unresolvable free names) are skipped and counted as such.

Every failure is a documentation bug: fix the doc (or the whitelist below,
with a reason). Exit code 1 on any failure.

Run:  python3 GUIDE/selfcheck.py            # verify snippets
      python3 GUIDE/selfcheck.py --inventory  # regenerate 07
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "GUIDE"

# Substrings that mark a block as intentionally incomplete (skipped).
PLACEHOLDER_MARKERS = ["...", "BODY", "H W", "COLOR-EXPR", "<", "…", "["]  # "[" = signature notation

# Free names some fragments assume; stubbed before evaluation.
STUB_DEFS = [
    "(define mask (cellmap g (r c v) (if (zero? v) 0 1)))",
    "(define cells (find-color g 3))",
    "(define proto (list (list 0 0) (list 0 1) (list 1 0)))",
    "(define target (list (list 0 0) (list 0 1) (list 1 0)))",
    "(define (wall? v) (member? v (list 1 7 9)))",
    "(define (related? a b) #f)",
    "(define seed-groups (list (list (list 0 0)) (list (list 2 2))))",
    "(define (blocked? p) #f)",
    "(define (inside? r c) (in-bounds? r c h w))",
    "(define (nb mask r c) (count-if (lambda (d) (= (safe-at mask (+ r (first d)) (+ c (second d)) 0) 1)) cardinal-deltas))",
    "(define start-mask (cellmap g (r c v) (if (zero? v) 0 1)))",
    "(define sep-rows (list))",
    "(define xs (list 1 2 3))",
    "(define (paint out x) out)",
    "(define (claim x) x)",
    "(define (key x) x)",
    "(define fr (first (objects g 0)))",
    "(define pat (list (list 1)))",
    "(define out (empty-grid h w 0))",
    "(define bg 0)",
    # meta-variables used by illustrative one-liners in 02/05
    "(define r 0)",
    "(define c 0)",
    "(define o (first (objects g 0)))",
    "(define sr 0)",
    "(define sc 1)",
    "(define from 2)",
    "(define to 8)",
    "(define start 0)",
    "(define (same-shape? x) #t)",
    "(define (matches-pattern? x) #t)",
    "(define (done? x) #t)",
    "(define (step x) x)",
]

PROBE = [
    [0, 2, 0, 0, 3],
    [2, 2, 0, 3, 3],
    [0, 0, 0, 0, 0],
    [5, 5, 5, 5, 5],
    [0, 1, 0, 4, 0],
]


def blocks():
    for md in sorted(GUIDE.glob("*.md")):
        text = md.read_text()
        for m in re.finditer(r"```scheme\n(.*?)```", text, re.S):
            yield md.name, m.group(1).strip()


def balanced(code: str) -> bool:
    depth = 0
    for line in code.splitlines():
        for ch in line:
            if ch == ";":
                break
            depth += (ch == "(") - (ch == ")")
    return depth == 0


def top_level_forms(code: str):
    forms, depth, cur = [], 0, []
    for ch in code:
        cur.append(ch)
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                forms.append("".join(cur).strip())
                cur = []
    tail = "".join(cur).strip()
    if tail and not tail.startswith(";"):
        forms.append(tail)
    return [f for f in forms if f.startswith("(")]


def regen_inventory() -> None:
    sigs, syntaxes = set(), set()
    prelude = ROOT / "arc_repl/racket_prelude/arc-prelude.rkt"
    for line in prelude.open():
        m = re.match(r"^\(define \(([^)\s]+)([^)]*)\)", line)
        if m:
            sigs.add((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r"^\(define-syntax-rule \(\(?([^)\s]+)([^)]*)\)", line)
        if m:
            syntaxes.add((m.group(1), m.group(2).strip()))
            continue
        m = re.match(r"^\(define ([a-z0-9!?<>=*/+-][^\s(]*) ", line)
        if m:
            sigs.add((m.group(1), "— constant"))
    out = [
        "# 07 · Prelude inventory (auto-generated)",
        "",
        "Every top-level definition in `arc_repl/racket_prelude/arc-prelude.rkt`,",
        "extracted mechanically. **If a name is not in this list (or a core Racket",
        "built-in like `first`, `sort`, `range`, `last`, `apply`), it does not",
        "exist — do not call it.** Regenerate with `python3 GUIDE/selfcheck.py",
        "--inventory` after prelude changes.",
        "",
        f"## Functions ({len(sigs)})",
        "",
        "```",
    ]
    for name, args in sorted(sigs):
        out.append(f"({name} {args})".replace("  ", " ").rstrip())
    out += ["```", "", f"## Macros / special forms ({len(syntaxes)})", "", "```"]
    for name, args in sorted(syntaxes):
        out.append(f"({name} {args} body ...)")
    out += ["```", ""]
    (GUIDE / "07-prelude-inventory.md").write_text("\n".join(out))
    print(f"07-prelude-inventory.md: {len(sigs)} functions, {len(syntaxes)} macros")


def main() -> int:
    if "--inventory" in sys.argv:
        regen_inventory()
        return 0

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    from arc_repl.racket_bridge import RacketBridge          # noqa: E402
    from coder_synth_verify import ProgramVerifier           # noqa: E402

    ver = ProgramVerifier()
    bridge = RacketBridge()
    bridge.define_grid("g", PROBE)
    bridge.eval_text("(define h (rows g))")
    bridge.eval_text("(define w (cols g))")
    for d in STUB_DEFS:
        bridge.eval_text(d)

    ran = skipped = failed = 0
    for src, code in blocks():
        if any(mk in code for mk in PLACEHOLDER_MARKERS) or not balanced(code):
            skipped += 1
            continue
        head = code.split(None, 1)[0] if code.split() else ""
        try:
            if code.startswith("(rule!"):
                out = ver.apply(code, PROBE)
                assert isinstance(out, list) and out and isinstance(out[0], list), \
                    f"rule returned non-grid: {out!r:.80}"
            elif head in ("(define", "(define-syntax-rule") or code.startswith("(define"):
                for form in top_level_forms(code):
                    bridge.eval_text(form)
            else:
                for form in top_level_forms(code):
                    bridge.eval_text(form)
            ran += 1
        except Exception as e:  # noqa: BLE001 — report, never hide
            failed += 1
            first = code.splitlines()[0][:70]
            print(f"FAIL [{src}] {first}")
            print(f"     {str(e).splitlines()[0][:160]}")
    print(f"snippets: {ran} executed OK, {skipped} skipped (placeholders), {failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
