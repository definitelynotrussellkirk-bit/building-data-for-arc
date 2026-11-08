"""Rule-source normalization pipeline.

Takes a `(rule! ...)` source string and returns a Racket lambda
string the bare RacketBridge can evaluate. The pipeline:

  1. strip_line_comments    — drop `;` line comments (the bridge
                              flattens newlines, so a surviving `;`
                              would eat the rest of the rule).
  2. convert_dict_literals  — `{K V K V}` →
                              `(make-immutable-hash (list (cons K V) ...))`.
  3. convert_for_shorthand  — `(for/X (var seq) body)` →
                              `(for/X ((var (in-list seq))) body)`.
  4. strip_rule_wrapper     — peel `(rule! BODY)` → BODY.
  5. wrap_rule              — if BODY is a lambda/λ form, wrap it in an
                              enclosing auto-bind preamble and apply it to g,
                              so free h/w references keep the REPL convention.
                              If BODY is another callable form (pipe / compose /
                              fork / power) or a bare symbol, return BODY
                              unchanged. Otherwise wrap with the REPL's
                              auto-bind preamble: `(lambda (g) (let* ((h (rows g))
                                          (w (cols g))) BODY))`.

Owners: puzzle_generators.runner uses this to feed RacketBridge.
The compactor verifier and any ad-hoc REPL/script tooling that wants
to evaluate `(rule! ...)` text against a bare bridge should import
from here too — they MUST NOT duplicate the pipeline.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from typing import Optional


# Heads whose value is already a callable (grid → grid). When the rule
# body has one of these as its outermost form, we don't wrap it in a
# `(lambda (g) (let* ...))` preamble. Mirrors
# arc_repl.executor._RULE_CALLABLE_HEADS.
RULE_CALLABLE_HEADS = {
    "lambda", "λ",
    "pipe", "compose", "fork", "power",
}


def strip_rule_wrapper(src: str) -> str:
    """Take '(rule! BODY)' source and return BODY as a substring of src."""
    s = src.lstrip()
    if not s.startswith("(rule!"):
        raise ValueError(f"expected '(rule! ...)' source, got: {s[:60]!r}")
    i = len("(rule!")
    while i < len(s) and s[i] in " \t\n":
        i += 1
    body_start = i
    depth = 1
    in_str = False
    while i < len(s) and depth > 0:
        c = s[i]
        if in_str:
            if c == "\\" and i + 1 < len(s):
                i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == ";":
            while i < len(s) and s[i] != "\n":
                i += 1
            continue
        if c == '"':
            in_str = True; i += 1; continue
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
            if depth == 0:
                return s[body_start:i].strip()
        i += 1
    raise ValueError("malformed (rule! ...) — unbalanced parens")


def _body_head(body: str) -> Optional[str]:
    """The first symbol after '(' in the body, e.g., 'lambda' for
    '(lambda (g) ...)'. None if body doesn't start with '('."""
    s = body.lstrip()
    if not s.startswith("("):
        return None
    j = 1
    while j < len(s) and s[j] in " \t\n":
        j += 1
    k = j
    while k < len(s) and s[k] not in " \t\n()[];":
        k += 1
    return s[j:k] if k > j else None


def strip_line_comments(src: str) -> str:
    """Drop `;` line comments. The bridge flattens newlines to spaces
    when sending to Racket; a surviving `;` would comment out the rest
    of the rule. Strings are respected — `;` inside `"..."` is preserved."""
    out = []
    i = 0
    in_str = False
    while i < len(src):
        c = src[i]
        if in_str:
            if c == "\\" and i + 1 < len(src):
                out.append(c); out.append(src[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            out.append(c); i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if c == ";":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        out.append(c); i += 1
    return "".join(out)


_DICT_RE = re.compile(r"\{([^{}]*)\}")


# `(for/<form> (var seq) body)` shorthand → racket-correct full form.
# The executor's `_expr_to_text` rewrites these; the bare bridge doesn't.
_FOR_FORMS = {
    "for/or", "for/and", "for/first", "for/sum", "for/list",
    "for/fold", "for/last", "for/product",
}


@lru_cache(maxsize=1)
def _comment_parser():
    """Load the parser from this checkout or this staged runtime only.

    Source packets retain it under shared/tools; execution snapshots map the
    same file to scripts/. Neither layout needs a global scripts namespace.
    """
    runtime = Path(__file__).resolve().parent.parent
    source_layout = runtime.name == "runtime" and runtime.parent.name == "shared"
    home = runtime.parent if source_layout else runtime
    path = home / ("tools/comment_solutions.py" if source_layout else "scripts/comment_solutions.py")
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(home):
        raise ImportError(f"Rule parser missing from current source/runtime layout: {path}")
    name = "_arcpuzzles_rule_wrap_parser_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load current rule parser: {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotated field types through the module registry.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


def convert_for_shorthand(src: str) -> str:
    """Rewrite `(for/X (var seq) body)` to `(for/X ([var (in-list seq)]) body)`.

    Mirrors what arc_repl.executor._expr_to_text does for these forms.
    Walks the parsed AST so nested forms inside the body get rewritten too."""
    parser = _comment_parser()
    parse_racket, Atom, List_ = parser.parse_racket, parser.Atom, parser.List_

    try:
        nodes = parse_racket(src)
    except Exception:
        return src   # fall back to original

    edits: list[tuple[int, int, int, str]] = []  # (line, col, length, replacement)

    def _rewrite(n):
        if not isinstance(n, List_):
            return
        head = n.head()
        if head in _FOR_FORMS and len(n.items) >= 3:
            bind_node = n.items[1]
            # Shorthand: bindings node is `(var seq)` — exactly 2 items, first is Atom.
            if (isinstance(bind_node, List_)
                    and len(bind_node.items) == 2
                    and isinstance(bind_node.items[0], Atom)):
                var = bind_node.items[0]
                seq = bind_node.items[1]
                # Replace the bind_node's source span with `([var (in-list seq)])`
                start_line, start_col = bind_node.line, bind_node.col
                end_line, end_col = bind_node.close_line, bind_node.close_col
                seq_text = _node_text(src, seq)
                replacement = f"([{var.text} (in-list {seq_text})])"
                edits.append((
                    start_line, start_col,
                    _span_length(src, start_line, start_col, end_line, end_col + 1),
                    replacement,
                ))
        for child in n.items:
            _rewrite(child)

    for n in nodes:
        _rewrite(n)
    if not edits:
        return src

    # Apply edits right-to-left so earlier positions stay valid.
    return _apply_edits(src, edits)


def _node_text(src: str, node) -> str:
    """Pull a node's exact source span back out of `src`."""
    parser = _comment_parser()
    Atom, List_ = parser.Atom, parser.List_
    if isinstance(node, Atom):
        return _slice_lines(src, node.line, node.col, node.line, node.col + len(node.text))
    if isinstance(node, List_):
        return _slice_lines(src, node.line, node.col, node.close_line, node.close_col + 1)
    return ""


def _slice_lines(src: str, l1: int, c1: int, l2: int, c2: int) -> str:
    lines = src.split("\n")
    if l1 == l2:
        return lines[l1][c1:c2]
    parts = [lines[l1][c1:]]
    for i in range(l1 + 1, l2):
        parts.append(lines[i])
    parts.append(lines[l2][:c2])
    return "\n".join(parts)


def _span_length(src: str, l1: int, c1: int, l2: int, c2: int) -> int:
    return len(_slice_lines(src, l1, c1, l2, c2))


def _apply_edits(src: str, edits: list[tuple[int, int, int, str]]) -> str:
    """Apply (line, col, length, replacement) edits to source.
    Edits are processed in reverse source order to keep offsets valid."""
    edits = sorted(edits, key=lambda e: (-e[0], -e[1]))
    lines = src.split("\n")
    for line, col, length, rep in edits:
        # Replace `length` characters starting at (line, col) with `rep`.
        # If length spans multiple lines, splice across lines.
        l = line
        cur_row = lines[l]
        if col + length <= len(cur_row):
            lines[l] = cur_row[:col] + rep + cur_row[col + length:]
            continue
        # Multi-line span
        head = cur_row[:col]
        consumed = len(cur_row) - col + 1  # +1 for the newline
        l_end = l
        while consumed < length and l_end + 1 < len(lines):
            l_end += 1
            consumed += len(lines[l_end]) + 1
        overshoot = consumed - length
        tail = lines[l_end][len(lines[l_end]) - overshoot + 1:] if overshoot > 0 else ""
        new_line = head + rep + tail
        lines = lines[:l] + [new_line] + lines[l_end + 1:]
    return "\n".join(lines)


def convert_dict_literals(src: str) -> str:
    """Rewrite `{K V K V ...}` to `(make-immutable-hash (list (cons K V) ...))`.

    The executor's `_expr_to_text` does this conversion when generating
    Racket text from its parsed AST. We replicate it via regex on
    source so the bare bridge can evaluate solutions verbatim."""
    def repl(m):
        items = m.group(1).split()
        if not items or len(items) % 2 != 0:
            return m.group(0)  # malformed — leave alone
        pairs = " ".join(
            f"(cons {items[i]} {items[i + 1]})"
            for i in range(0, len(items), 2)
        )
        return f"(make-immutable-hash (list {pairs}))"
    return _DICT_RE.sub(repl, src)


def wrap_rule(rule_source: str) -> str:
    """Produce a Racket lambda string that maps an input grid to the
    rule's output grid.

    For body-form rules (e.g., `(rule! (recolor g 5 0))`), wraps with
    the auto-bind preamble that the REPL's `rule!` macro provides.
    For lambda/λ rules, wraps the lambda in an enclosing preamble and
    applies it to `g`, so free `h`/`w` references resolve while the lambda's
    own parameter binding remains unchanged. For other callable-form rules
    (e.g., `(rule! flip-lr)`), passes the body through unchanged.

    Always strips line comments, converts dict literals, and rewrites
    `(for/X (var seq) body)` shorthand so the output is bare-bridge-safe."""
    src = convert_for_shorthand(
        convert_dict_literals(strip_line_comments(rule_source)))
    body = strip_rule_wrapper(src)
    head = _body_head(body)
    if head in ("lambda", "λ"):
        # LAMBDA form used to pass through with NO auto-bind preamble, so a lambda body that referenced
        # h/w (the g/h/w convention) hit "h: undefined" and every generated pair was rejected (killed
        # ~15 generators). Bind h/w in an ENCLOSING scope and apply the lambda to g: its body sees h/w
        # as free vars (= rows/cols of g) and its own arg = g. Safe for lambdas that don't use h/w
        # (bound-but-unused) or define their own (inner let shadows).
        return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) ({body} g)))"
    if head is None or head in RULE_CALLABLE_HEADS:
        return body
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"
