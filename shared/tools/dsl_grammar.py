#!/usr/bin/env python3
"""Typed incremental grammar for v2 DSL tokens — the constrained decoder.

The closed vocab alone does NOT prevent hallucination: once the model can spell
`<id> g r i d - h e i g h t <esc>`, it can invent `grid-height` again. The fix (per both
reviews, PICARD-style) is a typed incremental parser that, at every decode step, returns the
SET of tokens that keep the program valid:

  - OPERATOR position (right after `(`): ONLY real callable heads + special forms + nested `(`.
    `<id>` is allowed only for prefix-gated in-scope locals or rare real callable heads, so a
    fake global head in call position is structurally unreachable.
  - ARGUMENT position: heads/forms (as values), literals (<int>/<float>/<sym>/<kw>/<str>/#t/#f),
    a variable ref via `<id>`, nested `(`/`[`, or a closing `)` when depth>0.
  - LITERAL spelling: inside <int>/<id>/<sym>/<kw>/<str>/<float> only the right char/digit
    tokens then `<esc>`.
  - Parens stay balanced; `<eos>` only when the top form is closed (depth==0).

`mask_logits` turns the allowed set into a logit mask for generation. The grammar is validated
by feeding every gold program's v2 tokens through it (it must accept all of them — a false
reject means the grammar is too strict).

  python3 scripts/dsl_grammar.py            # validate vs all gold programs
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_ROOT))
from dsl_v2 import (CANONICAL, SPECIAL_FORMS, build_core_vocab, core_heads, to_tokens,
                    CHAR_TOKENS, DIGITS, runtime_callables)  # noqa: E402

# Special forms are MACRO KEYWORDS, not values: `(lcm unless)` -> "unless: bad syntax".
# The grammar admitted every callable atom in argument position, which made this the single
# largest surviving class in a Racket-expander fuzz of grammar-complete programs. `not` is the
# one genuine procedure in the list (checked with `procedure?` on the bridge, 2026-07-24).
MACRO_KEYWORDS = frozenset(SPECIAL_FORMS) - {"not"}
CLAUSE_KEYWORDS = frozenset({"else", "=>"})     # legal only as a cond/case clause head

LITERAL_START = {"<int>", "<float>", "<sym>", "<kw>", "<str>", "#t", "#f"}
# `{K V ...}` is the dict-literal (recolor-table) form. It is DATA, never a call, so it is a
# separate opener class: admissible wherever a value is admissible, never in operator/binding
# position. `CALL_OPENERS` is what may start a nested CALL. (kimi3 §2.1)
CALL_OPENERS = {"(", "["}
OPENERS = {"(", "[", "{"}
CLOSERS = {")", "]", "}"}
_CLOSER_OF = {"(": ")", "[": "]", "{": "}"}
CHARSET = set(CHAR_TOKENS)
DIGITSET = set(DIGITS)


BIND_FORMS = {"let", "let*", "letrec"}
# `(let-values ([(a b) expr] ...) body ...)` — same bind-list shape, but each pair's NAME slot is a
# LIST of names rather than one name. Without this the names were parsed as a call and the new
# argument-position check refused them (gold e5ead55c33e7, b27ef5e054f4, f273ee8b09ee, d7a65071b9e3).
VALUES_BIND_FORMS = {"let-values", "let*-values"}
LAMBDA_FORMS = {"lambda", "λ"}
# These identifiers need clause/class/module/signature contexts that are not
# expression calls. `place` specifically cannot expand in the bridge's eval
# namespace. Local variables shadowing these spellings remain admissible.
_NON_HEAD_KEYWORDS = {"else", "_", "open", "init", "lib", "inner", "place"}
FOR_FORMS = {"for", "for/list", "for/sum", "for/fold", "for/or", "for/and",
             "for/first", "for/last", "for/set", "for/hash", "for/product",
             "for/max", "for/min", "for*", "for*/list", "for*/fold", "for*/sum",
             "for*/or", "for*/and", "for*/first"}
FOLD_FORMS = {"for/fold", "for*/fold"}

# Prelude macros have binding tuples, not ordinary expression arguments.
# Values are (1-based tuple argument index, exact number of identifiers).
# Shapes are pinned to arc-prelude.rkt and exercised by real-Racket regressions.
BINDING_MACROS = {
    "with-bbox": (2, 4),
    "with-shape": (2, 4),
    "with-shape*": (2, 6),
    "build-grid": (3, 2),
    "build-like": (2, 3),
    "build-shape": (2, 2),
    "cellmap": (2, 3),
}
# Keep the checkpoint token table unchanged. These names already use character
# escapes; admitting their syntax must not insert/reorder embedding rows.
EXTRA_SYNTAX_HEADS = {"let*-values", "for/last"}
MACRO_KEYWORDS = MACRO_KEYWORDS | frozenset(
    FOR_FORMS | VALUES_BIND_FORMS | set(BINDING_MACROS)
    | {"set!", "match", "local", "open", "init", "lib", "place", "inner", "new", "_"}
)


# ---------------------------------------------------------------------------
# MINIMUM SUB-FORM TABLE (kimi3 §1.1).  `Frame.idx` counts COMPLETED sub-forms
# including the head, so `(if a b c)` reaches idx 4.  The frame's closer is
# WITHHELD (from both `allowed()` and `step()`) until idx >= the minimum, which
# makes every one of these unreadable-by-Racket shapes structurally unreachable:
#
#   (let* ((x 1)))      let*: bad syntax (missing body)          [215 measured deaths]
#   (define (f x))      define: bad syntax (no expressions ...)  [134]
#   (if x 1)            if: missing an "else" expression         [ 78]
#   (lambda (x))        lambda: bad syntax
#   (when t)            when: missing body
#   (for/list ((x s)))  for/list: missing body expression
#   (begin)             begin: bad syntax / last form not an expression
#
# Every entry was confirmed against the real Racket bridge on 2026-07-24; forms
# that Racket ACCEPTS empty are deliberately absent — `(cond)`, `(case 1)`,
# `(and)`, `(or)` are all legal and must stay admissible.
MIN_SUBFORMS = {
    "if": 4,                                  # (if test then else)
    "when": 3, "unless": 3,                   # (when test body ...+)
    "lambda": 3, "λ": 3,                      # (lambda formals body ...+)
    "let": 3, "let*": 3, "letrec": 3,         # (let bindings body ...+)  [named let -> 4, >=3 holds]
    "let-values": 3, "let*-values": 3,
    "define": 3,                              # (define sig body ...+) / (define name expr)
    "begin": 2,                               # (begin form ...+)  -- see _min_subforms for the
                                              # module-top-level exemption
    "quote": 2,                               # (quote datum)
    "case": 2,                                # (case key clause ...)   -- (case k) is legal
    "rule!": 2,                               # (rule! expr)
}
for _f in FOR_FORMS:
    MIN_SUBFORMS[_f] = 4 if _f in FOLD_FORMS else 3
del _f
for _f, (_slot, _count) in BINDING_MACROS.items():
    MIN_SUBFORMS[_f] = _slot + 2  # tuple plus at least one body expression
MIN_SUBFORMS.update({"set!": 3, "local": 3, "new": 2})
del _f, _slot, _count

# MAXIMUM SUB-FORM TABLE — the mirror image: once idx reaches the maximum, ONLY the
# closer is admissible, so an over-long form can't be built.  Only forms with a hard
# Racket arity are listed (both verified on the bridge):
#   (if a b c d)      -> if: bad syntax
#   (define x 1 2)    -> define: bad syntax (multiple expressions after identifier)
# `(define (f x) a b)` is a PROCEDURE define and has NO maximum, so the define entry is
# applied only when the signature was an atom (Frame.sig_is_list is False).
MAX_SUBFORMS = {"if": 4, "quote": 2, "set!": 3}

# BODY (internal-definition) POSITION — where `define` is legal and where a trailing
# `define` is illegal.  Value = the parent idx at which body forms start.
BODY_HEAD_START = {
    "lambda": 2, "λ": 2,
    "define": 2,
    "local": 2,
    "when": 2, "unless": 2,
    "with-bbox": 3,       # (with-bbox obj (r1 c1 r2 c2) body ...)
    "build-grid": 4,      # (build-grid h w (r c) body ...)
    "cellmap": 3,         # (cellmap g (r c v) body ...)
}


for _f, (_slot, _count) in BINDING_MACROS.items():
    BODY_HEAD_START[_f] = _slot + 1
del _f, _slot, _count


class Frame:
    __slots__ = ("role", "closer", "head", "idx", "named",
                 "is_body", "last_define", "sig_is_list", "binds", "pending", "for_is_list",
                 "clause_else", "terminal_clause")

    def __init__(self, role, closer, head=None, idx=0, is_body=False):
        self.role, self.closer, self.head, self.idx, self.named = role, closer, head, idx, False
        self.is_body = is_body        # True when this frame's own sub-forms sit in a body context
        self.last_define = False      # was the most recently completed sub-form a `(define ...)`?
        self.sig_is_list = False      # `define` only: was arg 1 a `(name . params)` list?
        self.binds: list[str] = []    # names this frame OWNS (dropped from scope when it closes)
        self.pending: list[str] = []  # BINDLIST only: plain-`let` names, visible when the list closes
        self.for_is_list = False      # FORCLAUSE only: is this the clause LIST, or one clause?
        self.clause_else = False
        self.terminal_clause = False


class DSLGrammar:
    """Incremental, SCOPE-AWARE validator/decoder-constraint over v2 program tokens.

    Tracks let/lambda/define/for binding contexts so that an `<id>` in a binding NAME slot is
    recorded in scope (not constrained to heads), and an `<id>` in CALL (operator) position is
    allowed iff it spells an in-scope local — blocking unknown globals like `grid-height`.
    All variables are <id>-spelled in v2 (var-slots are not atomic), so scope == set of <id>
    names introduced by a binding form so far.
    """

    def __init__(self, n_heads: int = 0):
        self.toks, self.core = build_core_vocab(n_heads)
        self.callable = set(self.core)          # atomic real heads + special forms
        self.all_callables = set(core_heads(0)) | set(self.callable) | runtime_callables()
        self.all_callables |= EXTRA_SYNTAX_HEADS
        self.rare_callables = self.all_callables - self.callable
        self.reset()

    def reset(self):
        self.depth = 0
        self.started = False
        self.stack: list[Frame] = []            # one Frame per open paren
        self.spell = None                       # None|'int'|'float'|'idlike'
        self.spell_kind = None                  # original marker token, e.g. <sym>/<id>/<int>
        self.spell_has_digit = False
        self.spell_int_neg = False
        self.spell_chars: list[str] = []        # accumulate spelled name
        self.spell_is_binding = False           # is this <id> in a binding-name slot?
        self.spell_is_operator = False          # is this <id> in call position?
        self.spell_is_arg = False               # is this <id> a plain argument-position ref?
        self.scope: set[str] = set()            # in-scope local names
        self.scope_counts: dict[str, int] = {}  # shadowing-safe multiset behind `scope`
        self.bad_call = None                    # set if an unknown global was called
        self.spell_allowed_names: set[str] | None = None
        self.spell_empty_ok = False
        self.quote_next = False                 # quote shorthand: '(...datum...) after empty <sym>
        return self

    # role of a NEW paren, from its parent context
    def _child_role(self) -> str:
        if not self.stack:
            return "CALL"
        p = self.stack[-1]
        if self.quote_next:
            return "DATA"
        if p.role == "DATA":
            return "DATA"
        if p.head == "quote" and p.idx == 1:
            return "DATA"
        if p.head == "cond" and p.idx >= 1:
            return "CONDCLAUSE"                # (cond (test expr...) ...); test may be bare var
        if p.role == "CONDCLAUSE":
            return "CALL"
        if p.head == "match" and p.idx >= 2:
            return "MATCHCLAUSE"
        if p.role == "MATCHCLAUSE" and p.idx == 0:
            return "DATA"  # compound pattern grammar remains conservatively permissive
        if p.head == "local" and p.idx == 1:
            return "DEFLIST"
        if p.head == "new" and p.idx >= 2:
            return "INITPAIR"                 # (new class-expr [field-id value] ...)
        if p.head == "case" and p.idx >= 2:
            return "CASECLAUSE"
        if p.role == "CASECLAUSE" and p.idx == 0:
            return "DATA"                      # case datum list: ((1 2 3) expr...)
        if p.head in LAMBDA_FORMS and p.idx == 1:
            return "PARAMLIST"
        if p.head in BIND_FORMS and ((not p.named and p.idx == 1) or (p.named and p.idx == 2)):
            return "BINDLIST"                 # plain let: idx1; named let: idx2 (after loop name)
        if p.head in VALUES_BIND_FORMS and p.idx == 1:
            return "BINDLIST"
        if p.role == "BINDLIST":
            return "BINDPAIR"
        if (p.role == "BINDPAIR" and p.idx == 0 and len(self.stack) >= 3
                and self.stack[-3].head in VALUES_BIND_FORMS):
            return "VALNAMES"                 # (let-values ([(a b) expr]) ...) -> a, b are bindings
        if p.role == "FORCLAUSE":
            # FORCLAUSE used to be INFECTIOUS — every paren nested anywhere under a for-clause
            # stayed a FORCLAUSE, so `(for/fold ((b (sort xs (lambda (a b) ...)))) ...)` parsed the
            # lambda's parameter list as a clause: `a` bound, `b` treated as an argument, and the
            # sequence expression's head (`sort`) recorded as a BINDING name (scope pollution).
            # A for-clause frame is either the clause LIST `((x s) (y s))` or ONE clause `(x s)`;
            # `for_is_list` records which, from whether its first sub-form was a paren or an atom.
            if p.idx == 0:
                p.for_is_list = True          # a paren at slot 0 => this frame is the clause LIST
                return "FORCLAUSE"
            return "FORCLAUSE" if p.for_is_list else "CALL"   # else: a sequence EXPRESSION
        if p.head == "define" and p.idx == 1:
            return "DEFSIG"
        if p.head in BINDING_MACROS and p.idx == BINDING_MACROS[p.head][0]:
            return "MACROPARAMS"              # exact, flat identifier tuple
        if p.head in FOLD_FORMS and p.idx in (1, 2):
            return "FORCLAUSE"                # for/fold accs (idx1) + iteration clause (idx2)
        if p.head in (FOR_FORMS - FOLD_FORMS) and p.idx == 1:
            return "FORCLAUSE"                # ordinary for: one clause list, then body forms
        return "CALL"

    def _name_slot(self) -> str:
        """'binding' | 'operator' | 'arg' for the current name position."""
        if not self.stack:
            return "arg"
        f = self.stack[-1]
        if f.role in ("DATA", "CONDCLAUSE", "CASECLAUSE"):
            return "arg"
        if f.role == "MATCHCLAUSE" and f.idx == 0:
            return "binding"
        if f.role == "INITPAIR" and f.idx == 0:
            return "field"                    # syntactic field name, NOT a lexical binding
        if f.role in ("PARAMLIST", "DEFSIG", "VALNAMES", "MACROPARAMS"):
            return "binding"
        if f.role in ("BINDPAIR", "FORCLAUSE") and f.idx == 0:
            return "binding"
        if f.head in LAMBDA_FORMS and f.idx == 1:
            return "binding"                  # (lambda rest-name body ...) binds the rest list
        if f.head == "define" and f.idx == 1:
            return "binding"                  # (define name expr) binds name in later local scope
        if f.head in BIND_FORMS and f.idx == 1 and not f.named:
            return "binding"                 # named-let loop name (or the bindlist `(`)
        if f.role == "CALL" and f.idx == 0:
            return "operator"
        return "arg"

    # ---- position / arity ---------------------------------------------------
    def _child_is_body(self) -> bool:
        """Would a form opened HERE sit in a body (internal-definition) context?

        Racket only permits `define` in a body, and a body's LAST form must be an
        expression.  Both facts were re-verified on the real bridge (2026-07-24):
          (let () (define x 1) x)      -> 1        legal
          (let () (define x 1))        -> ERROR    "the last form is not an expression"
          (+ 1 (define x 2))           -> ERROR    "define: not allowed in an expression context"
          (begin (define x 1))         -> legal ONLY at module top level
        """
        if not self.stack:
            return True                       # module top level
        p = self.stack[-1]
        if p.role in ("DATA", "BINDLIST", "BINDPAIR", "PARAMLIST", "DEFSIG", "FORCLAUSE",
                      "VALNAMES", "MACROPARAMS", "INITPAIR"):
            return False
        if p.role == "DEFLIST":
            return True
        if p.role in ("CONDCLAUSE", "CASECLAUSE", "MATCHCLAUSE"):
            return p.idx >= 1                 # (cond (test body ...)) / (case (d ...) body ...)
        h = p.head
        if h is None:
            return False
        if h == "begin":
            return p.is_body and p.idx >= 1   # begin SPLICES: a body begin is still a body
        if h in BIND_FORMS:
            return p.idx >= (3 if p.named else 2)
        if h in VALUES_BIND_FORMS:
            return p.idx >= 2
        if h in FOLD_FORMS:
            return p.idx >= 3
        if h in FOR_FORMS:
            return p.idx >= 2
        start = BODY_HEAD_START.get(h)
        return start is not None and p.idx >= start

    def _min_subforms(self, f: "Frame") -> int:
        # A let/let-values binding pair is EXACTLY `(name expr)` — verified: `(let ((x)) 1)` and
        # `(let ((x 1 2)) 1)` both raise "not an identifier and expression for a binding".
        if f.role == "MACROPARAMS":
            return BINDING_MACROS[self.stack[-2].head][1]
        if f.role == "CONDCLAUSE":
            return 2 if f.clause_else else 1
        if f.role in ("CASECLAUSE", "MATCHCLAUSE"):
            return 2
        if f.role in ("BINDPAIR", "INITPAIR"):
            return 2
        if f.head is None:
            return 0
        if f.head == "let" and f.named:
            return 4                    # (let name (bindings) body ...+) — verified "(let f [])"
                                        # -> "let: bad syntax (missing body)"
        if f.head == "begin" and len(self.stack) == 1:
            # A bare `(begin)` / `(begin (define x 1))` IS legal at module top level (verified).
            # Only reachable if a whole program were a top-level begin; never inside `(rule! ...)`.
            return 0
        return MIN_SUBFORMS.get(f.head, 0)

    def _max_subforms(self, f: "Frame"):
        if f.role == "MACROPARAMS":
            return BINDING_MACROS[self.stack[-2].head][1]
        if f.role in ("BINDPAIR", "INITPAIR"):
            return 2
        if f.head is None:
            return None
        if f.head == "define":
            return None if f.sig_is_list else 3      # (define name expr) takes exactly one expr
        return MAX_SUBFORMS.get(f.head)

    def _requires_list(self) -> bool:
        """True where ONLY a `(`/`[` sub-form is admissible — a binding/clause LIST slot.

        Verified on the bridge (2026-07-24): `(let* x 1)` / `(letrec x 1)` -> "not a sequence of
        identifier--expression bindings"; `(for/list x 1)` -> "bad sequence binding clauses";
        `(for/fold x y 1)` -> "invalid accumulator binding clause(s)"; `(cond 1)` -> "clause is
        not a test-value pair"; `(case 1 2)` -> bad syntax.  Deliberately NOT listed:
        `(lambda x 1)` is LEGAL (rest-arg form) and `(let name ((i 0)) ...)` takes the loop
        NAME at index 1, so plain `let` is only constrained once it is known to be named.
        """
        f = self.stack[-1] if self.stack else None
        if f is None:
            return False
        if f.role == "CONDCLAUSE" or f.role == "DATA":
            return False
        if f.role in ("BINDLIST", "DEFLIST"):
            return True          # every element is a `(name expr)` pair: `(let* (x) 1)` is an error
        h, i = f.head, f.idx
        if h is None:
            return False
        if h in BINDING_MACROS:
            return i == BINDING_MACROS[h][0]
        if h == "local":
            return i == 1
        if h in ("match", "new"):
            return i >= 2
        if h in ("let*", "letrec") or h in VALUES_BIND_FORMS:
            return i == 1
        if h == "let":
            return i == 2 and f.named
        if h in FOLD_FORMS:
            return i in (1, 2)
        if h in FOR_FORMS:
            return i == 1
        if h == "cond":
            return i >= 1
        if h == "case":
            return i >= 2
        return False

    def _closer_ready(self) -> bool:
        """May the current frame be closed?  False while a mandatory sub-form is still
        missing, or while the last completed sub-form was a `define` (a body may not end
        on a definition)."""
        if not self.stack:
            return False
        f = self.stack[-1]
        if f.idx < self._min_subforms(f):
            return False
        # `len(self.stack) == 1` is the module-top-level form, whose children ARE top-level
        # forms, where a trailing define is legal.
        if f.last_define and len(self.stack) > 1 and f.role != "DEFLIST":
            return False
        return True

    def _at_max(self) -> bool:
        f = self.stack[-1] if self.stack else None
        if f is None:
            return False
        if f.terminal_clause:
            return True
        mx = self._max_subforms(f)
        return mx is not None and f.idx >= mx

    # ---- lexical scope ------------------------------------------------------
    # Scope used to be MONOTONIC — `CLOSERS` popped the frame but never unbound, so
    # `(begin (let ((x 1)) 2) (+ x 1))` was accepted and died at the bridge with
    # "x: undefined" (kimi3 §1.3).  Every binding is now OWNED by the frame whose
    # extent it has, and released when that frame closes.  A multiset keeps shadowing
    # (`(let ((g 1)) (let ((g 2)) ...))`) correct.
    def _add_scope(self, name: str):
        self.scope_counts[name] = self.scope_counts.get(name, 0) + 1
        self.scope.add(name)

    def _drop_scope(self, name: str):
        c = self.scope_counts.get(name, 0) - 1
        if c <= 0:
            self.scope_counts.pop(name, None)
            self.scope.discard(name)
        else:
            self.scope_counts[name] = c

    def _bind_target(self):
        """(owning_frame_or_None, deferred_bindlist_or_None) for a name in a binding slot.

        The owner is the frame whose EXTENT the binding has, which is rarely the frame the
        name is written inside:
          (lambda (x) ...)      x  -> the lambda frame, not the PARAMLIST
          (define (f a) ...)    f  -> the frame ENCLOSING the define (it stays in scope for
                                      sibling body forms);  a -> the define frame
          (define n expr)       n  -> the enclosing frame
          (let* ((x 1)) ...)    x  -> the let frame, visible immediately (let* semantics)
          (let  ((x 1)) ...)    x  -> DEFERRED to the bindlist: plain `let` evaluates all RHS
                                      in the OUTER scope, so `(let ((x 1) (y x)) y)` is an
                                      error — "x: undefined" (kimi3 §1.4, verified on bridge)
          (for/list ((x s)) …)  x  -> the for frame
        """
        st = self.stack
        if not st:
            return None, None
        f = st[-1]
        if f.role == "VALNAMES":
            # Simultaneous let-values RHSs use the OUTER scope; let*-values
            # exposes a tuple only AFTER its own RHS, to subsequent pairs.
            if len(st) >= 4 and st[-4].head == "let-values":
                return None, st[-3]           # defer to BINDLIST close
            if len(st) >= 4 and st[-4].head == "let*-values":
                return None, st[-2]           # defer to BINDPAIR close
            return (st[-4] if len(st) >= 4 else None), None
        if f.role in ("PARAMLIST", "MACROPARAMS"):
            return (st[-2] if len(st) >= 2 else None), None
        if f.role == "DEFSIG":
            if f.idx == 0:                              # the procedure name
                if len(st) >= 4 and st[-3].role == "DEFLIST":
                    return st[-4], None
                return (st[-3] if len(st) >= 3 else None), None
            return (st[-2] if len(st) >= 2 else None), None      # its parameters
        if f.role == "BINDPAIR":
            letf = st[-3] if len(st) >= 3 else None
            head = letf.head if letf is not None else None
            if head == "let":
                return None, st[-2]     # plain let: visible only once the whole bindlist closes
            if head == "let*":
                return None, f          # let*: visible to LATER pairs, but not to its own RHS
            return letf, None           # letrec / let-values: recursive, visible immediately
        if f.role == "FORCLAUSE":
            i = len(st) - 1
            while i > 0 and st[i].role == "FORCLAUSE":
                i -= 1
            return st[i], None
        if f.head == "define" and f.idx == 1:
            if len(st) >= 3 and st[-2].role == "DEFLIST":
                return st[-3], None
            return (st[-2] if len(st) >= 2 else None), None
        return f, None

    def _bind(self, name: str):
        if not name:
            return
        if name == "_" and self.stack and self.stack[-1].role == "MATCHCLAUSE":
            return                              # match wildcard does not bind a variable
        owner, deferred = self._bind_target()
        if deferred is not None:
            deferred.pending.append(name)
            return
        self._add_scope(name)
        if owner is not None:
            owner.binds.append(name)        # owner is None -> program-lifetime binding

    def _close_frame(self, f: "Frame"):
        for name in f.binds:
            self._drop_scope(name)
        if f.pending:
            # A deferred binding becomes visible now. Its OWNER is always the let form, which is
            # one frame further out for a BINDPAIR (pair -> bindlist -> let) than for a BINDLIST.
            if f.role == "BINDPAIR":
                owner = self.stack[-2] if len(self.stack) >= 2 else None
            else:
                owner = self.stack[-1] if self.stack else None
            for name in f.pending:
                self._add_scope(name)
                if owner is not None:
                    owner.binds.append(name)

    def _in_datum_position(self) -> bool:
        """True where an identifier is DATA, not a variable reference: inside a quoted list,
        inside a `{K V ...}` table, or as a `case` clause datum. Those must stay unchecked."""
        if not self.stack:
            return False
        f = self.stack[-1]
        return (f.role == "DATA" or self.quote_next
                or (f.head == "quote" and f.idx >= 1))     # (quote down) — `down` is a datum

    def _arg_gate_names(self) -> set[str]:
        """Names a SPELLED `<id>` may complete to in argument position: an in-scope local, or a
        real callable passed as a value (`(filter number? ...)`). Atomic-vocab names never reach
        here — the tokenizer emits those as single tokens, which are separately admissible."""
        gate = self.scope | (self.rare_callables - MACRO_KEYWORDS)
        if (self.stack and self.stack[-1].role == "CONDCLAUSE"
                and self.stack[-1].idx == 1):
            gate = gate | {"=>"}            # (cond [test => proc]) — a clause keyword, not a var
        return gate

    def _blocked_value_atoms(self) -> frozenset:
        """Atomic tokens that may NOT stand as a VALUE at the current position.

        A macro keyword SHADOWED by a local binding is an ordinary variable again — gold
        5a85abd1e231 binds `(let ((or (* 3 ...))) ...)` and 9df67b512dad takes `(or oc)` as a
        build-grid parameter pair — so anything currently in scope is exempt.
        """
        if self._in_datum_position():
            return frozenset()                        # inside quoted data anything is a datum
        blocked = MACRO_KEYWORDS
        f = self.stack[-1] if self.stack else None
        if f is not None and f.role in ("CONDCLAUSE", "CASECLAUSE") and f.idx == 0:
            blocked = blocked - {"else"}
        if f is not None and f.role == "CONDCLAUSE" and f.idx == 1:
            blocked = blocked - {"=>"}
        return blocked - self.scope

    def _arg_id_ok(self) -> bool:
        """May a spelled `<id>` start here at all? Free in datum positions; otherwise only when
        SOMETHING is in scope for it to spell."""
        return self._in_datum_position() or bool(self._arg_gate_names())

    def _head_allowed(self, t: str) -> bool:
        """Operator-position keyword gate (kimi3 §1.6).

        `define` is a DEFINITION, legal only in a body (internal-definition) context:
        `(+ 1 (define x 2))` -> "define: not allowed in an expression context".
        `else` is a cond/case CLAUSE keyword and is never a callable head; a real
        `(else ...)` clause is parsed with role CONDCLAUSE/CASECLAUSE, where the slot
        is `arg`, so this gate never sees it.
        """
        if t in self.scope:
            return True                      # a local shadow is a procedure/value, not syntax
        if t == "define":
            return bool(self.stack) and self.stack[-1].is_body
        if t in _NON_HEAD_KEYWORDS:
            return False
        return True

    def _current_closer(self) -> set[str]:
        """The closer for the open frame — EMPTY while mandatory sub-forms are missing, so the
        generation mask never offers a premature `)` (kimi3 §1.1: 'mirror the same table in
        allowed()')."""
        return {self.stack[-1].closer} if (self.stack and self._closer_ready()) else set()

    def _allowed_name_chars(self) -> set[str]:
        """Prefix-gate a spelled operator to known callables or in-scope locals."""
        if self.spell_allowed_names is None:
            out = set(CHARSET)
            if self.spell_chars or self.spell_empty_ok:
                out.add("<esc>")
            return out
        prefix = "".join(c[1:] for c in self.spell_chars)
        out: set[str] = set()
        if prefix and prefix in self.spell_allowed_names:
            out.add("<esc>")
        for name in self.spell_allowed_names:
            if name.startswith(prefix) and len(name) > len(prefix):
                tok = "§" + name[len(prefix)]
                if tok in CHARSET:
                    out.add(tok)
        return out


    def _name_char_allowed(self, t: str) -> bool:
        """Fast membership check while spelling an id/symbol/string.

        `allowed()` materializes a full token set for generation masks, but the
        validator calls `step()` once per gold token. This mirrors
        `_allowed_name_chars()` without building multi-thousand element sets.
        """
        if self.spell_allowed_names is None:
            return t in CHARSET or ((self.spell_chars or self.spell_empty_ok) and t == "<esc>")
        prefix = "".join(c[1:] for c in self.spell_chars)
        if t == "<esc>":
            return bool(prefix and prefix in self.spell_allowed_names)
        if not t.startswith("§") or t not in CHARSET:
            return False
        nxt = prefix + t[1:]
        return any(name.startswith(nxt) and len(name) > len(prefix) for name in self.spell_allowed_names)

    def _token_allowed(self, t: str) -> bool:
        """Membership-only version of `allowed()` for validation/per-token stepping."""
        if self.bad_call is not None:
            return False
        if self.spell == "int":
            return (t in DIGITSET or (self.spell_has_digit and t == "<esc>")
                    or ((not self.spell_has_digit) and (not self.spell_int_neg) and t == "<neg>"))
        if self.spell == "idlike":
            return self._name_char_allowed(t)
        if self.spell == "float":
            return t in CHARSET or (bool(self.spell_chars) and t == "<esc>")
        if not self.started:
            return t == "("
        if self.depth == 0:
            return t == "<eos>"
        if self._at_implicit_rule_close():
            return t == ")"              # the outer rule! wrapper must be closed explicitly
        slot = self._name_slot()
        closer_ok = bool(self.stack and t == self.stack[-1].closer) and self._closer_ready()
        if self._at_max():
            return closer_ok                 # arity is full: nothing but the closer fits
        if self._requires_list():
            # a binding/clause LIST slot takes only a list — but the frame may still be closed
            # (e.g. `(cond (a 1))` requires a list at idx 1 AND must be closable at idx 2)
            return t in CALL_OPENERS or closer_ok
        if self.stack and self.stack[-1].role == "DATA":
            return t in self.callable or t in OPENERS or t in LITERAL_START or t == "<id>" or closer_ok
        if slot == "field":
            return t in self.callable or t == "<id>"
        if self.stack and self.stack[-1].head == "set!" and self.stack[-1].idx == 1:
            return (t in self.callable and t not in self._blocked_value_atoms()) or (
                t == "<id>" and self._arg_id_ok())
        if self.stack and self.stack[-1].role == "MATCHCLAUSE" and self.stack[-1].idx == 0:
            return t in self.callable or t == "<id>" or t in OPENERS or t in LITERAL_START
        if self.stack and self.stack[-1].role == "MACROPARAMS":
            return t in self.callable or t == "<id>" or closer_ok
        if slot == "binding":
            return t in self.callable or t == "<id>" or t in CALL_OPENERS or closer_ok
        if slot == "operator":
            if not self._head_allowed(t):
                return False
            return (t in self.callable or t in CALL_OPENERS
                    or (t == "<id>" and bool(self.scope or self.rare_callables)))
        return ((t in self.callable and t not in self._blocked_value_atoms())
                or t in OPENERS or t in LITERAL_START or closer_ok
                or (t == "<id>" and self._arg_id_ok()))

    def allowed(self) -> set[str]:
        if self.bad_call is not None:
            return set()
        if self.spell == "int":
            out = set(DIGITSET)
            if self.spell_has_digit:
                out.add("<esc>")
            elif not self.spell_int_neg:   # next259: <neg> allowed only ONCE, before any digit
                out.add("<neg>")
            return out
        if self.spell == "idlike":
            return self._allowed_name_chars()
        if self.spell == "float":
            out = set(CHARSET)
            if self.spell_chars:
                out.add("<esc>")
            return out
        if not self.started:
            return {"("}
        if self.depth == 0:
            return {"<eos>"}
        if self._at_implicit_rule_close():
            return {")"}                # the outer rule! wrapper must be closed explicitly
        if self._at_max():
            return self._current_closer()          # arity is full: nothing but the closer fits
        if self._requires_list():
            return set(CALL_OPENERS) | self._current_closer()   # a LIST slot, or close the frame
        if self.stack and self.stack[-1].role == "DATA":
            out = set(self.callable) | OPENERS | LITERAL_START | {"<id>"} | self._current_closer()
            return out
        slot = self._name_slot()
        if slot == "field":
            return set(self.callable) | {"<id>"}
        if self.stack and self.stack[-1].head == "set!" and self.stack[-1].idx == 1:
            return (set(self.callable) - self._blocked_value_atoms()) | (
                {"<id>"} if self._arg_id_ok() else set())
        if self.stack and self.stack[-1].role == "MATCHCLAUSE" and self.stack[-1].idx == 0:
            return set(self.callable) | {"<id>"} | OPENERS | LITERAL_START
        if self.stack and self.stack[-1].role == "MACROPARAMS":
            return set(self.callable) | {"<id>"} | self._current_closer()
        if slot == "binding":
            # names may be atomic (g/h/w leaked into the head set) or <id>-spelled; both fine —
            # the closed atomic set can't spell new hallucinations, only <id> can.
            return set(self.callable) | {"<id>"} | CALL_OPENERS | self._current_closer()
        if slot == "operator":
            out = (set(self.callable) - (_NON_HEAD_KEYWORDS - self.scope)) | CALL_OPENERS
            if "define" not in self.scope and not (self.stack and self.stack[-1].is_body):
                out.discard("define")            # definitions are illegal in expression position
            if self.scope or (self.all_callables - self.callable):
                out.add("<id>")                          # prefix-gated local or rare real callable
            return out
        out = (set(self.callable) - self._blocked_value_atoms()) | OPENERS | LITERAL_START
        if self._arg_id_ok():
            out.add("<id>")        # never offer <id> with nothing it could legally spell
        if self.depth > 0:
            out |= self._current_closer()
        return out

    def _at_implicit_rule_close(self) -> bool:
        """True when only the root (rule! ...) frame is unclosed AND it has
        already received its one argument (idx >= 2).

        Gold programs in canonical/grounded_rules.py are stored without the
        final closing paren for rule!  (the REPL treats rule! as a top-level
        command and accepts the expression-inside as the complete unit).
        Accepting depth==1 + sole rule! frame (post-arg) as 'complete' matches
        that convention without weakening any other structural constraint.

        idx accounting: the rule! frame starts at idx=0; rule! itself bumps it
        to 1 (operator slot); its one child expression (a paren form or atom)
        bumps it to 2 when closed.  So idx >= 2 means the body expr is done.
        """
        return (self.depth == 1 and self.spell is None and self.bad_call is None
                and len(self.stack) == 1 and self.stack[0].head == "rule!"
                and self.stack[0].idx >= 2)

    def complete(self) -> bool:
        # STRICT: a program is complete only at depth 0 (all parens closed). The old
        # implicit-rule!-close allowance existed for 3 gold programs that omitted their final
        # ')' — those are fixed at source (2026-07-02); the allowance let constrained decode
        # stop one paren short, which detokenized to an UNBALANCED program the verifier then
        # rejected ("unbalanced parentheses" ~ a third of sampled failures — phantom crashes).
        return (self.started and self.depth == 0 and self.spell is None
                and self.bad_call is None)

    def step(self, t: str) -> bool:
        if not self._token_allowed(t):
            return False
        if self.spell is not None:
            if t == "<esc>":
                name = "".join(c[1:] for c in self.spell_chars)
                if self.spell_kind == "<sym>" and name == "":
                    # Tokenizer represents quote shorthand before a datum list, `'(`, as an
                    # empty symbol marker followed by the quoted list.  The following list is
                    # data, not a function call, so integers/symbols in operator position are OK.
                    self.quote_next = True
                if self.spell == "idlike":
                    if self.spell_is_operator and self.stack:
                        self.stack[-1].head = None if name in self.scope else name
                    if self.spell_is_binding:
                        self._bind(name)
                    elif self.spell_is_operator and name not in self.scope \
                            and name not in self.all_callables:
                        self.bad_call = name             # unknown global in call position
                self.spell = None; self.spell_chars = []
                self.spell_allowed_names = None
                self.spell_empty_ok = False
                self.spell_kind = None
                self.spell_is_binding = self.spell_is_operator = self.spell_is_arg = False
                # The `'(` shorthand is an EMPTY <sym> marker followed by the quoted list. The
                # marker is not a sub-form of its own — the list that follows completes the single
                # quoted datum — so counting it would inflate `idx` by one and make the arity
                # tables (MIN_SUBFORMS/MAX_SUBFORMS) misfire on e.g. `(define x '(1 2))`.
                if self.stack and not self.quote_next:
                    self.stack[-1].idx += 1
                    self.stack[-1].last_define = False
            elif self.spell == "int" and t == "<neg>":
                self.spell_int_neg = True
            elif self.spell == "int" and t in DIGITSET:
                self.spell_has_digit = True; self.spell_chars.append("§" + t)
            elif t.startswith("§"):
                self.spell_chars.append(t)
            return True
        if t in OPENERS:
            self.depth += 1; self.started = True
            # `{...}` is always a data table, never a call — its contents are literal keys/values.
            role = "DATA" if (self.quote_next or t == "{") else self._child_role()
            is_body = (not self.quote_next and t != "{" and self._child_is_body())
            self.quote_next = False
            if role == "DEFSIG" and self.stack:
                self.stack[-1].sig_is_list = True      # (define (f x) ...) -> procedure form
            self.stack.append(Frame(role, _CLOSER_OF[t], is_body=is_body))
            return True
        if t in CLOSERS:
            self.depth -= 1
            popped = self.stack.pop() if self.stack else None
            if popped is not None:
                self._close_frame(popped)
            if self.stack:
                self.stack[-1].idx += 1
                # a body may not END on a definition (verified: "(let () (define x 1))" ->
                # "the last form is not an expression"), so remember what just closed.
                self.stack[-1].last_define = (popped is not None and popped.head == "define")
                if popped is not None and popped.clause_else:
                    self.stack[-1].terminal_clause = True
            return True
        # an atom
        slot = self._name_slot()
        nf = self.stack[-1] if self.stack else None
        if nf is not None and nf.head in BIND_FORMS and nf.idx == 1 and not nf.named:
            nf.named = True                   # this name token is the named-let loop name
        if t in ("<int>", "<float>", "<sym>", "<kw>", "<str>"):
            self.spell = "int" if t == "<int>" else ("float" if t == "<float>" else "idlike")
            self.spell_kind = t
            self.spell_has_digit = False; self.spell_int_neg = False; self.spell_chars = []
            self.spell_allowed_names = None
            self.spell_empty_ok = (t in ("<sym>", "<str>"))
            return True
        if t == "<id>":
            self.spell = "idlike"; self.spell_chars = []
            self.spell_kind = t
            self.spell_empty_ok = False
            self.spell_is_binding = (slot == "binding")
            self.spell_is_operator = (slot == "operator")
            # DATA / quoted / clause roles are datum positions, not variable refs — exempt.
            self.spell_is_arg = (slot == "arg" and not self._in_datum_position())
            if slot == "operator":
                self.spell_allowed_names = self.scope | {
                    name for name in self.rare_callables if self._head_allowed(name)
                }
            elif self.spell_is_arg:
                # kimi3 §1.2: argument-position identifiers were NEVER scope-checked, so
                # `(+ zztop 1)` was `complete()` and died at the bridge on "zztop: undefined".
                # Prefix-gating (rather than a check at <esc>) means the generation MASK enforces
                # it too, so the decoder can never spell itself into an unbound name.
                self.spell_allowed_names = self._arg_gate_names()
            else:
                self.spell_allowed_names = None
            return True
        # atomic head / special form / #t / #f / atomic var (g/h/w...)
        f = self.stack[-1] if self.stack else None
        if f is not None and f.role == "DATA":
            f.idx += 1
            f.last_define = False
            return True
        if slot == "binding" and t not in ("#t", "#f"):
            self._bind(t)                                 # atomic binding name (g, h, w, ...)
        if f is not None and f.role == "CALL" and f.idx == 0:
            f.head = None if t in self.scope else t        # shadowed syntax is an ordinary call
        if f is not None:
            if (f.role in ("CONDCLAUSE", "CASECLAUSE") and f.idx == 0
                    and t == "else" and t not in self.scope):
                f.clause_else = True
            f.idx += 1
            f.last_define = False
        return True

    # ---- logit mask for generation ------------------------------------------
    def mask_logits(self, logits, tok2id: dict):
        import torch
        allowed = self.allowed()
        mask = torch.full_like(logits, float("-inf"))
        idx = [tok2id[t] for t in allowed if t in tok2id]
        if idx:
            mask[..., idx] = 0.0
        return logits + mask


def _validate(n_heads: int = 0, limit: int = 0) -> int:
    g = DSLGrammar(n_heads)
    canonical = CANONICAL
    n = ok = 0
    rejects = []
    for line in canonical.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = (r.get("program_solution") or "").strip()
        if not p:
            continue
        n += 1
        g.reset()
        toks = to_tokens(p, g.core)
        good = True
        for i, t in enumerate(toks):
            if not g.step(t):
                rejects.append((r.get("task_id"), i, t, toks[max(0, i - 4):i + 1]))
                good = False
                break
        if good and not g.complete():
            rejects.append((r.get("task_id"), -1, "INCOMPLETE", toks[-5:]))
            good = False
        ok += good
        if limit and n >= limit:
            break
    print(f"grammar vs gold: accepted {ok}/{n}  (vocab={len(g.toks)}, callable={len(g.callable)})")
    if rejects:
        print(f"LOUD: {len(rejects)} gold programs rejected (grammar too strict) — first 8:")
        for tid, i, t, ctx in rejects[:8]:
            print(f"  {tid} @tok{i} '{t}'  ctx={ctx}")
    else:
        print("OK: grammar admits EVERY gold program AND gates operator position to real heads.")
    return 0 if not rejects else 1


if __name__ == "__main__":
    raise SystemExit(_validate(0, int(sys.argv[1]) if len(sys.argv) > 1 else 0))
