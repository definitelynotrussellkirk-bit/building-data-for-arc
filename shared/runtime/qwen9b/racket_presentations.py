"""Seeded presentation variants for one selected Racket authority.

The canonical program remains the semantic authority.  This module only adds
conservative comments and mechanically equivalent surface forms so repeated
generator seeds do not teach one exact spelling of the rule.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from scripts.comment_solutions import (
    Atom,
    List_,
    comment_solution,
    parens_balanced,
    parse_racket,
)


@dataclass(frozen=True)
class RacketPresentation:
    """One training presentation derived from a selected authority."""

    program: str
    variant_id: str
    authority_hash: str
    comments_added: int


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for index, char in enumerate(source):
        if char == "\n":
            offsets.append(index + 1)
    return offsets


def _node_span(node: Atom | List_, offsets: list[int]) -> tuple[int, int]:
    start = offsets[node.line] + node.col
    if isinstance(node, Atom):
        return start, start + len(node.text)
    return start, offsets[node.close_line] + node.close_col + 1


def _replace_span(source: str, span: tuple[int, int], replacement: str) -> str:
    start, end = span
    return source[:start] + replacement + source[end:]


def _rule_form(source: str) -> List_ | None:
    """Return the sole top-level ``rule!`` form, if it is unambiguous."""
    if not parens_balanced(source):
        return None
    try:
        nodes = parse_racket(source)
    except Exception:
        return None
    forms = [
        node for node in nodes
        if isinstance(node, List_) and node.head() == "rule!" and len(node.items) == 2
    ]
    return forms[0] if len(forms) == 1 else None


def _surface_variant(source: str, requested: int) -> tuple[str, str]:
    """Apply a parser-located, semantics-preserving Racket surface variant."""
    form = _rule_form(source)
    if form is None:
        return source, "comments_only"
    argument = form.items[1]
    offsets = _line_offsets(source)
    head = argument.head() if isinstance(argument, List_) else None

    # Body-form rules are evaluated in the auto-bound g/h/w scope.  Each of
    # these one-expression wrappers returns exactly the wrapped body value.
    if head not in {"lambda", "λ", "pipe", "compose", "fork", "power"} \
            and not isinstance(argument, Atom):
        wrappers = (
            ("body_begin", "(begin {body})"),
            ("body_let", "(let () {body})"),
            ("body_let_star", "(let* () {body})"),
            ("body_begin0", "(begin0 {body})"),
        )
        name, template = wrappers[requested % len(wrappers)]
        span = _node_span(argument, offsets)
        body = source[span[0]:span[1]]
        return _replace_span(source, span, template.format(body=body)), name

    # For legacy lambdas, vary the lambda spelling or introduce a local scope
    # around its body.  Both forms preserve lexical binding and return value.
    if isinstance(argument, List_) and head in {"lambda", "λ"} \
            and len(argument.items) >= 3:
        if requested % 3 == 0:
            head_atom = argument.items[0]
            assert isinstance(head_atom, Atom)
            replacement = "λ" if head_atom.text == "lambda" else "lambda"
            return _replace_span(source, _node_span(head_atom, offsets), replacement), \
                "lambda_alias"
        body_start = _node_span(argument.items[2], offsets)[0]
        body_end = _node_span(argument.items[-1], offsets)[1]
        body = source[body_start:body_end]
        wrapper = "(begin {body})" if requested % 3 == 1 else "(let () {body})"
        name = "lambda_body_begin" if requested % 3 == 1 else "lambda_body_let"
        return _replace_span(source, (body_start, body_end), wrapper.format(body=body)), name

    return source, "comments_only"


def present_racket_program(
    authority_program: str,
    *,
    task_id: str,
    seed: object,
    sample_index: object,
    description: str = "",
) -> RacketPresentation:
    """Create a deterministic training spelling of ``authority_program``.

    The seed selects only a presentation form.  It never selects between
    historical rules and never changes literals, control flow, or behavior.
    """
    authority_hash = hashlib.sha256(authority_program.encode()).hexdigest()
    commented, inserts = comment_solution(authority_program, description)
    selector = hashlib.sha256(
        f"{task_id}\0{seed!r}\0{sample_index!r}".encode()
    ).digest()[0]
    program, variant_id = _surface_variant(commented, selector)
    return RacketPresentation(
        program=program,
        variant_id=variant_id,
        authority_hash=authority_hash,
        comments_added=len(inserts),
    )
