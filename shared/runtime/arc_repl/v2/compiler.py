"""Typed ARC-Racket v2 core compiler.

The compiler is intentionally additive: it emits ordinary ``(rule! ...)``
source for the existing protected evaluator and does not modify that evaluator.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping

from .sexpr import Node, SExprSyntaxError, Span, format_node, list_node, parse, string, symbol
from .signatures import CONSTANTS, LEGACY_ALIASES, RESERVED_BINDERS, SIGNATURES, Constant, Signature
from .version import LANGUAGE_VERSION
from .lowering import lower_guarded
from .types import AXIS, BOOLEAN, COLOR, DIRECTION, GRID, INTEGER, REFLECTION, ROTATION, V2Type


_LITERAL_ENUM_TYPES = frozenset({DIRECTION, REFLECTION, ROTATION, AXIS})


@dataclass(frozen=True, slots=True)
class CostLimits:
    max_nodes: int = 512
    max_depth: int = 40
    max_integer_abs: int = 256
    max_scale_or_tile_factor: int = 16
    max_construct_dimension: int = 64
    max_source_chars: int = 65_536
    max_grid_cells: int = 4096
    max_runtime_integer_abs: int = 1_000_000
    max_runtime_work: int = 1_000_000

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        # Downstream typed AST visitors are recursive; never allow a caller to
        # configure a reader depth beyond their tested Python stack envelope.
        if self.max_depth > 128:
            raise ValueError("max_depth cannot exceed the implementation ceiling 128")
        if self.max_integer_abs > self.max_runtime_integer_abs:
            raise ValueError("literal bound must not exceed runtime integer bound")
        if self.max_construct_dimension > self.max_runtime_integer_abs:
            raise ValueError("dimension bound must not exceed runtime integer bound")
        if self.max_scale_or_tile_factor > self.max_runtime_integer_abs:
            raise ValueError("factor bound must not exceed runtime integer bound")


@dataclass(frozen=True, slots=True)
class SourceMapEntry:
    path: str
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True, slots=True)
class CompilationResult:
    version: str
    canonical_source: str
    racket_source: str
    result_type: V2Type
    ast_nodes: int
    ast_depth: int
    canonical_sha256: str
    primitive_heads: tuple[str, ...]
    limits_sha256: str
    compiled_sha256: str
    source_map: tuple[SourceMapEntry, ...]


class V2CompileError(ValueError):
    """Localized compiler failure with stable phase/code fields."""

    def __init__(
        self,
        phase: str,
        code: str,
        message: str,
        *,
        span: Span | None = None,
        path: str = "$",
    ):
        super().__init__(message)
        self.phase = phase
        self.code = code
        self.message = message
        self.span = span or Span.synthetic()
        self.path = path

    def __str__(self) -> str:
        return (
            f"{self.phase}:{self.code} at "
            f"{self.span.line}:{self.span.column} {self.path}: {self.message}"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "line": self.span.line,
            "column": self.span.column,
        }


def _is_symbol(node: Node, name: str | None = None) -> bool:
    return node.kind == "symbol" and (name is None or node.text == name)


def _head(node: Node) -> str | None:
    if node.kind == "list" and node.items and node.items[0].kind == "symbol":
        return node.items[0].text
    return None


def _measure(node: Node) -> tuple[int, int]:
    if node.kind != "list":
        return 1, 1
    if not node.items:
        return 1, 1
    measured = [_measure(item) for item in node.items]
    return 1 + sum(count for count, _ in measured), 1 + max(depth for _, depth in measured)


def _type_error(node: Node, expected: V2Type, actual: V2Type, path: str) -> V2CompileError:
    return V2CompileError(
        "type",
        "E_TYPE_MISMATCH",
        f"expected {expected}, found {actual}",
        span=node.span,
        path=path,
    )


class _Checker:
    def __init__(self, limits: CostLimits):
        self.limits = limits
        self.primitive_heads: set[str] = set()
        self.resolved_constants: dict[tuple[int, int], Constant] = {}

    def check_root(self, root: Node) -> tuple[Node, V2Type]:
        if root.kind != "list" or len(root.items) != 2 or not _is_symbol(root.items[0], "rule!"):
            raise V2CompileError(
                "syntax",
                "E_RULE_WRAPPER",
                "canonical source is exactly (rule! BODY)",
                span=root.span,
            )
        body = root.items[1]
        result = self.check(body, {"input": GRID}, expected=GRID, path="$[1]")
        if result != GRID:
            raise _type_error(body, GRID, result, "$[1]")
        return body, result

    def _resolve_constant(self, node: Node, expected: V2Type | None, path: str) -> Constant | None:
        choices = CONSTANTS.get(node.text, ())
        if not choices:
            return None
        if expected is not None:
            matches = [item for item in choices if item.type == expected]
            if len(matches) == 1:
                self.resolved_constants[(node.span.start, node.span.end)] = matches[0]
                return matches[0]
            if not matches:
                available = ", ".join(sorted({str(item.type) for item in choices}))
                raise V2CompileError(
                    "type",
                    "E_CONSTANT_TYPE",
                    f"constant {node.text} has type {available}, not {expected}",
                    span=node.span,
                    path=path,
                )
        if len(choices) == 1:
            self.resolved_constants[(node.span.start, node.span.end)] = choices[0]
            return choices[0]
        raise V2CompileError(
            "type",
            "E_AMBIGUOUS_CONSTANT",
            f"constant {node.text} needs an expected type",
            span=node.span,
            path=path,
        )

    def check(
        self,
        node: Node,
        env: Mapping[str, V2Type],
        *,
        expected: V2Type | None = None,
        path: str,
    ) -> V2Type:
        if node.kind == "integer":
            value = int(node.value)
            if abs(value) > self.limits.max_integer_abs:
                raise V2CompileError(
                    "cost",
                    "E_INTEGER_BOUND",
                    f"integer literal {value} exceeds ±{self.limits.max_integer_abs}",
                    span=node.span,
                    path=path,
                )
            actual = INTEGER
            if expected is not None and expected != actual:
                raise _type_error(node, expected, actual, path)
            return actual
        if node.kind == "boolean":
            if expected is not None and expected != BOOLEAN:
                raise _type_error(node, expected, BOOLEAN, path)
            return BOOLEAN
        if node.kind == "float":
            raise V2CompileError(
                "type",
                "E_FLOAT_FORBIDDEN",
                "the v2 core has no floating-point type",
                span=node.span,
                path=path,
            )
        if node.kind == "string":
            raise V2CompileError(
                "type",
                "E_STRING_FORBIDDEN",
                "model-facing v2 uses typed constants instead of strings",
                span=node.span,
                path=path,
            )
        if node.kind == "symbol":
            if node.text in env:
                actual = env[node.text]
                if expected is not None and expected != actual:
                    raise _type_error(node, expected, actual, path)
                return actual
            constant = self._resolve_constant(node, expected, path)
            if constant is not None:
                return constant.type
            if node.text in SIGNATURES:
                raise V2CompileError(
                    "type",
                    "E_FUNCTION_AS_VALUE",
                    f"primitive {node.text} is not first-class in core 0.1",
                    span=node.span,
                    path=path,
                )
            raise V2CompileError(
                "scope",
                "E_UNBOUND_NAME",
                f"unbound identifier {node.text}",
                span=node.span,
                path=path,
            )
        if node.kind != "list" or not node.items:
            raise V2CompileError(
                "syntax",
                "E_EMPTY_APPLICATION",
                "empty lists are outside the v2 expression core",
                span=node.span,
                path=path,
            )
        if node.items[0].kind != "symbol":
            raise V2CompileError(
                "syntax",
                "E_NON_SYMBOL_HEAD",
                "call head must be a model-facing primitive or special form",
                span=node.items[0].span,
                path=f"{path}[0]",
            )
        name = node.items[0].text
        args = node.items[1:]

        if name == "let*":
            if len(args) != 2:
                raise self._arity(node, name, 2, len(args), path)
            bindings, body = args
            if bindings.kind != "list":
                raise V2CompileError("syntax", "E_BINDINGS_SHAPE", "let* bindings must be a list", span=bindings.span, path=f"{path}[1]")
            local = dict(env)
            for index, binding in enumerate(bindings.items):
                bpath = f"{path}[1][{index}]"
                if binding.kind != "list" or len(binding.items) != 2 or binding.items[0].kind != "symbol":
                    raise V2CompileError("syntax", "E_BINDING_SHAPE", "each let* binding is (name expression)", span=binding.span, path=bpath)
                binder = binding.items[0]
                if binder.text in RESERVED_BINDERS:
                    raise V2CompileError("scope", "E_RESERVED_BINDER", f"binder {binder.text} is reserved", span=binder.span, path=f"{bpath}[0]")
                if binder.text in local:
                    raise V2CompileError("scope", "E_BINDER_REUSE", f"binder {binder.text} duplicates or shadows an existing name", span=binder.span, path=f"{bpath}[0]")
                value_type = self.check(binding.items[1], local, path=f"{bpath}[1]")
                local[binder.text] = value_type
            return self.check(body, local, expected=expected, path=f"{path}[2]")

        if name == "if":
            if len(args) != 3:
                raise self._arity(node, name, 3, len(args), path)
            self.check(args[0], env, expected=BOOLEAN, path=f"{path}[1]")
            left = self.check(args[1], env, expected=expected, path=f"{path}[2]")
            right = self.check(args[2], env, expected=expected or left, path=f"{path}[3]")
            if left != right:
                raise V2CompileError("type", "E_BRANCH_TYPE", f"if branches differ: {left} versus {right}", span=node.span, path=path)
            return left

        if name in {"and", "or"}:
            if len(args) != 2:
                raise self._arity(node, name, 2, len(args), path)
            for index, arg in enumerate(args, start=1):
                self.check(arg, env, expected=BOOLEAN, path=f"{path}[{index}]")
            if expected is not None and expected != BOOLEAN:
                raise _type_error(node, expected, BOOLEAN, path)
            return BOOLEAN

        if name == "not":
            if len(args) != 1:
                raise self._arity(node, name, 1, len(args), path)
            self.check(args[0], env, expected=BOOLEAN, path=f"{path}[1]")
            if expected is not None and expected != BOOLEAN:
                raise _type_error(node, expected, BOOLEAN, path)
            return BOOLEAN

        if name == "build-grid":
            if len(args) != 4:
                raise self._arity(node, name, 4, len(args), path)
            self.check(args[0], env, expected=INTEGER, path=f"{path}[1]")
            self.check(args[1], env, expected=INTEGER, path=f"{path}[2]")
            binders = args[2]
            if binders.kind != "list" or [item.text if item.kind == "symbol" else None for item in binders.items] != ["r", "c"]:
                raise V2CompileError("syntax", "E_BUILD_BINDERS", "build-grid binders are exactly (r c)", span=binders.span, path=f"{path}[3]")
            local = dict(env)
            local.update({"r": INTEGER, "c": INTEGER})
            self.check(args[3], local, expected=COLOR, path=f"{path}[4]")
            for index, dimension in enumerate(args[:2], start=1):
                if dimension.kind == "integer" and not 1 <= int(dimension.value) <= self.limits.max_construct_dimension:
                    raise V2CompileError(
                        "cost",
                        "E_CONSTRUCT_DIMENSION",
                        f"literal output dimension must be 1 through {self.limits.max_construct_dimension}",
                        span=dimension.span,
                        path=f"{path}[{index}]",
                    )
            if expected is not None and expected != GRID:
                raise _type_error(node, expected, GRID, path)
            self.primitive_heads.add(name)
            return GRID

        if name == "cellmap":
            if len(args) != 3:
                raise self._arity(node, name, 3, len(args), path)
            self.check(args[0], env, expected=GRID, path=f"{path}[1]")
            binders = args[1]
            if binders.kind != "list" or [item.text if item.kind == "symbol" else None for item in binders.items] != ["r", "c", "v"]:
                raise V2CompileError("syntax", "E_CELLMAP_BINDERS", "cellmap binders are exactly (r c v)", span=binders.span, path=f"{path}[2]")
            local = dict(env)
            local.update({"r": INTEGER, "c": INTEGER, "v": COLOR})
            self.check(args[2], local, expected=COLOR, path=f"{path}[3]")
            if expected is not None and expected != GRID:
                raise _type_error(node, expected, GRID, path)
            self.primitive_heads.add(name)
            return GRID

        signature = SIGNATURES.get(name)
        if signature is None:
            if name in LEGACY_ALIASES:
                message = f"legacy operation {name} is not model-facing; use {LEGACY_ALIASES[name]}"
            else:
                message = f"operation {name} is outside the approved v2 core"
            raise V2CompileError("safety", "E_FORBIDDEN_OPERATION", message, span=node.items[0].span, path=f"{path}[0]")
        if len(args) != signature.arity:
            raise self._arity(node, name, signature.arity, len(args), path)
        for index, (arg, param_type) in enumerate(zip(args, signature.params), start=1):
            if param_type in _LITERAL_ENUM_TYPES:
                if arg.kind != "symbol" or arg.text not in CONSTANTS:
                    raise V2CompileError(
                        "type",
                        "E_ENUM_LITERAL_REQUIRED",
                        f"{param_type} arguments must be an explicit typed constant",
                        span=arg.span,
                        path=f"{path}[{index}]",
                    )
            self.check(arg, env, expected=param_type, path=f"{path}[{index}]")
        if expected is not None and expected != signature.result:
            raise _type_error(node, expected, signature.result, path)
        if name in {"scale-up", "scale-down"} and args[1].kind == "integer":
            factor = int(args[1].value)
            if factor < 1:
                raise V2CompileError("cost", "E_FACTOR_POSITIVE", "scale factor must be positive", span=args[1].span, path=f"{path}[2]")
            if factor > self.limits.max_scale_or_tile_factor:
                raise V2CompileError("cost", "E_SCALE_BOUND", f"factor exceeds {self.limits.max_scale_or_tile_factor}", span=args[1].span, path=f"{path}[2]")
        if name == "tile":
            for index in (1, 2):
                if args[index].kind == "integer":
                    factor = int(args[index].value)
                    if factor < 1:
                        raise V2CompileError("cost", "E_FACTOR_POSITIVE", "tile factor must be positive", span=args[index].span, path=f"{path}[{index + 1}]")
                    if factor > self.limits.max_scale_or_tile_factor:
                        raise V2CompileError("cost", "E_TILE_BOUND", f"tile factor exceeds {self.limits.max_scale_or_tile_factor}", span=args[index].span, path=f"{path}[{index + 1}]")
        if name == "empty-grid":
            for index in (0, 1):
                dimension = args[index]
                if dimension.kind == "integer" and not 1 <= int(dimension.value) <= self.limits.max_construct_dimension:
                    raise V2CompileError(
                        "cost",
                        "E_CONSTRUCT_DIMENSION",
                        f"literal output dimension must be 1 through {self.limits.max_construct_dimension}",
                        span=dimension.span,
                        path=f"{path}[{index + 1}]",
                    )
        if name in {"quotient", "mod"} and args[1].kind == "integer" and int(args[1].value) == 0:
            raise V2CompileError("cost", "E_ZERO_DIVISOR", f"{name} divisor cannot be zero", span=args[1].span, path=f"{path}[2]")
        self.primitive_heads.add(name)
        return signature.result

    @staticmethod
    def _arity(node: Node, name: str, expected: int, actual: int, path: str) -> V2CompileError:
        return V2CompileError(
            "type",
            "E_ARITY",
            f"{name} expects {expected} arguments, found {actual}",
            span=node.span,
            path=path,
        )


def _rename(node: Node, env: Mapping[str, str], counter: list[int]) -> Node:
    if node.kind == "symbol":
        return symbol(env.get(node.text, node.text), node.span)
    if node.kind != "list" or not node.items:
        return node
    head = _head(node)
    if head == "let*":
        bindings = node.items[1]
        local = dict(env)
        renamed_bindings: list[Node] = []
        for binding in bindings.items:
            old = binding.items[0].text
            value = _rename(binding.items[1], local, counter)
            new = f"v{counter[0]}"
            counter[0] += 1
            local[old] = new
            renamed_bindings.append(list_node(symbol(new, binding.items[0].span), value, span=binding.span))
        body = _rename(node.items[2], local, counter)
        return list_node(symbol("let*", node.items[0].span), Node("list", tuple(renamed_bindings), bindings.span), body, span=node.span)
    if head == "build-grid":
        local = dict(env)
        old_r, old_c = node.items[3].items
        local[old_r.text] = "r"
        local[old_c.text] = "c"
        return list_node(
            symbol("build-grid", node.items[0].span),
            _rename(node.items[1], env, counter),
            _rename(node.items[2], env, counter),
            list_node(symbol("r"), symbol("c"), span=node.items[3].span),
            _rename(node.items[4], local, counter),
            span=node.span,
        )
    if head == "cellmap":
        local = dict(env)
        old_r, old_c, old_v = node.items[2].items
        local[old_r.text] = "r"
        local[old_c.text] = "c"
        local[old_v.text] = "v"
        return list_node(
            symbol("cellmap", node.items[0].span),
            _rename(node.items[1], env, counter),
            list_node(symbol("r"), symbol("c"), symbol("v"), span=node.items[2].span),
            _rename(node.items[3], local, counter),
            span=node.span,
        )
    return Node("list", tuple(_rename(item, env, counter) for item in node.items), node.span)


def compile_source(source: str, *, limits: CostLimits | None = None) -> CompilationResult:
    """Parse, normalize, type-check, safety-check, and lower one v2 rule."""

    limits = limits or CostLimits()
    try:
        root = parse(source, max_nodes=limits.max_nodes, max_depth=limits.max_depth,
                     max_source_chars=limits.max_source_chars,
                     max_integer_abs=limits.max_integer_abs)
    except SExprSyntaxError as error:
        raise V2CompileError(
            error.phase,
            error.code,
            error.message,
            span=error.span,
            path=error.path,
        ) from error
    nodes, depth = _measure(root)
    if nodes > limits.max_nodes:
        raise V2CompileError("cost", "E_NODE_LIMIT", f"AST has {nodes} nodes; limit is {limits.max_nodes}", span=root.span)
    if depth > limits.max_depth:
        raise V2CompileError("cost", "E_DEPTH_LIMIT", f"AST depth is {depth}; limit is {limits.max_depth}", span=root.span)

    checker = _Checker(limits)
    body, result_type = checker.check_root(root)
    normalized_body = _rename(body, {"input": "input"}, [0])
    canonical_root = list_node(symbol("rule!"), normalized_body, span=root.span)
    canonical = format_node(canonical_root)
    # Runtime diagnostics use canonical coordinates and AST paths, so whitespace
    # and author binder names cannot change the emitted program/cache key. The
    # separate map resolves those paths back to this submission's source.
    canonical_tree = parse(canonical)
    canonical_checker = _Checker(limits)
    canonical_body, _ = canonical_checker.check_root(canonical_tree)
    racket_source = format_node(lower_guarded(canonical_body, limits, canonical_checker.resolved_constants))
    entries: list[SourceMapEntry] = []
    pending = [(root, "$")]
    while pending:
        original, path = pending.pop()
        span = original.span
        entries.append(SourceMapEntry(path, span.line, span.column, span.end_line, span.end_column))
        if original.kind == "list":
            pending.extend((child, f"{path}[{i}]") for i, child in reversed(list(enumerate(original.items))))

    limits_json = json.dumps(asdict(limits), sort_keys=True, separators=(",", ":"))
    return CompilationResult(
        version=LANGUAGE_VERSION,
        canonical_source=canonical,
        racket_source=racket_source,
        result_type=result_type,
        ast_nodes=nodes,
        ast_depth=depth,
        canonical_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        primitive_heads=tuple(sorted(checker.primitive_heads)),
        limits_sha256=hashlib.sha256(limits_json.encode()).hexdigest(),
        compiled_sha256=hashlib.sha256(racket_source.encode()).hexdigest(),
        source_map=tuple(entries),
    )
