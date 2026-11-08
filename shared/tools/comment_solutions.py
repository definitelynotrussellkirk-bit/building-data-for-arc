#!/usr/bin/env python3
"""
Backlog commenter — adds inline comments to uncommented Racket solutions.

Implements the rule from docs/RACKET_COMMENT_STYLE.md by walking each
solution's parsed sexpr tree and matching binding RHS shapes against a
pattern catalog. The catalog maps shapes like (find-color g 2),
(min-list (map first cells)), (objects g bg) to short value-grounded
comments. Description text is consulted to substitute color names
("red cells" instead of "color 2") when the description mentions them.

Usage:
    python3 scripts/comment_solutions.py --dry-run            # preview
    python3 scripts/comment_solutions.py --dry-run --task ID  # one
    python3 scripts/comment_solutions.py --sample 10          # show 10 random previews
    python3 scripts/comment_solutions.py                      # commit (writes JSON)

The script is conservative — if a binding doesn't match any pattern, it
is left untouched. Better to leave a binding bare than emit a misleading
comment. Re-runnable: solutions that already carry comments are skipped.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
SOL_DIR = ROOT / "data" / "base" / "solutions"

COLOR_NAMES = {
    0: "black", 1: "blue", 2: "red", 3: "green", 4: "yellow",
    5: "gray", 6: "magenta", 7: "orange", 8: "cyan", 9: "maroon",
}
NAME_TO_COLOR = {v: k for k, v in COLOR_NAMES.items()}


# ---------------------------------------------------------------------------
# Racket sexpr parser — preserves source positions so we can insert
# comments at exact line indices without disturbing existing formatting.
# ---------------------------------------------------------------------------

@dataclass
class Atom:
    text: str
    line: int      # 0-indexed line where the atom starts
    col: int

    def __repr__(self):
        return f"Atom({self.text!r})"


@dataclass
class List_:
    items: list                  # list[Atom | List_]
    line: int                    # opening bracket line
    col: int
    close_line: int = 0          # closing bracket line
    close_col: int = 0
    bracket: str = "("           # '(' or '['

    def head(self) -> Optional[str]:
        if self.items and isinstance(self.items[0], Atom):
            return self.items[0].text
        return None


def parse_racket(src: str) -> list:
    """Parse Racket source into a flat list of top-level nodes (Atom | List_).
    Comments and whitespace are skipped; their positions don't matter to us."""
    nodes, _ = _parse_tokens(_tokenize(src), 0)
    return nodes


def _tokenize(src: str) -> list[tuple]:
    """Yield (kind, text, line, col). kind in {'(', ')', '[', ']', 'atom', 'str'}."""
    out = []
    i, n = 0, len(src)
    line, col = 0, 0
    while i < n:
        c = src[i]
        if c == "\n":
            i += 1; line += 1; col = 0; continue
        if c.isspace():
            i += 1; col += 1; continue
        if c == ";":
            # skip to end of line
            while i < n and src[i] != "\n":
                i += 1; col += 1
            continue
        if c in "()[]":
            out.append((c, c, line, col))
            i += 1; col += 1; continue
        if c == '"':
            j = i + 1
            sline, scol = line, col
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    if src[j] == "\n": line += 1; col = -1
                    j += 1
                col += 1
            j = min(j + 1, n)
            out.append(("str", src[i:j], sline, scol))
            col += 1; i = j; continue
        # atom
        j = i
        sline, scol = line, col
        while j < n and not src[j].isspace() and src[j] not in '()[]";':
            j += 1; col += 1
        out.append(("atom", src[i:j], sline, scol))
        i = j
    return out


def _parse_tokens(tokens: list, pos: int) -> tuple[list, int]:
    out = []
    while pos < len(tokens):
        kind, text, line, col = tokens[pos]
        if kind in ")]":
            return out, pos
        if kind in "([":
            sub, end = _parse_tokens(tokens, pos + 1)
            close_kind, _, cline, ccol = (
                tokens[end] if end < len(tokens) else (")", ")", line, col))
            node = List_(items=sub, line=line, col=col,
                         close_line=cline, close_col=ccol, bracket=kind)
            out.append(node)
            pos = end + 1
        else:
            out.append(Atom(text=text, line=line, col=col))
            pos += 1
    return out, pos


# ---------------------------------------------------------------------------
# Pattern matching — small predicates over List_/Atom shapes.
# ---------------------------------------------------------------------------

def is_atom(n, *texts) -> bool:
    return isinstance(n, Atom) and (not texts or n.text in texts)


def is_list(n, head: Optional[str] = None, arity: Optional[int] = None) -> bool:
    if not isinstance(n, List_):
        return False
    if head is not None and n.head() != head:
        return False
    if arity is not None and len(n.items) != arity:
        return False
    return True


def atom_text(n) -> Optional[str]:
    return n.text if isinstance(n, Atom) else None


def as_int(n) -> Optional[int]:
    if isinstance(n, Atom):
        try:
            return int(n.text)
        except ValueError:
            return None
    return None


# Binding extraction --------------------------------------------------------

@dataclass
class Binding:
    name: str
    rhs: object        # Atom | List_
    line: int          # line of the (NAME RHS) clause
    col: int           # column of the clause's opening '(' or define
    is_define: bool    # True for `define`, False for let/let* clauses
    # For let-clauses, record sibling positions so we can decide whether
    # the "first clause on the let-keyword line" rescue applies — the
    # only safe-insert relaxation we make for shared-line bindings.
    let_keyword_line: int = -1   # line of the parent (let / (let*
    sibling_lines: tuple = ()    # lines of all clauses in the same let
    is_first_in_let: bool = False


def extract_bindings(node) -> list[Binding]:
    """Walk the tree and collect every binding worth commenting:
       - (define NAME EXPR)
       - (define (NAME ARGS...) BODY...)   — function definitions
       - clauses inside (let ((N E) ...) ...) and (let* ((N E) ...) ...)
       - clauses inside (let NAME ((N E) ...) ...)         — named let
       - clauses inside (let-values (((N...) E) ...) ...)  — destructuring
    Returns bindings in source order."""
    out = []
    _walk_collect(node, out)
    out.sort(key=lambda b: b.line)
    # Deduplicate by line — a (NAME EXPR) clause shouldn't be commented twice
    seen = set()
    uniq = []
    for b in out:
        if b.line in seen:
            continue
        seen.add(b.line)
        uniq.append(b)
    return uniq


def _walk_collect(node, out: list):
    if isinstance(node, list):
        for x in node:
            _walk_collect(x, out)
        return
    if not isinstance(node, List_):
        return
    head = node.head()
    if head == "define" and len(node.items) >= 3:
        # (define NAME EXPR) or (define (NAME ARGS...) BODY...)
        n2 = node.items[1]
        # Insert above the entire (define ...) form — use the form's open-paren.
        if isinstance(n2, Atom):
            out.append(Binding(name=n2.text, rhs=node.items[2],
                               line=node.line, col=node.col, is_define=True))
        elif isinstance(n2, List_) and n2.items and isinstance(n2.items[0], Atom):
            fn_name = n2.items[0].text
            out.append(Binding(name=fn_name, rhs=node, line=node.line, col=node.col,
                               is_define=True))
    elif head in ("let", "let*", "letrec", "letrec*"):
        idx = 1
        if idx < len(node.items) and isinstance(node.items[idx], Atom):
            idx += 1  # named-let label
        if idx < len(node.items) and isinstance(node.items[idx], List_):
            blist = node.items[idx]
            sibling_lines = tuple(
                c.line for c in blist.items
                if isinstance(c, List_) and len(c.items) == 2 and isinstance(c.items[0], Atom)
            )
            for i, clause in enumerate(blist.items):
                if isinstance(clause, List_) and len(clause.items) == 2:
                    name_node, rhs = clause.items
                    if isinstance(name_node, Atom):
                        out.append(Binding(
                            name=name_node.text, rhs=rhs,
                            line=clause.line, col=clause.col, is_define=False,
                            let_keyword_line=node.line,
                            sibling_lines=sibling_lines,
                            is_first_in_let=(i == 0),
                        ))
    # Recurse into all children regardless
    for x in node.items:
        _walk_collect(x, out)


# ---------------------------------------------------------------------------
# Pattern catalog — each rule takes (name, rhs, ctx) and returns a comment
# string or None.
# ---------------------------------------------------------------------------

@dataclass
class CommentCtx:
    """Per-task context shared across rules: the puzzle description
    (lower-cased) and the set of color names mentioned in it."""
    description: str
    desc_lc: str
    desc_colors: set[int] = field(default_factory=set)
    desc_nouns: set[str] = field(default_factory=set)
    # Symbol table {name -> rhs node}, populated before commenting.
    symbols: dict = field(default_factory=dict)


def resolve(node, ctx: "CommentCtx", depth: int = 3):
    """Follow atom→rhs links up to `depth` levels so a rule can see what
    `(first bb)` actually references when bb is bound to (obj-bbox X)."""
    while depth > 0 and isinstance(node, Atom):
        nxt = ctx.symbols.get(node.text)
        if nxt is None or nxt is node:
            return node
        node = nxt
        depth -= 1
    return node


def color_phrase(c: int, ctx: CommentCtx) -> str:
    """Format a color reference: 'red(2)' if the description mentions
    'red', else just 'color 2'."""
    name = COLOR_NAMES.get(c)
    if name and name in ctx.desc_lc:
        return f"{name}({c})"
    return f"color {c}"


def _build_ctx(description: str) -> CommentCtx:
    desc_lc = (description or "").lower()
    colors = {NAME_TO_COLOR[n] for n in NAME_TO_COLOR if n in desc_lc}
    NOUNS = {
        "rectangle", "rectangles", "frame", "frames", "object", "objects",
        "shape", "shapes", "border", "borders", "endpoint", "endpoints",
        "anchor", "anchors", "marker", "markers", "occluder", "occluders",
        "stripe", "stripes", "wall", "walls", "cup", "cups",
        "row", "rows", "column", "columns", "diagonal", "diagonals",
        "ring", "rings", "axis", "block", "blocks", "tile", "tiles",
        "seed", "seeds", "noise", "background", "interior", "exterior",
        "corner", "corners", "edge", "edges", "line", "lines", "path",
        "grid", "cell", "cells", "point", "points", "cluster", "clusters",
    }
    nouns = {n for n in NOUNS if n in desc_lc}
    return CommentCtx(description=description, desc_lc=desc_lc,
                      desc_colors=colors, desc_nouns=nouns)


# Each rule: (name, rhs, ctx) -> Optional[str].
RULES: list[Callable] = []


def rule(fn):
    RULES.append(fn)
    return fn


# --- Color queries ---------------------------------------------------------

@rule
def r_find_color(name, rhs, ctx):
    """(find-color g K) → 'Cells of <color>'."""
    if not is_list(rhs, "find-color"): return None
    if len(rhs.items) < 3: return None
    k = as_int(rhs.items[2])
    if k is None: return None
    return f"Positions of every {color_phrase(k, ctx)} cell"


@rule
def r_color_frequency(name, rhs, ctx):
    if is_list(rhs, "color-frequency"):
        return "Color → count for the whole grid"
    return None


@rule
def r_count_color(name, rhs, ctx):
    if is_list(rhs, "count-color") and len(rhs.items) >= 3:
        k = as_int(rhs.items[2])
        if k is not None:
            return f"How many {color_phrase(k, ctx)} cells in the grid"
    return None


@rule
def r_mode(name, rhs, ctx):
    """(mode g) / (mode g bg) → background color."""
    if is_list(rhs, "mode"):
        return "Most common color (the background)"
    return None


@rule
def r_minority(name, rhs, ctx):
    if is_list(rhs, "minority"):
        return "Least common non-bg color (the marker)"
    return None


# --- Bounding box extraction ----------------------------------------------

# Helpers: detect (apply min/max ...) or (min-list/max-list ...) over
# (map first/second/fst/snd CELLS).
_MIN_HEADS = {"min-list", "min", "apply"}
_MAX_HEADS = {"max-list", "max", "apply"}
_FIRST = {"first", "fst", "car"}
_SECOND = {"second", "snd"}


def _is_minmax(rhs: object, kind: str) -> Optional[tuple[str, object]]:
    """Match all common edge-extraction forms and return (axis, CELLS):
       - (min-list (map first CELLS))
       - (apply min (map fst CELLS))
       - (min (map fst CELLS))
       - (reduce min INIT (map first CELLS))
       kind is 'min' or 'max'."""
    if not isinstance(rhs, List_) or not rhs.items:
        return None
    head = rhs.head()
    arg = None
    if head in {"min-list", "max-list"} and len(rhs.items) == 2:
        if (kind == "min" and head != "min-list") or (kind == "max" and head != "max-list"):
            return None
        arg = rhs.items[1]
    elif head == "apply" and len(rhs.items) == 3:
        op = atom_text(rhs.items[1])
        if op != kind: return None
        arg = rhs.items[2]
    elif head in {"min", "max"} and head == kind and len(rhs.items) == 2:
        arg = rhs.items[1]
    elif head == "reduce" and len(rhs.items) == 4:
        # (reduce min INIT LIST) — INIT is a sentinel like 999
        op = atom_text(rhs.items[1])
        if op != kind: return None
        arg = rhs.items[3]
    else:
        return None
    if not is_list(arg, "map") or len(arg.items) != 3:
        return None
    proj = atom_text(arg.items[1])
    if proj in _FIRST: axis = "row"
    elif proj in _SECOND: axis = "col"
    else: return None
    return axis, arg.items[2]


def _cells_label(node) -> Optional[str]:
    """Best-effort name for what cells-list this is, e.g. 'rect' from rect-cells."""
    if isinstance(node, Atom):
        t = node.text
        for suffix in ("-cells", "-cs", "-coords", "-pts", "-points", "-positions"):
            if t.endswith(suffix):
                return t[: -len(suffix)].replace("-", " ")
        if t in ("cells", "pts", "points", "coords", "positions"):
            return None
        return t.replace("-", " ")
    if is_list(node, "find-color") and len(node.items) >= 3:
        c = as_int(node.items[2])
        if c is not None:
            return f"{COLOR_NAMES.get(c, 'color-' + str(c))}"
    return None


@rule
def r_bbox(name, rhs, ctx):
    """Detect bbox edges: (min-list (map first cells)) → 'Top edge'."""
    for kind, edge_row, edge_col in [("min", "Top", "Left"), ("max", "Bottom", "Right")]:
        m = _is_minmax(rhs, kind)
        if not m:
            continue
        axis, cells = m
        edge = edge_row if axis == "row" else edge_col
        label = _cells_label(cells)
        if label:
            return f"{edge} edge of the {label} bbox"
        return f"{edge} edge of the bbox"
    return None


@rule
def r_bbox_dim(name, rhs, ctx):
    """(+ 1 (- A B)) or (+ (- A B) 1) → height/width depending on which
    edges A and B come from. Conservative: only fires when names match
    a known pair (r2/r1, c2/c1, third bb / first bb, etc.)."""
    if not is_list(rhs, "+") or len(rhs.items) != 3: return None
    a, b = rhs.items[1], rhs.items[2]
    if as_int(a) == 1: inner = b
    elif as_int(b) == 1: inner = a
    else: return None
    if not is_list(inner, "-") or len(inner.items) != 3: return None
    x, y = inner.items[1], inner.items[2]

    nlow = name.lower()
    if nlow in {"h", "height", "kh", "oh", "tile-h", "th", "ih", "sh"}: return "Bbox height (rows)"
    if nlow in {"w", "width", "kw", "ow", "tile-w", "tw", "iw", "sw"}: return "Bbox width (cols)"

    # Tuple-accessor inference: (third bb) - (first bb) → row span.
    def axis_of(node):
        if not isinstance(node, List_): return None
        head = node.head()
        if head in _FIRST or head == "third": return "row"   # first/third → r1/r2
        if head in _SECOND or head == "fourth": return "col" # second/fourth → c1/c2
        return None
    ax = axis_of(x) or axis_of(y)
    if ax == "row": return "Bbox height (rows)"
    if ax == "col": return "Bbox width (cols)"

    # Pattern from var-name suffixes: r2/r1, c2/c1, kr2/kr1
    xt, yt = atom_text(x), atom_text(y)
    if xt and yt and xt.endswith("2") and yt.endswith("1"):
        if xt[0] in "ry" or yt[0] in "ry": return "Bbox height (rows)"
        if xt[0] in "cx" or yt[0] in "cx": return "Bbox width (cols)"
    return None


# --- Object / region queries ----------------------------------------------

@rule
def r_objects(name, rhs, ctx):
    if is_list(rhs, "objects"): return "4-connected components (excluding background)"
    if is_list(rhs, "objects-8"): return "8-connected components (diagonals included)"
    if is_list(rhs, "objects-multicolor"): return "Multi-color 8-connected components"
    return None


@rule
def r_filter_by_color(name, rhs, ctx):
    """(filter (lambda (o) (= (obj-color o) K)) OBJS) → objects of color K."""
    if not is_list(rhs, "filter") or len(rhs.items) != 3: return None
    pred = rhs.items[1]
    if not is_list(pred, "lambda") or len(pred.items) < 3: return None
    body = pred.items[2]
    if not is_list(body, "=") or len(body.items) != 3: return None
    a, b = body.items[1], body.items[2]
    inner_color_call, color_atom = (a, b) if is_list(a, "obj-color") else (b, a)
    if not is_list(inner_color_call, "obj-color"): return None
    k = as_int(color_atom)
    if k is None: return None
    return f"Objects whose color is {color_phrase(k, ctx)}"


@rule
def r_filter_object_predicate(name, rhs, ctx):
    """(filter (lambda (o) PRED) OBJS) — common predicates beyond color:
       size comparisons, border-touching, shape predicates."""
    if not is_list(rhs, "filter") or len(rhs.items) != 3: return None
    pred = rhs.items[1]
    if not is_list(pred, "lambda") or len(pred.items) < 3: return None
    body = pred.items[2]
    txt = _flatten_text(body)

    # Bail unless the source resolves to objects/objects-8/objects-multicolor
    src = rhs.items[2]
    src_resolved = resolve(src, ctx)
    src_head = src_resolved.head() if isinstance(src_resolved, List_) else None
    if src_head not in {"objects", "objects-8", "objects-multicolor"}:
        return None

    if "obj-size" in txt:
        if "<" in txt and ">" not in txt: return "Objects below a size threshold"
        if ">" in txt and "<" not in txt: return "Objects above a size threshold"
        if "=" in txt: return "Objects with a specific cell count"
        return "Objects filtered by size"
    if "bordering?" in txt:
        if "not" in txt.split(): return "Objects that don't touch the grid border"
        return "Objects that touch the grid border"
    if "filled?" in txt: return "Solid objects (bbox fully filled)"
    if "hollow?" in txt: return "Hollow objects (bbox has gaps)"
    if "square?" in txt: return "Square objects"
    if "vline?" in txt: return "Vertical-line objects (1 column wide)"
    if "hline?" in txt: return "Horizontal-line objects (1 row tall)"
    return None


@rule
def r_largest_smallest(name, rhs, ctx):
    """(sort-by ... obj-size) / (pick-max ... obj-size) → biggest object."""
    head = rhs.head() if isinstance(rhs, List_) else None
    if head not in {"sort-by", "pick-max", "pick-min", "largest-object", "extract-largest"}:
        return None
    if head == "largest-object": return "The largest connected component"
    if head == "extract-largest": return "Crop to the largest component"
    if head == "pick-max":
        return "Pick the object that maximizes the given key"
    if head == "pick-min":
        return "Pick the object that minimizes the given key"
    if head == "sort-by":
        # Only comment when the key function reveals a meaningful order;
        # a generic "Sorted list" tells the reader nothing.
        if len(rhs.items) >= 3:
            keytxt = _flatten_text(rhs.items[2])
            if "obj-size" in keytxt or "length" in keytxt:
                return "Objects sorted by size"
            if "count-color" in keytxt:
                return "Sorted by color count"
            if "obj-color" in keytxt:
                return "Sorted by color"
            if "obj-r1" in keytxt or "obj-c1" in keytxt:
                return "Objects sorted by bbox position"
        return None
    return None


def _flatten_text(node) -> str:
    if isinstance(node, Atom): return node.text
    if isinstance(node, List_):
        return " ".join(_flatten_text(x) for x in node.items)
    return ""


# --- Output construction --------------------------------------------------

@rule
def r_grid_from_fn(name, rhs, ctx):
    if is_list(rhs, "grid-from-fn"):
        return "Build the output grid"
    return None


@rule
def r_empty_grid(name, rhs, ctx):
    if is_list(rhs, "empty-grid"):
        return "Blank canvas to paint into"
    return None


# --- Cells-of-condition (filter (lambda (p) (= (cell-at g r c) K)) ...) ---

def _cellat_args(call):
    """If `call` is (cell-at g R C) or (at g R C), return (R, C) atoms."""
    if not isinstance(call, List_): return None
    if call.head() not in {"cell-at", "at"} or len(call.items) != 4: return None
    return call.items[2], call.items[3]


@rule
def r_filter_cells_eq_color(name, rhs, ctx):
    """(filter (lambda (P) (= (cell-at g (first P) (second P)) K)) SRC)
       → 'Positions of every K cell' regardless of how SRC is built.

       Reject the (range 0 (cols g)) shape — that's a column-index filter,
       not a cell filter — and route it to the row/col-index form."""
    if not is_list(rhs, "filter") or len(rhs.items) != 3: return None
    pred, src = rhs.items[1], rhs.items[2]
    if not is_list(pred, "lambda") or len(pred.items) < 3: return None
    arg_list = pred.items[1]
    body = pred.items[2]
    if not is_list(body, "=") or len(body.items) != 3: return None
    a, b = body.items[1], body.items[2]
    cell_call, col_node = (a, b) if isinstance(a, List_) and a.head() in {"cell-at", "at"} \
                                  else (b, a)
    args = _cellat_args(cell_call)
    if args is None: return None
    k = as_int(col_node)
    if k is None: return None

    # Single-arg lambda: predicate sees a position-pair.
    args_lambda = arg_list.items if isinstance(arg_list, List_) else []
    pos_arg = args_lambda[0].text if len(args_lambda) == 1 and isinstance(args_lambda[0], Atom) else None

    R, C = args
    Rt = atom_text(R); Ct = atom_text(C)
    is_pos_indexing = (
        pos_arg is not None and (
            (isinstance(R, List_) and R.head() in _FIRST and atom_text(R.items[1]) == pos_arg) or
            (isinstance(R, List_) and R.head() in _SECOND and atom_text(R.items[1]) == pos_arg) or
            Rt == pos_arg or Ct == pos_arg
        )
    )

    if is_pos_indexing:
        return f"Positions of every {color_phrase(k, ctx)} cell"

    # Not a per-position predicate — try the index forms.
    axis = _range_axis(src)
    if axis == "rows":
        return f"Row indices where the leftmost cell is {color_phrase(k, ctx)}"
    if axis == "cols":
        return f"Column indices where the top cell is {color_phrase(k, ctx)}"
    return None


def _range_axis(node) -> Optional[str]:
    """For (range 0 EXPR) where EXPR is (rows g), (cols g), h, or w,
    return 'rows' or 'cols'. None if it doesn't look like a row/col range."""
    if not is_list(node, "range") or len(node.items) != 3: return None
    upper = node.items[2]
    if is_list(upper, "rows"): return "rows"
    if is_list(upper, "cols"): return "cols"
    if isinstance(upper, Atom):
        t = upper.text.lower()
        if t in {"h", "hh", "height"}: return "rows"
        if t in {"w", "ww", "width"}: return "cols"
    return None


@rule
def r_full_row_or_col(name, rhs, ctx):
    """(filter (lambda (R) (all? (lambda (C) (= K (at g R C))) (range 0 ...))) (range 0 ...))
       → 'Rows entirely color K' / 'Columns entirely color K'."""
    if not is_list(rhs, "filter") or len(rhs.items) != 3: return None
    pred, src = rhs.items[1], rhs.items[2]
    if not is_list(pred, "lambda") or len(pred.items) < 3: return None
    body = pred.items[2]
    if not isinstance(body, List_): return None
    if body.head() not in {"all?", "andmap", "for/and"}: return None
    axis = _range_axis(src)
    if axis is None: return None

    # Pull the target color out of the inner predicate body.
    color = None
    def find_color_eq(node):
        nonlocal color
        if not isinstance(node, List_): return
        if node.head() == "=" and len(node.items) == 3:
            for x in node.items[1:]:
                v = as_int(x)
                if v is not None: color = v
        for c in node.items:
            find_color_eq(c)
    find_color_eq(body)

    word = "Rows" if axis == "rows" else "Columns"
    if color is not None:
        return f"{word} entirely filled with {color_phrase(color, ctx)}"
    return f"{word} that are uniform"


# --- Bbox / cells / hash / normalize ------------------------------------

@rule
def r_obj_bbox(name, rhs, ctx):
    if is_list(rhs, "obj-bbox") and len(rhs.items) >= 2:
        target = atom_text(rhs.items[1]) or "object"
        return f"Bounding box (r1 c1 r2 c2) of {target}"
    if is_list(rhs, "bbox-of-cells") and len(rhs.items) >= 2:
        return "Bounding box enclosing the cells"
    return None


@rule
def r_obj_cells(name, rhs, ctx):
    if is_list(rhs, "obj-cells") and len(rhs.items) >= 2:
        target = atom_text(rhs.items[1]) or "object"
        return f"List of (r c) cells in {target}"
    return None


@rule
def r_normalize_cells(name, rhs, ctx):
    if is_list(rhs, "normalize-cells"):
        return "Same shape, translated so its bbox starts at (0,0)"
    return None


@rule
def r_make_hash(name, rhs, ctx):
    if is_list(rhs, "make-hash") or is_list(rhs, "make-hasheq") or is_list(rhs, "make-hasheqv"):
        return f"Mutable lookup table for {name}"
    return None


@rule
def r_length_of(name, rhs, ctx):
    """(length COLL) — comment if COLL resolves to a familiar collection."""
    if not is_list(rhs, "length") or len(rhs.items) != 2: return None
    arg = rhs.items[1]
    target = resolve(arg, ctx)
    if isinstance(target, List_):
        head = target.head()
        if head == "find-color" and len(target.items) >= 3:
            k = as_int(target.items[2])
            if k is not None:
                return f"Count of {color_phrase(k, ctx)} cells"
        if head in {"objects", "objects-8", "objects-multicolor"}:
            return "Number of connected components"
        if head == "obj-cells":
            return "Cell count of this object"
        if head in {"grid-positions", "grid-positions-pairs", "grid-cells"}:
            return "Total positions in the grid (h*w)"
    if isinstance(arg, Atom):
        # Use the binding name to hint at meaning
        nm = arg.text.lower()
        if "obj" in nm or nm == "objs" or nm == "objects":
            return "Number of objects"
        if nm.endswith("-cells") or nm == "cells":
            return "Cell count"
    return None


@rule
def r_sort_with_cmp(name, rhs, ctx):
    """(sort LIST CMP) — comment when CMP reveals the order direction."""
    if not is_list(rhs, "sort") or len(rhs.items) != 3: return None
    cmp = rhs.items[2]
    txt = _flatten_text(cmp)
    if "obj-size" in txt:
        if " > " in f" {txt} ": return "Objects largest-first"
        if " < " in f" {txt} ": return "Objects smallest-first"
        return "Objects sorted by size"
    if "obj-color" in txt:
        return "Objects sorted by color"
    if "obj-r1" in txt or "obj-c1" in txt:
        return "Objects sorted by bbox position"
    return None


@rule
def r_recolor(name, rhs, ctx):
    if is_list(rhs, "recolor") and len(rhs.items) >= 4:
        a = as_int(rhs.items[2]); b = as_int(rhs.items[3])
        if a is not None and b is not None:
            return f"Replace every {color_phrase(a, ctx)} with {color_phrase(b, ctx)}"
        return "Recolor one color to another"
    if is_list(rhs, "recolor-map") or is_list(rhs, "recolor-map*"):
        return "Apply a color-to-color mapping across the grid"
    if is_list(rhs, "remove-color") and len(rhs.items) >= 3:
        k = as_int(rhs.items[2])
        if k is not None:
            return f"Erase every {color_phrase(k, ctx)} cell (set to background)"
    if is_list(rhs, "swap-colors") and len(rhs.items) >= 4:
        a = as_int(rhs.items[2]); b = as_int(rhs.items[3])
        if a is not None and b is not None:
            return f"Swap {color_phrase(a, ctx)} and {color_phrase(b, ctx)} everywhere"
    return None


# --- (first/second/third/fourth BB) where BB is a bbox tuple --------------

# Position-in-tuple → which bbox edge it corresponds to.
_BBOX_TUPLE_HEAD = {"obj-bbox", "bbox-of-cells", "largest-rect"}
_TUPLE_ACCESSORS = {
    "first": ("Top edge (row r1)", 0),
    "fst":   ("Top edge (row r1)", 0),
    "car":   ("Top edge (row r1)", 0),
    "second":("Left edge (col c1)", 1),
    "snd":   ("Left edge (col c1)", 1),
    "third": ("Bottom edge (row r2)", 2),
    "fourth":("Right edge (col c2)", 3),
}


@rule
def r_bbox_tuple_accessor(name, rhs, ctx):
    """`(first bb)` etc. when bb resolves to (obj-bbox X) or
    (bbox-of-cells X) — emit a meaningful edge name."""
    if not isinstance(rhs, List_): return None
    head = rhs.head()
    accessor = _TUPLE_ACCESSORS.get(head)
    if accessor is None or len(rhs.items) != 2: return None
    arg = rhs.items[1]
    target = resolve(arg, ctx)
    if not isinstance(target, List_): return None
    if target.head() in _BBOX_TUPLE_HEAD:
        return accessor[0]
    return None


@rule
def r_nth_bbox(name, rhs, ctx):
    """(nth bb 2) → 'Bottom edge', etc."""
    if not is_list(rhs, "nth") or len(rhs.items) != 3: return None
    idx = as_int(rhs.items[2])
    if idx is None: return None
    arg = rhs.items[1]
    target = resolve(arg, ctx)
    if not (isinstance(target, List_) and target.head() in _BBOX_TUPLE_HEAD):
        return None
    edges = ["Top edge (row r1)", "Left edge (col c1)",
             "Bottom edge (row r2)", "Right edge (col c2)"]
    if 0 <= idx < 4:
        return edges[idx]
    return None


# --- (first (find-color g K)) and similar position pickers ----------------

@rule
def r_first_of_color(name, rhs, ctx):
    """(first (find-color g K)) → 'Position of the (first) K cell'."""
    if not isinstance(rhs, List_): return None
    head = rhs.head()
    if head not in _FIRST and head not in _SECOND: return None
    if len(rhs.items) != 2: return None
    inner = rhs.items[1]
    # Direct: (first (find-color g K))
    if is_list(inner, "find-color") and len(inner.items) >= 3:
        k = as_int(inner.items[2])
        if k is None: return None
        word = "first" if head in _FIRST else "second"
        return f"Position of the {word} {color_phrase(k, ctx)} cell"
    # Indirect: (first VAR) where VAR is bound to (find-color g K)
    if isinstance(inner, Atom):
        target = resolve(inner, ctx)
        if is_list(target, "find-color") and len(target.items) >= 3:
            k = as_int(target.items[2])
            if k is not None:
                word = "first" if head in _FIRST else "second"
                # If the resolved name is descriptive (e.g. cells), reuse it
                return f"Position of the {word} {color_phrase(k, ctx)} cell"
    return None


@rule
def r_first_position_of(name, rhs, ctx):
    """(first (positions-of g LAMBDA)) → 'First position matching predicate'.
    Only fires when name suggests a single-position role (seed, anchor, p1...)."""
    if not isinstance(rhs, List_): return None
    if rhs.head() not in _FIRST: return None
    if len(rhs.items) != 2: return None
    inner = rhs.items[1]
    if not is_list(inner, "positions-of"): return None
    nlow = name.lower()
    if not (nlow.startswith(("seed", "anchor", "p", "pos", "start", "src", "origin"))
            or nlow in {"a", "b", "c"}):
        return None
    return "First grid position matching the predicate"


# --- Predicate-defined helpers ------------------------------------------

@rule
def r_for_each_position(name, rhs, ctx):
    """(for*/list ((r ...) (c ...) #:when ...)) → 'Positions where ...'."""
    if not isinstance(rhs, List_): return None
    if rhs.head() not in {"for/list", "for*/list"}: return None
    txt = _flatten_text(rhs)
    if "cell-at" in txt and "= " in txt:
        # Heuristic: looks like a per-cell condition over the grid
        return "Positions matching a per-cell condition"
    return None


@rule
def r_first_finder(name, rhs, ctx):
    """(find-first ...) / (for/first ...) — only annotate when the name
    suggests a single-target role; 'First match' alone is too vague."""
    if not (is_list(rhs, "find-first") or is_list(rhs, "for/first")):
        return None
    nlow = name.lower()
    if nlow.endswith("-cell") or nlow.endswith("-pos") or nlow == "control-cell":
        return "First cell matching the predicate"
    return None


# Function-definition labels (Helper: foo (2 args)) were emitted in v1
# but dropped — they restate what `(define (foo a b) ...)` already says
# without adding value-grounding or narrative content. Comments that
# only echo the binding name don't earn their line.


# --- Position iterations and broad transforms ---------------------------

@rule
def r_grid_positions_filter(name, rhs, ctx):
    """(filter PRED (grid-positions g))/(positions-of g PRED) -> 'Cells where ...'."""
    if is_list(rhs, "positions-of"):
        return "Every cell whose value satisfies the predicate"
    if not is_list(rhs, "filter") or len(rhs.items) != 3: return None
    src = rhs.items[2]
    if isinstance(src, List_) and src.head() in {"grid-positions", "grid-positions-pairs"}:
        return "Cells filtered out of every (r,c) position"
    return None


@rule
def r_for_star_positions(name, rhs, ctx):
    """(for*/list ((r ...) (c ...) #:when ...)) → 'Positions where ...'."""
    if not isinstance(rhs, List_): return None
    if rhs.head() not in {"for*/list", "for/list"}: return None
    txt = _flatten_text(rhs)
    if "#:when" in txt and ("cell-at" in txt or " at " in txt or "(at " in txt):
        return "Every (r,c) position where a per-cell condition holds"
    return None


@rule
def r_row_col_pick(name, rhs, ctx):
    """Common picks of a single row or column of the grid:
       (first g)   → top row
       (last g)    → bottom row
       (row g R)   → a specific row
       (col g C)   → a specific column
       (map first g)  → left column
       (map last g)   → right column
       (subgrid g r1 c1 r2 c2) → sub-rectangle of the grid"""
    if not isinstance(rhs, List_): return None
    head = rhs.head()
    # (first g) / (last g) — but ONLY when the arg resolves to the grid `g`
    if head in {"first", "last", "fst"} and len(rhs.items) == 2:
        arg = rhs.items[1]
        if isinstance(arg, Atom) and arg.text == "g":
            if head == "last":
                return "Bottom row of the grid"
            return "Top row of the grid"
    if head == "row" and len(rhs.items) >= 3:
        return "A specific row of the grid"
    if head == "col" and len(rhs.items) >= 3:
        return "A specific column of the grid"
    if head == "map" and len(rhs.items) == 3:
        proj = atom_text(rhs.items[1])
        src = rhs.items[2]
        if isinstance(src, Atom) and src.text == "g":
            if proj in _FIRST: return "Left column of the grid"
            if proj == "last":  return "Right column of the grid"
    if head == "subgrid":
        return "Sub-rectangle of the grid"
    if head == "crop-to-content":
        return "Crop to the non-background bounding box"
    if head == "crop-object":
        return "Crop to the object's bounding box"
    return None


@rule
def r_geom_transform(name, rhs, ctx):
    if not isinstance(rhs, List_): return None
    table = {
        "rotate-cw":   "Rotate the grid 90° clockwise",
        "rotate-ccw":  "Rotate the grid 90° counter-clockwise",
        "rotate-180":  "Rotate the grid 180°",
        "flip-lr":     "Mirror the grid left-right",
        "flip-ud":     "Mirror the grid top-bottom",
        "transpose":   "Transpose: swap rows and columns",
        "upscale":     "Scale up each cell to a larger block",
        "downscale":   "Reduce by an integer factor",
        "self-tile":   "Fractal: repeat the grid where its non-bg cells are",
        "kaleidoscope":"Four-fold reflective tiling",
    }
    msg = table.get(rhs.head())
    return msg


@rule
def r_physics(name, rhs, ctx):
    if not isinstance(rhs, List_): return None
    table = {
        "gravity":         "Slide non-bg cells in the given direction until they hit a wall",
        "slide-color":     "Slide every cell of one color in a direction",
        "slide-object":    "Slide a specific object until it bumps into something",
        "smear-color":     "Shoot rays of one color in a direction",
        "flood-fill":      "Flood-fill the connected region from (r,c)",
        "bucket-fill":     "Bucket-fill the same-color region from (r,c)",
        "fill-all-enclosed": "Fill every bg region not reachable from the border",
    }
    msg = table.get(rhs.head())
    return msg


@rule
def r_reduce_grid_init(name, rhs, ctx):
    """(reduce FN INIT LIST) where INIT is `g` or `(empty-grid ...)` →
    a fold that builds the output by sequentially modifying a grid."""
    if not is_list(rhs, "reduce") or len(rhs.items) != 4: return None
    init = rhs.items[2]
    if isinstance(init, Atom) and init.text == "g":
        return "Fold over inputs, mutating g step-by-step into the output"
    if isinstance(init, List_) and init.head() in {"empty-grid", "grid-from-fn"}:
        return "Fold paint operations onto a fresh canvas"
    return None


# --- Auto-bound shadowing — skip ----------------------------------------

SKIP_NAMES = {"h", "w", "g"}


def comment_for_binding(b: Binding, ctx: CommentCtx) -> Optional[str]:
    """Try every rule in order; return the first non-None comment."""
    if b.name in SKIP_NAMES:
        return None
    for fn in RULES:
        try:
            c = fn(b.name, b.rhs, ctx)
        except Exception:
            c = None
        if c:
            return c
    return None


# ---------------------------------------------------------------------------
# Top-level commenter — applies the rules to one solution's source.
# ---------------------------------------------------------------------------

def parens_balanced(code: str) -> bool:
    """Quick balance check that handles Racket's interchangeable () and []
    plus line comments and strings. Conservative: false if anything is
    suspicious. We use this to skip codex-generated solutions whose source
    is already malformed — adding comments to broken code only makes the
    breakage harder to spot."""
    depth = 0
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c == ";":
            while i < n and code[i] != "\n": i += 1
            continue
        if c == '"':
            i += 1
            while i < n and code[i] != '"':
                i += 2 if code[i] == "\\" else 1
            i = min(i + 1, n)
            continue
        if c in "([": depth += 1
        elif c in ")]":
            depth -= 1
            if depth < 0: return False
        i += 1
    return depth == 0


def comment_solution(code: str, description: str = "") -> tuple[str, list]:
    """Return (commented_source, [(line, comment_text), ...] inserts).
    Existing comment lines are preserved; new comments are inserted above
    the binding clause they describe."""
    if not code.strip():
        return code, []
    if not parens_balanced(code):
        # Pre-existing breakage — leave it alone so the bug is visible.
        return code, []
    lines = code.split("\n")
    try:
        nodes = parse_racket(code)
    except Exception:
        return code, []
    bindings: list[Binding] = []
    for n in nodes:
        bindings.extend(extract_bindings(n))

    ctx = _build_ctx(description)
    # First pass — build a symbol table so rules can resolve references
    # like (first bb) when bb itself is bound to (obj-bbox X).
    ctx.symbols = {b.name: b.rhs for b in bindings}

    # Lines that already have a `;` comment immediately above.
    has_comment_above = set()
    for i, ln in enumerate(lines):
        if ln.strip().startswith(";"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                has_comment_above.add(j)

    def is_safe_insert(b: Binding) -> tuple[bool, int]:
        """Return (allowed, target_line). target_line is where the
        comment should be inserted (typically b.line). Two relaxations:
          1. Standard: clause is the first non-whitespace on its line.
          2. First clause of a let-list whose siblings are all on
             different lines — emit the comment above the (let*) line
             instead of the clause line. The reader sees the comment
             attached to the let, but since only one binding is on the
             keyword line, the attribution is unambiguous."""
        if b.line >= len(lines): return (False, b.line)
        prefix = lines[b.line][: b.col]
        if prefix.strip() == "":
            return (True, b.line)
        if (b.is_first_in_let and b.line == b.let_keyword_line
                and len([s for s in b.sibling_lines if s == b.line]) == 1):
            # The first clause shares a line ONLY with the (let* keyword.
            # Insert above the let* line; the comment then naturally
            # attaches to the single first binding.
            return (True, b.let_keyword_line)
        return (False, b.line)

    inserts: list[tuple[int, str]] = []
    for b in bindings:
        ok, target_line = is_safe_insert(b)
        if not ok:
            continue
        if target_line in has_comment_above:
            continue
        comment = comment_for_binding(b, ctx)
        if not comment:
            continue
        src_line = lines[target_line] if target_line < len(lines) else ""
        indent = src_line[: len(src_line) - len(src_line.lstrip())]
        inserts.append((target_line, f"{indent};; {comment}"))

    if not inserts:
        return code, []

    out_lines = list(lines)
    for line, text in sorted(inserts, key=lambda x: -x[0]):
        out_lines.insert(line, text)
    return "\n".join(out_lines), inserts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def iter_solution_files() -> Iterable[Path]:
    return SOL_DIR.rglob("*.json")


def show_diff(orig: str, new: str) -> None:
    """Print a tiny side-by-side diff: just the lines that changed."""
    a, b = orig.split("\n"), new.split("\n")
    # Re-walk b, printing inserted comment lines + their following code line.
    i = j = 0
    while i < len(a) or j < len(b):
        if i < len(a) and j < len(b) and a[i] == b[j]:
            i += 1; j += 1; continue
        if j < len(b):
            print("+ " + b[j])
            j += 1
        elif i < len(a):
            print("- " + a[i])
            i += 1


def already_commented(code: str) -> bool:
    return any(l.strip().startswith(";") for l in code.split("\n"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Show diffs; don't write JSON.")
    ap.add_argument("--task", help="Process just this task_id")
    ap.add_argument("--sample", type=int, default=0,
                    help="Random N solutions to preview (implies --dry-run)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.sample:
        args.dry_run = True

    files = sorted(iter_solution_files())
    if args.task:
        files = [f for f in files if json.loads(f.read_text()).get("task_id") == args.task]
        if not files:
            print(f"no file matches task_id {args.task}", file=sys.stderr); sys.exit(1)
    elif args.sample:
        random.seed(args.seed)
        # Sample only from solutions that have racket but no comments
        candidates = []
        for f in files:
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            code = ((d.get("racket_target") or {}).get("target_code") or
                    (d.get("racket_target") or {}).get("raw_code") or "")
            if code.strip() and not already_commented(code):
                candidates.append(f)
        random.shuffle(candidates)
        files = candidates[: args.sample]

    n_total = 0
    n_skipped_no_code = 0
    n_skipped_already = 0
    n_modified = 0
    n_inserts_total = 0
    n_no_match = 0

    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception as e:
            print(f"skip {f}: {e}", file=sys.stderr); continue
        rt = d.get("racket_target") or {}
        code = rt.get("target_code") or rt.get("raw_code") or ""
        if not code.strip():
            n_skipped_no_code += 1; continue
        n_total += 1
        # Don't skip "already commented" files — comment_solution itself
        # tracks per-line `has_comment_above` and won't double-comment.
        # Skipping the file would leave bindings uncommented when later
        # rule additions or bug fixes would otherwise reach them on a
        # second pass.
        had_comments = already_commented(code)

        desc = (d.get("description_target") or {}).get("target_text") or ""
        new_code, inserts = comment_solution(code, desc)
        if not inserts:
            if had_comments:
                n_skipped_already += 1
            else:
                n_no_match += 1
            continue
        n_modified += 1
        n_inserts_total += len(inserts)

        if args.dry_run:
            print(f"\n=== {d.get('task_id')}  +{len(inserts)} comments ===")
            print(f"DESC: {desc[:200]}")
            print()
            print(new_code)
            print()
        else:
            rt["target_code"] = new_code
            d["racket_target"] = rt
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")

    print()
    print(f"inspected:        {n_total}")
    print(f"already commented: {n_skipped_already}")
    print(f"modified:         {n_modified}  (+{n_inserts_total} comments)")
    print(f"no patterns matched: {n_no_match}")


if __name__ == "__main__":
    main()
