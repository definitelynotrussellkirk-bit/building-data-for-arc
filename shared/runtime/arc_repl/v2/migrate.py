"""Offline legacy-to-v2 migration for the executable core-0.1 subset."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .compiler import CompilationResult, compile_source
from .sexpr import Node, Span, format_node, list_node, parse, symbol
from .signatures import SIGNATURES
from .types import COLOR, GRID, V2Type


@dataclass(frozen=True, slots=True)
class MigrationResult:
    original_source: str
    v2_source: str
    compilation: CompilationResult


class UnsupportedMigration(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _is_symbol(node: Node, name: str | None = None) -> bool:
    return node.kind == "symbol" and (name is None or node.text == name)


def _call(name: str, *args: Node, span: Span | None = None) -> Node:
    return list_node(symbol(name), *args, span=span)


def _color(node: Node) -> Node:
    """Rewrite a legacy numeric ARC color to its explicit v2 constant."""

    if node.kind != "integer" or not 0 <= int(node.value) <= 9:
        raise UnsupportedMigration(
            "M_COLOR_LITERAL",
            "core-0.1 migration requires a literal ARC color 0 through 9",
        )
    return symbol(f"C{int(node.value)}", node.span)


def _rewrite_typed(
    node: Node,
    expected: V2Type,
    env: Mapping[str, str],
    counter: list[int],
) -> Node:
    if expected == COLOR and node.kind == "integer":
        return _color(node)
    return _rewrite(node, env, counter, expected=expected)


def _fresh_binder(counter: list[int]) -> str:
    value = f"m{counter[0]}"
    counter[0] += 1
    return value


def _legacy_delimiters_to_round(source: str) -> str:
    """Normalize Racket's interchangeable legacy delimiters for migration only.

    The model-facing v2 parser remains round-parentheses-only.  This scanner is
    deliberately separate so strings and comments cannot be rewritten, and a
    mismatched delimiter still fails rather than being guessed through.
    """

    opening = {"(": ")", "[": "]", "{": "}"}
    closing = {value: key for key, value in opening.items()}
    stack: list[str] = []
    output: list[str] = []
    in_string = False
    escaped = False
    in_comment = False
    for char in source:
        if in_comment:
            output.append(char)
            if char == "\n":
                in_comment = False
            continue
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == ";":
            in_comment = True
            output.append(char)
            continue
        if char == '"':
            in_string = True
            output.append(char)
            continue
        if char in opening:
            stack.append(char)
            output.append("(")
            continue
        if char in closing:
            if not stack or stack[-1] != closing[char]:
                raise UnsupportedMigration(
                    "M_DELIMITER_MISMATCH",
                    f"mismatched legacy delimiter {char!r}",
                )
            stack.pop()
            output.append(")")
            continue
        output.append(char)
    if stack:
        raise UnsupportedMigration(
            "M_DELIMITER_MISMATCH",
            f"unclosed legacy delimiter {stack[-1]!r}",
        )
    return "".join(output)


def _direction(node: Node) -> Node:
    if node.kind != "string":
        raise UnsupportedMigration("M_DIRECTION_LITERAL", "legacy gravity direction is not a string literal")
    mapping = {"up": "N", "right": "E", "down": "S", "left": "W"}
    if node.text not in mapping:
        raise UnsupportedMigration("M_DIRECTION_VALUE", f"unknown gravity direction {node.text!r}")
    return symbol(mapping[node.text], node.span)


def _rewrite_binding(
    node: Node,
    env: Mapping[str, str],
    counter: list[int],
    *,
    expected: V2Type | None,
) -> Node:
    name = node.items[0].text
    args = node.items[1:]
    if len(args) != 2:
        raise UnsupportedMigration(
            "M_BINDING_BODY",
            f"legacy {name} must contain one binding list and one body expression",
        )
    bindings, body = args
    if bindings.kind == "symbol":
        raise UnsupportedMigration("M_NAMED_LET", "named let is outside the migration subset")
    if bindings.kind != "list":
        raise UnsupportedMigration("M_BINDING_SHAPE", f"legacy {name} bindings are not a list")

    local = dict(env)
    rewritten: list[Node] = []
    pending: list[tuple[str, str, Node, Span]] = []
    for binding in bindings.items:
        if (
            binding.kind != "list"
            or len(binding.items) != 2
            or binding.items[0].kind != "symbol"
        ):
            raise UnsupportedMigration(
                "M_BINDING_SHAPE",
                f"legacy {name} binding is not (name expression)",
            )
        old_name = binding.items[0].text
        new_name = _fresh_binder(counter)
        value_env = local if name == "let*" else env
        value = _rewrite(binding.items[1], value_env, counter)
        pending.append((old_name, new_name, value, binding.span))
        if name == "let*":
            local[old_name] = new_name

    if name == "let":
        for old_name, new_name, _, _ in pending:
            local[old_name] = new_name
    for _, new_name, value, span in pending:
        rewritten.append(list_node(symbol(new_name), value, span=span))
    return _call(
        "let*",
        Node("list", tuple(rewritten), bindings.span),
        _rewrite(body, local, counter, expected=expected),
        span=node.span,
    )


def _rewrite_grid_builder(
    node: Node,
    env: Mapping[str, str],
    counter: list[int],
) -> Node:
    name = node.items[0].text
    args = node.items[1:]
    if name == "grid-from-fn":
        if len(args) != 3:
            raise UnsupportedMigration("M_ARITY", "grid-from-fn requires height, width, and lambda")
        height, width, function = args
        if (
            function.kind != "list"
            or len(function.items) != 3
            or not _is_symbol(function.items[0], "lambda")
            or function.items[1].kind != "list"
            or len(function.items[1].items) != 2
            or any(item.kind != "symbol" for item in function.items[1].items)
        ):
            raise UnsupportedMigration("M_GRID_LAMBDA", "grid-from-fn lambda must bind exactly two names")
        old_r, old_c = function.items[1].items
        body = function.items[2]
    else:
        if len(args) != 4:
            raise UnsupportedMigration("M_ARITY", "build-grid requires height, width, binders, and body")
        height, width, binders, body = args
        if (
            binders.kind != "list"
            or len(binders.items) != 2
            or any(item.kind != "symbol" for item in binders.items)
        ):
            raise UnsupportedMigration("M_GRID_BINDERS", "build-grid must bind exactly two names")
        old_r, old_c = binders.items
    local = dict(env)
    local[old_r.text] = "r"
    local[old_c.text] = "c"
    return _call(
        "build-grid",
        _rewrite(height, env, counter),
        _rewrite(width, env, counter),
        list_node(symbol("r"), symbol("c")),
        _rewrite_typed(body, COLOR, local, counter),
        span=node.span,
    )


def _rewrite_cellmap(
    node: Node,
    env: Mapping[str, str],
    counter: list[int],
) -> Node:
    args = node.items[1:]
    if len(args) != 3:
        raise UnsupportedMigration("M_ARITY", "cellmap requires a grid, binders, and body")
    grid, binders, body = args
    if (
        binders.kind != "list"
        or len(binders.items) != 3
        or any(item.kind != "symbol" for item in binders.items)
    ):
        raise UnsupportedMigration("M_CELLMAP_BINDERS", "cellmap must bind exactly three names")
    local = dict(env)
    for old, new in zip(binders.items, ("r", "c", "v")):
        local[old.text] = new
    return _call(
        "cellmap",
        _rewrite(grid, env, counter),
        list_node(symbol("r"), symbol("c"), symbol("v")),
        _rewrite_typed(body, COLOR, local, counter),
        span=node.span,
    )


def _fold_call(name: str, args: tuple[Node, ...], span: Span) -> Node:
    if name == "-" and len(args) == 1:
        return _call("-", Node("integer", 0, span), args[0], span=span)
    if len(args) < 2:
        raise UnsupportedMigration("M_ARITY", f"legacy {name} requires at least two arguments")
    result = _call(name, args[0], args[1], span=span)
    for arg in args[2:]:
        result = _call(name, result, arg, span=span)
    return result


def _rewrite(
    node: Node,
    env: Mapping[str, str],
    counter: list[int],
    *,
    expected: V2Type | None = None,
) -> Node:
    if node.kind in {"integer", "boolean"}:
        if expected == COLOR and node.kind == "integer":
            return _color(node)
        return node
    if node.kind == "symbol":
        mapped = env.get(node.text)
        if mapped is not None:
            return symbol(mapped, node.span)
        # ArcExecutor's legacy callable wrapper exposes these two derived
        # dimensions even when an old source only binds its grid parameter.
        # Reconstruct them explicitly in v2 instead of treating them as
        # undocumented public names.
        if node.text == "h":
            return _call("rows", symbol("input", node.span), span=node.span)
        if node.text == "w":
            return _call("cols", symbol("input", node.span), span=node.span)
        raise UnsupportedMigration("M_FREE_SYMBOL", f"unsupported free symbol {node.text}")
    if node.kind in {"string", "float"}:
        raise UnsupportedMigration("M_LITERAL", f"unsupported literal kind {node.kind}")
    if not node.items or node.items[0].kind != "symbol":
        raise UnsupportedMigration("M_CALL_SHAPE", "legacy expression is not a simple call")
    name = node.items[0].text
    args = node.items[1:]

    if name in {"let", "let*"}:
        return _rewrite_binding(node, env, counter, expected=expected)
    if name in {"letrec", "define", "set!"}:
        raise UnsupportedMigration("M_BINDING_FORM", f"legacy {name} is outside the migration subset")
    if name == "if":
        if len(args) != 3:
            raise UnsupportedMigration("M_ARITY", "legacy if requires three arguments")
        return _call(
            "if",
            _rewrite(args[0], env, counter),
            _rewrite(args[1], env, counter, expected=expected),
            _rewrite(args[2], env, counter, expected=expected),
            span=node.span,
        )
    if name in {"and", "or"}:
        rewritten = tuple(_rewrite(arg, env, counter) for arg in args)
        return _fold_call(name, rewritten, node.span)
    if name == "not":
        if len(args) != 1:
            raise UnsupportedMigration("M_ARITY", "legacy not requires one argument")
        return _call("not", _rewrite(args[0], env, counter), span=node.span)
    if name in {"grid-from-fn", "build-grid"}:
        return _rewrite_grid_builder(node, env, counter)
    if name == "cellmap":
        return _rewrite_cellmap(node, env, counter)

    unary = {
        "transpose": "transpose",
        "compress-grid": "compress-period",
        "self-tile": "self-tile",
    }
    if name in unary and len(args) == 1:
        return _call(unary[name], _rewrite(args[0], env, counter), span=node.span)
    if name == "flip-lr" and len(args) == 1:
        return _call("mirror", _rewrite(args[0], env, counter), symbol("LR"), span=node.span)
    if name == "flip-ud" and len(args) == 1:
        return _call("mirror", _rewrite(args[0], env, counter), symbol("UD"), span=node.span)
    rotate = {"rotate-cw": "CW", "rotate-ccw": "CCW", "rotate-180": "R180"}
    if name in rotate and len(args) == 1:
        return _call("rotate", _rewrite(args[0], env, counter), symbol(rotate[name]), span=node.span)
    if name == "overlay" and len(args) in {2, 3}:
        bg = _color(args[2]) if len(args) == 3 else symbol("C0")
        return _call("overlay", _rewrite(args[0], env, counter), _rewrite(args[1], env, counter), bg, span=node.span)
    if name == "gravity" and len(args) in {2, 3}:
        bg = _color(args[2]) if len(args) == 3 else symbol("C0")
        return _call("pack", _rewrite(args[0], env, counter), _direction(args[1]), bg, span=node.span)
    if name == "crop-to-content" and len(args) in {1, 2}:
        bg = _color(args[1]) if len(args) == 2 else symbol("C0")
        return _call("crop-content", _rewrite(args[0], env, counter), bg, span=node.span)
    if name == "upscale" and len(args) == 2:
        return _call("scale-up", _rewrite(args[0], env, counter), _rewrite(args[1], env, counter), span=node.span)
    if name == "downscale" and len(args) == 2:
        return _call("scale-down", _rewrite(args[0], env, counter), _rewrite(args[1], env, counter), span=node.span)
    if name == "fill-all-enclosed" and len(args) in {2, 3}:
        bg = _color(args[2]) if len(args) == 3 else symbol("C0")
        return _call("fill-holes", _rewrite(args[0], env, counter), _color(args[1]), bg, span=node.span)
    if name == "hconcat" and len(args) == 2:
        return _call("concat", symbol("H"), _rewrite(args[0], env, counter), _rewrite(args[1], env, counter), span=node.span)
    if name == "vconcat" and len(args) == 2:
        return _call("concat", symbol("V"), _rewrite(args[0], env, counter), _rewrite(args[1], env, counter), span=node.span)
    if name in {"+", "-", "*", "min", "max"}:
        rewritten = tuple(_rewrite(arg, env, counter) for arg in args)
        return _fold_call(name, rewritten, node.span)
    direct = {
        "tile": "tile",
        "recolor": "recolor",
        "swap-colors": "swap-colors",
        "at": "at",
        "set-cell": "set-cell",
        "rows": "rows",
        "cols": "cols",
        "empty-grid": "empty-grid",
        "subgrid": "subgrid",
        "blank-like": "blank-like",
        "quotient": "quotient",
        "mod": "mod",
        "=": "=",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
        "zero?": "zero?",
    }
    if name in direct:
        target = direct[name]
        signature = SIGNATURES[target]
        if len(args) != signature.arity:
            raise UnsupportedMigration(
                "M_ARITY",
                f"legacy {name} has {len(args)} arguments; v2 {target} requires {signature.arity}",
            )
        return _call(
            target,
            *[
                _rewrite_typed(arg, parameter_type, env, counter)
                for arg, parameter_type in zip(args, signature.params)
            ],
            span=node.span,
        )
    raise UnsupportedMigration("M_UNSUPPORTED_HEAD", f"unsupported legacy head {name}")


def migrate_legacy_source(source: str) -> MigrationResult:
    """Migrate one behavior-preserving legacy rule in the supported subset."""

    root = parse(_legacy_delimiters_to_round(source))
    if root.kind != "list" or len(root.items) != 2 or not _is_symbol(root.items[0], "rule!"):
        raise UnsupportedMigration("M_RULE_WRAPPER", "legacy source is not one (rule! expression)")
    expression = root.items[1]
    if expression.kind == "symbol":
        # Callable-form legacy rules such as `(rule! transpose)`.
        expression = _call(expression.text, symbol("input"), span=expression.span)
        env = {"input": "input"}
    elif expression.kind == "list" and expression.items and _is_symbol(expression.items[0], "lambda"):
        if len(expression.items) != 3:
            raise UnsupportedMigration("M_LAMBDA_BODY", "lambda must have exactly one body expression")
        params = expression.items[1]
        if params.kind != "list" or len(params.items) != 1 or params.items[0].kind != "symbol":
            raise UnsupportedMigration("M_LAMBDA_PARAMS", "lambda must bind exactly one input")
        expression = expression.items[2]
        env = {params.items[0].text: "input", "input": "input"}
    else:
        # Body-form legacy rules use the executor's auto-bound `g`.
        env = {"g": "input", "input": "input"}
    v2_body = _rewrite(expression, env, [0], expected=GRID)
    v2_source = format_node(_call("rule!", v2_body))
    compilation = compile_source(v2_source)
    return MigrationResult(source, v2_source, compilation)
