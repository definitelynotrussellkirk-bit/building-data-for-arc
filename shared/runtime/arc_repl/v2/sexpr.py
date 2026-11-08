"""Small source-located S-expression reader for ARC-Racket v2.

The legacy REPL reader intentionally accepts several convenience syntaxes and
returns location-free Python values.  The v2 compiler needs the opposite
trade-off: one canonical surface and errors that identify the exact source
location.  This reader therefore accepts only round-parenthesized forms,
scalars, strings (for legacy migration), booleans, and symbols.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterator, Literal


@dataclass(frozen=True, slots=True)
class Span:
    """Half-open source span."""

    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int

    @classmethod
    def synthetic(cls) -> "Span":
        return cls(0, 0, 1, 1, 1, 1)


NodeKind = Literal["list", "symbol", "string", "integer", "float", "boolean"]


@dataclass(frozen=True, slots=True)
class Node:
    kind: NodeKind
    value: object
    span: Span

    @property
    def items(self) -> tuple["Node", ...]:
        if self.kind != "list":
            raise TypeError(f"{self.kind} node has no items")
        return self.value  # type: ignore[return-value]

    @property
    def text(self) -> str:
        if self.kind not in {"symbol", "string"}:
            raise TypeError(f"{self.kind} node has no text")
        return self.value  # type: ignore[return-value]


class SExprSyntaxError(ValueError):
    """Syntax error with a stable machine-readable code and source point."""

    def __init__(self, code: str, message: str, *, line: int, column: int,
                 phase: str = "syntax", path: str = "$", span: Span | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        self.phase = phase
        self.path = path
        self.span = span or Span(0, 0, line, column, line, column)

    def __str__(self) -> str:
        return f"{self.phase}:{self.code} at {self.line}:{self.column}: {self.message}"


@dataclass(frozen=True, slots=True)
class _Token:
    kind: Literal["lparen", "rparen", "atom", "string"]
    text: str
    span: Span


_INT_RE = re.compile(r"[+-]?[0-9]+\Z")
_FLOAT_RE = re.compile(r"[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?\Z")


def _advance(text: str, line: int, column: int) -> tuple[int, int]:
    for char in text:
        if char == "\n":
            line += 1
            column = 1
        else:
            column += 1
    return line, column


def _span(start: int, end: int, line: int, column: int, token_text: str) -> Span:
    end_line, end_column = _advance(token_text, line, column)
    return Span(start, end, line, column, end_line, end_column)


def tokenize(source: str) -> Iterator[_Token]:
    """Yield located tokens.

    A semicolon starts a line comment, matching Racket rather than the legacy
    reader's older ``;;``-only behavior.  Square/curly delimiters are rejected
    loudly because mixed bracket styles are outside the v2 canonical surface.
    """

    i = 0
    line = 1
    column = 1
    n = len(source)
    while i < n:
        char = source[i]
        if char.isspace():
            line, column = _advance(char, line, column)
            i += 1
            continue
        if char == ";":
            start = i
            while i < n and source[i] != "\n":
                i += 1
            line, column = _advance(source[start:i], line, column)
            continue
        if char in "[]{}":
            raise SExprSyntaxError(
                "E_NONCANONICAL_DELIMITER",
                "ARC-Racket v2 uses round parentheses only",
                line=line,
                column=column,
            )
        if char == "'":
            raise SExprSyntaxError(
                "E_QUOTE_SHORTHAND",
                "quote shorthand is outside the v2 core; use a typed constant",
                line=line,
                column=column,
            )
        if char == "(":
            span = _span(i, i + 1, line, column, char)
            yield _Token("lparen", char, span)
            i += 1
            column += 1
            continue
        if char == ")":
            span = _span(i, i + 1, line, column, char)
            yield _Token("rparen", char, span)
            i += 1
            column += 1
            continue
        if char == '"':
            start = i
            start_line, start_column = line, column
            i += 1
            column += 1
            chars: list[str] = []
            closed = False
            while i < n:
                char = source[i]
                if char == '"':
                    i += 1
                    column += 1
                    closed = True
                    break
                if char == "\\":
                    if i + 1 >= n:
                        break
                    escaped = source[i + 1]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                    i += 2
                    column += 2
                    continue
                chars.append(char)
                line, column = _advance(char, line, column)
                i += 1
            if not closed:
                raise SExprSyntaxError(
                    "E_UNTERMINATED_STRING",
                    "unterminated string literal",
                    line=start_line,
                    column=start_column,
                )
            raw = source[start:i]
            yield _Token(
                "string",
                "".join(chars),
                _span(start, i, start_line, start_column, raw),
            )
            continue

        start = i
        start_line, start_column = line, column
        while i < n and not source[i].isspace() and source[i] not in "();[]{}'\"":
            i += 1
        if i == start:
            raise SExprSyntaxError(
                "E_BAD_CHARACTER",
                f"unexpected character {source[i]!r}",
                line=line,
                column=column,
            )
        raw = source[start:i]
        line, column = _advance(raw, line, column)
        yield _Token("atom", raw, _span(start, i, start_line, start_column, raw))


def parse(
    source: str, *, max_nodes: int = 100_000, max_depth: int = 128,
    max_source_chars: int = 1_048_576, max_integer_abs: int | None = None,
) -> Node:
    """Read one expression without recursive descent or an unbounded token list.

    Limits are charged while reading, before Python integer conversion or AST
    construction. Defaults also bound trusted offline migration/runtime reads;
    the model-facing compiler supplies its stricter release limits.
    """
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    if len(source) > max_source_chars:
        raise SExprSyntaxError("E_SOURCE_LIMIT", "source exceeds character budget",
                               line=1, column=1, phase="cost")
    # Each frame is [opening token, child nodes, AST path]. Closing a list does
    # not charge a second node; the opening delimiter already paid for it.
    stack: list[tuple[_Token, list[Node], str]] = []
    root: Node | None = None
    count = 0

    def fail(code: str, message: str, token: _Token, path: str,
             phase: str = "syntax") -> None:
        raise SExprSyntaxError(code, message, line=token.span.line,
                               column=token.span.column, phase=phase,
                               path=path, span=token.span)

    def append(node: Node) -> None:
        nonlocal root
        if stack:
            stack[-1][1].append(node)
        else:
            root = node

    for token in tokenize(source):
        path = stack[-1][2] + f"[{len(stack[-1][1])}]" if stack else "$"
        if token.kind == "rparen":
            if not stack:
                fail("E_UNEXPECTED_CLOSE", "unexpected ')'", token, path)
            opening, items, list_path = stack.pop()
            append(Node("list", tuple(items), Span(
                opening.span.start, token.span.end, opening.span.line,
                opening.span.column, token.span.end_line, token.span.end_column)))
            continue
        if root is not None and not stack:
            fail("E_TRAILING_FORM", "canonical source contains exactly one top-level expression", token, path)
        count += 1
        if count > max_nodes:
            fail("E_NODE_LIMIT", f"AST exceeds {max_nodes} nodes", token, path, "cost")
        if len(stack) + 1 > max_depth:
            fail("E_DEPTH_LIMIT", f"AST depth exceeds {max_depth}", token, path, "cost")
        if token.kind == "lparen":
            stack.append((token, [], path))
            continue
        if token.kind == "string":
            node = Node("string", token.text, token.span)
        elif token.text in {"#t", "#f"}:
            node = Node("boolean", token.text == "#t", token.span)
        elif _INT_RE.fullmatch(token.text):
            # Strip zeros before conversion, then compare decimal magnitudes
            # lexically. Never disable Python's global integer safety limit.
            magnitude = token.text.lstrip("+-").lstrip("0") or "0"
            bound = str(max_integer_abs) if max_integer_abs is not None else "9" * 1024
            if len(magnitude) > len(bound) or (len(magnitude) == len(bound) and magnitude > bound):
                fail("E_INTEGER_BOUND", "integer literal exceeds the reader budget", token, path, "cost")
            value = int(magnitude) * (-1 if token.text.startswith("-") else 1)
            node = Node("integer", value, token.span)
        elif _FLOAT_RE.fullmatch(token.text):
            node = Node("float", float(token.text), token.span)
        else:
            node = Node("symbol", token.text, token.span)
        append(node)
    if stack:
        opening, _, path = stack[-1]
        fail("E_MISSING_CLOSE", "missing ')' for this list", opening, path)
    if root is None:
        raise SExprSyntaxError("E_EMPTY_SOURCE", "expected one expression", line=1, column=1)
    return root


def symbol(name: str, span: Span | None = None) -> Node:
    return Node("symbol", name, span or Span.synthetic())


def integer(value: int, span: Span | None = None) -> Node:
    return Node("integer", int(value), span or Span.synthetic())


def string(value: str, span: Span | None = None) -> Node:
    return Node("string", value, span or Span.synthetic())


def list_node(*items: Node, span: Span | None = None) -> Node:
    return Node("list", tuple(items), span or Span.synthetic())


def format_node(node: Node) -> str:
    """Deterministic one-line formatter used by canonical v2 source."""

    if node.kind == "list":
        return "(" + " ".join(format_node(item) for item in node.items) + ")"
    if node.kind == "symbol":
        return node.text
    if node.kind == "string":
        escaped = node.text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        return f'"{escaped}"'
    if node.kind == "boolean":
        return "#t" if node.value else "#f"
    if node.kind == "integer":
        return str(node.value)
    if node.kind == "float":
        return repr(node.value)
    raise AssertionError(f"unknown node kind: {node.kind}")
