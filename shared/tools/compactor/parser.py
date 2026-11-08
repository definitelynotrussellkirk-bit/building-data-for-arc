"""Minimal s-expression parser tuned for our Racket rule corpus.

Parses to immutable nested tuples of:
- `Sym(str)` — symbol (subclass of str so equality works against literals)
- `int` / `float` — numbers
- `str` — string literals (kept double-quoted)
- `tuple(...)` — list (paren or bracket form)

Round-trips: parse → emit → parse yields the same AST (modulo bracket choice).

Design choice: tuples (not dataclasses) so passes can pattern-match with
`==` and use them as dict keys. Position info is dropped — this module
is for transformation, not source-faithful editing.
"""
from __future__ import annotations

import re
from typing import Iterable


class Sym(str):
    """Symbol type. Subclass of str so `(node[0] == 'lambda')` works."""

    __slots__ = ()

    def __repr__(self) -> str:
        return f"Sym({str(self)!r})"


# Tokens we care about: parens, brackets, dict braces, strings, atoms.
_TOK_RE = re.compile(
    r'\(|\)|\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s()\[\]{};]+'
)


def strip_comments(src: str) -> str:
    """Strip Racket `;` line comments. Conservative — does not touch strings."""
    out_lines = []
    for line in src.split("\n"):
        # find first ';' not inside a string literal
        in_str = False
        i = 0
        while i < len(line):
            c = line[i]
            if c == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
            if c == ";" and not in_str:
                break
            i += 1
        out_lines.append(line[:i].rstrip())
    return "\n".join(out_lines)


def tokenize(src: str) -> list[str]:
    """Tokens: parens/brackets/braces, string literals, atoms."""
    return _TOK_RE.findall(strip_comments(src))


def parse(src: str):
    """Parse a complete top-level s-expression. Returns a single AST node.

    If the source has multiple top-level forms, returns a tuple beginning
    with `Sym('begin')` wrapping them.
    """
    toks = tokenize(src)
    nodes, end = _parse_seq(toks, 0, None)
    if end != len(toks):
        raise ValueError(f"trailing tokens at pos {end}: {toks[end:end+5]}")
    if len(nodes) == 1:
        return nodes[0]
    return (Sym("begin"), *nodes)


def parse_all(src: str):
    """Parse and return a list of top-level forms (no auto-wrap)."""
    toks = tokenize(src)
    nodes, end = _parse_seq(toks, 0, None)
    if end != len(toks):
        raise ValueError(f"trailing tokens at pos {end}")
    return nodes


_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}


def _parse_seq(toks: list[str], pos: int, expected_close: str | None):
    """Parse a sequence of forms until expected_close (or end)."""
    out = []
    while pos < len(toks):
        t = toks[pos]
        if t == expected_close:
            return out, pos + 1
        if t in (")", "]", "}"):
            raise ValueError(f"unexpected {t} at pos {pos}")
        if t in ("(", "[", "{"):
            close = _OPEN_TO_CLOSE[t]
            inner, pos = _parse_seq(toks, pos + 1, close)
            if t == "{":
                # Brace dict literal: keep as a tagged structure for downstream
                # passes to recognize. (make-immutable-hash (list (cons K V) ...))
                # We don't pre-expand here; the runner does that for execution.
                out.append((Sym("__dict__"), *inner))
            else:
                out.append(tuple(inner))
        elif t.startswith('"') and t.endswith('"'):
            out.append(t)  # keep quoted form
            pos += 1
        else:
            out.append(_atom(t))
            pos += 1
    if expected_close is not None:
        raise ValueError(f"missing {expected_close}")
    return out, pos


def _atom(s: str):
    # int
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    # float
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    # boolean
    if s == "#t":
        return True
    if s == "#f":
        return False
    # symbol
    return Sym(s)


def emit(node) -> str:
    """Emit an AST as Racket source (single line)."""
    if isinstance(node, tuple):
        if node and node[0] == Sym("__dict__"):
            return "{" + " ".join(emit(c) for c in node[1:]) + "}"
        return "(" + " ".join(emit(c) for c in node) + ")"
    if isinstance(node, bool):
        return "#t" if node else "#f"
    if isinstance(node, str) and not isinstance(node, Sym):
        return node  # string literal already quoted
    return str(node)


def emit_pretty(node, indent: int = 0) -> str:
    """Emit with newlines for top-level let/cond/lambda bodies. Useful for
    storing compacted rules in a human-readable form."""
    s = emit(node)
    return s  # simple emitter — pretty-printing not required for our metrics
