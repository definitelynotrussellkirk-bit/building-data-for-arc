#!/usr/bin/env python3
"""
Mine primitive usage from grounded Racket rules.

The output is meant to feed generator work: each task gets a primitive chain,
family tags, and call counts that can be used for retrieval, mixing, and
generator scaffolds.

Examples:
    python scripts/mine_primitive_usage.py --top 40
    python scripts/mine_primitive_usage.py --task-id 0607ce86
    python scripts/mine_primitive_usage.py --write-jsonl tmp/primitive_usage.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from solvers.grounded_rules import GROUNDED_RULES  # noqa: E402
from src.core.data_loader import load_challenges  # noqa: E402


SPECIAL_FORMS = {
    "and",
    "begin",
    "case",
    "cond",
    "define",
    "else",
    "for",
    "for*",
    "if",
    "lambda",
    "let",
    "let*",
    "let-values",
    "letrec",
    "or",
    "quote",
    "set!",
    "when",
    "unless",
    "rule!",
}

LOW_SIGNAL_CALLS = {
    "+",
    "-",
    "*",
    "/",
    "=",
    "!=",
    "<",
    ">",
    "<=",
    ">=",
    "not",
    "abs",
    "add1",
    "cdr",
    "car",
    "last",
    "cons",
    "list",
    "list-ref",
    "make-list",
    "sort",
    "reverse",
    "append",
    "append*",
    "rest",
    "take",
    "empty?",
    "null?",
    "length",
    "member",
    "member?",
    "remove-duplicates",
    "equal?",
    "eq?",
    "mod",
    "modulo",
    "odd?",
    "even?",
    "zero?",
    "remainder",
    "quotient",
    "floor",
    "ceiling",
    "round",
    "min",
    "max",
    "apply",
    "make-hash",
    "mutable-set",
    "set",
    "set-add!",
    "set-member?",
    "hash-set!",
    "hash-update!",
    "hash-ref",
    "hash-has-key?",
    "hash-keys",
    "hash-values",
    "in-list",
    "in-range",
    "in-naturals",
    "format",
    "string>?",
    "string<?",
    # Loop binding names can appear as call heads in for-clause syntax.
    "r",
    "c",
    "p",
    "q",
    "d",
    "nr",
    "nc",
}


@dataclass(frozen=True)
class PrimitiveFamily:
    name: str
    description: str
    generator_role: str


FAMILIES: dict[str, PrimitiveFamily] = {
    "grid_construction": PrimitiveFamily(
        "grid_construction",
        "Build or modify grids cell by cell.",
        "Create outputs, initialize canvases, paste generated motifs.",
    ),
    "cell_access": PrimitiveFamily(
        "cell_access",
        "Read grid dimensions, positions, and cell values.",
        "Parameterize generators by size, anchor positions, and local neighborhoods.",
    ),
    "iteration": PrimitiveFamily(
        "iteration",
        "Map, filter, fold, count, and enumerate candidate spaces.",
        "Sample candidates, score them, and assemble outputs from parts.",
    ),
    "color": PrimitiveFamily(
        "color",
        "Discover, count, rank, and remap colors.",
        "Vary palettes, role colors, key colors, and distractor colors.",
    ),
    "object": PrimitiveFamily(
        "object",
        "Find connected components and object properties.",
        "Generate object-centric puzzles with count, size, bbox, and color controls.",
    ),
    "geometry": PrimitiveFamily(
        "geometry",
        "Crop, paste, transform, align, ray, path, and bbox geometry.",
        "Mutate placements, axes, symmetries, paths, and spatial relations.",
    ),
    "topology": PrimitiveFamily(
        "topology",
        "Reason about holes, enclosed regions, borders, and connectivity.",
        "Generate frame, containment, fill, and inside/outside puzzles.",
    ),
    "pattern": PrimitiveFamily(
        "pattern",
        "Detect periodic, tiled, ranked, or repeated patterns.",
        "Create denoising, extrapolation, compression, and repeated-template puzzles.",
    ),
    "selection": PrimitiveFamily(
        "selection",
        "Choose first, best, unique, nearest, largest, smallest, or ranked candidates.",
        "Add ambiguity controls and distractors while keeping one intended solution.",
    ),
    "encoding": PrimitiveFamily(
        "encoding",
        "Turn counts or classifications into small output grids.",
        "Build summary, bar, indicator, and class-label outputs.",
    ),
    "functional": PrimitiveFamily(
        "functional",
        "Compose local helper functions and higher-order operations.",
        "Express generated programs compactly and make primitive chains composable.",
    ),
    "unknown": PrimitiveFamily(
        "unknown",
        "Calls not yet assigned to a primitive family.",
        "Candidates for catalog cleanup or future primitive extraction.",
    ),
}


NAME_TO_FAMILY: dict[str, str] = {
    # Grid construction.
    "grid-from-fn": "grid_construction",
    "cellmap": "grid_construction",
    "build-grid": "grid_construction",
    "empty-grid": "grid_construction",
    "set-cell": "grid_construction",
    "map-grid": "grid_construction",
    "overlay": "grid_construction",
    "overlay-all": "grid_construction",
    "paint-cells": "grid_construction",
    "erase-cells": "grid_construction",
    "paste": "grid_construction",
    "clear-cells": "grid_construction",
    "keep-only": "selection",
    # Cell access and positions.
    "rows": "cell_access",
    "cols": "cell_access",
    "cell-at": "cell_access",
    "at": "cell_access",
    "fst": "cell_access",
    "snd": "cell_access",
    "first": "cell_access",
    "second": "cell_access",
    "third": "cell_access",
    "fourth": "cell_access",
    "nth": "cell_access",
    "in-bounds?": "cell_access",
    "pos-in-bounds?": "cell_access",
    "pos-manhattan": "cell_access",
    "grid-positions": "cell_access",
    "grid-cells": "cell_access",
    "filter-cells": "cell_access",
    "row": "cell_access",
    "col": "cell_access",
    "row-at": "cell_access",
    "col-at": "cell_access",
    "row-count": "cell_access",
    "col-count": "cell_access",
    "cell-up": "cell_access",
    "cell-down": "cell_access",
    "cell-left": "cell_access",
    "cell-right": "cell_access",
    "safe-at": "cell_access",
    # Iteration / scoring.
    "map": "iteration",
    "filter": "iteration",
    "reduce": "iteration",
    "foldl": "iteration",
    "foldr": "iteration",
    "fold-cells": "iteration",
    "flatmap": "iteration",
    "flat-map": "iteration",
    "range": "iteration",
    "zip-lists": "iteration",
    "enumerate-list": "iteration",
    "pairs": "iteration",
    "count": "iteration",
    "count-where": "iteration",
    "for/list": "iteration",
    "for*/list": "iteration",
    "for/sum": "iteration",
    "for/or": "iteration",
    "for/and": "iteration",
    "for*/sum": "iteration",
    "for*/or": "iteration",
    "for*/and": "iteration",
    "for/fold": "iteration",
    "for*/fold": "iteration",
    "any?": "iteration",
    "all?": "iteration",
    # Color.
    "colors": "color",
    "grid-colors": "color",
    "color-frequency": "color",
    "find-color": "color",
    "mode": "color",
    "minority": "color",
    "mode-list": "color",
    "row-mode": "color",
    "col-mode": "color",
    "recolor-map*": "color",
    "recolor-by-rank": "color",
    "recolor-by-nearest-marker": "color",
    "color-majority": "color",
    "color-filter": "color",
    "not-color-filter": "color",
    "const-target": "color",
    "count-color": "color",
    "color-shift": "color",
    # Objects.
    "objects": "object",
    "objects-8": "object",
    "objects-multicolor": "object",
    "largest-object": "object",
    "smallest-object": "object",
    "obj-cells": "object",
    "obj-color": "object",
    "obj-size": "object",
    "obj-bbox": "object",
    "obj-rs": "object",
    "obj-cs": "object",
    "obj-row-range": "object",
    "obj-col-range": "object",
    "obj-r1": "object",
    "obj-c1": "object",
    "obj-r2": "object",
    "obj-c2": "object",
    "obj-h": "object",
    "obj-w": "object",
    "object-at": "object",
    "filter-objects": "object",
    "object-translate": "object",
    "object-paint": "object",
    "object-erase": "object",
    "object-cells-set": "object",
    "object-intersect": "object",
    "object-grow": "object",
    "object-shrink": "object",
    # Geometry.
    "subgrid": "geometry",
    "crop": "geometry",
    "crop-object": "geometry",
    "crop-to-content": "geometry",
    "normalize-cells": "geometry",
    "rotate-cells-cw": "geometry",
    "flip-cells-lr": "geometry",
    "all-transforms": "geometry",
    "stamp-normalized-cells": "geometry",
    "flip-lr": "geometry",
    "flip-ud": "geometry",
    "rotate-cw": "geometry",
    "rotate-ccw": "geometry",
    "transpose": "geometry",
    "draw-line": "geometry",
    "ray": "geometry",
    "shortest-path-fill": "geometry",
    "shift": "geometry",
    "tile": "geometry",
    "stack-objects-right": "geometry",
    "assemble-at": "geometry",
    "kaleidoscope": "geometry",
    "center-of-mass": "geometry",
    "gravitate": "geometry",
    "move-to-wall": "geometry",
    "smear-color": "geometry",
    "bbox-of-cells": "geometry",
    "positions-in-rect": "geometry",
    "top-half": "geometry",
    "bottom-half": "geometry",
    "left-half": "geometry",
    "right-half": "geometry",
    "hconcat": "geometry",
    "vconcat": "geometry",
    "stack-grids": "geometry",
    "diagonal": "geometry",
    "anti-diagonal": "geometry",
    "pad-grid": "geometry",
    "pad-grid-asym": "geometry",
    "draw-rect-filled": "geometry",
    "draw-rect-outline": "geometry",
    "draw-cross": "geometry",
    "draw-x-shape": "geometry",
    "draw-border": "geometry",
    "phys-raycast": "geometry",
    "phys-distance": "geometry",
    "phys-has-los?": "geometry",
    "phys-bounce-ray": "geometry",
    # Topology.
    "find-0-regions": "topology",
    "enclosed?": "topology",
    "fill-all-enclosed": "topology",
    "recolor-enclosing-objects": "topology",
    "holey-object-cells": "topology",
    "hollow-objects": "topology",
    "obj-contact": "topology",
    "fill-enclosed": "topology",
    "obj-boundary-cells": "topology",
    "obj-interior-cells": "topology",
    "obj-neighbor-cells": "topology",
    "obj-delta": "topology",
    "square?": "topology",
    "vline?": "topology",
    "hline?": "topology",
    "bordering?": "topology",
    "hmatching?": "topology",
    "vmatching?": "topology",
    "above-of?": "topology",
    "below-of?": "topology",
    "left-of?": "topology",
    "right-of?": "topology",
    "filled?": "topology",
    "hollow?": "topology",
    "same-shape?": "topology",
    "topo-count-holes": "topology",
    "topo-rectangle?": "topology",
    "topo-corners": "topology",
    # Pattern.
    "detect-translational-period": "pattern",
    "detect-mirror-symmetry": "pattern",
    "detect-rotational-symmetry": "pattern",
    "compress-grid": "pattern",
    "count-blocks": "pattern",
    "fill-frame-interiors": "pattern",
    "stamp-grid": "pattern",
    "self-tile": "pattern",
    "unique-rows": "pattern",
    "unique-cols": "pattern",
    "grid-hash": "pattern",
    "shape-hash": "pattern",
    "diff-positions": "pattern",
    "diff-recolor-map": "pattern",
    "diff-translation": "pattern",
    # Selection.
    "find": "selection",
    "find-first": "selection",
    "argmin": "selection",
    "argmax": "selection",
    "sort-by": "selection",
    "unique": "selection",
    "min-list": "selection",
    "max-list": "selection",
    "mean-list": "selection",
    "pick-max": "selection",
    "pick-min": "selection",
    "pick-unique": "selection",
    "cluster-by": "selection",
    "cluster-by-color": "selection",
    "cluster-by-size": "selection",
    "cluster-aligned-row": "selection",
    "cluster-aligned-col": "selection",
    # Encoding.
    "encode-bar": "encoding",
    "encode-grid": "encoding",
    "list->grid": "encoding",
    # Functional.
    "pipe": "functional",
    "compose": "functional",
    "identity": "functional",
}


def strip_comments_and_strings(source: str) -> str:
    """Remove Racket comments and string literals without changing paren shape."""
    out: list[str] = []
    i = 0
    in_string = False
    while i < len(source):
        ch = source[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == ";":
            while i < len(source) and source[i] != "\n":
                i += 1
            out.append("\n")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


SExpr = str | list["SExpr"]


def tokenize_racket(source: str) -> list[str]:
    """Tokenize enough Racket syntax for primitive-call mining."""
    src = strip_comments_and_strings(source)
    tokens: list[str] = []
    i = 0
    while i < len(src):
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "([":
            tokens.append("(")
            i += 1
            continue
        if ch in ")]":
            tokens.append(")")
            i += 1
            continue
        if ch in "{}":
            i += 1
            continue
        start = i
        while i < len(src) and not src[i].isspace() and src[i] not in "()[]{}":
            i += 1
        tokens.append(src[start:i])
    return tokens


def parse_sexprs(tokens: list[str]) -> list[SExpr]:
    """Parse tokens into a lightweight S-expression tree."""
    def parse_one(index: int) -> tuple[SExpr, int]:
        if tokens[index] != "(":
            return tokens[index], index + 1

        expr: list[SExpr] = []
        index += 1
        while index < len(tokens) and tokens[index] != ")":
            child, index = parse_one(index)
            expr.append(child)
        if index < len(tokens) and tokens[index] == ")":
            index += 1
        return expr, index

    exprs: list[SExpr] = []
    i = 0
    while i < len(tokens):
        if tokens[i] == ")":
            i += 1
            continue
        expr, i = parse_one(i)
        exprs.append(expr)
    return exprs


FOR_FORMS = {
    "for/list",
    "for*/list",
    "for/sum",
    "for/or",
    "for/and",
    "for*/sum",
    "for*/or",
    "for*/and",
    "for/fold",
    "for*/fold",
}


# These DSL forms bind the names in one positional parameter list.  That list
# is syntax, not an application: for example, ``(build-grid 3 3 (r c) ...)``
# must not report a call to ``r``.  Keep this aligned with the binding-macro
# handling in scripts/dsl_grammar.py.
BINDING_MACRO_PARAMETER_INDEX = {
    "with-bbox": 2,
    "build-grid": 3,
    "cellmap": 2,
}


def call_heads(source: str) -> list[str]:
    """Return call heads while skipping binding names."""
    calls: list[str] = []

    def walk_binding_clauses(bindings: SExpr) -> None:
        if not isinstance(bindings, list):
            return
        if bindings and isinstance(bindings[0], str):
            for init_expr in bindings[1:]:
                walk(init_expr)
            return
        for clause in bindings:
            if isinstance(clause, list) and clause and isinstance(clause[0], str):
                for init_expr in clause[1:]:
                    walk(init_expr)
            else:
                walk(clause)

    def walk(expr: SExpr) -> None:
        if not isinstance(expr, list) or not expr:
            return
        head = expr[0] if isinstance(expr[0], str) else None

        if head in {"quote", "quasiquote", "unquote", "unquote-splicing"}:
            return

        if head in {"let", "let*", "letrec"}:
            binding_index = 1
            if len(expr) > 2 and isinstance(expr[1], str):
                binding_index = 2
            if binding_index < len(expr):
                walk_binding_clauses(expr[binding_index])
            for body_expr in expr[binding_index + 1:]:
                walk(body_expr)
            return

        if head == "define":
            for body_expr in expr[2:]:
                walk(body_expr)
            return

        if head == "lambda":
            for body_expr in expr[2:]:
                walk(body_expr)
            return

        if head in FOR_FORMS:
            calls.append(head)
            if len(expr) > 1:
                walk_binding_clauses(expr[1])
            body_start = 2
            if head in {"for/fold", "for*/fold"} and len(expr) > 2:
                walk_binding_clauses(expr[2])
                body_start = 3
            for body_expr in expr[body_start:]:
                walk(body_expr)
            return

        if head in BINDING_MACRO_PARAMETER_INDEX:
            calls.append(head)
            parameter_index = BINDING_MACRO_PARAMETER_INDEX[head]
            for index, arg in enumerate(expr[1:], start=1):
                if index != parameter_index:
                    walk(arg)
            return

        if head == "cond":
            # A cond clause is syntax shaped like (test body ...), not an
            # application of its test.  Bare variable tests such as
            # ``(same-row (list 0 1))`` must therefore not become call heads.
            for clause in expr[1:]:
                if not isinstance(clause, list) or not clause:
                    walk(clause)
                    continue
                test = clause[0]
                if isinstance(test, list):
                    walk(test)
                body = clause[1:]
                if body and body[0] == "=>":
                    body = body[1:]
                for body_expr in body:
                    walk(body_expr)
            return

        if head in SPECIAL_FORMS:
            for arg in expr[1:]:
                walk(arg)
            return

        if head:
            calls.append(head)
        for arg in expr[1:]:
            walk(arg)

    for expr in parse_sexprs(tokenize_racket(source)):
        walk(expr)
    return calls


def classify(name: str) -> str:
    """Classify a call head into a primitive family."""
    if name in NAME_TO_FAMILY:
        return NAME_TO_FAMILY[name]
    if name.startswith("obj-") or name.startswith("objects"):
        return "object"
    if "color" in name or "recolor" in name:
        return "color"
    if "bbox" in name or "crop" in name or "rotate" in name or "flip" in name:
        return "geometry"
    if "region" in name or "enclos" in name or "hole" in name:
        return "topology"
    if "period" in name or "tile" in name or "pattern" in name:
        return "pattern"
    if name.startswith("for/") or name.startswith("for*/"):
        return "iteration"
    return "unknown"


def useful_calls(source: str, include_unknown: bool = False) -> list[str]:
    """Extract useful primitive-ish calls from one rule."""
    result: list[str] = []
    for name in call_heads(source):
        if name in SPECIAL_FORMS or name in LOW_SIGNAL_CALLS:
            continue
        if name.startswith("'") or name.startswith("#"):
            continue
        if not include_unknown and classify(name) == "unknown":
            continue
        result.append(name)
    return result


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def local_defined_functions(source: str) -> set[str]:
    names = set(re.findall(r"\(define\s+\(([^()\s]+)", source))
    names.update(re.findall(r"\(let\s+([^()\s]+)\s+\(", source))
    return names


def summarize_task(task_id: str, rule_text: str, include_unknown: bool = False) -> dict:
    local_defs = local_defined_functions(rule_text)
    calls = [
        name
        for name in useful_calls(rule_text, include_unknown=include_unknown)
        if name not in local_defs
    ]
    call_counts = Counter(calls)
    family_counts = Counter(classify(name) for name in calls)
    family_chain = unique_in_order(classify(name) for name in calls)
    return {
        "task_id": task_id,
        "primitive_chain": unique_in_order(calls),
        "family_chain": family_chain,
        "families": [
            {"family": family, "count": count}
            for family, count in family_counts.most_common()
        ],
        "call_counts": dict(call_counts.most_common()),
    }


def markdown_summary(
    task_summaries: list[dict],
    primitive_counts: Counter[str],
    family_counts: Counter[str],
    primitive_to_tasks: dict[str, set[str]],
    family_to_tasks: dict[str, set[str]],
    top: int,
) -> str:
    lines = [
        "# Primitive Usage Summary",
        "",
        f"Grounded rules analyzed: {len(task_summaries)}",
        "",
        "## Top Primitive Families",
        "",
        "| Family | Calls | Tasks | Generator role |",
        "|---|---:|---:|---|",
    ]
    for family, count in family_counts.most_common():
        role = FAMILIES.get(family, FAMILIES["unknown"]).generator_role
        task_count = len(family_to_tasks[family])
        lines.append(f"| `{family}` | {count} | {task_count} | {role} |")

    lines.extend([
        "",
        "## Top Primitive Calls",
        "",
        "| Primitive | Calls | Tasks | Family |",
        "|---|---:|---:|---|",
    ])
    for name, count in primitive_counts.most_common(top):
        task_count = len(primitive_to_tasks[name])
        lines.append(f"| `{name}` | {count} | {task_count} | `{classify(name)}` |")

    lines.extend([
        "",
        "## Task Records",
        "",
        "Each JSONL record from `--write-jsonl` has:",
        "",
        "- `task_id`",
        "- `primitive_chain`: unique primitive calls in first-use order",
        "- `family_chain`: unique primitive families in first-use order",
        "- `families`: primitive family counts",
        "- `call_counts`: raw primitive call counts",
        "",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine primitive usage from solvers/grounded_rules.py."
    )
    parser.add_argument("--top", type=int, default=40, help="Number of primitive rows to print.")
    parser.add_argument("--task-id", help="Print one task's primitive record.")
    parser.add_argument(
        "--include-unknown",
        action="store_true",
        help="Include unclassified local helper calls in task records.",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--training-only",
        action="store_true",
        default=True,
        help="Only analyze rules whose IDs are in the training challenges. This is the default.",
    )
    scope.add_argument(
        "--all-grounded",
        action="store_true",
        help="Analyze every ID in GROUNDED_RULES, including non-training entries.",
    )
    parser.add_argument("--write-jsonl", type=Path, help="Write per-task primitive records.")
    parser.add_argument("--write-markdown", type=Path, help="Write a Markdown summary.")
    args = parser.parse_args()

    task_ids = set(GROUNDED_RULES)
    if args.training_only and not args.all_grounded:
        task_ids &= set(load_challenges("training"))

    task_summaries = [
        summarize_task(tid, GROUNDED_RULES[tid], include_unknown=args.include_unknown)
        for tid in sorted(task_ids)
    ]

    primitive_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    family_to_tasks: dict[str, set[str]] = defaultdict(set)
    primitive_to_tasks: dict[str, set[str]] = defaultdict(set)
    for summary in task_summaries:
        tid = summary["task_id"]
        primitive_counts.update(summary["call_counts"])
        for item in summary["families"]:
            family_counts[item["family"]] += item["count"]
            family_to_tasks[item["family"]].add(tid)
        for name in summary["primitive_chain"]:
            primitive_to_tasks[name].add(tid)

    if args.task_id:
        if args.task_id not in GROUNDED_RULES:
            print(f"ERROR: unknown grounded task id: {args.task_id}", file=sys.stderr)
            return 1
        print(json.dumps(
            summarize_task(args.task_id, GROUNDED_RULES[args.task_id], args.include_unknown),
            indent=2,
            sort_keys=True,
        ))
        return 0

    print(f"Grounded rules analyzed: {len(task_summaries)}")
    print("\nTop primitive families:")
    for family, count in family_counts.most_common():
        print(f"  {family:<18} {count:>5} calls  {len(family_to_tasks[family]):>4} tasks")

    print(f"\nTop {args.top} primitive calls:")
    for name, count in primitive_counts.most_common(args.top):
        print(f"  {name:<28} {count:>5} calls  {len(primitive_to_tasks[name]):>4} tasks  {classify(name)}")

    if args.write_jsonl:
        args.write_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.write_jsonl.open("w") as f:
            for summary in task_summaries:
                f.write(json.dumps(summary, sort_keys=True) + "\n")
        print(f"\nWrote {args.write_jsonl}")

    if args.write_markdown:
        args.write_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.write_markdown.write_text(
            markdown_summary(
                task_summaries,
                primitive_counts,
                family_counts,
                primitive_to_tasks,
                family_to_tasks,
                args.top,
            )
        )
        print(f"Wrote {args.write_markdown}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
