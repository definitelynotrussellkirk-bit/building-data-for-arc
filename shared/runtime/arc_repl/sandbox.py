"""
Sandbox — isolated rule testing for the swarm pipeline.

Provides:
- try_rule_isolated(): test a rule in a fresh executor, no side effects
- classify_error(): structured error classification
- known_symbols(): all defined function/variable names
- validate_syntax(): check S-expression syntax before executing

These are used by the swarm's lint/filter/shadow-execution layers.
"""

from __future__ import annotations

import re
import os
from dataclasses import dataclass, field
from typing import Any

from .builtins import Grid, _unwrap, make_global_env
from .executor import ArcExecutor
from .parser import parse


# ============================================================
# Structured results
# ============================================================

@dataclass
class PairResult:
    """Result of testing a rule on one training pair."""
    pair_idx: int
    passed: bool
    diff_cells: int = 0
    total_cells: int = 0
    shape_match: bool = True
    error: str | None = None
    error_class: str | None = None   # classified error type
    detail: str = ""                 # full REPL output
    got_shape: tuple[int, int] | None = None
    expected_shape: tuple[int, int] | None = None


@dataclass
class RuleResult:
    """Result of testing a rule on all training pairs."""
    rule_text: str
    pairs: list[PairResult] = field(default_factory=list)
    pass_count: int = 0
    total: int = 0
    all_pass: bool = False
    set_error: str | None = None     # error from setting the rule itself
    set_error_class: str | None = None
    test_outputs: list | None = None  # grids for test inputs (only if all_pass)
    diff_score: float = float('inf')  # lower = better, 0 = perfect
    backend: str = 'unknown'  # set only after successful executor initialization
    requested_backend: str = 'unknown'


# ============================================================
# Error classification
# ============================================================

# Common wrong names → correct names with examples
FUNCTION_CORRECTIONS = {
    "quot": ("/", "(/ a b) — integer division"),
    "quotient": ("/", "(/ a b) — integer division"),
    "integer-divide": ("/", "(/ a b)"),
    "div": ("/", "(/ a b)"),
    "mod": ("modulo", "(modulo a b)"),
    "remainder": ("modulo", "(modulo a b)"),
    "car": ("first", "(first lst)"),
    "cdr": ("rest", "(rest lst) or (cdr lst)"),
    "cadr": ("second", "(second lst)"),
    "vector-ref": ("nth", "(nth lst i)"),
    "list-ref": ("nth", "(nth lst i)"),
    "string->number": ("(use literal integers)", "just write the number directly"),
    "number->string": ("(not needed)", "the REPL handles display"),
    "apply": ("(call directly)", "(fn arg1 arg2) not (apply fn args)"),
    "expt": ("(not available)", "use (* a a) for squaring"),
    "abs": ("(if (< x 0) (- 0 x) x)", "no abs builtin, use conditional"),
    "null": ("nil", "nil or '()"),
    "true": ("#t", "use #t for true"),
    "false": ("#f", "use #f for false"),
    "eq?": ("=", "(= a b)"),
    "equal?": ("=", "(= a b)"),
    "zero?": ("(= x 0)", "use (= x 0)"),
    "positive?": ("(> x 0)", "use (> x 0)"),
    "negative?": ("(< x 0)", "use (< x 0)"),
    "even?": ("(= (modulo x 2) 0)", "use modulo"),
    "odd?": ("(!= (modulo x 2) 0)", "use modulo"),
    "display": ("(not needed)", "REPL shows results automatically"),
    "print": ("(not needed)", "REPL shows results automatically"),
    "newline": ("(not needed)", ""),
    "begin": ("(begin e1 e2 ...)", "begin is available"),
    "set!": ("set-cell", "use set-cell for grids, define for bindings"),
    "make-vector": ("empty-grid", "(empty-grid h w)"),
    "make-list": ("(map (lambda (_) val) (range 0 n))", "build via map"),
    "hash-ref": ("(not available)", "use dicts with {} syntax"),
}


@dataclass
class ErrorInfo:
    """Classified error with actionable feedback."""
    rule: str           # error class name
    message: str        # original error message
    suggestion: str     # what to do instead
    recoverable: bool   # worth retrying?
    context: dict = field(default_factory=dict)


def classify_error(error_text: str) -> ErrorInfo:
    """Classify a REPL error into a category with actionable feedback."""
    if not error_text:
        return ErrorInfo("unknown", "", "No error text", False)

    msg = error_text.strip()

    # Unbound variable
    m = re.search(r'[Uu]nbound:?\s+(\S+)', msg)
    if m:
        name = m.group(1)
        if name in FUNCTION_CORRECTIONS:
            correct, example = FUNCTION_CORRECTIONS[name]
            return ErrorInfo(
                "unbound_known_fix", msg,
                f"'{name}' is not available. Use {correct}: {example}",
                True, {"name": name, "correction": correct},
            )
        return ErrorInfo(
            "unbound", msg,
            f"'{name}' is not defined. Check spelling, or use an available primitive.",
            True, {"name": name},
        )

    # Parse error
    if "parse" in msg.lower() or "syntax" in msg.lower():
        return ErrorInfo(
            "parse_error", msg,
            "S-expression syntax error. Check balanced parens and quoting.",
            True,
        )

    # Type error
    if "type" in msg.lower() and ("error" in msg.lower() or "expected" in msg.lower()):
        return ErrorInfo(
            "type_error", msg,
            "Type mismatch. Check that you're passing the right types (grid vs list vs int).",
            True,
        )

    # Arity error
    if "arity" in msg.lower() or ("expected" in msg.lower() and "arg" in msg.lower()):
        return ErrorInfo(
            "arity_error", msg,
            "Wrong number of arguments. Check the function signature.",
            True,
        )

    # Shape mismatch (output wrong size)
    if "shape" in msg.lower() and "mismatch" in msg.lower():
        return ErrorInfo(
            "shape_mismatch", msg,
            "Output grid has wrong dimensions. Check your size calculations.",
            True,
        )

    # Max turns / cost exceeded
    if "max" in msg.lower() and ("turn" in msg.lower() or "test" in msg.lower() or "exceed" in msg.lower()):
        return ErrorInfo(
            "cost_limit", msg,
            "Cost limit exceeded. Simplify the expression.",
            False,
        )

    # Not callable
    if "callable" in msg.lower() or "not a function" in msg.lower():
        return ErrorInfo(
            "not_callable", msg,
            "The expression didn't evaluate to a function. Use (lambda (g) ...) to wrap it.",
            True,
        )

    # No rule set
    if "no rule" in msg.lower():
        return ErrorInfo(
            "no_rule", msg,
            "Set a rule first with (rule! (lambda (g) ...)).",
            True,
        )

    # Empty command
    if "empty" in msg.lower():
        return ErrorInfo("empty", msg, "Empty command.", False)

    return ErrorInfo("unknown", msg, f"Unknown error: {msg[:100]}", True)


# ============================================================
# Known symbols
# ============================================================

_KNOWN_SYMBOLS_CACHE: set[str] | None = None


def known_symbols() -> set[str]:
    """Return the set of all defined names available to rules.

    Includes both Python builtins AND Racket prelude symbols,
    since the swarm uses Racket mode.
    """
    global _KNOWN_SYMBOLS_CACHE
    if _KNOWN_SYMBOLS_CACHE is not None:
        return _KNOWN_SYMBOLS_CACHE

    # Python environment symbols
    env = make_global_env()
    symbols = set()
    current = env
    while current is not None:
        symbols.update(current.bindings.keys())
        current = current.parent

    # Add Racket prelude symbols (these exist in Racket mode but not Python)
    # Extracted from arc-prelude.rkt and standard Racket
    racket_extras = {
        # Math
        "quotient", "remainder", "modulo", "floor", "ceiling", "round",
        "abs", "max", "min", "add1", "sub1", "zero?", "positive?", "negative?",
        "even?", "odd?", "number?", "integer?", "exact?",
        # Lists
        "car", "cdr", "cadr", "caddr", "null?", "pair?", "list?",
        "member", "assoc", "remove", "take", "drop",
        "foldl", "foldr", "andmap", "ormap",
        "for/list", "for/sum", "for/and", "for/or", "for/first",
        "for/fold", "for/hash", "for*", "for*/list", "for*/sum",
        "in-range", "in-list", "in-naturals",
        # Hash
        "make-hash", "hash-ref", "hash-set!", "hash-set", "hash-has-key?",
        "hash-keys", "hash-values", "hash-count", "hash->list",
        "make-immutable-hash",
        # Mutation
        "set!", "begin", "void", "when", "unless",
        # Strings
        "string-append", "number->string", "string->number",
        "string-length", "substring", "format",
        # Boolean
        "boolean?", "not", "and", "or", "xor",
        # Grid extras from arc-prelude.rkt
        "safe-at", "in-bounds?", "bbox-of-cells", "paint-cells",
        "recolor-cells", "erase-cells", "positions-in-rect",
        "obj-r1", "obj-c1", "obj-r2", "obj-c2", "obj-h", "obj-w",
        "obj-rs", "obj-cs", "obj-center", "obj-neighbor-cells",
        "obj-boundary-cells", "obj-interior-cells",
        "grid-positions", "fold-cells", "for-each-cell",
        "mode-list", "normalize-cells", "cells-equal?",
        "rotate-cells-cw", "flip-cells-lr", "all-transforms",
        "match-transform", "convex-hull", "convex-hull-fill",
        "line-cells", "draw-line", "connected-region",
        "spiral-cells", "spiral-fill",
        "zip-grids", "grid-and", "grid-or", "grid-xor",
        "grid-diff", "grid-overlay-on",
        "hconcat", "vconcat", "stack-grids",
        "pad-grid", "pad-grid-asym",
        "row-uniform?", "col-uniform?", "row-count", "col-count",
        "unique-rows", "unique-cols",
        "top-half", "bottom-half", "left-half", "right-half",
        "cellwise", "power", "fork",
        "pick-max", "pick-min", "pick-unique",
        "smear-color", "move-to-wall",
        "slide-until-contact", "cup-opening",
        "occurrences", "center-of-mass", "gravitate",
        "obj-delta", "frontiers", "compress-grid",
        "square?", "vline?", "hline?", "bordering?",
        "hmatching?", "vmatching?", "filled?", "hollow?",
        "same-shape?", "above-of?", "below-of?", "left-of?", "right-of?",
        "detect-mirror-symmetry", "detect-rotational-symmetry",
        "detect-translational-period", "obj-contact", "objects-touching?",
    }
    symbols.update(racket_extras)

    _KNOWN_SYMBOLS_CACHE = symbols
    return symbols


def find_near_matches(name: str, max_results: int = 3) -> list[str]:
    """Find similar symbol names for typo suggestions."""
    symbols = known_symbols()

    # Check corrections table first
    if name in FUNCTION_CORRECTIONS:
        correct, _ = FUNCTION_CORRECTIONS[name]
        return [correct]

    # Simple edit-distance-1 matches
    matches = []
    name_lower = name.lower()
    for sym in symbols:
        sym_lower = sym.lower()
        if sym_lower == name_lower:
            matches.insert(0, sym)  # case mismatch
            continue
        # Dash vs underscore
        if sym_lower.replace("-", "_") == name_lower.replace("-", "_"):
            matches.append(sym)
            continue
        # One char different
        if len(sym) == len(name):
            diffs = sum(1 for a, b in zip(sym_lower, name_lower) if a != b)
            if diffs == 1:
                matches.append(sym)
        # One char added/removed
        if abs(len(sym) - len(name)) == 1:
            longer, shorter = (sym_lower, name_lower) if len(sym) > len(name) else (name_lower, sym_lower)
            for i in range(len(longer)):
                if longer[:i] + longer[i+1:] == shorter:
                    matches.append(sym)
                    break

    return matches[:max_results]


# ============================================================
# Syntax validation
# ============================================================

def validate_syntax(text: str) -> tuple[bool, str]:
    """Check S-expression syntax without executing.

    Returns (ok, error_message).
    """
    text = text.strip()
    if not text:
        return False, "Empty expression"

    # Check balanced parens
    depth = 0
    in_str = False
    for ch in text:
        if in_str:
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                return False, "Unbalanced parentheses: extra closing paren"
    if depth > 0:
        return False, f"Unbalanced parentheses: {depth} unclosed"
    if in_str:
        return False, "Unterminated string literal"

    # Must start with (rule!
    if not text.startswith("(rule!"):
        return False, "Must start with (rule! ...). Got: " + text[:30]

    # Try to parse
    try:
        parsed = parse(text)
    except Exception as e:
        return False, f"Parse error: {e}"

    if parsed is None:
        return False, "Parsed to None"

    return True, ""


def check_unknown_symbols(text: str) -> list[tuple[str, list[str]]]:
    """Find symbols in the expression that aren't known builtins.

    Returns list of (unknown_name, [suggestions]).
    Skips: variable names in lambda/let bindings, string literals, numbers.
    """
    syms = known_symbols()

    # Extract all symbol-like tokens (simplified — not a full parser)
    # Skip things inside quotes, skip numbers
    tokens = set()
    in_str = False
    current = ""
    for ch in text:
        if in_str:
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            current = ""
            continue
        if ch in '(){}[] \t\n\r':
            if current:
                tokens.add(current)
            current = ""
        else:
            current += ch
    if current:
        tokens.add(current)

    # Filter out numbers, booleans, known special forms
    special = {
        "rule!", "lambda", "let", "let*", "if", "cond", "else", "begin",
        "define", "and", "or", "not", "quote", "#t", "#f",
        "g", "r", "c", "v", "x", "y", "h", "w", "i", "j", "k", "n", "m",
        "obj", "acc", "pair", "cell", "row", "col", "grid", "color",
        "fn", "pred", "lst", "val", "result", "bg",
    }

    unknowns = []
    for tok in tokens:
        # Skip numbers
        if re.match(r'^-?\d+(\.\d+)?$', tok):
            continue
        # Skip artifact refs
        if re.match(r'^[@#_!~$*&]\d+$', tok):
            continue
        # Skip special forms and common variable names
        if tok in special:
            continue
        # Check if known
        if tok not in syms:
            suggestions = find_near_matches(tok)
            unknowns.append((tok, suggestions))

    return unknowns


# ============================================================
# Isolated rule testing
# ============================================================

def try_rule_isolated(task: dict, rule_text: str,
                      use_racket: bool = True) -> RuleResult:
    """Evaluate in a fresh executor; a requested Racket backend never falls back.

    Explicit ``use_racket=False`` remains available for Python-only controls.
    For bounded concurrent synthesis/repair use isolated_verifier.verify_candidate.
    """
    result = RuleResult(rule_text=rule_text, total=len(task["train"]),
                        requested_backend="racket" if use_racket else "python")
    if use_racket and os.getenv("ARC_FORCE_PYTHON_EVAL"):
        result.set_error = "ARC_FORCE_PYTHON_EVAL conflicts with use_racket=True; request Python explicitly"
        result.set_error_class = "backend_conflict"
        return result
    try:
        executor = ArcExecutor(task, auto_scan_on_load=False, use_racket=use_racket)
    except Exception as exc:
        result.set_error = str(exc)
        result.set_error_class = "executor_init"
        return result
    result.backend = "racket" if use_racket else "python"
    try:
        return _test_loaded_executor(executor, task, rule_text, result)
    finally:
        executor.close()


def _test_loaded_executor(executor, task: dict, rule_text: str, result: RuleResult) -> RuleResult:
    # Set the rule
    obs = executor.step(rule_text)
    if obs.startswith("ERROR"):
        info = classify_error(obs)
        result.set_error = obs
        result.set_error_class = info.rule
        return result

    # Test each training pair
    for i in range(len(task["train"])):
        obs = executor.step(f"(test! {i})")
        passed = "PASS" in obs and "FAIL" not in obs

        pr = PairResult(pair_idx=i, passed=passed, detail=obs)

        if not passed:
            if "rule error" in obs:
                # Extract error from "rule error: <msg>"
                err_match = re.search(r'rule error:\s*(.*)', obs)
                err_msg = err_match.group(1) if err_match else obs
                info = classify_error(f"ERROR: {err_msg}")
                pr.error = err_msg
                pr.error_class = info.rule
                pr.diff_cells = 9999
            elif "shape" in obs.lower() and "vs" in obs:
                # Shape mismatch
                pr.shape_match = False
                pr.diff_cells = 9999
                m = re.search(r'\[(\d+), (\d+)\] vs \[(\d+), (\d+)\]', obs)
                if m:
                    pr.got_shape = (int(m.group(1)), int(m.group(2)))
                    pr.expected_shape = (int(m.group(3)), int(m.group(4)))
            else:
                # Wrong values — extract diff count
                m = re.search(r'(\d+)/(\d+) differ', obs)
                if m:
                    pr.diff_cells = int(m.group(1))
                    pr.total_cells = int(m.group(2))
        else:
            pair = task["train"][i]
            out = pair["output"]
            pr.total_cells = len(out) * len(out[0])

        result.pairs.append(pr)
        if passed:
            result.pass_count += 1

    result.all_pass = (result.total > 0 and result.pass_count == result.total)

    # Compute diff score
    if result.all_pass:
        result.diff_score = 0.0
    else:
        total_diff = sum(p.diff_cells for p in result.pairs if not p.passed)
        pair_penalty = (result.total - result.pass_count) * 1000
        result.diff_score = total_diff + pair_penalty

    # Generate test outputs if all training pairs pass
    if result.all_pass:
        test_outputs = []
        for i in range(len(task.get("test", []))):
            obs = executor.step(f"(apply! {i})")
            if obs.startswith("ERROR"):
                test_outputs = None
                break
            # Find result ref and extract grid
            for token in obs.split():
                if token.startswith("_") and token[1:].isdigit():
                    if token in executor._results:
                        test_outputs.append(_unwrap(executor._results[token]))
                    break
            else:
                test_outputs = None
                break
        result.test_outputs = test_outputs

    return result
