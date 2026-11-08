#!/usr/bin/env python3
"""
Canonicalize a Racket rule by abstracting color literals into slots.

Two rules that implement the same algorithm modulo color choices hash
to the same `concept_hash`. Use this to cluster puzzles by concept and
to enable variant generation by re-instantiating the slot template
with different colors.

Phase 1 of the puzzle-generator roadmap (docs/PUZZLE_GENERATOR_ROADMAP.md):
  - Walk the AST.
  - Identify positions where 0-9 atoms are *colors* (not arithmetic).
  - Replace each unique color value with $c0, $c1, ... in
    first-appearance source order.
  - Hash the canonicalized text.

Returned dict:
    {
      "concept_hash": "<sha256[:12] of canonical text>",
      "template":     "<rule with $c0, $c1, ... slots>",
      "color_slots":  [original_value_for_$c0, original_value_for_$c1, ...],
      "size_slots":   []  # reserved for Phase 7
    }

Color positions detected:
  - Direct args of known color-arg functions (find-color, recolor,
    swap-colors, remove-color, count-color, set-cell, empty-grid,
    paint-cells, recolor-cells, erase-cells, color-filter,
    not-color-filter, const-target, keep-only, fill-region, fill-bbox).
  - Equality literals against color-valued expressions:
    `(= EXPR LIT)` or `(= LIT EXPR)` where EXPR is or resolves to a
    cell-at / at / mode / minority / obj-color call.
  - Digit tokens inside {...} dict literals (recolor-map sugar).

Size literals (e.g., the 4 in `(>= (obj-size o) 4)`) are NOT slotted
in this phase — Phase 7 refinement.

Usage:
    from scripts.canonicalize_rule import canonicalize_rule
    info = canonicalize_rule(racket_source)
    print(info["concept_hash"], info["color_slots"])
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Reuse the sexpr parser from the commenter — same project, same primitives.
from scripts.comment_solutions import (  # noqa: E402
    parse_racket, extract_bindings, parens_balanced,
    Atom, List_, resolve, atom_text, _flatten_text,
)


# ---------------------------------------------------------------------------
# Color-position catalog
# ---------------------------------------------------------------------------

# head -> set of arg positions (1-indexed within node.items, since items[0] is the head)
# whose values are color literals when atomic.
COLOR_ARG_POSITIONS: dict[str, set[int]] = {
    "find-color":       {2},
    "recolor":          {2, 3},
    "swap-colors":      {2, 3},
    "remove-color":     {2},
    "count-color":      {2},
    "keep-only":        {2},
    "set-cell":         {4},
    "empty-grid":       {3},
    "paint-cells":      {3},     # scalar form (paint-cells g cells COLOR)
    "recolor-cells":    {3},
    "erase-cells":      {2, 3},  # (erase-cells g [bg]) — bg may be passed
    "color-filter":     {1},
    "not-color-filter": {1},
    "const-target":     {1},
    "fill-region":      {4},
    "fill-bbox":        {4},
    "fill-row":         {4},
    "fill-col":         {4},
    "fill-border":      {2},
    "draw-line":        {6},     # (draw-line g r1 c1 r2 c2 COLOR)
    "draw-rect":        {6},
    "draw-cross":       {4},
    "objects":          {2},     # (objects g BG) — bg color
    "objects-8":        {2},
    "objects-multicolor":{2},
    "mode":             {2},     # (mode g BG) — bg
    "minority":         {2},
    "smear-color":      {2},     # (smear-color g COLOR ...)
    "slide-color":      {2},
    "gravity":          {3},     # (gravity g dir BG)
    "fill-all-enclosed":{2, 3},
    "convex-hull-fill": {3},     # (convex-hull-fill g points COLOR)
    "spiral-fill":      {2},     # (spiral-fill g colors ...) — first arg if scalar
}

# Heads whose RETURN value is a single color (used to detect (= EXPR LIT) where LIT is a color).
COLOR_VALUED_HEADS: set[str] = {
    "cell-at", "at", "safe-at", "cell", "mode", "minority", "obj-color",
}


# ---------------------------------------------------------------------------
# Walk: collect color-literal Atoms with their source positions
# ---------------------------------------------------------------------------

def _collect_color_atoms(
    node: object,
    hits: list[tuple[Atom, int]],
    symbols: dict[str, object],
) -> None:
    """Recursively walk `node`, append every (Atom, color_value) we find
    in a known color position. Atoms are NOT mutated; we record references
    so the rewrite step can locate them by source position later."""
    if isinstance(node, list):
        for x in node:
            _collect_color_atoms(x, hits, symbols)
        return
    if not isinstance(node, List_):
        return

    head = node.head()

    # 1. Direct color-arg positions
    if head in COLOR_ARG_POSITIONS:
        for idx in COLOR_ARG_POSITIONS[head]:
            if idx < len(node.items):
                child = node.items[idx]
                if isinstance(child, Atom):
                    v = _try_color(child)
                    if v is not None:
                        hits.append((child, v))

    # 2. Comparison: (= EXPR LIT) or (= LIT EXPR) where EXPR is color-valued
    if head in {"=", "eq?", "equal?"} and len(node.items) == 3:
        a, b = node.items[1], node.items[2]
        for lit_node, expr_node in [(a, b), (b, a)]:
            if not isinstance(lit_node, Atom):
                continue
            v = _try_color(lit_node)
            if v is None:
                continue
            resolved = resolve(expr_node, _SymCtx(symbols)) if isinstance(expr_node, Atom) \
                       else expr_node
            if isinstance(resolved, List_) and resolved.head() in COLOR_VALUED_HEADS:
                hits.append((lit_node, v))

    # 3. Recurse
    for x in node.items:
        _collect_color_atoms(x, hits, symbols)


def _try_color(atom: Atom) -> Optional[int]:
    """If atom.text is a single digit 0..9, return the int. Else None.
    A 2-digit literal like 10 is never a color (max 9), so only single-char."""
    t = atom.text
    if len(t) == 1 and t.isdigit():
        return int(t)
    return None


class _SymCtx:
    """Minimal shim with .symbols so resolve() from comment_solutions works."""
    def __init__(self, syms: dict[str, object]):
        self.symbols = syms


# ---------------------------------------------------------------------------
# Dict-literal {a b c d} support — these tokenize as fragmented atoms
# ('{8', '7', '0}', etc.) so we handle them via regex on the source text.
# ---------------------------------------------------------------------------

_DICT_BLOCK = re.compile(r"\{[^{}]*\}")
_DIGIT = re.compile(r"\b(\d)\b")  # single-digit token only (matches 0..9)


def _dict_color_positions(src: str) -> list[tuple[int, int, int]]:
    """Return [(line, col, value), ...] for every single-digit color
    that appears inside a {...} dict-literal block."""
    out: list[tuple[int, int, int]] = []
    for m in _DICT_BLOCK.finditer(src):
        block = m.group(0)
        block_start = m.start()
        for dm in _DIGIT.finditer(block):
            offset = block_start + dm.start()
            line, col = _offset_to_linecol(src, offset)
            out.append((line, col, int(dm.group(1))))
    return out


def _offset_to_linecol(src: str, offset: int) -> tuple[int, int]:
    """Convert a 0-indexed character offset to (line, col) — both 0-indexed."""
    head = src[:offset]
    line = head.count("\n")
    last_nl = head.rfind("\n")
    col = offset - (last_nl + 1) if last_nl >= 0 else offset
    return line, col


# ---------------------------------------------------------------------------
# Canonicalization — apply slots and hash
# ---------------------------------------------------------------------------

UNCANONICALIZABLE = {
    "concept_hash": None,
    "template": None,
    "color_slots": [],
    "size_slots": [],
    "reason": "uncanonicalizable",
}


def canonicalize_rule(src: str) -> dict:
    """Compute (concept_hash, template, color_slots) for a Racket rule.
    Returns a dict; concept_hash is None if the source can't be parsed
    or has unbalanced parens (codex breakage)."""
    if not src or not src.strip():
        return {**UNCANONICALIZABLE, "reason": "empty"}
    if not parens_balanced(src):
        return {**UNCANONICALIZABLE, "reason": "unbalanced_parens"}

    try:
        nodes = parse_racket(src)
    except Exception as e:
        return {**UNCANONICALIZABLE, "reason": f"parse_error: {e}"}

    # Build symbol table so (= var LIT) can resolve var to its definition.
    bindings = []
    for n in nodes:
        bindings.extend(extract_bindings(n))
    symbols = {b.name: b.rhs for b in bindings}

    # Collect AST-based color hits.
    ast_hits: list[tuple[Atom, int]] = []
    for n in nodes:
        _collect_color_atoms(n, ast_hits, symbols)

    # Convert AST hits to positional edits: (line, col, length, value).
    edits: list[tuple[int, int, int, int]] = []
    seen_positions: set[tuple[int, int]] = set()
    for atom, value in ast_hits:
        key = (atom.line, atom.col)
        if key in seen_positions:
            continue
        seen_positions.add(key)
        edits.append((atom.line, atom.col, len(atom.text), value))

    # Add dict-literal hits.
    for line, col, value in _dict_color_positions(src):
        key = (line, col)
        if key in seen_positions:
            continue
        seen_positions.add(key)
        edits.append((line, col, 1, value))

    # Sort by source order so slot indices follow first-appearance.
    edits.sort()

    # Assign slots: first time we see a value V, give it the next slot number;
    # subsequent appearances of V reuse that slot.
    value_to_slot: dict[int, int] = {}
    slots_in_order: list[int] = []
    final_edits: list[tuple[int, int, int, str]] = []
    for line, col, length, value in edits:
        if value not in value_to_slot:
            value_to_slot[value] = len(value_to_slot)
            slots_in_order.append(value)
        final_edits.append((line, col, length, f"$c{value_to_slot[value]}"))

    # Apply edits to the source — group by line, replace right-to-left so
    # earlier offsets stay valid as we splice.
    lines = src.split("\n")
    by_line: dict[int, list[tuple[int, int, str]]] = {}
    for line, col, length, replacement in final_edits:
        by_line.setdefault(line, []).append((col, length, replacement))
    for line_idx, items in by_line.items():
        items.sort(reverse=True)
        line = lines[line_idx]
        for col, length, rep in items:
            line = line[:col] + rep + line[col + length:]
        lines[line_idx] = line
    rewritten = "\n".join(lines)

    # Normalize whitespace before hashing so formatting differences don't
    # create different concept hashes for the same algorithm.
    canonical = _normalize_whitespace(rewritten)
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    return {
        "concept_hash": h,
        "template":     rewritten,
        "color_slots":  slots_in_order,
        "size_slots":   [],
    }


def _normalize_whitespace(s: str) -> str:
    """Strip line comments, collapse whitespace, drop trailing empties.
    The output is ONLY used for hashing — `template` keeps the original
    formatting so a human can read it."""
    out_lines = []
    for line in s.split("\n"):
        # Strip inline comments (everything from ';' to EOL, but not inside strings)
        stripped = _strip_inline_comment(line).rstrip()
        if stripped.strip():
            out_lines.append(re.sub(r"\s+", " ", stripped.strip()))
    return "\n".join(out_lines)


def _strip_inline_comment(line: str) -> str:
    in_str = False
    out = []
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"':
            in_str = not in_str
            out.append(c)
        elif c == ";" and not in_str:
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# CLI for ad-hoc inspection
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse, json
    ap = argparse.ArgumentParser(description="Canonicalize a Racket rule from a file or task_id.")
    ap.add_argument("--task", help="task_id; reads from data/base/solutions")
    ap.add_argument("--file", help="path to a Racket source file")
    ap.add_argument("--json", action="store_true", help="emit full result as JSON")
    args = ap.parse_args()

    if args.file:
        src = Path(args.file).read_text()
    elif args.task:
        import glob, json as _json
        match = None
        for f in glob.glob(str(ROOT / "data/base/solutions/**/*.json"), recursive=True):
            d = _json.load(open(f))
            if d.get("task_id") == args.task:
                rt = d.get("racket_target") or {}
                src = (rt.get("target_code") or rt.get("raw_code") or "").strip()
                match = f
                break
        if match is None:
            print(f"task_id {args.task} not found", file=sys.stderr); sys.exit(1)
    else:
        ap.error("--task or --file required")

    info = canonicalize_rule(src)
    if args.json:
        import json as _json
        print(_json.dumps(info, indent=2))
    else:
        print(f"concept_hash: {info['concept_hash']}")
        print(f"color_slots:  {info['color_slots']}")
        print()
        print(info["template"] or "(uncanonicalizable)")


if __name__ == "__main__":
    _main()
