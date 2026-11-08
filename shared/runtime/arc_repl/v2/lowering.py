"""Compiler-owned lexical guards; the protected Racket backend is unchanged.

Only the typed AST enters here. Model code cannot name these helpers: user
binders have already been alpha-normalized, and call heads are allowlisted.
Guards check allocating dimensions BEFORE the backend call, not after OOM.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Mapping

from .sexpr import Node, format_node, parse
from .signatures import Constant, SIGNATURES
from .types import GRID, INTEGER

if TYPE_CHECKING:
    from .compiler import CostLimits


def _call(name: str, *args: str) -> str:
    return "(" + " ".join((name, *args)) + ")"


class _Lowerer:
    def __init__(self, limits: CostLimits, constants: Mapping[tuple[int, int], Constant]):
        self.limits = limits
        self.constants = constants
        self.counter = 0

    def loc(self, node: Node, path: str) -> str:
        return json.dumps(f"at {node.span.line}:{node.span.column} {path}")

    def const(self, node: Node) -> Constant | None:
        return self.constants.get((node.span.start, node.span.end))

    def bind(self, values: list[str], make_body) -> str:
        names = []
        for _ in values:
            names.append(f"__v2_arg_{self.counter}")
            self.counter += 1
        bindings = "(" + " ".join(_call(n, v) for n, v in zip(names, values)) + ")"
        return _call("let*", bindings, make_body(names))

    def lower(self, node: Node, path: str) -> str:
        if node.kind != "list":
            constant = self.const(node) if node.kind == "symbol" else None
            return constant.runtime_value if constant is not None else format_node(node)
        name = node.items[0].text
        args = node.items[1:]
        loc = self.loc(node, path)
        if name == "let*":
            bindings = "(" + " ".join(
                _call(b.items[0].text, self.lower(b.items[1], f"{path}[1][{i}][1]"))
                for i, b in enumerate(args[0].items)
            ) + ")"
            return _call("let*", bindings, self.lower(args[1], f"{path}[2]"))
        if name in {"if", "and", "or", "not"}:
            # Keep conditional and short-circuit evaluation lazy.
            return _call(name, *(self.lower(a, f"{path}[{i}]") for i, a in enumerate(args, 1)))
        if name == "build-grid":
            h, w = (self.lower(args[i], f"{path}[{i+1}]") for i in (0, 1))
            body = self.lower(args[3], f"{path}[4]")
            return self.bind([h, w], lambda n: _call("begin",
                _call("__v2_dims", *n, loc),
                _call("__v2_grid", _call("build-grid", *n, "(r c)", body), loc)))
        if name == "cellmap":
            value = self.lower(args[0], f"{path}[1]")
            body = self.lower(args[2], f"{path}[3]")
            return self.bind([value], lambda n: _call("begin",
                _call("__v2_dims", _call("rows", n[0]), _call("cols", n[0]), loc),
                _call("__v2_grid", _call("cellmap", n[0], "(r c v)", body), loc)))

        sig = SIGNATURES[name]
        enum = sig.lowering.enum_arg
        values = [self.lower(a, f"{path}[{i+1}]") for i, a in enumerate(args) if i != enum]
        if enum is not None:
            resolved = self.const(args[enum])
            assert resolved is not None  # checker records the exact typed choice
            enum_value = resolved.runtime_value
        else:
            enum_value = None

        def emit(n: list[str]) -> str:
            guards: list[str] = [_call("__v2_tick", "1", loc)]
            if name in {"empty-grid"}:
                guards.append(_call("__v2_dims", n[0], n[1], loc))
            elif name in {"scale-up", "scale-down", "tile"}:
                for factor in n[1:]:
                    guards.append(_call("__v2_factor", factor, loc))
                op = "quotient" if name == "scale-down" else "*"
                h = _call(op, _call("rows", n[0]), n[1])
                w = _call(op, _call("cols", n[0]), n[2] if name == "tile" else n[1])
                guards.append(_call("__v2_dims", h, w, loc))
            elif name == "self-tile":
                h, w = _call("rows", n[0]), _call("cols", n[0])
                guards.append(_call("__v2_dims", _call("*", h, h), _call("*", w, w), loc))
            elif name == "concat":
                axis = "H" if enum_value == "hconcat" else "V"
                if enum_value not in {"hconcat", "vconcat"}:
                    raise ValueError("invalid Axis runtime target in registry")
                h1, h2 = _call("rows", n[0]), _call("rows", n[1])
                w1, w2 = _call("cols", n[0]), _call("cols", n[1])
                condition = _call("=", h1, h2) if axis == "H" else _call("=", w1, w2)
                guards.append(_call("__v2_require", condition, '"E_CONCAT_SHAPE"', loc))
                guards.append(_call("__v2_dims", h1 if axis == "H" else _call("+", h1, h2),
                                    _call("+", w1, w2) if axis == "H" else w1, loc))
            elif name == "overlay":
                # Legacy overlay can use a larger top grid, but not a smaller one.
                guards.append(_call("__v2_require", _call("and",
                    _call(">=", _call("rows", n[1]), _call("rows", n[0])),
                    _call(">=", _call("cols", n[1]), _call("cols", n[0]))),
                    '"E_OVERLAY_SHAPE"', loc))
            elif name in {"at", "set-cell", "subgrid"}:
                guards.append(_call("__v2_index", n[0], n[1], n[2], loc))
                if name == "subgrid":
                    guards.append(_call("__v2_index", n[0], n[3], n[4], loc))
                    guards.append(_call("__v2_require", _call("and", _call("<=", n[1], n[3]),
                        _call("<=", n[2], n[4])), '"E_SUBGRID_ORDER"', loc))
            elif name in {"quotient", "mod"}:
                guards.append(_call("__v2_require", _call("not", _call("zero?", n[1])),
                                    '"E_ZERO_DIVISOR"', loc))

            if sig.lowering.kind == "direct":
                value = _call(sig.lowering.target, *n)
            elif sig.lowering.kind == "enum-head":
                if enum_value not in sig.lowering.cases.values():
                    raise ValueError("unregistered enum runtime target")
                value = _call(enum_value, *n)
            elif sig.lowering.kind == "enum-string":
                nargs = list(n)
                nargs.insert(enum, enum_value)
                value = _call(sig.lowering.target, *nargs)
            elif name == "blank-like":
                value = _call("empty-grid", _call("rows", n[0]), _call("cols", n[0]), n[1])
            else:
                raise ValueError(f"unhandled lowering for {name}")
            if sig.result == GRID:
                value = _call("__v2_grid", value, loc)
            elif sig.result == INTEGER:
                value = _call("__v2_integer", value, loc)
            return _call("begin", *guards, value) if guards else value

        # Bind each argument exactly once, left-to-right. Fresh lexical names
        # cannot capture normalized user v0/v1/... or fixed fallback binders.
        return self.bind(values, emit)

    def program(self, body: Node) -> Node:
        lim = self.limits
        # This fixed trusted template is not part of the model-facing language.
        # Every diagnostic is constructed from compiler-owned strings.
        helpers = f'''(
          (__v2_remaining {lim.max_runtime_work})
          (__v2_require (lambda (ok code loc)
            (if ok #t (error (string-append "v2:runtime:" code " " loc)))))
          (__v2_tick (lambda (amount loc)
            (begin
              (set! __v2_remaining (- __v2_remaining amount))
              (__v2_require (>= __v2_remaining 0) "E_WORK_LIMIT" loc))))
          (__v2_dims (lambda (h w loc)
            (begin (__v2_require (and (exact-integer? h) (exact-integer? w)
              (<= 1 h {lim.max_construct_dimension}) (<= 1 w {lim.max_construct_dimension})
              (<= (* h w) {lim.max_grid_cells})) "E_GRID_BOUND" loc)
              (__v2_tick (* h w) loc))))
          (__v2_integer (lambda (x loc)
            (begin (__v2_require (and (exact-integer? x)
              (<= (- {lim.max_runtime_integer_abs}) x {lim.max_runtime_integer_abs}))
              "E_RUNTIME_INTEGER_BOUND" loc) x)))
          (__v2_factor (lambda (x loc)
            (__v2_require (and (exact-integer? x) (<= 1 x {lim.max_scale_or_tile_factor}))
              "E_FACTOR_BOUND" loc)))
          (__v2_grid (lambda (x loc)
            (begin
              (__v2_require (and (list? x) (pair? x) (list? (car x)) (pair? (car x)))
                "E_GRID_VALUE" loc)
              (__v2_dims (length x) (length (car x)) loc)
              (__v2_require (andmap (lambda (row)
                (and (list? row) (= (length row) (length (car x)))
                  (andmap (lambda (v) (and (exact-integer? v) (<= 0 v 9))) row))) x)
                "E_GRID_VALUE" loc) x)))
          (__v2_index (lambda (x r c loc)
            (__v2_require (and (<= 0 r) (< r (rows x)) (<= 0 c) (< c (cols x)))
              "E_INDEX_BOUND" loc)))
          (input (__v2_grid g "at 1:1 $input")))'''
        return parse(_call("rule!", _call("let*", helpers, self.lower(body, "$[1]"))),
                     max_depth=512, max_nodes=lim.max_nodes * 32 + 512,
                     max_source_chars=lim.max_source_chars * 32 + 10_000)


def lower_guarded(body: Node, limits: CostLimits,
                  constants: Mapping[tuple[int, int], Constant]) -> Node:
    return _Lowerer(limits, constants).program(body)
